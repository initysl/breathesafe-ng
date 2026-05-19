import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ML_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = ML_ROOT / ".env"
ENV_FILE_ENV_VAR = "BREATHESAFE_ML_ENV_FILE"
LEGACY_ENV_FILE_ENV_VAR = "BREATHESAFE_ENV_FILE"


@lru_cache(maxsize=1)
def load_ml_env() -> Path | None:
    """Load ML env config without searching parent directories."""
    env_override_var = next(
        (name for name in (ENV_FILE_ENV_VAR, LEGACY_ENV_FILE_ENV_VAR) if os.getenv(name)),
        None,
    )
    env_override = os.getenv(env_override_var) if env_override_var else None
    env_path = Path(env_override).expanduser().resolve() if env_override else DEFAULT_ENV_PATH

    if env_override and not env_path.exists():
        raise FileNotFoundError(
            f"{env_override_var} points to a missing file: {env_path}"
        )

    if not env_path.exists():
        return None

    load_dotenv(dotenv_path=env_path, override=False)
    return env_path
