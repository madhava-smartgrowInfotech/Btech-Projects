from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "CipherVault"
    APP_PORT: int = 8413
    # Default to local SQLite so one-click local deployment works with zero setup.
    # Set DATABASE_URL to a PostgreSQL URL (e.g. postgresql+psycopg://user:pass@localhost:5432/ciphervault)
    # for production-style deployment / Docker.
    DATABASE_URL: str = "sqlite:///./ciphervault.db"
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    STORAGE_DIR: str = "storage/encrypted"
    MAX_UPLOAD_MB: int = 25
    # Simple brute-force mitigation: max failed logins tracked per IP/email in memory
    LOGIN_MAX_ATTEMPTS: int = 20
    LOGIN_WINDOW_SECONDS: int = 300

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
