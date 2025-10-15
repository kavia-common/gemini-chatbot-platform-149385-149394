from __future__ import annotations

import os
from typing import Optional

import google.generativeai as genai


class GeminiService:
    """Simple wrapper around Google Generative AI for synchronous text generation."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable not set. Please provide an API key."
            )
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    # PUBLIC_INTERFACE
    def generate_reply(self, prompt: str) -> str:
        """Generate a reply for a given user prompt.

        Args:
            prompt: The user prompt text.

        Returns:
            A string containing the assistant's reply.

        Raises:
            Exception: If the Gemini API call fails.
        """
        response = self.model.generate_content(prompt)
        # The SDK returns a structured response; pick best text representation
        if hasattr(response, "text") and response.text:
            return response.text
        # Fallbacks for older/newer SDK structures
        try:
            return str(response)
        except Exception:
            return "I'm sorry, I couldn't generate a response at this time."
