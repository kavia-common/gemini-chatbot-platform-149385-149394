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
    """Simple wrapper around Google Generative AI for synchronous text generation."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY environment variable not set. Please provide an API key."
            )

        # Configure client
        genai.configure(api_key=self.api_key)

        # Initialize model (common models: 'gemini-1.5-flash', 'gemini-1.5-pro')
        try:
            self.model = genai.GenerativeModel(model_name)
            logger.debug("Initialized GeminiService with model '%s'", model_name)
        except Exception as exc:
            # Surface model/initialization errors as provider errors
            raise GeminiProviderError(f"Failed to initialize Gemini model '{model_name}': {exc}") from exc

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
        try:
            response = self.model.generate_content(prompt)
        except Exception as exc:
            # Attempt to classify common provider errors for clearer messages
            msg = str(exc)
            if any(term in msg.lower() for term in ["unauthorized", "permission", "auth", "invalid api key"]):
                raise GeminiProviderError("Authentication with Gemini failed. Check GEMINI_API_KEY.") from exc
            raise GeminiProviderError(f"Failed to call Gemini API: {exc}") from exc

        # The SDK returns a structured response; use best text representation
        try:
            # Prefer .text when available
            if hasattr(response, "text") and response.text:
                return response.text

            # Check for known block reasons in prompt_feedback
            prompt_feedback = getattr(response, "prompt_feedback", None)
            block_reason = getattr(prompt_feedback, "block_reason", None) if prompt_feedback else None
            if block_reason:
                raise GeminiProviderError(f"Request blocked by safety settings: {block_reason}")

            # Fallbacks for different SDK structures
            candidates = getattr(response, "candidates", None)
            if candidates:
                # Try to extract first candidate text
                try:
                    parts = candidates[0].content.parts  # type: ignore[attr-defined]
                    texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
                    if texts:
                        return " ".join(texts).strip()
                except Exception:
                    pass

            # Last resort: stringification
            return str(response)
        except GeminiProviderError:
            # Re-raise provider errors as-is
            raise
        except Exception as exc:
            # Unknown parsing shape
            logger.exception("Unexpected response parsing error: %s", exc)
            return "I'm sorry, I couldn't generate a response at this time."
