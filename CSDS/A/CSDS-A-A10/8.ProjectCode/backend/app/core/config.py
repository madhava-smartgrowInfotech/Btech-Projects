import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MedFlow API"
    database_url: str = "sqlite:///./medflow.db"
    secret_key: str = os.environ.get("MEDFLOW_SECRET_KEY", "medflow-dev-secret-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_prefix = "MEDFLOW_"


settings = Settings()
