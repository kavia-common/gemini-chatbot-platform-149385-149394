from __future__ import annotations

import os
import re
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from dotenv import load_dotenv

from .extensions import init_extensions, db
from .routes.health import blp as health_blp
from .routes.chat import blp as chat_blp
from .routes.minichat import minichat_bp
from .routes.models import blp as models_blp


# Initialize environment variables from .env (if present)
load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [o.strip() for o in value.split(",") if o.strip()]


def _get_cors_origins() -> list[str] | str:
    """Compute CORS allowed origins with support for FRONTEND_ORIGIN.

    Priority:
    - FRONTEND_ORIGIN: single origin or comma-separated list
    - CORS_ALLOWED_ORIGINS: fallback compatibility (single or comma-separated)
    - Defaults: localhost:3000 and VSCode preview domain at port 3000

    Returns:
        A list of allowed origins or '*' for allow-all.
    """
    # New explicit env for frontend origin(s)
    fe_origin = os.getenv("FRONTEND_ORIGIN", "").strip()
    if fe_origin:
        # comma-separated support
        origins = _split_csv(fe_origin)
        return origins if origins else fe_origin

    # Backward compatible env
    legacy = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if legacy:
        if legacy == "*":
            return "*"
        return _split_csv(legacy)

    # Sensible defaults for local and workspace preview
    defaults = [
        "http://localhost:3000",
        "https://localhost:3000",
        # VSCode preview domains used in this workspace; allow subdomain wildcard via regex when applied below
        # Note: flask-cors accepts strings or regex patterns. We'll pass as strings and patterns in config.
    ]
    return defaults


# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask application.

    Configuration:
    - DATABASE_URL: SQLAlchemy database URL (required for Postgres).
      Falls back to local SQLite when not provided.
    - FRONTEND_ORIGIN: Allowed origin(s) for CORS (comma-separated supported).
      Example: http://localhost:3000,https://vscode-internal-*.cloud.kavia.ai:3000
    - CORS_ALLOWED_ORIGINS: Legacy fallback; if set to '*', allows all.

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

    # CORS: Restrict to API routes and allow required methods/headers
    cors_origins = _get_cors_origins()

    # Build resources config for /api/* only
    resources = {
        r"/api/*": {
            "origins": cors_origins
            if cors_origins != "*"
            else "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": False,
            "max_age": 600,
        }
    }

    # If defaults were used, also accept VSCode preview domains via regex
    if isinstance(cors_origins, list) and any("localhost:3000" in o for o in cors_origins):
        # Add regex for preview domain on port 3000
        resources[r"/api/*"]["origins"] = list(cors_origins) + [
            re.compile(r"^https://vscode-internal-[\w-]+\.cloud\.kavia\.ai:3000$")
        ]

    CORS(app, resources=resources)

    # API / Blueprints
    api = Api(app)
    api.register_blueprint(health_blp)
    api.register_blueprint(chat_blp)
    api.register_blueprint(models_blp)

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
