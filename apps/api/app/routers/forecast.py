from fastapi import APIRouter, HTTPException
from app.services.forecast_service import get_city_forecast

router = APIRouter()

VALID_CITIES = ["abuja", "lagos", "kano", "port_harcourt", "ibadan", "osogbo"]


@router.get("/{city}")
def city_forecast(city: str):
    """Get all forecast horizons (1h, 6h, 12h, 24h) for a city."""
    if city not in VALID_CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    forecasts = get_city_forecast(city)
    return {"city": city, "forecasts": forecasts}


@router.get("/{city}/{horizon}")
def city_forecast_horizon(city: str, horizon: int):
    """Get forecast for a specific horizon."""
    if city not in VALID_CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    if horizon not in [1, 6, 12, 24]:
        raise HTTPException(status_code=400, detail="Horizon must be 1, 6, 12, or 24")
    forecasts = get_city_forecast(city, horizon_hours=horizon)
    return {"city": city, "horizon_hours": horizon, "forecasts": forecasts}