from loguru import logger
from app.db.database import supabase
from app.services.aqi_service import get_aqi_meta


def get_city_forecast(city: str, horizon_hours: int = None) -> list[dict]: # type: ignore
    """
    Fetch latest forecasts for a city from aqi_forecasts table.
    Optionally filter by horizon.
    """
    try:
        query = (
            supabase.table("aqi_forecasts")
            .select("*")
            .eq("city", city)
            .order("forecast_for", desc=False)
        )
        if horizon_hours:
            query = query.eq("horizon_hours", horizon_hours)

        # Only get forecasts made in the last 2 hours (fresh ones)
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        query  = query.gte("forecast_made_at", cutoff)

        response = query.execute()
        rows     = response.data or []

        enriched = []
        for row in rows:
            aqi                  = row.get("predicted_aqi", 0)
            category, color, _   = get_aqi_meta(aqi)
            enriched.append({
                "forecast_for":       row["forecast_for"],
                "horizon_hours":      row["horizon_hours"],
                "predicted_aqi":      round(aqi, 1),
                "predicted_category": category,
                "color":              color,
            })

        return enriched

    except Exception as e:
        logger.error(f"Failed to get forecast for {city}: {e}")
        return []