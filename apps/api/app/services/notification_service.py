import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
from app.config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM, TWILIO_SMS_FROM,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_FROM_EMAIL
)


def build_alert_message(city: str, predicted_aqi: float, category: str, advice: str) -> str:
    return (
        f"⚠️ BreatheSafe NG Alert — {city.title()}\n"
        f"AQI Forecast: {predicted_aqi} ({category})\n"
        f"Advice: {advice}\n"
        f"Stay safe. — breathesafe.ng"
    )


def send_whatsapp(to: str, message: str) -> bool:
    """Send WhatsApp alert via Twilio."""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Ensure number is in whatsapp: format
        to_formatted = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to

        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=to_formatted,
            body=message,
        )
        logger.success(f"WhatsApp alert sent to {to}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to}: {e}")
        return False


def send_sms(to: str, message: str) -> bool:
    """Send SMS alert via Twilio."""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(from_=TWILIO_SMS_FROM, to=to, body=message)
        logger.success(f"SMS alert sent to {to}")
        return True
    except Exception as e:
        logger.error(f"SMS send failed to {to}: {e}")
        return False


def send_email(to: str, subject: str, message: str) -> bool:
    """Send email alert via SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"]    = ALERT_FROM_EMAIL
        msg["To"]      = to
        msg["Subject"] = subject

        # Plain text + simple HTML version
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:20px;border:1px solid #ddd;border-radius:8px;">
            <h2 style="color:#e53e3e;">⚠️ BreatheSafe NG Alert</h2>
            <p style="white-space:pre-line;">{message}</p>
            <hr/>
            <small style="color:#888;">You are receiving this because you subscribed at breathesafe.ng.
            <a href="breathesafe.ng/alerts/manage">Manage alerts</a></small>
        </div>
        """
        msg.attach(MIMEText(message, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_FROM_EMAIL, to, msg.as_string())

        logger.success(f"Email alert sent to {to}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


def dispatch_alert(channel: str, contact: str, message: str, subject: str = "Air Quality Alert") -> bool:
    """Route alert to the correct channel."""
    if channel == "whatsapp":
        return send_whatsapp(contact, message)
    elif channel == "sms":
        return send_sms(contact, message)
    elif channel == "email":
        return send_email(contact, subject, message)
    else:
        logger.warning(f"Unknown alert channel: {channel}")
        return False