from fastapi import APIRouter, HTTPException
from app.models.aqi import AlertSubscriptionRequest
from app.services.alert_service import subscribe, unsubscribe

router = APIRouter()

VALID_CITIES   = ["abuja", "lagos", "kano", "port_harcourt", "ibadan", "osogbo"]
VALID_CHANNELS = ["whatsapp", "sms", "email"]
VALID_THRESHOLDS = ["moderate", "unhealthy_sensitive", "unhealthy", "very_unhealthy", "hazardous"]


@router.post("/subscribe")
def subscribe_alerts(payload: AlertSubscriptionRequest):
    """Subscribe to AQI alerts for a city."""
    if payload.city not in VALID_CITIES:
        raise HTTPException(status_code=400, detail=f"Invalid city: {payload.city}")
    if payload.channel not in VALID_CHANNELS:
        raise HTTPException(status_code=400, detail=f"Invalid channel: {payload.channel}")
    if payload.threshold not in VALID_THRESHOLDS:
        raise HTTPException(status_code=400, detail=f"Invalid threshold: {payload.threshold}")

    result = subscribe(
        city=payload.city,
        channel=payload.channel,
        contact=payload.contact,
        threshold=payload.threshold,
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.delete("/unsubscribe")
def unsubscribe_alerts(city: str, channel: str, contact: str):
    """Unsubscribe from AQI alerts."""
    result = unsubscribe(city=city, channel=channel, contact=contact)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result