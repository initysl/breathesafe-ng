import pandas as pd
import numpy as np
from loguru import logger



# Physical limits for pollutants: Values outside these are sensor errors
POLLUTANT_LIMITS = {
    "pm25":  (0, 1000),    # µg/m³
    "pm10":  (0, 2000),    # µg/m³
    "no2":   (0, 2000),    # µg/m³
    "o3":    (0, 600),     # µg/m³
    "co":    (0, 50000),   # µg/m³ (or ppm × 1000)
    "so2":   (0, 2000),    # µg/m³
}

WEATHER_LIMITS = {
    "temperature_c":   (-10, 55),    # Nigeria range
    "humidity_pct":    (0, 100),
    "wind_speed_ms":   (0, 50),
    "pressure_hpa":    (900, 1100),
    "rainfall_1h_mm":  (0, 200),
}



# Normalize units to µg/m³
# OpenAQ sometimes returns ppm for CO

PPM_TO_UGM3 = {
    "co":  1145,    # 1 ppm CO = 1145 µg/m³ at 25°C
    "so2": 2620,    # 1 ppm SO₂ = 2620 µg/m³
    "no2": 1880,    # 1 ppm NO₂ = 1880 µg/m³
    "o3":  1960,    # 1 ppm O₃ = 1960 µg/m³
}

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert ppm readings to µg/m³ for consistency."""
    df = df.copy()

    ppm_mask = df["unit"].str.lower().isin(["ppm", "ppb"])
    if not ppm_mask.any():
        return df

    for parameter, conversion in PPM_TO_UGM3.items():
        mask = ppm_mask & (df["parameter"] == parameter)
        if mask.any():
            # PPB = PPM / 1000, so handle both
            ppb_mask = mask & (df["unit"].str.lower() == "ppb")
            df.loc[ppb_mask, "value"] = df.loc[ppb_mask, "value"] * conversion / 1000
            ppm_only_mask = mask & (df["unit"].str.lower() == "ppm")
            df.loc[ppm_only_mask, "value"] = df.loc[ppm_only_mask, "value"] * conversion
            df.loc[mask, "unit"] = "µg/m³"

    logger.debug(f"Normalized {ppm_mask.sum()} ppm/ppb readings to µg/m³")
    return df



# Remove physically impossible values
def remove_outliers(df: pd.DataFrame, data_type: str = "aqi") -> pd.DataFrame:
    """Remove readings that are physically impossible (sensor errors)."""
    df = df.copy()
    original_len = len(df)

    if data_type == "aqi":
        limits = POLLUTANT_LIMITS
        value_col = "value"
        param_col = "parameter"

        for parameter, (min_val, max_val) in limits.items():
            mask = (df[param_col] == parameter) & (
                (df[value_col] < min_val) | (df[value_col] > max_val)
            )
            if mask.any():
                logger.warning(f"Removing {mask.sum()} outlier readings for {parameter}")
                df = df[~mask]

    elif data_type == "weather":
        for col, (min_val, max_val) in WEATHER_LIMITS.items():
            if col in df.columns:
                mask = (df[col] < min_val) | (df[col] > max_val)
                if mask.any():
                    logger.warning(f"Clipping {mask.sum()} outliers in {col}")
                    df[col] = df[col].clip(min_val, max_val)

    removed = original_len - len(df)
    if removed > 0:
        logger.info(f"Removed {removed} outlier records")

    return df



# Handle missing values
def handle_missing_values(df: pd.DataFrame, method: str = "interpolate") -> pd.DataFrame:
    """
    Handle missing sensor readings.
    - interpolate: fill gaps using time-based interpolation (default)
    - forward_fill: carry last known value forward (max 3 hours)
    - drop: remove rows with missing values
    """
    df = df.copy()
    missing_before = df.isnull().sum().sum()

    if missing_before == 0:
        return df

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if method == "interpolate":
        # Time-based interpolation — best for sensor gaps up to ~6 hours
        df[numeric_cols] = df[numeric_cols].interpolate(
            method="time", limit=6, limit_direction="forward"
        )
    elif method == "forward_fill":
        # Only fill forward up to 3 readings (3 hours if hourly data)
        df[numeric_cols] = df[numeric_cols].ffill(limit=3)
    elif method == "drop":
        df = df.dropna(subset=numeric_cols)

    missing_after = df.isnull().sum().sum()
    logger.info(f"Missing values: {missing_before} → {missing_after} (method: {method})")

    return df



# Full cleaning pipeline
def clean_aqi_data(df: pd.DataFrame) -> pd.DataFrame:
    """Run full cleaning pipeline on raw AQI data."""
    if df.empty:
        return df

    logger.info(f"Cleaning AQI data: {len(df)} records")
    df = normalize_units(df)
    df = remove_outliers(df, data_type="aqi")
    df = df.drop_duplicates(subset=["city", "parameter", "timestamp_utc"])
    df = df.sort_values(["city", "parameter", "timestamp_utc"])
    logger.success(f"Cleaned AQI data: {len(df)} records remaining")
    return df


def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """Run full cleaning pipeline on raw weather data."""
    if df.empty:
        return df

    logger.info(f"Cleaning weather data: {len(df)} records")
    df = remove_outliers(df, data_type="weather")
    df = df.drop_duplicates(subset=["city", "timestamp_utc"])
    df = df.sort_values(["city", "timestamp_utc"])
    logger.success(f"Cleaned weather data: {len(df)} records remaining")
    return df