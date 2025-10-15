from __future__ import annotations

import logging
import os
from typing import Optional

import google.generativeai as genai


class GeminiConfigurationError(Exception):
    """Raised for configuration issues (e.g., missing API key)."""


class GeminiProviderError(Exception):
    """Raised when the Gemini provider returns an error or request fails."""


logger = logging.getLogger(__name__)


class GeminiService:
    """Simple wrapper around Google Generative AI for synchronous text generation.

    Model selection and configuration:
    - Reads GEMINI_API_KEY from the environment (required).
    - Reads GEMINI_MODEL from the environment; defaults to 'gemini-1.5-flash' if unset.
    - Uses the official google-generativeai SDK (no direct v1beta REST calls).
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # Resolve credentials
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY environment variable not set. Please provide an API key."
            )

        # Resolve model with safe default
        env_model = (os.getenv("GEMINI_MODEL") or "").strip()
        self.model_name = model_name or env_model or "gemini-1.5-flash"

        # Configure client once per process
        try:
            genai.configure(api_key=self.api_key)
        except Exception as exc:
            raise GeminiConfigurationError(f"Failed to configure Gemini client: {exc}") from exc

        # Initialize model (current sdk supports e.g. 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro')
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.debug("Initialized GeminiService with model '%s'", self.model_name)
        except Exception as exc:
            raise GeminiProviderError(f"Failed to initialize Gemini model '{self.model_name}': {exc}") from exc

    # PUBLIC_INTERFACE
    def generate_reply(self, prompt: str) -> str:
        """Generate a reply for a given user prompt.

        Args:
            prompt: The user prompt text.

        Returns:
            A string containing the assistant's reply.

        Raises:
            GeminiConfigurationError: If configuration is invalid.
            GeminiProviderError: If the Gemini API call fails or content is blocked.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return ""

        try:
            # Use standard SDK method; avoids manual v1beta REST usage.
            response = self.model.generate_content(prompt)
        except Exception as exc:
            msg = str(exc)
            lower = msg.lower()
            if any(term in lower for term in ["unauthorized", "permission", "auth", "invalid api key", "apikey"]):
                raise GeminiProviderError("Authentication with Gemini failed. Check GEMINI_API_KEY.") from exc
            if "not found" in lower or "model" in lower and "not" in lower and "found" in lower:
                raise GeminiProviderError(
                    f"Model '{self.model_name}' not found or not available. "
                    "Try setting GEMINI_MODEL to a valid model (e.g., 'gemini-1.5-flash' or 'gemini-1.5-flash-8b')."
                ) from exc
            raise GeminiProviderError(f"Failed to call Gemini API: {exc}") from exc

        # Parse response consistently across SDK versions
        try:
            # Prefer .text when available
            if getattr(response, "text", None):
                return str(response.text)

            # Check for prompt feedback blocking
            prompt_feedback = getattr(response, "prompt_feedback", None)
            block_reason = getattr(prompt_feedback, "block_reason", None) if prompt_feedback else None
            if block_reason:
                raise GeminiProviderError(f"Request blocked by safety settings: {block_reason}")

            # Fallback: try candidates structure
            candidates = getattr(response, "candidates", None)
            if candidates:
                try:
                    parts = getattr(candidates[0].content, "parts", None)
                    if parts:
                        texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
                        if texts:
                            return " ".join(texts).strip()
                except Exception:
                    pass

            # Last resort
            return str(response)
        except GeminiProviderError:
            raise
        except Exception as exc:
            logger.exception("Unexpected response parsing error: %s", exc)
            return "I'm sorry, I couldn't generate a response at this time."
