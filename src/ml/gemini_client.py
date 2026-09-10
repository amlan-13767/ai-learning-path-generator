"""Small server-side REST client for Gemini text generation."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests

from src.utils.config import GEMINI_API_KEY, GEMINI_MODEL

DEFAULT_GEMINI_MAX_TOKENS = 4000
TRANSIENT_GEMINI_STATUS_CODES = (500, 502, 503, 504)


class GeminiError(RuntimeError):
    """Controlled error raised when Gemini cannot return generated text."""


class GeminiClient:
    """Call Gemini's generateContent REST endpoint without exposing credentials."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        self.model = model or os.getenv("GEMINI_MODEL") or GEMINI_MODEL
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self.backoff_base_seconds = max(0.25, float(backoff_base_seconds))

    @staticmethod
    def _json_detail(response: requests.Response) -> str:
        try:
            return response.json().get("error", {}).get("message", "unknown error")
        except ValueError:
            return response.text[:500]

    @staticmethod
    def _safe_retry_after(response: requests.Response) -> Optional[float]:
        retry_after = getattr(response, "headers", {}).get("Retry-After")
        if retry_after is None:
            return None
        try:
            value = float(retry_after)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        return min(value, 5.0)

    def _retry_delay(self, attempt: int, response: Optional[requests.Response] = None) -> float:
        retry_after = self._safe_retry_after(response) if response is not None else None
        if retry_after is not None:
            return retry_after
        return min(self.backoff_base_seconds * (2 ** attempt), 4.0)

    def _request_with_retry(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        last_response: Optional[requests.Response] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout as exc:
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt))
                    continue
                raise GeminiError("Gemini request timed out.") from exc
            except requests.exceptions.RequestException as exc:
                raise GeminiError("Gemini network request failed.") from exc

            status_code = response.status_code
            last_response = response

            if status_code == 429:
                if attempt < self.max_retries:
                    retry_after = self._safe_retry_after(response)
                    if retry_after is not None:
                        time.sleep(retry_after)
                        continue
                raise GeminiError("Gemini rate limit reached. Please try again later.")

            if status_code in (400, 401, 403):
                raise GeminiError(
                    f"Gemini rejected the request ({status_code}): {self._json_detail(response)}"
                )

            if status_code in TRANSIENT_GEMINI_STATUS_CODES:
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt, response))
                    continue
                detail = self._json_detail(response)
                raise GeminiError(
                    f"Gemini service is temporarily unavailable after retries ({status_code}): {detail}. Please try again later."
                )

            if not response.ok:
                raise GeminiError(
                    f"Gemini request failed ({status_code}): {response.text[:500]}"
                )

            return response

        if last_response is not None:
            raise GeminiError(
                f"Gemini request failed ({last_response.status_code}): {last_response.text[:500]}"
            )
        raise GeminiError("Gemini request failed.")

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return clean generated text or raise a safe, actionable GeminiError."""
        if not self.api_key:
            raise GeminiError("Gemini API key is not configured.")
        if not prompt or not prompt.strip():
            raise GeminiError("Gemini prompt cannot be empty.")

        effective_max_tokens = int(max_tokens) if max_tokens is not None else DEFAULT_GEMINI_MAX_TOKENS
        if effective_max_tokens <= 0:
            effective_max_tokens = DEFAULT_GEMINI_MAX_TOKENS

        model = self.model.removeprefix("models/")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        contents: list[Dict[str, Any]] = [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": effective_max_tokens,
            },
        }
        if system_message:
            payload["systemInstruction"] = {
                "parts": [{"text": system_message}]
            }

        response = self._request_with_retry(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            payload=payload,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise GeminiError("Gemini returned malformed JSON.") from exc

        return self._extract_text(data)

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            raise GeminiError("Gemini returned malformed JSON.")

        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiError("Gemini returned no candidates in the response.")

        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise GeminiError("Gemini returned an empty or malformed candidate.")

        finish_reason = candidate.get("finishReason")
        content = candidate.get("content")
        if not isinstance(content, dict):
            if finish_reason == "MAX_TOKENS":
                raise GeminiError(
                    "Gemini generation exhausted its token budget before producing visible text. Increase max_tokens and try again."
                )
            raise GeminiError("Gemini returned an empty response.")

        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            if finish_reason == "MAX_TOKENS":
                raise GeminiError(
                    "Gemini generation exhausted its token budget before producing visible text. Increase max_tokens and try again."
                )
            raise GeminiError("Gemini returned no visible text content.")

        texts = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str):
                texts.append(text)

        if not texts:
            if finish_reason == "MAX_TOKENS":
                raise GeminiError(
                    "Gemini generation exhausted its token budget before producing visible text. Increase max_tokens and try again."
                )
            raise GeminiError("Gemini returned no visible text content.")

        return "".join(texts).strip()