from __future__ import annotations

import os
from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, jsonify, request

# Use a plain Flask Blueprint for a minimal endpoint (no OpenAPI required)
minichat_bp = Blueprint("MiniChat", __name__, url_prefix="/api")


# PUBLIC_INTERFACE
@minichat_bp.route("/chat", methods=["POST"])
def chat() -> tuple[Any, int] | Any:
    """Minimal chat endpoint that generates a reply using the Gemini API.

    Request:
    - Content-Type: application/json
    - Body: {"message": "<user message string>"}

    Environment:
    - AI_PROVIDER: defaults to "gemini"; currently only "gemini" is supported
    - GEMINI_API_KEY: Google Generative AI API key

    Responses:
    - 200: {"reply": "<assistant reply string>"}
    - 400: {"error": "<message>"} on invalid/missing payload
    - 500: {"error": "<message>"} on provider or internal error
    """
    # Validate JSON body
    if not request.is_json:
        return jsonify({"error": "Request must be application/json"}), HTTPStatus.BAD_REQUEST

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    message = payload.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Field 'message' is required and must be a non-empty string"}), HTTPStatus.BAD_REQUEST

    # Check provider (default to 'gemini')
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    if provider != "gemini":
        # For this minimal endpoint, only Gemini is supported.
        return (
            jsonify({"error": f"AI_PROVIDER '{provider}' is not supported by this endpoint"}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    # Call Gemini via the existing service wrapper
    try:
        from ..services.gemini_service import GeminiService

        gemini = GeminiService()
        reply_text = gemini.generate_reply(message)
        # Ensure a string response even if service returns None/empty
        reply_text = reply_text if isinstance(reply_text, str) else ""
        return jsonify({"reply": reply_text}), HTTPStatus.OK
    except Exception:
        # Do not leak internal details to the client
        return jsonify({"error": "Provider error"}), HTTPStatus.INTERNAL_SERVER_ERROR
