import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE = os.path.join(BASE_DIR, "instance", "app.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Optional: set this env var to enable real generative answers via Anthropic.
    # If not set, the app falls back to extractive (TF-IDF based) answering,
    # so the project runs fully offline out of the box.
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
