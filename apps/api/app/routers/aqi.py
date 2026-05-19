from fastapi import APIRouter, HTTPException
from app.services.aqi_service import get_latest_aqi, get_historical_aqi, get_all_cities_status

router = APIRouter()

VALID_CITIES = ["abuja", "lagos", "kano", "port_harcourt", "ibadan", "osogbo"]


@router.get("/")
def all_cities_status():
    """Current AQI for all cities — used for the map."""
    return get_all_cities_status()


@router.get("/{city}")
def city_aqi(city: str):
    """Latest AQI reading for a single city."""
    if city not in VALID_CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    data = get_latest_aqi(city)
    if not data:
        raise HTTPException(status_code=404, detail=f"No AQI data available for {city}")
    return data


@router.get("/{city}/history")
def city_history(city: str, hours: int = 24):
    """Historical AQI for charts. Default last 24 hours."""
    if city not in VALID_CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    if hours > 720:
        raise HTTPException(status_code=400, detail="Maximum history is 720 hours (30 days)")
    return get_historical_aqi(city, hours=hours)