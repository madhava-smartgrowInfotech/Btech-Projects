"""CipherGuard Shield entry point."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def _env_port(default: int) -> int:
    """BACKEND_PORT from the environment or the .env next to this file (8305 by default)."""
    if os.environ.get("BACKEND_PORT"):
        return int(os.environ["BACKEND_PORT"])
    env = Path(__file__).parent / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("BACKEND_PORT="):
                return int(line.split("=", 1)[1].strip())
    return default


if __name__ == "__main__":
    import uvicorn
    # Bind to 127.0.0.1 (localhost) to avoid firewall prompts and ensure browser resolution
    uvicorn.run("cipherguard.api.main:app", host="127.0.0.1", port=_env_port(8305), reload=False)
