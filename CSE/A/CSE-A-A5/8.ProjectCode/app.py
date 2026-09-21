"""CipherGuard Shield entry point."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    # Bind to 127.0.0.1 (localhost) to avoid firewall prompts and ensure browser resolution
    uvicorn.run("cipherguard.api.main:app", host="127.0.0.1", port=8000, reload=False)
