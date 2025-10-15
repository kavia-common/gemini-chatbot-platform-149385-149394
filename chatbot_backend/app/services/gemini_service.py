from __future__ import annotations

import logging
import os
from typing import Optional, Tuple, List

import google.generativeai as genai


class GeminiConfigurationError(Exception):
    """Raised for configuration issues (e.g., missing API key)."""


class GeminiProviderError(Exception):
    """Raised when the Gemini provider returns an error or request fails."""


logger = logging.getLogger(__name__)

# A conservative, known-good shortlist of text-capable models for this project.
# This should align with versions commonly available in the google-generativeai SDK used.
_SUPPORTED_MODELS: List[str] = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

# Default fallback model if provided model is unsupported/unavailable.
_DEFAULT_FALLBACK_MODEL = "gemini-1.5-flash"


def _normalize_model_name(name: str) -> str:
    """Normalize model name by trimming whitespace."""
    return (name or "").strip()


def _select_model(env_model: str | None, override: str | None) -> Tuple[str, Optional[str]]:
    """
    Determine the model to use based on override and environment with validation.

    Priority:
    1) Explicit override passed to the service
    2) GEMINI_MODEL environment variable
    3) Default fallback

    Returns:
        (chosen_model, warning_message_if_any)
    """
    # Strictly respect the provided override if present; otherwise use env; else fallback
    candidate = _normalize_model_name(override) or _normalize_model_name(env_model)
    warning: Optional[str] = None

    if candidate:
        # If candidate is supported from our shortlist, use it directly.
        if candidate in _SUPPORTED_MODELS:
            return candidate, None
        # If candidate not in shortlist, attempt to initialize later and gracefully fallback
        # but record a warning for logs.
        warning = (
            f"GEMINI_MODEL '{candidate}' is not in supported shortlist. "
            f"Will attempt to initialize; if it fails, falling back to '{_DEFAULT_FALLBACK_MODEL}'."
        )
        return candidate, warning

    # No candidate provided -> use default
    return _DEFAULT_FALLBACK_MODEL, None


class GeminiService:
    """Simple wrapper around Google Generative AI for synchronous text generation.

    Model selection and configuration:
    - Reads GEMINI_API_KEY from the environment (required).
    - Reads GEMINI_MODEL from the environment; defaults to a safe fallback if unset.
    - Uses the official google-generativeai SDK (no direct v1beta REST calls).
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # Resolve credentials
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY environment variable not set. Please provide an API key."
            )

        # Configure client once per process
        try:
            genai.configure(api_key=self.api_key)
        except Exception as exc:
            raise GeminiConfigurationError(f"Failed to configure Gemini client: {exc}") from exc

        # Resolve model with validation and potential fallback
        env_model = os.getenv("GEMINI_MODEL")
        chosen, warn = _select_model(env_model, model_name)
        self.requested_model_name = _normalize_model_name(model_name) or _normalize_model_name(env_model) or ""
        self.model_name = chosen

        if warn:
            logger.warning(warn)

        # Try to initialize the chosen model; if it fails and is not the default fallback, try fallback.
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Initialized GeminiService using model '%s'", self.model_name)
        except Exception as primary_exc:
            # If user requested a model that fails to init, gracefully fallback once.
            if self.model_name != _DEFAULT_FALLBACK_MODEL:
                logger.warning(
                    "Failed to initialize requested model '%s': %s. Falling back to '%s'.",
                    self.model_name,
                    primary_exc,
                    _DEFAULT_FALLBACK_MODEL,
                )
                try:
                    self.model_name = _DEFAULT_FALLBACK_MODEL
                    self.model = genai.GenerativeModel(self.model_name)
                    logger.info("Fallback initialization successful with model '%s'", self.model_name)
                except Exception as fallback_exc:
                    # Provide a clear, actionable error including valid models
                    raise GeminiProviderError(
                        "Failed to initialize Gemini model(s). "
                        f"Requested: '{self.requested_model_name or 'N/A'}' | "
                        f"Tried: '{chosen}', then fallback '{_DEFAULT_FALLBACK_MODEL}'. "
                        f"Error: {fallback_exc}. "
                        "Set GEMINI_MODEL to one of: "
                        + ", ".join(_SUPPORTED_MODELS)
                    ) from fallback_exc
            else:
                # Even default failed: surface a detailed error
                raise GeminiProviderError(
                    f"Failed to initialize default Gemini model '{self.model_name}': {primary_exc}. "
                    "Consider checking your SDK version or setting GEMINI_MODEL to one of: "
                    + ", ".join(_SUPPORTED_MODELS)
                ) from primary_exc

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
                raise GeminiProviderError(
                    f"Authentication with Gemini failed while using model '{self.model_name}'. "
                    "Check GEMINI_API_KEY."
                ) from exc
            if "not found" in lower or ("model" in lower and "not" in lower and "found" in lower):
                raise GeminiProviderError(
                    f"Model '{self.model_name}' not found or not available in the current SDK/account. "
                    "Set GEMINI_MODEL to a supported model such as: "
                    + ", ".join(_SUPPORTED_MODELS)
                ) from exc
            raise GeminiProviderError(
                f"Failed to call Gemini API with model '{self.model_name}': {exc}"
            ) from exc

        # Parse response consistently across SDK versions
        try:
            # Prefer .text when available
            if getattr(response, "text", None):
                return str(response.text)

            # Check for prompt feedback blocking
            prompt_feedback = getattr(response, "prompt_feedback", None)
            block_reason = getattr(prompt_feedback, "block_reason", None) if prompt_feedback else None
            if block_reason:
                raise GeminiProviderError(
                    f"Request blocked by safety settings (model '{self.model_name}'): {block_reason}"
                )

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
            logger.exception("Unexpected response parsing error for model '%s': %s", self.model_name, exc)
            return "I'm sorry, I couldn't generate a response at this time."
