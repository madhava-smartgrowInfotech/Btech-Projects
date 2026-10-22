"""Run the FinSight AI Flask app (localhost only)."""
import os
from pathlib import Path
from app import create_app


def _load_env(path):
    """Minimal .env reader: KEY=VALUE lines, never overrides real environment variables."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env(Path(__file__).resolve().parent / ".env")
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
