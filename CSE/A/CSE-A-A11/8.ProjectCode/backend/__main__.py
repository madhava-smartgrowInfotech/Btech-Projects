"""`python -m backend` - serve the API on BACKEND_PORT from .env (default 8311)."""
import uvicorn

from .main import BACKEND_PORT

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=BACKEND_PORT, log_level="info")
