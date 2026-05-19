from datetime import datetime, timezone, timedelta
from loguru import logger
from app.db.database import supabase
from app.services.aqi_service import get_aqi_meta
from app.services.notification_service import build_alert_message, dispatch_alert

# AQI category severity order — only alert when crossing upward
SEVERITY_ORDER = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous",
]

THRESHOLD_MAP = {
    "moderate":           "Moderate",
    "unhealthy_sensitive": "Unhealthy for Sensitive Groups",
    "unhealthy":          "Unhealthy",
    "very_unhealthy":     "Very Unhealthy",
    "hazardous":          "Hazardous",
}


def should_alert(predicted_category: str, threshold: str) -> bool:
    """Check if predicted AQI category meets or exceeds the user's alert threshold."""
    threshold_cat = THRESHOLD_MAP.get(threshold, "Unhealthy")
    pred_idx      = SEVERITY_ORDER.index(predicted_category) if predicted_category in SEVERITY_ORDER else 0
    thresh_idx    = SEVERITY_ORDER.index(threshold_cat)
    return pred_idx >= thresh_idx


def is_on_cooldown(subscription_id: int, cooldown_hours: int = 6) -> bool:
    """Prevent alert spam — max one alert per 6 hours per subscription."""
    try:
        cutoff   = (datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)).isoformat()
        response = (
            supabase.table("alert_log")
            .select("id")
            .eq("subscription_id", subscription_id)
            .gte("sent_at", cutoff)
            .limit(1)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        logger.warning(f"Could not check cooldown: {e}")
        return False


def subscribe(city: str, channel: str, contact: str, threshold: str = "unhealthy") -> dict:
    """Create or update an alert subscription."""
    try:
        response = (
            supabase.table("alert_subscriptions")
            .upsert({
                "city":       city,
                "channel":    channel,
                "contact":    contact,
                "threshold":  threshold,
                "is_active":  True,
            }, on_conflict="city,channel,contact")
            .execute()
        )
        data = response.data[0] if response.data else {}
        logger.success(f"Subscription saved: {channel} → {contact} for {city}")
        return {"success": True, "message": "Subscribed successfully", "id": data.get("id")}
    except Exception as e:
        logger.error(f"Subscription failed: {e}")
        return {"success": False, "message": str(e)}


def unsubscribe(city: str, channel: str, contact: str) -> dict:
    """Deactivate an alert subscription."""
    try:
        supabase.table("alert_subscriptions").update(
            {"is_active": False}
        ).eq("city", city).eq("channel", channel).eq("contact", contact).execute()
        return {"success": True, "message": "Unsubscribed successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_alert_checks():
    """
    Check all active subscriptions against latest forecasts.
    Sends alerts where AQI forecast meets the threshold.
    Called hourly by the scheduler.
    """
    logger.info("═══ Running alert checks ═══")

    try:
        # Get all active subscriptions
        subs = (
            supabase.table("alert_subscriptions")
            .select("*")
            .eq("is_active", True)
            .execute()
        ).data

        # Get latest 1h forecasts for all cities
        forecasts = (
            supabase.table("aqi_forecasts")
            .select("*")
            .eq("horizon_hours", 1)
            .order("forecast_made_at", desc=True)
            .execute()
        ).data

        # Map city → latest forecast
        city_forecast = {}
        for f in forecasts:
            if f["city"] not in city_forecast:
                city_forecast[f["city"]] = f

        alerts_sent = 0

        for sub in subs:
            city     = sub["city"]
            forecast = city_forecast.get(city)
            if not forecast:
                continue

            predicted_aqi      = forecast["predicted_aqi"]
            predicted_category = forecast["predicted_category"]

            if not should_alert(predicted_category, sub["threshold"]):
                continue

            if is_on_cooldown(sub["id"]):
                continue

            # Build and send alert
            _, _, advice = get_aqi_meta(predicted_aqi)
            message      = build_alert_message(city, predicted_aqi, predicted_category, advice)
            success      = dispatch_alert(sub["channel"], sub["contact"], message)

            # Log alert
            supabase.table("alert_log").insert({
                "subscription_id": sub["id"],
                "city":            city,
                "channel":         sub["channel"],
                "contact":         sub["contact"],
                "predicted_aqi":   predicted_aqi,
                "aqi_category":    predicted_category,
                "message_sent":    message,
                "delivery_status": "sent" if success else "failed",
            }).execute()

            # Update last alerted timestamp
            supabase.table("alert_subscriptions").update(
                {"last_alerted_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", sub["id"]).execute()

            if success:
                alerts_sent += 1

        logger.info(f"Alert checks complete — {alerts_sent} alerts sent")

    except Exception as e:
        logger.error(f"Alert check failed: {e}")