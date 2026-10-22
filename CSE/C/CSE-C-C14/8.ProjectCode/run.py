"""WSGI entry point for VeriVision AI. Binds to 127.0.0.1 by default."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def _load_env(path):
    """Tiny .env reader (KEY=VALUE lines); real environment variables win."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_env(os.path.join(ROOT, ".env"))

from app import config, create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    try:
        from app import inference
        inference.ensure_models_loaded()
        print(f"Models loaded on {inference.get_device_name()}")
    except Exception as exc:
        print(f"WARNING: starting without trained models: {exc}")
        print("Run the training workflow in HOW_TO_RUN.md to generate model artifacts.")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
