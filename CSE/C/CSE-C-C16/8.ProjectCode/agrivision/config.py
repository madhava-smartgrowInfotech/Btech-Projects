import os
SECRET_KEY = os.environ.get("AGRIVISION_SECRET", "agrivision-dev-secret-change-me")
DB_PATH = os.path.join(os.path.dirname(__file__), "agrivision.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
