from __future__ import annotations

import os
from app import app

if __name__ == "__main__":
    # Bind to 0.0.0.0 and port 3001 by default to support workspace preview and Docker.
    # Allow overrides via environment variables FLASK_HOST and FLASK_PORT.
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("FLASK_PORT", os.getenv("PORT", "3001")))
    except ValueError:
        port = 3001

    debug = os.getenv("FLASK_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")
    app.run(host=host, port=port, debug=debug)
