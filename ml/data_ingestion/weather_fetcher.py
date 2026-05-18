import os
import math
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY")



# Encode wind direction as sin/cos
def encode_wind_direction(degrees: float) -> tuple[float, float]:
    """
    Convert wind direction degrees to sin/cos pair.
    Avoids the 0°/360° discontinuity issue in ML models.
    e.g. 0° and 359° are actually 1° apart but numerically far — this fixes that.
    """
    radians = math.radians(degrees)
    return math.sin(radians), math.cos(radians)



# Fetch current weather for a city
def fetch_current_weather(city_name: str, lat: float, lon: float) -> dict | None:
    """
    Fetch current weather conditions for a city by coordinates.
    Using lat/lon is more precise than city name (avoids wrong city matches).
    """
    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",    # Celsius, m/s
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        wind_deg = data.get("wind", {}).get("deg", 0)
        wind_sin, wind_cos = encode_wind_direction(wind_deg)

        record = {
            "city":                 city_name.lower(),
            "timestamp_utc":        pd.to_datetime(data.get("dt"), unit="s", utc=True),
            "temperature_c":        data.get("main", {}).get("temp"),
            "humidity_pct":         data.get("main", {}).get("humidity"),
            "wind_speed_ms":        data.get("wind", {}).get("speed"),
            "wind_direction_deg":   wind_deg,
            "wind_sin":             wind_sin,
            "wind_cos":             wind_cos,
            "rainfall_1h_mm":       data.get("rain", {}).get("1h", 0.0),
            "pressure_hpa":         data.get("main", {}).get("pressure"),
            "visibility_m":         data.get("visibility"),
            "weather_description":  data.get("weather", [{}])[0].get("description", ""),
            "source":               "openweathermap"
        }

        logger.info(f"Fetched weather for {city_name}: {record['temperature_c']}°C, "
                    f"humidity {record['humidity_pct']}%")
        return record

    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error fetching weather for {city_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch weather for {city_name}: {e}")
        return None



# Fetch 5-day / 3-hour forecast
# (Used to give the model future weather context)
def fetch_weather_forecast(city_name: str, lat: float, lon: float) -> pd.DataFrame:
    """
    Fetch 5-day weather forecast in 3-hour steps.
    Gives the model weather context for future predictions.
    """
    url = f"{OPENWEATHER_BASE_URL}/forecast"
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        records = []
        for item in data.get("list", []):
            wind_deg = item.get("wind", {}).get("deg", 0)
            wind_sin, wind_cos = encode_wind_direction(wind_deg)

            records.append({
                "city":                 city_name.lower(),
                "timestamp_utc":        pd.to_datetime(item.get("dt"), unit="s", utc=True),
                "temperature_c":        item.get("main", {}).get("temp"),
                "humidity_pct":         item.get("main", {}).get("humidity"),
                "wind_speed_ms":        item.get("wind", {}).get("speed"),
                "wind_direction_deg":   wind_deg,
                "wind_sin":             wind_sin,
                "wind_cos":             wind_cos,
                "rainfall_1h_mm":       item.get("rain", {}).get("3h", 0.0),
                "pressure_hpa":         item.get("main", {}).get("pressure"),
                "weather_description":  item.get("weather", [{}])[0].get("description", ""),
                "source":               "openweathermap_forecast"
            })

        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} forecast steps for {city_name}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch forecast for {city_name}: {e}")
        return pd.DataFrame()



# Main fetch function (called by scheduler)
def fetch_all_cities_weather(cities_config: dict) -> pd.DataFrame:
    """
    Fetch current weather for all cities in one pass.
    cities_config comes from cities.yaml parsed as a dict.
    """
    records = []

    for city_key, city_data in cities_config.items():
        record = fetch_current_weather(
            city_name=city_key,
            lat=city_data["latitude"],
            lon=city_data["longitude"]
        )
        if record:
            records.append(record)

    if not records:
        logger.warning("No weather data fetched for any city")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    logger.success(f"Weather fetched for {len(df)} cities")
    return df