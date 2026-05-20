import os
import yaml
import pandas as pd
from datetime import datetime, timezone
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from data_ingestion.openaq_fetcher import fetch_city_readings
from data_ingestion.weather_fetcher import fetch_all_cities_weather
from config.supabase_client import supabase
from preprocessing.cleaner import clean_aqi_data, clean_weather_data
from preprocessing.feature_engineer import build_features


# Load city config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "cities.yaml")

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

CITIES = CONFIG["cities"]
INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 60))



# Save to database (Supabase)
def save_to_db(df: pd.DataFrame, table: str) -> int:
    if df.empty:
        return 0
    try:
        df_copy = df.copy()

        # Convert timestamps to ISO string
        for col in df_copy.select_dtypes(include=["datetime64[ns, UTC]", "datetime64[ns]"]).columns:
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Convert boolean columns to int (Supabase JSON safe)
        for col in df_copy.select_dtypes(include=["bool"]).columns:
            df_copy[col] = df_copy[col].astype(int)

        # Replace ALL NaN/inf with None — critical for JSON serialization
        import math
        df_copy = df_copy.astype(object)
        df_copy = df_copy.where(pd.notna(df_copy), None)

        # Extra pass — catch any remaining float nan/inf
        def sanitize(val):
            if val is None:
                return None
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val

        records = [
            {k: sanitize(v) for k, v in row.items()}
            for row in df_copy.to_dict(orient="records")
        ]

        conflict_map = {
            "raw_aqi_readings":   "city,parameter,timestamp_utc,location_id",
            "raw_weather":        "city,timestamp_utc",
            "processed_features": "city,timestamp_utc",
        }
        conflict_col = conflict_map.get(table, "id")

        supabase.table(table).upsert(records, on_conflict=conflict_col).execute()
        logger.success(f"Saved {len(records)} records to {table}")
        return len(records)

    except Exception as e:
        logger.error(f"Failed to save to {table}: {e}")
        return 0
    
def log_pipeline_run(run_type: str, city: str, status: str,
                     records_fetched: int, records_saved: int,
                     error: str | None = None, started_at: datetime | None = None):
    """Log pipeline run to database for monitoring."""
    try:
        supabase.table("pipeline_log").insert({
            "run_type":        run_type,
            "city":            city,
            "status":          status,
            "records_fetched": records_fetched,
            "records_saved":   records_saved,
            "error_message":   error,
            "started_at":      started_at.isoformat() if started_at else None,
            "completed_at":    datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        logger.warning(f"Could not log pipeline run: {e}")



# Job 1 — Fetch AQI data (every hour)
def job_fetch_aqi():
    """Fetch and store AQI readings for all cities."""
    logger.info("═══ Starting AQI fetch job ═══")
    started = datetime.now(timezone.utc)

    for city_key, city_data in CITIES.items():
        location_ids = city_data.get("openaq_location_ids", [])

        if not location_ids:
            logger.warning(f"No location IDs configured for {city_key} — skipping")
            continue

        try:
            raw_df = fetch_city_readings(city_key, location_ids)
            if raw_df.empty:
                log_pipeline_run("openaq_fetch", city_key, "partial", 0, 0, started_at=started)
                continue

            clean_df = clean_aqi_data(raw_df)
            saved = save_to_db(clean_df, "raw_aqi_readings")

            log_pipeline_run("openaq_fetch", city_key, "success",
                             len(raw_df), saved, started_at=started)

        except Exception as e:
            logger.error(f"AQI fetch failed for {city_key}: {e}")
            log_pipeline_run("openaq_fetch", city_key, "failed", 0, 0,
                             error=str(e), started_at=started)

    logger.info("═══ AQI fetch job complete ═══")



# Job 2 — Fetch weather data (every hour)

def job_fetch_weather():
    """Fetch and store weather data for all cities."""
    logger.info("═══ Starting weather fetch job ═══")
    started = datetime.now(timezone.utc)

    try:
        raw_df = fetch_all_cities_weather(CITIES)
        if raw_df.empty:
            logger.warning("No weather data returned")
            return

        clean_df = clean_weather_data(raw_df)
        saved = save_to_db(clean_df, "raw_weather")

        log_pipeline_run("weather_fetch", "all", "success",
                         len(raw_df), saved, started_at=started)

    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        log_pipeline_run("weather_fetch", "all", "failed", 0, 0,
                         error=str(e), started_at=started)

    logger.info("═══ Weather fetch job complete ═══")



# Job 3 — Feature engineering (every hour, after fetch)

def job_build_features():
    """Build and store processed ML features for all cities."""
    logger.info("═══ Starting feature engineering job ═══")
    started = datetime.now(timezone.utc)

    try:
        # Pull last 72 hours of raw data for each city
        aqi_response     = supabase.table("raw_aqi_readings").select("*").execute()
        weather_response = supabase.table("raw_weather").select("*").execute()

        aqi_df     = pd.DataFrame(aqi_response.data)
        weather_df = pd.DataFrame(weather_response.data)

        if aqi_df.empty:
            logger.warning("No AQI data available for feature engineering")
            return

        for city_key in CITIES.keys():
            features_df = build_features(aqi_df, weather_df, city=city_key)
            if not features_df.empty:
                save_to_db(features_df, "processed_features")

        log_pipeline_run("feature_engineering", "all", "success",
                         len(aqi_df), 0, started_at=started)

    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        log_pipeline_run("feature_engineering", "all", "failed", 0, 0,
                         error=str(e), started_at=started)

    logger.info("═══ Feature engineering job complete ═══")



# Scheduler Setup

def start_scheduler():
    scheduler = BlockingScheduler(timezone="Africa/Lagos")

    # Fetch AQI — every hour at :05 (offset to avoid API peak)
    scheduler.add_job(
        job_fetch_aqi,
        trigger=CronTrigger(minute=5),
        id="fetch_aqi",
        name="Fetch OpenAQ readings",
        max_instances=1,
        misfire_grace_time=300    # 5 min grace if server was down
    )

    # Fetch weather — every hour at :10
    scheduler.add_job(
        job_fetch_weather,
        trigger=CronTrigger(minute=10),
        id="fetch_weather",
        name="Fetch OpenWeatherMap data",
        max_instances=1,
        misfire_grace_time=300
    )

    # Build features — every hour at :20 (after both fetches complete)
    scheduler.add_job(
        job_build_features,
        trigger=CronTrigger(minute=20),
        id="build_features",
        name="Build ML features",
        max_instances=1,
        misfire_grace_time=300
    )

    logger.info("✅ Scheduler started. Jobs:")
    logger.info("   - AQI fetch:         every hour at :05")
    logger.info("   - Weather fetch:     every hour at :10")
    logger.info("   - Feature building:  every hour at :20")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


if __name__ == "__main__":
    logger.info("BreatheSafe NG — Starting data pipeline...")

    # Run once immediately on startup, then schedule
    logger.info("Running initial data fetch...")
    job_fetch_aqi()
    job_fetch_weather()
    job_build_features()

    # Start recurring schedule
    start_scheduler()
