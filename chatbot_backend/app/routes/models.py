from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, jsonify
from ..services.gemini_service import GeminiService, GeminiConfigurationError

blp = Blueprint("Models", __name__, url_prefix="/api")

# PUBLIC_INTERFACE
@blp.route("/models", methods=["GET"])
def list_models():
    """List available Gemini model IDs accessible to the current API key.

    Returns:
        200: JSON with fields:
            - models: list of all visible model names
            - chat_capable: filtered list of likely chat-capable models
        502: if GEMINI_API_KEY is missing
    """
    try:
        all_models = GeminiService.list_available_models()
        chat_capable = GeminiService.filter_chat_capable(all_models)
        return jsonify({"models": all_models, "chat_capable": chat_capable}), HTTPStatus.OK
    except GeminiConfigurationError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_GATEWAY
