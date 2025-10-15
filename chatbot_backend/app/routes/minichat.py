from __future__ import annotations

import os
from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, jsonify, request, current_app

# Use a plain Flask Blueprint for a minimal endpoint (no OpenAPI required)
minichat_bp = Blueprint("MiniChat", __name__, url_prefix="/api")


# PUBLIC_INTERFACE
@minichat_bp.route("/chat", methods=["POST", "OPTIONS"])
def chat() -> tuple[Any, int] | Any:
    """Minimal chat endpoint that generates a reply using the Gemini API.

    Request:
    - Content-Type: application/json
    - Body: {"message": "<user message string>"}

    Environment:
    - AI_PROVIDER: defaults to "gemini"; currently only "gemini" is supported
    - GEMINI_API_KEY: Google Generative AI API key
    - GEMINI_MODEL: Optional model override (default 'gemini-2.5-flash')

    Responses:
    - 200: {"reply": "<assistant reply string>"}
    - 400: {"error": "<message>"} on invalid/missing payload or unsupported provider
    - 502: {"error": "<message>"} on provider/configuration error (e.g., missing/invalid API key or invalid model)
    - 500: {"error": "Internal server error"} on unexpected error

    Example curl:
        curl -s -X POST http://localhost:3001/api/chat \\
            -H "Content-Type: application/json" \\
            -d '{"message":"Hello! Who are you?"}'
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
        current_app.logger.warning("Unsupported AI_PROVIDER value received: %s", provider)
        return (
            jsonify({"error": f"AI_PROVIDER '{provider}' is not supported by this endpoint"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Call Gemini via the existing service wrapper
    try:
        from ..services.gemini_service import (
            GeminiService,
            GeminiConfigurationError,
            GeminiProviderError,
        )

        gemini = GeminiService()
        reply_text = gemini.generate_reply(message)
        # Ensure a string response even if service returns None/empty
        reply_text = reply_text if isinstance(reply_text, str) else ""
        return jsonify({"reply": reply_text}), HTTPStatus.OK

    except GeminiConfigurationError as exc:
        # Configuration issues (e.g., missing GEMINI_API_KEY) -> 502
        current_app.logger.error("Gemini configuration error: %s", exc)
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_GATEWAY

    except GeminiProviderError as exc:
        # Provider returned an error (auth, quota, model not found, content blocked, etc.) -> 502
        current_app.logger.error("Gemini provider error: %s", exc)
        # Include the actual model attempted if available
        from ..services.gemini_service import GeminiService  # type: ignore
        model_used = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        return jsonify({
            "error": f"Gemini provider error while using model '{model_used}': {exc}",
            "hint": "Ensure GEMINI_MODEL is supported by your API key and SDK. "
                    "Visit GET /api/models to see available chat-capable models and set GEMINI_MODEL accordingly."
        }), HTTPStatus.BAD_GATEWAY

    except Exception as exc:
        # Unexpected error; log with traceback but return generic message to client
        current_app.logger.exception("Unexpected error invoking Gemini: %s", exc)
        return jsonify({"error": "Internal server error"}), HTTPStatus.INTERNAL_SERVER_ERROR
