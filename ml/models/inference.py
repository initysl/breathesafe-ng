import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger


ML_ROOT   = Path(__file__).resolve().parent.parent
ARTIFACTS = ML_ROOT / "artifacts"


# Load latest model for a city + horizon
def load_latest_model(city: str, horizon: int) -> tuple:
    """
    Load the most recently trained model for a city and horizon.
    Returns (model, scaler, feature_cols, version).
    """
    # Find all meta files for this city + horizon
    pattern    = f"meta_{city}_{horizon}h_*.json"
    meta_files = sorted(ARTIFACTS.glob(pattern))

    if not meta_files:
        raise FileNotFoundError(
            f"No trained model found for {city} {horizon}h. "
            f"Run training/train_xgboost.py first."
        )

    # Latest = last alphabetically (timestamps in filename)
    latest_meta = meta_files[-1]

    with open(latest_meta) as f:
        meta = json.load(f)

    model_path  = ARTIFACTS / meta["model_file"]
    scaler_path = ARTIFACTS / meta["scaler_file"]

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    logger.info(f"Loaded model: {meta['model_file']} (v{meta['version']})")
    return model, scaler, meta["feature_cols"], meta["version"]


# Build feature row from latest city data
def build_inference_row(city: str, feature_cols: list) -> pd.DataFrame:
    """
    Pull the latest processed features for a city from Supabase
    and return a single-row DataFrame ready for model input.
    """
    try:
        import os
        from supabase import create_client
        from config.settings import SUPABASE_URL, SUPABASE_KEY

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        response = (
            supabase.table("processed_features")
            .select("*")
            .eq("city", city)
            .order("timestamp_utc", desc=True)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise ValueError(f"No processed features found for {city}")

        row = pd.DataFrame(response.data)

        # Keep only the feature columns the model was trained on
        available = [c for c in feature_cols if c in row.columns]
        row = row[available]

        return row

    except Exception as e:
        logger.error(f"Failed to build inference row for {city}: {e}")
        raise


# Generate forecast for one city
def forecast_city(city: str, horizons: list[int] = [1, 6, 12, 24]) -> list[dict]:
    """
    Generate AQI forecasts for a city across all horizons.
    Returns list of forecast dicts ready to save to aqi_forecasts table.
    """
    from preprocessing.feature_engineer import get_aqi_category

    forecasts = []
    now = datetime.now(timezone.utc)

    for horizon in horizons:
        try:
            model, scaler, feature_cols, version = load_latest_model(city, horizon)
            row = build_inference_row(city, feature_cols)

            # Scale
            row_scaled = pd.DataFrame(
                scaler.transform(row),
                columns=row.columns
            )

            # Predict
            predicted_aqi = float(model.predict(row_scaled)[0])
            predicted_aqi = round(np.clip(predicted_aqi, 0, 500), 1)
            category      = get_aqi_category(predicted_aqi)

            forecast = {
                "city":               city,
                "forecast_made_at":   now.isoformat(),
                "forecast_for":       (now + pd.Timedelta(hours=horizon)).isoformat(),
                "horizon_hours":      horizon,
                "predicted_aqi":      predicted_aqi,
                "predicted_category": category,
                "model_version":      version,
            }
            forecasts.append(forecast)
            logger.info(f"{city} +{horizon}h → AQI {predicted_aqi} ({category})")

        except Exception as e:
            logger.error(f"Forecast failed for {city} {horizon}h: {e}")

    return forecasts


# Save forecasts to Supabase
def save_forecasts(forecasts: list[dict]) -> int:
    """Save forecast results to aqi_forecasts table."""
    if not forecasts:
        return 0
    try:
        import os
        from supabase import create_client
        from config.settings import SUPABASE_URL, SUPABASE_KEY

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table("aqi_forecasts").insert(forecasts).execute()
        logger.success(f"Saved {len(forecasts)} forecasts to Supabase")
        return len(forecasts)
    except Exception as e:
        logger.error(f"Failed to save forecasts: {e}")
        return 0


# Run forecast for all cities
def run_all_forecasts(cities: list[str]) -> list[dict]:
    """Generate and save forecasts for all cities. Called hourly by scheduler."""
    if cities is None:
        cities = ["abuja", "lagos", "kano", "port_harcourt", "ibadan", "osogbo"]

    all_forecasts = []
    for city in cities:
        forecasts = forecast_city(city)
        all_forecasts.extend(forecasts)

    save_forecasts(all_forecasts)
    return all_forecasts