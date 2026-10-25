"""Start the API with torch imported first (on some Windows hosts torch's DLLs fail to load after numpy/pandas).

    python scripts/serve.py [port]
"""
import torch  # noqa: F401
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8305
    uvicorn.run("cipherguard.api.main:app", host="127.0.0.1", port=port, log_level="warning")
