import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from loguru import logger



# City pollution profiles
CITY_PROFILES = {
    "lagos": {
        "base_pm25":       35.0,
        "base_pm10":       55.0,
        "traffic_factor":  1.8,    # Heavy traffic
        "industrial":      True,
        "noise_std":       12.0,
    },
    "abuja": {
        "base_pm25":       22.0,
        "base_pm10":       38.0,
        "traffic_factor":  1.3,
        "industrial":      False,
        "noise_std":       8.0,
    },
    "kano": {
        "base_pm25":       45.0,
        "base_pm10":       80.0,
        "traffic_factor":  1.4,
        "industrial":      True,
        "noise_std":       15.0,
    },
    "port_harcourt": {
        "base_pm25":       40.0,
        "base_pm10":       65.0,
        "traffic_factor":  1.5,
        "industrial":      True,
        "noise_std":       14.0,
    },
    "ibadan": {
        "base_pm25":       28.0,
        "base_pm10":       48.0,
        "traffic_factor":  1.4,
        "industrial":      False,
        "noise_std":       10.0,
    },
    "osogbo": {
        "base_pm25":       20.0,
        "base_pm10":       35.0,
        "traffic_factor":  1.1,
        "industrial":      False,
        "noise_std":       7.0,
    },
}

# Hour-of-day pollution multipliers (rush hours = higher)
HOURLY_PATTERN = {
    0: 0.6, 1: 0.5, 2: 0.5, 3: 0.5, 4: 0.6, 5: 0.7,
    6: 0.9, 7: 1.3, 8: 1.5, 9: 1.4, 10: 1.2, 11: 1.1,
    12: 1.0, 13: 1.0, 14: 1.0, 15: 1.1, 16: 1.3, 17: 1.6,
    18: 1.5, 19: 1.3, 20: 1.1, 21: 0.9, 22: 0.8, 23: 0.7,
}


def is_harmattan(month: int) -> bool:
    return month in [10, 11, 12, 1, 2]


def harmattan_multiplier(month: int, city: str) -> float:
    """Harmattan effect varies by city location."""
    if not is_harmattan(month):
        return 1.0
    multipliers = {
        "kano":          2.8,
        "abuja":         2.2,
        "ibadan":        1.6,
        "lagos":         1.4,
        "osogbo":        1.5,
        "port_harcourt": 1.1,
    }
    return multipliers.get(city, 1.5)


def generate_city_data(city: str, days: int = 90) -> pd.DataFrame:
    """
    Generate synthetic hourly AQI data for a city.
    90 days default gives enough data for model training.
    """
    profile = CITY_PROFILES.get(city, CITY_PROFILES["abuja"])
    logger.info(f"Generating {days} days of synthetic data for {city}")

    end_dt   = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=days)
    timestamps = pd.date_range(start=start_dt, end=end_dt, freq="h", tz="UTC")

    records = []
    prev_pm25 = profile["base_pm25"]   # track autocorrelation

    for ts in timestamps:
        hour   = ts.hour
        month  = ts.month
        dow    = ts.dayofweek
        is_wkd = dow >= 5

        # --- PM2.5 ---
        hourly_mult    = HOURLY_PATTERN[hour]
        harmattan_mult = harmattan_multiplier(month, city)
        weekend_factor = 0.75 if is_wkd else 1.0
        noise          = np.random.normal(0, profile["noise_std"])

        # Autocorrelation — next reading influenced by previous (realistic)
        pm25 = (
            0.6 * prev_pm25 +
            0.4 * (profile["base_pm25"] * hourly_mult * harmattan_mult * weekend_factor) +
            noise
        )
        pm25 = max(0.0, pm25)
        prev_pm25 = pm25

        # --- Other pollutants correlated with PM2.5 ---
        pm10 = pm25 * 1.6 + np.random.normal(0, 5)
        no2  = pm25 * 0.4 + np.random.normal(0, 3)
        o3   = max(0, 40 - pm25 * 0.1 + np.random.normal(0, 5))  # inversely related
        co   = pm25 * 0.08 + np.random.normal(0, 0.5)
        so2  = pm25 * 0.05 + np.random.normal(0, 2) if profile["industrial"] else pm25 * 0.02

        # --- Weather ---
        base_temp  = 28 + 5 * np.sin(2 * np.pi * (month - 3) / 12)
        temp       = base_temp + np.random.normal(0, 2) + (3 if hour in range(12, 16) else 0)
        humidity   = max(10, min(100, 70 - (temp - 28) * 2 + np.random.normal(0, 8)))
        wind_speed = max(0, np.random.gamma(2, 1.5))
        wind_dir   = np.random.uniform(0, 360)
        rainfall   = max(0, np.random.exponential(0.5) if month in [4,5,6,7,8,9,10] else 0)
        pressure   = 1013 + np.random.normal(0, 3)

        import math
        wind_sin = math.sin(math.radians(wind_dir))
        wind_cos = math.cos(math.radians(wind_dir))

        records.append({
            "city":               city,
            "timestamp_utc":      ts,
            "pm25":               round(max(0, pm25), 2),
            "pm10":               round(max(0, pm10), 2),
            "no2":                round(max(0, no2), 2),
            "o3":                 round(max(0, o3), 2),
            "co":                 round(max(0, co), 3),
            "so2":                round(max(0, so2), 2),
            "temperature_c":      round(temp, 1),
            "humidity_pct":       round(humidity, 1),
            "wind_speed_ms":      round(wind_speed, 2),
            "wind_sin":           round(wind_sin, 4),
            "wind_cos":           round(wind_cos, 4),
            "rainfall_1h_mm":     round(rainfall, 2),
            "pressure_hpa":       round(pressure, 1),
            "hour_of_day":        hour,
            "day_of_week":        dow,
            "month":              month,
            "is_weekend":         is_wkd,
            "is_harmattan":       is_harmattan(month),
        })

    df = pd.DataFrame(records)
    logger.success(f"Generated {len(df)} synthetic records for {city}")
    return df


def generate_all_cities(days: int = 90) -> pd.DataFrame:
    """Generate synthetic data for all cities."""
    frames = [generate_city_data(city, days) for city in CITY_PROFILES.keys()]
    df = pd.concat(frames, ignore_index=True)
    logger.success(f"Total synthetic records: {len(df)}")
    return df