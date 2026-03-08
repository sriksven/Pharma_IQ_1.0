import os
from pydantic_settings import BaseSettings

# Project root is two levels up from this file (backend/app/config.py)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    groq_api_key: str = ""
    openai_api_key: str = ""
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    data_dir: str = os.path.join(_PROJECT_ROOT, "data_pipeline", "raw")
    sqlite_db_path: str = os.path.join(_PROJECT_ROOT, "pharma_iq.db")
    log_level: str = "INFO"
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    class Config:
        env_file = _ENV_FILE


settings = Settings()
