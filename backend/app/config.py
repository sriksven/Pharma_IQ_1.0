from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    openai_api_key: str = ""
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    data_dir: str = "./data_pipeline/raw"
    sqlite_db_path: str = "./pharma_iq.db"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
