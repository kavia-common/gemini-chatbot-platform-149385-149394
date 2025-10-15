from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

# PUBLIC_INTERFACE
db = SQLAlchemy()


# PUBLIC_INTERFACE
def init_extensions(app) -> None:
    """Initialize Flask extensions with the provided app.

    This currently initializes:
    - SQLAlchemy (db)

    Args:
        app: Flask application instance.
    """
    db.init_app(app)
