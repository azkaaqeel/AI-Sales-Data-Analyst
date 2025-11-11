from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from utils.errors import InsightModelError

class GeminiClient:
    """
    Thin wrapper around Google's Gemini GenerativeModel that conforms to InsightLLM.
    """
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        client_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise InsightModelError("Missing GOOGLE_API_KEY for Gemini.")
        genai.configure(api_key=key)

        try:
            self.model = genai.GenerativeModel(model_name, **(client_config or {}))
        except Exception as exc:
            raise InsightModelError(f"Failed to initialize Gemini model '{model_name}': {exc}") from exc

    def generate(
        self,
        prompt: str,
        images: List[bytes],
        *,
        temperature: float = 0.6,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            parts: List[Dict[str, Any]] = [{"text": prompt}]
            for data in images:
                if data:
                    parts.append({"mime_type": "image/png", "data": data})

            # Allow text-only prompts (no images required)
            # Only require images for insight generation use case
            if len(parts) == 1 and not prompt.strip():
                raise InsightModelError("Empty prompt provided to Gemini.")

            cfg = {"temperature": temperature}
            if extra and "generation_config" in extra:
                # allow caller overrides
                cfg.update(extra["generation_config"])

            resp = self.model.generate_content(parts, generation_config=cfg)
            text_output: Optional[str] = getattr(resp, "text", None)
            if not text_output or not text_output.strip():
                raise InsightModelError("Gemini returned empty text.")

            return text_output.strip()

        except GoogleAPIError as exc:
            raise InsightModelError(f"Gemini API error: {exc}") from exc
        except Exception as exc:
            raise InsightModelError(f"Unexpected Gemini error: {exc}") from exc
    
    def generate_text_only(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate text without images (for column mapping, classification, etc.)
        """
        return self.generate(prompt, images=[], temperature=temperature, extra=extra)
