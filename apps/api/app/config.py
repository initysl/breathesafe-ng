import os
from pathlib import Path
from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = API_ROOT / ".env"
ENV_FILE_ENV_VAR = "BREATHESAFE_API_ENV_FILE"

env_override = os.getenv(ENV_FILE_ENV_VAR)
ENV_PATH = Path(env_override).expanduser().resolve() if env_override else DEFAULT_ENV_PATH

if env_override and not ENV_PATH.exists():
    raise FileNotFoundError(f"{ENV_FILE_ENV_VAR} points to a missing file: {ENV_PATH}")

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
