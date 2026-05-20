import os
from dotenv import load_dotenv
load_dotenv()

OPENAQ_API_KEY       = os.getenv("OPENAQ_API_KEY", "")
OPENAQ_BASE_URL      = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3")
OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY         = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DATABASE_URL         = os.getenv("DATABASE_URL", "")
SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 60))

# Twilio
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_SMS_FROM      = os.getenv("TWILIO_SMS_FROM", "")

# Email
SMTP_HOST        = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", 587))
SMTP_USER        = os.getenv("SMTP_USER", "")
SMTP_PASSWORD    = os.getenv("SMTP_PASSWORD", "")
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "")

# App
APP_ENV       = os.getenv("APP_ENV", "development")
IS_PRODUCTION = APP_ENV == "production"

# Fail fast if critical values are missing
assert SUPABASE_URL,  "SUPABASE_URL is not set in .env"
assert SUPABASE_KEY,  "SUPABASE_SERVICE_ROLE_KEY is not set in .env"
assert DATABASE_URL,  "DATABASE_URL is not set in .env"

