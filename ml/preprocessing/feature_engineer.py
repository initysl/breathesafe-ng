import pandas as pd
import numpy as np
from loguru import logger



# Compute AQI from PM2.5 (EPA formula)
# This is the standard used globally


# EPA AQI breakpoints for PM2.5 (µg/m³)
PM25_BREAKPOINTS = [
    (0.0,   12.0,   0,   50),
    (12.1,  35.4,   51,  100),
    (35.5,  55.4,   101, 150),
    (55.5,  150.4,  151, 200),
    (150.5, 250.4,  201, 300),
    (250.5, 350.4,  301, 400),
    (350.5, 500.4,  401, 500),
]

def compute_aqi_from_pm25(pm25: float) -> float:
    """Convert PM2.5 concentration to AQI value using EPA formula."""
    if pm25 < 0:
        return 0.0

    for c_low, c_high, i_low, i_high in PM25_BREAKPOINTS:
        if c_low <= pm25 <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low
            return round(aqi, 1)

    return 500.0   # Hazardous ceiling


def get_aqi_category(aqi: float) -> str:
    """Map AQI value to health category label."""
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy for Sensitive Groups"
    if aqi <= 200:  return "Unhealthy"
    if aqi <= 300:  return "Very Unhealthy"
    return "Hazardous"



# Is Harmattan season?

def is_harmattan(timestamp: pd.Timestamp) -> bool:
    """Flag October–February as harmattan season."""
    return timestamp.month in [10, 11, 12, 1, 2]



# Pivot AQI readings: one row per city/hour

def pivot_aqi_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert long-format AQI data (one row per reading)
    to wide format (one row per city/timestamp, columns per pollutant).
    """
    df_pivot = df.pivot_table(
        index=["city", "timestamp_utc"],
        columns="parameter",
        values="value",
        aggfunc="mean"
    ).reset_index()

    df_pivot.columns.name = None

    # Rename columns for clarity
    df_pivot = df_pivot.rename(columns={
        "pm25": "pm25",
        "pm10": "pm10",
        "no2":  "no2",
        "o3":   "o3",
        "co":   "co",
        "so2":  "so2",
    })

    return df_pivot



# Build time features
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical and categorical time-based features."""
    df = df.copy()
    ts = pd.to_datetime(df["timestamp_utc"])

    df["hour_of_day"]  = ts.dt.hour
    df["day_of_week"]  = ts.dt.dayofweek     # 0=Monday, 6=Sunday
    df["month"]        = ts.dt.month
    df["is_weekend"]   = ts.dt.dayofweek >= 5
    df["is_harmattan"] = ts.apply(is_harmattan)

    # Cyclical encoding for hour (so 23 and 0 are close, not far)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)

    # Cyclical encoding for month
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df



# Build lag and rolling features
def add_lag_features(df: pd.DataFrame, city: str) -> pd.DataFrame:
    """
    Add lag values and rolling statistics for a single city.
    Must be applied per-city (not across cities).
    """
    df = df.copy().sort_values("timestamp_utc")

    LAG_HOURS    = [1, 3, 6, 12, 24, 48]
    ROLLING_WINS = [6, 12, 24]

    # PM2.5 lags
    for h in LAG_HOURS:
        df[f"pm25_lag_{h}h"] = df["pm25"].shift(h)

    # AQI lags
    for h in [1, 6, 24]:
        df[f"aqi_lag_{h}h"] = df["aqi_value"].shift(h)

    # Rolling statistics for PM2.5
    for w in ROLLING_WINS:
        df[f"pm25_rolling_{w}h_mean"] = df["pm25"].rolling(w, min_periods=1).mean()
        df[f"pm25_rolling_{w}h_std"]  = df["pm25"].rolling(w, min_periods=1).std()

    # Rolling max (useful for catching pollution spikes)
    df["pm25_rolling_24h_max"] = df["pm25"].rolling(24, min_periods=1).max()

    logger.debug(f"Added lag + rolling features for {city}")
    return df



# Full feature engineering pipeline
def build_features( aqi_df: pd.DataFrame, weather_df: pd.DataFrame, city: str) -> pd.DataFrame:
    """
    Full feature engineering pipeline for one city.
    1. Pivot AQI wide
    2. Compute AQI value + category
    3. Merge with weather
    4. Add time features
    5. Add lag + rolling features
    """
    logger.info(f"Building features for {city}")

    # Step 1: Pivot AQI wide
    aqi_city = aqi_df[aqi_df["city"] == city].copy()
    weather_city = weather_df[weather_df["city"] == city].copy()

    if aqi_city.empty:
        logger.warning(f"No AQI data for {city}")
        return pd.DataFrame()

    df = pivot_aqi_wide(aqi_city)

    # Step 2: Compute AQI value
    if "pm25" in df.columns:
        df["aqi_value"]    = df["pm25"].apply(
            lambda x: compute_aqi_from_pm25(x) if pd.notna(x) else np.nan
        )
        df["aqi_category"] = df["aqi_value"].apply(
            lambda x: get_aqi_category(x) if pd.notna(x) else None
        )
    else:
        logger.warning(f"No PM2.5 data for {city} — AQI cannot be computed")
        df["aqi_value"]    = np.nan
        df["aqi_category"] = None

    # Step 3: Merge with weather
    if not weather_city.empty:
        weather_cols = [
            "timestamp_utc", "temperature_c", "humidity_pct",
            "wind_speed_ms", "wind_sin", "wind_cos",
            "rainfall_1h_mm", "pressure_hpa"
        ]
        weather_city = weather_city[[c for c in weather_cols if c in weather_city.columns]]

        # Round timestamps to nearest hour before merging
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"]).dt.round("h")
        weather_city["timestamp_utc"] = pd.to_datetime(weather_city["timestamp_utc"]).dt.round("h")

        df = pd.merge(df, weather_city, on="timestamp_utc", how="left")
    else:
        logger.warning(f"No weather data for {city} — proceeding without weather features")

    # Step 4: Time features
    df = add_time_features(df)

    # Step 5: Lag + rolling features
    df = add_lag_features(df, city)

    df["city"] = city
    logger.success(f"Features built for {city}: {len(df)} rows, {len(df.columns)} features")
    return df