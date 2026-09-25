from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "app" / "data"


class Settings(BaseSettings):
    app_name: str = "CropSight API"
    secret_key: str = "cropsight-dev-secret-change-in-production-9f83a1c2"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = f"sqlite:///{(BASE_DIR / 'cropsight.db').as_posix()}"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
DATA_DIR.mkdir(parents=True, exist_ok=True)
