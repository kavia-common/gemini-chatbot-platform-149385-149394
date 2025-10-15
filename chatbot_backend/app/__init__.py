from __future__ import annotations

import os
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from dotenv import load_dotenv

from .extensions import init_extensions, db
from .routes.health import blp as health_blp
from .routes.chat import blp as chat_blp
from .routes.minichat import minichat_bp


# Initialize environment variables from .env (if present)
load_dotenv()


def _get_cors_origins() -> list[str] | str:
    """Compute CORS allowed origins from env var CORS_ALLOWED_ORIGINS.

    Returns:
        A list of origins if provided as comma-separated values,
        or '*' if not set.
    """
    origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    if origins.strip() == "*":
        return "*"
    return [o.strip() for o in origins.split(",") if o.strip()]


# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask application.

    Configuration:
    - DATABASE_URL: SQLAlchemy database URL (required for Postgres).
      Falls back to local SQLite when not provided.
    - CORS_ALLOWED_ORIGINS: Comma-separated origins for CORS (default '*').

    Returns:
        The configured Flask app instance.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # OpenAPI / API metadata
    app.config["API_TITLE"] = "Gemini Chatbot API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Database configuration
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Safe local fallback for development
        database_url = "sqlite:///chat.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    init_extensions(app)

    # CORS
    cors_origins = _get_cors_origins()
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # API / Blueprints
    api = Api(app)
    api.register_blueprint(health_blp)
    api.register_blueprint(chat_blp)

    # Register minimal chat endpoint (no DB usage, lightweight CORS already configured)
    app.register_blueprint(minichat_bp)

    # Create DB tables (for simple setup; in prod, use migrations)
    with app.app_context():
        db.create_all()

    # Expose api for external tools like generate_openapi.py
    app.api = api  # type: ignore[attr-defined]
    return app


# Keep compatibility with existing run.py and generate_openapi.py imports
app = create_app()
api = app.api  # type: ignore[attr-defined]
