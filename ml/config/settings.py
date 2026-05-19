import os

from config.env import load_ml_env

ENV_PATH = load_ml_env()

OPENAQ_API_KEY       = os.getenv("OPENAQ_API_KEY")
OPENAQ_BASE_URL      = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3")
OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DATABASE_URL         = os.getenv("DATABASE_URL")
SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 60))
