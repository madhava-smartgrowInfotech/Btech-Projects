from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "VisionForge AI"
    jwt_secret: str = "dev-secret-change-me-in-production-a15x9f2q"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = f"sqlite:///{BACKEND_ROOT / 'storage' / 'visionforge.db'}"

    model_path: Path = BACKEND_ROOT / "models" / "defect_classifier.pt"
    class_names_path: Path = BACKEND_ROOT / "models" / "class_names.json"
    metrics_path: Path = BACKEND_ROOT / "models" / "metrics.json"

    storage_dir: Path = BACKEND_ROOT / "storage"
    uploads_dir: Path = BACKEND_ROOT / "storage" / "uploads"
    heatmaps_dir: Path = BACKEND_ROOT / "storage" / "heatmaps"
    reports_dir: Path = BACKEND_ROOT / "storage" / "reports"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"


settings = Settings()

for d in [settings.storage_dir, settings.uploads_dir, settings.heatmaps_dir, settings.reports_dir]:
    d.mkdir(parents=True, exist_ok=True)
