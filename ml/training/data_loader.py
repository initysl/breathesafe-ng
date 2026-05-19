import os
import pandas as pd
import numpy as np
from loguru import logger
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

MIN_SAMPLES_REQUIRED = 720   # 30 days * 24 hours


def load_from_supabase(city: str) -> pd.DataFrame:
    """Pull processed features from Supabase for a city."""
    try:
        from supabase import create_client
        from config.settings import SUPABASE_URL, SUPABASE_KEY
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        response = (
            supabase.table("processed_features")
            .select("*")
            .eq("city", city)
            .order("timestamp_utc", desc=False)
            .execute()
        )
        df = pd.DataFrame(response.data)
        logger.info(f"Loaded {len(df)} records from Supabase for {city}")
        return df
    except Exception as e:
        logger.warning(f"Could not load from Supabase: {e}")
        return pd.DataFrame()


def load_training_data(city: str, use_synthetic_if_sparse: bool = True) -> tuple[pd.DataFrame, str]:
    """
    Load training data for a city.
    Returns (dataframe, source) where source is 'real', 'synthetic', or 'mixed'.
    """
    real_df = load_from_supabase(city)

    if len(real_df) >= MIN_SAMPLES_REQUIRED:
        logger.success(f"Using real data for {city}: {len(real_df)} records")
        return real_df, "real"

    if not use_synthetic_if_sparse:
        logger.warning(f"Insufficient real data for {city} and synthetic fallback disabled")
        return real_df, "real"

    # Not enough real data — generate synthetic
    from training.synthetic_data import generate_city_data
    synthetic_df = generate_city_data(city, days=90)

    if real_df.empty:
        logger.info(f"No real data for {city} — using 100% synthetic data")
        return synthetic_df, "synthetic"

    # Mix real + synthetic
    logger.info(f"Mixing {len(real_df)} real + {len(synthetic_df)} synthetic records for {city}")
    combined = pd.concat([synthetic_df, real_df], ignore_index=True)
    combined = combined.sort_values("timestamp_utc").reset_index(drop=True)
    return combined, "mixed"


def prepare_features_and_targets(
    df: pd.DataFrame,
    horizon_hours: int = 1
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Prepare X (features) and y (target) for model training.
    Target: AQI value N hours into the future.
    """
    df = df.copy().sort_values("timestamp_utc").reset_index(drop=True)

    # Compute AQI if not already present
    if "aqi_value" not in df.columns and "pm25" in df.columns:
        from preprocessing.feature_engineer import compute_aqi_from_pm25
        df["aqi_value"] = df["pm25"].apply(
            lambda x: compute_aqi_from_pm25(x) if pd.notna(x) else np.nan
        )

    # Build lag features if not present
    if "pm25_lag_1h" not in df.columns and "pm25" in df.columns:
        from preprocessing.feature_engineer import add_lag_features
        df = add_lag_features(df, city=df["city"].iloc[0] if "city" in df.columns else "unknown")

    if "hour_of_day" not in df.columns:
        from preprocessing.feature_engineer import add_time_features
        df = add_time_features(df)

    # Target = AQI N hours ahead
    df["target"] = df["aqi_value"].shift(-horizon_hours)

    # Drop rows where target is NaN
    df = df.dropna(subset=["target", "aqi_value"])

    # Feature columns
    FEATURE_COLS = [
        # Pollutants
        "pm25", "pm10", "no2", "o3", "co", "so2",
        # Weather
        "temperature_c", "humidity_pct", "wind_speed_ms",
        "wind_sin", "wind_cos", "rainfall_1h_mm", "pressure_hpa",
        # Time
        "hour_of_day", "day_of_week", "month",
        "is_weekend", "is_harmattan",
        # Lag features
        "pm25_lag_1h", "pm25_lag_3h", "pm25_lag_6h",
        "pm25_lag_12h", "pm25_lag_24h",
        "aqi_lag_1h", "aqi_lag_6h", "aqi_lag_24h",
        # Rolling features
        "pm25_rolling_6h_mean", "pm25_rolling_12h_mean",
        "pm25_rolling_24h_mean", "pm25_rolling_24h_max",
    ]

    # Only use columns that exist in the dataframe
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    missing = set(FEATURE_COLS) - set(available_features)
    if missing:
        logger.warning(f"Missing features (will skip): {missing}")

    X = df[available_features].copy()
    y = df["target"].copy()

    # Boolean columns → int
    for col in ["is_weekend", "is_harmattan"]:
        if col in X.columns:
            X[col] = X[col].astype(int)

    # Drop rows with any NaN in features
    valid_mask = X.notna().all(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]

    logger.info(f"Training data ready: {len(X)} samples, {len(X.columns)} features")
    return X, y