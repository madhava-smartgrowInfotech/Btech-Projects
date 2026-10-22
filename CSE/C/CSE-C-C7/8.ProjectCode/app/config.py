from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "LearnPathIQ"
    database_url: str = f"sqlite:///{(BASE_DIR / 'learnpathiq.db').as_posix()}"
    secret_key: str = "learnpathiq-local-dev-secret-change-me"
    token_expire_hours: int = 72
    artifacts_dir: str = str(BASE_DIR / "artifacts")
    models_dir: str = str(BASE_DIR / "models")
    data_dir: str = str(BASE_DIR / "data")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

