import json
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from loguru import logger

ML_ROOT   = Path(__file__).resolve().parent.parent
ARTIFACTS = ML_ROOT / "artifacts"

RETRAIN_INTERVAL_DAYS    = 30
PERFORMANCE_DEGRADATION_THRESHOLD = 15   # Retrain if MAE increases by 15+ points


def get_latest_model_metrics(city: str, horizon: int) -> dict | None:
    """Load metrics from the latest trained model."""
    pattern    = f"meta_{city}_{horizon}h_*.json"
    meta_files = sorted(ARTIFACTS.glob(pattern))
    if not meta_files:
        return None
    with open(meta_files[-1]) as f:
        meta = json.load(f)
    return meta.get("metrics")


def is_retraining_due(city: str, horizon: int) -> bool:
    """Check if 30 days have passed since last training."""
    pattern    = f"meta_{city}_{horizon}h_*.json"
    meta_files = sorted(ARTIFACTS.glob(pattern))
    if not meta_files:
        return True   # Never trained — definitely retrain

    with open(meta_files[-1]) as f:
        meta = json.load(f)

    version_str  = meta.get("version", "")
    try:
        trained_at = datetime.strptime(version_str, "%Y%m%d_%H%M").replace(tzinfo=timezone.utc)
        days_since = (datetime.now(timezone.utc) - trained_at).days
        if days_since >= RETRAIN_INTERVAL_DAYS:
            logger.info(f"{city} {horizon}h model is {days_since} days old — retraining due")
            return True
    except Exception:
        return True   # Can't parse date — retrain to be safe

    return False


def check_performance_drift(city: str, horizon: int) -> bool:
    """
    Compare recent model predictions vs actual readings.
    Triggers early retraining if performance has degraded significantly.
    """
    try:
        import os
        from supabase import create_client
        from config.settings import SUPABASE_URL, SUPABASE_KEY

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Get forecasts made in last 7 days
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        forecasts = (
            supabase.table("aqi_forecasts")
            .select("forecast_for, predicted_aqi")
            .eq("city", city)
            .eq("horizon_hours", horizon)
            .gte("forecast_made_at", week_ago)
            .execute()
        ).data

        actuals = (
            supabase.table("processed_features")
            .select("timestamp_utc, aqi_value")
            .eq("city", city)
            .gte("timestamp_utc", week_ago)
            .execute()
        ).data

        if not forecasts or not actuals:
            return False

        import pandas as pd
        forecast_df = pd.DataFrame(forecasts)
        actual_df   = pd.DataFrame(actuals)
        forecast_df["forecast_for"]   = pd.to_datetime(forecast_df["forecast_for"])
        actual_df["timestamp_utc"]    = pd.to_datetime(actual_df["timestamp_utc"])

        merged = pd.merge_asof(
            forecast_df.sort_values("forecast_for"),
            actual_df.sort_values("timestamp_utc"),
            left_on="forecast_for",
            right_on="timestamp_utc",
            tolerance=pd.Timedelta("1h")
        ).dropna()

        if len(merged) < 10:
            return False

        recent_mae = np.abs(merged["predicted_aqi"] - merged["aqi_value"]).mean()
        baseline   = get_latest_model_metrics(city, horizon)
        if not baseline:
            return False

        baseline_mae = baseline.get("mae", 999)
        drift        = recent_mae - baseline_mae

        if drift > PERFORMANCE_DEGRADATION_THRESHOLD:
            logger.warning(
                f"Performance drift detected for {city} {horizon}h: "
                f"baseline MAE={baseline_mae:.1f}, recent MAE={recent_mae:.1f} (+{drift:.1f})"
            )
            return True

    except Exception as e:
        logger.warning(f"Could not check performance drift: {e}")

    return False


def run_retraining_check():
    """
    Run retraining check for all cities and horizons.
    Called monthly by the scheduler.
    """
    from models.xgboost_model import FORECAST_HORIZONS
    from training.train_xgboost import CITIES

    logger.info("═══ Running retraining check ═══")
    retrained = []

    for city in CITIES:
        for horizon in FORECAST_HORIZONS:
            needs_retrain = is_retraining_due(city, horizon) or check_performance_drift(city, horizon)
            if needs_retrain:
                logger.info(f"Retraining {city} {horizon}h model...")
                from models.xgboost_model import train_city_models
                train_city_models(city)
                retrained.append(f"{city}_{horizon}h")
                break   # train_city_models handles all horizons for a city

    if retrained:
        logger.success(f"Retrained models: {retrained}")
    else:
        logger.info("All models are current — no retraining needed")