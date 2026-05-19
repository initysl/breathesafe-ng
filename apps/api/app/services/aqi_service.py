from datetime import datetime, timezone, timedelta
from loguru import logger
from app.db.database import supabase

AQI_THRESHOLDS = {
    (0,   50):  ("Good",                          "#00e400", "Air quality is satisfactory. Outdoor activities are safe."),
    (51,  100): ("Moderate",                      "#ffff00", "Acceptable. Sensitive individuals should limit outdoor exertion."),
    (101, 150): ("Unhealthy for Sensitive Groups","#ff7e00", "Children and elderly should reduce outdoor activity."),
    (151, 200): ("Unhealthy",                     "#ff0000", "Everyone should reduce prolonged outdoor exertion."),
    (201, 300): ("Very Unhealthy",                "#8f3f97", "Health alert. Avoid all outdoor activities."),
    (301, 999): ("Hazardous",                     "#7e0023", "Emergency conditions. Stay indoors."),
}

CITY_META = {
    "abuja":         {"display_name": "Abuja",         "latitude": 9.0765,  "longitude": 7.3986},
    "lagos":         {"display_name": "Lagos",         "latitude": 6.5244,  "longitude": 3.3792},
    "kano":          {"display_name": "Kano",          "latitude": 12.0022, "longitude": 8.5919},
    "port_harcourt": {"display_name": "Port Harcourt", "latitude": 4.8156,  "longitude": 7.0498},
    "ibadan":        {"display_name": "Ibadan",        "latitude": 7.3776,  "longitude": 3.9470},
    "osogbo":        {"display_name": "Osogbo",        "latitude": 7.7719,  "longitude": 4.5624},
}


def get_aqi_meta(aqi_value: float) -> tuple[str, str, str]:
    for (low, high), (category, color, advice) in AQI_THRESHOLDS.items():
        if low <= aqi_value <= high:
            return category, color, advice
    return "Hazardous", "#7e0023", "Emergency conditions. Stay indoors."


def get_latest_aqi(city: str) -> dict | None:
    """Fetch the most recent AQI reading for a city."""
    try:
        response = (
            supabase.table("processed_features")
            .select("*")
            .eq("city", city)
            .order("timestamp_utc", desc=True)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None

        row      = response.data[0]
        aqi      = row.get("aqi_value") or 0
        category, color, advice = get_aqi_meta(aqi)

        return {
            "city":          city,
            "aqi_value":     round(aqi, 1),
            "aqi_category":  category,
            "pm25":          row.get("pm25"),
            "pm10":          row.get("pm10"),
            "no2":           row.get("no2"),
            "o3":            row.get("o3"),
            "co":            row.get("co"),
            "so2":           row.get("so2"),
            "temperature_c": row.get("temperature_c"),
            "humidity_pct":  row.get("humidity_pct"),
            "timestamp_utc": row.get("timestamp_utc"),
            "color":         color,
            "advice":        advice,
        }
    except Exception as e:
        logger.error(f"Failed to get latest AQI for {city}: {e}")
        return None


def get_historical_aqi(city: str, hours: int = 24) -> list[dict]:
    """Fetch last N hours of AQI readings for charts."""
    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        response = (
            supabase.table("processed_features")
            .select("timestamp_utc, aqi_value, pm25, pm10, temperature_c, humidity_pct")
            .eq("city", city)
            .gte("timestamp_utc", since)
            .order("timestamp_utc", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"Failed to get historical AQI for {city}: {e}")
        return []


def get_all_cities_status() -> list[dict]:
    """Get current AQI status for all cities — used for the map."""
    results = []
    for city, meta in CITY_META.items():
        latest = get_latest_aqi(city)
        results.append({
            "city":         city,
            "display_name": meta["display_name"],
            "latitude":     meta["latitude"],
            "longitude":    meta["longitude"],
            "aqi_value":    latest["aqi_value"]    if latest else None,
            "aqi_category": latest["aqi_category"] if latest else None,
            "color":        latest["color"]         if latest else "#cccccc",
            "last_updated": latest["timestamp_utc"] if latest else None,
        })
    return results