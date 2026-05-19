import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import Optional

from config.settings import OPENAQ_API_KEY, OPENAQ_BASE_URL


def _openaq_headers() -> dict[str, str]:
    if not OPENAQ_API_KEY:
        raise ValueError(
            "OPENAQ_API_KEY is not configured. Set it in ml/.env or provide "
            "BREATHESAFE_ML_ENV_FILE."
        )

    return {
        "X-API-Key": OPENAQ_API_KEY,
        "Accept": "application/json",
    }


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(value.casefold().replace("_", " ").split())


def _fetch_country_locations(
    country_code: str = "NG",
    limit: int = 100,
    max_pages: int = 10,
) -> list[dict]:
    """Fetch paginated locations for a country using OpenAQ's documented v3 filters."""
    url = f"{OPENAQ_BASE_URL}/locations"
    all_locations: list[dict] = []

    for page in range(1, max_pages + 1):
        params = {
            "iso": country_code.upper(),
            "limit": limit,
            "page": page,
        }
        response = requests.get(url, headers=_openaq_headers(), params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        all_locations.extend(results)

        found = data.get("meta", {}).get("found")
        if isinstance(found, int) and len(all_locations) >= found:
            break

        if len(results) < limit:
            break

    return all_locations


def _location_matches_city(location: dict, city_name: str) -> bool:
    target = _normalize_text(city_name)
    locality = _normalize_text(location.get("locality"))
    station_name = _normalize_text(location.get("name"))

    return any(
        (
            candidate == target,
            candidate.startswith(f"{target} "),
            candidate.endswith(f" {target}"),
            f" {target} " in f" {candidate} ",
        )
        for candidate in (locality, station_name)
        if candidate
    )

# Pollutants we care about
TARGET_PARAMETERS = ["pm25", "pm10", "no2", "o3", "co", "so2"]


def discover_cities(country_code: str = "NG", limit: int = 100, max_pages: int = 10) -> list[str]:
    """Return distinct OpenAQ localities for a country."""
    try:
        locations = _fetch_country_locations(country_code=country_code, limit=limit, max_pages=max_pages)
        cities = sorted(
            {
                locality.strip()
                for locality in (location.get("locality") for location in locations)
                if locality
            }
        )
        logger.info(f"Found {len(cities)} OpenAQ localities in {country_code.upper()}")
        return cities
    except Exception as e:
        logger.error(f"Failed to discover cities for {country_code.upper()}: {e}")
        return []



# Discover location IDs for Nigerian cities (Run this once to find your real IDs)
def discover_locations(city_name: str, country_code: str = "NG", limit: int = 100, max_pages: int = 10) -> list[dict]:
    """
    Find OpenAQ location IDs for a city.
    Run this once per city to get real location IDs,
    then hardcode them in cities.yaml.
    """
    try:
        locations = _fetch_country_locations(country_code=country_code, limit=limit, max_pages=max_pages)
        matches = [location for location in locations if _location_matches_city(location, city_name)]
        matches.sort(key=lambda item: (_normalize_text(item.get("locality")), _normalize_text(item.get("name"))))

        logger.info(
            f"Found {len(matches)} locations for {city_name} in {country_code.upper()} "
            f"from {len(locations)} country locations"
        )
        return matches
    except Exception as e:
        logger.error(f"Failed to discover locations for {city_name}: {e}")
        return []



def fetch_location_sensors(location_id: int) -> dict:
    """
    Fetch sensor metadata for a location.
    Returns a dict mapping sensorsId → parameter name.
    e.g. {15886622: 'pm25', 15886623: 'pm10'}
    """
    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/sensors"
    try:
        response = requests.get(url, headers=_openaq_headers(), timeout=15)
        response.raise_for_status()
        data = response.json()
        sensor_map = {}
        for sensor in data.get("results", []):
            sensor_id  = sensor["id"]
            param_name = sensor.get("parameter", {}).get("name", "unknown")
            sensor_map[sensor_id] = param_name
        logger.debug(f"Sensor map for location {location_id}: {sensor_map}")
        return sensor_map
    except Exception as e:
        logger.error(f"Failed to fetch sensors for location {location_id}: {e}")
        return {}
    


# Fetch latest readings for a location
def fetch_latest_readings(location_id: int) -> list[dict]:
    """Fetch the latest pollutant readings for a specific location ID."""
    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/latest"

    try:
        response = requests.get(url, headers=_openaq_headers(), timeout=15)
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
            response = requests.get(url, headers=_openaq_headers(), params=params, timeout=20)
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
def parse_readings(raw_results: list[dict], city: str, sensor_map: dict | None = None) -> pd.DataFrame:
    if sensor_map is None:
        sensor_map = {}

    records = []
    for result in raw_results:
        sensor_id = result.get("sensorsId")
        parameter = sensor_map.get(sensor_id, "unknown")

        if parameter not in TARGET_PARAMETERS:
            continue

        value = result.get("value")
        if value is None or value < 0:
            continue

        timestamp_str = result.get("datetime", {}).get("utc")
        if not timestamp_str:
            continue

        records.append({
            "city":          city,
            "parameter":     parameter,
            "value":         float(value),
            "unit":          "µg/m³",
            "timestamp_utc": pd.to_datetime(timestamp_str, utc=True),
            "location_id":   str(result.get("locationsId", "")),
            "source":        "openaq"
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["city", "parameter", "timestamp_utc", "location_id"])
    logger.info(f"Parsed {len(df)} clean readings for {city}")
    return df



# Main fetch function (called by scheduler)
def fetch_city_readings(city_name: str, location_ids: list[int]) -> pd.DataFrame:
    all_readings = []

    for location_id in location_ids:
        logger.info(f"Fetching readings for {city_name} — location {location_id}")

        # Step 1 — get sensor → parameter map for this location
        sensor_map = fetch_location_sensors(location_id)
        if not sensor_map:
            continue

        # Step 2 — get latest readings
        readings = fetch_latest_readings(location_id)
        if readings:
            # Attach sensor map to each reading for parsing
            df = parse_readings(readings, city=city_name.lower(), sensor_map=sensor_map)
            all_readings.append(df)

        time.sleep(0.3)

    if not all_readings:
        logger.warning(f"No readings returned for {city_name}")
        return pd.DataFrame()

    return pd.concat(all_readings, ignore_index=True)


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
