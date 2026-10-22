"""FinSight AI — Flask application factory."""
import logging
import os
from pathlib import Path
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]


def create_app():
    app = Flask(__name__,
                template_folder=str(ROOT / "app" / "templates"),
                static_folder=str(ROOT / "app" / "static"))
    app.secret_key = os.environ.get("FINSIGHT_SECRET_KEY", "finsight-local-dev-key")
    app.config["PORT"] = int(os.environ.get("PORT", "5000"))

    logging.basicConfig(level=logging.INFO)

    # Preload model artifacts at startup (fast per-request predictions).
    try:
        from app.services.predictor import get_model, get_model_name
        get_model()
        app.logger.info("Loaded model: %s", get_model_name())
    except Exception as e:
        app.logger.warning("Model preload failed (training may be required): %s", e)

    from app.routes import bp
    app.register_blueprint(bp)

    from app.api import api_bp
    app.register_blueprint(api_bp)
    return app
