"""Flask application factory for VeriVision AI."""
import os

from flask import Flask

from . import config


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    from .routes import bp
    app.register_blueprint(bp)
    from .api import api_bp
    app.register_blueprint(api_bp)

    @app.errorhandler(413)
    def too_large(_e):
        from flask import jsonify, render_template, request
        if request.path.startswith("/api/"):
            return jsonify({"error": f"Image exceeds the {config.MAX_UPLOAD_MB} MB size limit. Please upload a smaller file."}), 413
        return render_template(
            "error.html",
            message=f"Image exceeds the {config.MAX_UPLOAD_MB} MB size limit. Please upload a smaller file.",
        ), 413

    return app
