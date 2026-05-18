import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from loguru import logger
from typing import Optional

load_dotenv()

OPENAQ_BASE_URL = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.io/v3")
OPENAQ_API_KEY  = os.getenv("OPENAQ_API_KEY")

HEADERS = {
    "X-API-Key": OPENAQ_API_KEY,
    "Accept": "application/json"
}

# Pollutants we care about
TARGET_PARAMETERS = ["pm25", "pm10", "no2", "o3", "co", "so2"]



# Discover location IDs for Nigerian cities (Run this once to find your real IDs)
def discover_locations(city_name: str, country_code: str = "NG") -> list[dict]:
    """
    Find OpenAQ location IDs for a city.
    Run this once per city to get real location IDs,
    then hardcode them in cities.yaml.
    """
    url = f"{OPENAQ_BASE_URL}/locations"
    params = {
        "country_id": country_code,
        "city":       city_name,
        "limit":      10,
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        locations = data.get("results", [])
        logger.info(f"Found {len(locations)} locations in {city_name}")
        return locations
    except Exception as e:
        logger.error(f"Failed to discover locations for {city_name}: {e}")
        return []



# Fetch latest readings for a location
def fetch_latest_readings(location_id: int) -> list[dict]:
    """Fetch the latest pollutant readings for a specific location ID."""
    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/latest"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error for location {location_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching readings for location {location_id}: {e}")
        return []



# Fetch historical readings (for backfilling)
def fetch_historical_readings(
    location_id: int,
    date_from: datetime,
    date_to: datetime,
    parameter: Optional[str] = None
) -> list[dict]:
    """
    Fetch historical readings for a location over a date range.
    Use this for initial data backfill (last 30 days).
    """
    url = f"{OPENAQ_BASE_URL}/measurements"
    params = {
        "location_id":  location_id,
        "date_from":    date_from.isoformat(),
        "date_to":      date_to.isoformat(),
        "limit":        1000,
    }
    if parameter:
        params["parameter"] = parameter

    all_results = []
    page = 1

    while True:
        params["page"] = page
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            if not results:
                break

            all_results.extend(results)
            logger.debug(f"Page {page}: fetched {len(results)} records for location {location_id}")

            # Respect rate limits
            time.sleep(0.5)
            page += 1

        except Exception as e:
            logger.error(f"Error on page {page} for location {location_id}: {e}")
            break

    return all_results



# Parse raw OpenAQ results → clean DataFrame
def parse_readings(raw_results: list[dict], city: str) -> pd.DataFrame:
    """
    Convert raw OpenAQ API results into a clean DataFrame
    ready for database insertion.
    """
    records = []

    for result in raw_results:
        parameter = result.get("parameter", "")

        # Only keep parameters we care about
        if parameter not in TARGET_PARAMETERS:
            continue

        value = result.get("value")
        if value is None or value < 0:
            continue

        # Handle different timestamp formats
        date_info = result.get("date", {})
        timestamp_str = date_info.get("utc") or result.get("datetime", {}).get("utc")
        if not timestamp_str:
            continue

        records.append({
            "city":          city,
            "parameter":     parameter,
            "value":         float(value),
            "unit":          result.get("unit", "µg/m³"),
            "timestamp_utc": pd.to_datetime(timestamp_str, utc=True),
            "location_id":   str(result.get("locationId", "")),
            "source":        "openaq"
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Drop duplicates
    df = df.drop_duplicates(subset=["city", "parameter", "timestamp_utc", "location_id"])

    logger.info(f"Parsed {len(df)} clean readings for {city}")
    return df



# Main fetch function (called by scheduler)
def fetch_city_readings(city_name: str, location_ids: list[int]) -> pd.DataFrame:
    """
    Fetch latest AQI readings for a city across all its monitoring stations.
    This is the primary function called every hour by the scheduler.
    """
    all_readings = []

    for location_id in location_ids:
        logger.info(f"Fetching readings for {city_name} — location {location_id}")
        readings = fetch_latest_readings(location_id)
        if readings:
            all_readings.extend(readings)
        time.sleep(0.3)   # Be polite to the API

    if not all_readings:
        logger.warning(f"No readings returned for {city_name}")
        return pd.DataFrame()

    df = parse_readings(all_readings, city=city_name.lower())
    return df



# Backfill — fetch last N days of data
def backfill_city(city_name: str, location_ids: list[int], days: int = 30) -> pd.DataFrame:
    """
    Fetch the last N days of historical data for a city.
    Run this ONCE when setting up a new city.
    """
    date_to   = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    all_readings = []

    for location_id in location_ids:
        for parameter in TARGET_PARAMETERS:
            logger.info(f"Backfilling {parameter} for {city_name} — location {location_id}")
            readings = fetch_historical_readings(
                location_id=location_id,
                date_from=date_from,
                date_to=date_to,
                parameter=parameter
            )
            all_readings.extend(readings)
            time.sleep(1)  # Slower during backfill to avoid rate limits

    if not all_readings:
        return pd.DataFrame()

    df = parse_readings(all_readings, city=city_name.lower())
    logger.success(f"Backfill complete for {city_name}: {len(df)} records")
    return df