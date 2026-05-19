from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AQIReading(BaseModel):
    city:          str
    aqi_value:     float
    aqi_category:  str
    pm25:          Optional[float]
    pm10:          Optional[float]
    no2:           Optional[float]
    o3:            Optional[float]
    co:            Optional[float]
    so2:           Optional[float]
    temperature_c: Optional[float]
    humidity_pct:  Optional[float]
    timestamp_utc: datetime
    color:         str
    advice:        str


class ForecastPoint(BaseModel):
    forecast_for:       datetime
    horizon_hours:      int
    predicted_aqi:      float
    predicted_category: str
    color:              str


class CityForecast(BaseModel):
    city:      str
    forecasts: list[ForecastPoint]


class AlertSubscriptionRequest(BaseModel):
    city:      str
    channel:   str           # whatsapp, sms, email
    contact:   str           # phone or email
    threshold: str = "unhealthy"


class AlertSubscriptionResponse(BaseModel):
    success: bool
    message: str
    id:      Optional[int] = None


class CityStatus(BaseModel):
    city:         str
    display_name: str
    aqi_value:    Optional[float]
    aqi_category: Optional[str]
    color:        Optional[str]
    latitude:     float
    longitude:    float
    last_updated: Optional[datetime]