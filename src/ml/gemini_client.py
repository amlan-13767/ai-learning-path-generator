"""Small server-side REST client for Gemini text generation."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from src.utils.config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiError(RuntimeError):
    """Controlled error raised when Gemini cannot return generated text."""


class GeminiClient:
    """Call Gemini's generateContent REST endpoint without exposing credentials."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        self.model = model or os.getenv("GEMINI_MODEL") or GEMINI_MODEL
        self.timeout = timeout

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Return clean generated text or raise a safe, actionable GeminiError."""
        if not self.api_key:
            raise GeminiError("Gemini API key is not configured.")
        if not prompt or not prompt.strip():
            raise GeminiError("Gemini prompt cannot be empty.")

        model = self.model.removeprefix("models/")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        contents: list[Dict[str, Any]] = [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_message:
            payload["systemInstruction"] = {
                "parts": [{"text": system_message}]
            }

        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise GeminiError("Gemini request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise GeminiError("Gemini network request failed.") from exc

        if response.status_code == 429:
            raise GeminiError("Gemini rate limit reached. Please try again later.")

        if response.status_code in (400, 401, 403):
            try:
                detail = response.json().get("error", {}).get("message", "unknown error")
            except ValueError:
                detail = response.text[:500]
            raise GeminiError(
                f"Gemini rejected the request ({response.status_code}): {detail}"
            )

        if response.status_code >= 500:
            try:
                detail = response.json().get("error", {}).get("message", "unknown error")
            except ValueError:
                detail = response.text[:500]
            raise GeminiError(
                f"Gemini service error ({response.status_code}): {detail}"
            )

        if not response.ok:
            raise GeminiError(
                f"Gemini request failed ({response.status_code}): {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise GeminiError("Gemini returned malformed JSON.") from exc

        text = self._extract_text(data)
        if not text:
            raise GeminiError("Gemini returned an empty response.")
        return text.strip()

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return ""
        content = candidates[0].get("content")
        if not isinstance(content, dict):
            return ""
        parts = content.get("parts")
        if not isinstance(parts, list):
            return ""
        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )