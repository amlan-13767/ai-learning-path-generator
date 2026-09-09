"""Helpers to fetch real-time job-market data using Perplexity API.

The function `get_job_market_stats` queries Perplexity (online search model)
with a carefully crafted prompt asking for a JSON-only response containing:
  - open_positions: string (e.g. "15,000+")
  - average_salary: string (e.g. "$110,000 - $150,000")
  - trending_employers: array[str] of 3 employer names

Perplexity provides real-time web search results, making it useful for
current job market data.

If the API or JSON parsing fails, we return a static fallback so the UI
still renders a snapshot.
"""
from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any

import requests

_DEFAULT_SNAPSHOT: Dict[str, Any] = {
    "open_positions": "5,000+",
    "average_salary": "$120,000 - $160,000",
    "trending_employers": ["Big Tech Co", "Innovative Startup", "Data Insights Inc"],
}

PROMPT_TEMPLATE = (
    "Search the web for current US job market data for '{topic}' roles. "
    "Provide real-time statistics from job boards like LinkedIn, Indeed, Glassdoor. "
    "Return ONLY valid JSON (no markdown, no code blocks) with keys: "
    "open_positions (string like '15,000+'), "
    "average_salary (string like '$110,000 - $150,000'), "
    "trending_employers (array of 3 real company names currently hiring)."
)


def _call_perplexity(prompt: str, timeout: int = 45) -> str:
    """Call Perplexity API for real-time web search results."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("PERPLEXITY_API_KEY env var not set")
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that searches the web for current job market data. Always return valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Malformed Perplexity response") from exc


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.strip().startswith("json"):
                text = part[4:].strip()
            elif part.strip() and not part.strip().startswith("```"):
                text = part.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    
    raise ValueError("Unable to parse JSON from API response")


def get_job_market_stats(topic: str) -> Dict[str, Any]:
    """Return real-time job-market stats using Perplexity or a static snapshot."""
    if topic == "__fallback__":
        return _DEFAULT_SNAPSHOT.copy()
    
    prompt = PROMPT_TEMPLATE.format(topic=topic)
    
    # Try Perplexity first (real-time web search)
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    print(f"DEBUG: Perplexity API key present: {bool(perplexity_key)}")
    
    if perplexity_key:
        try:
            print(f"DEBUG: Attempting Perplexity search for '{topic}'...")
            logging.info(f"Fetching job market data for '{topic}' using Perplexity (real-time search)...")
            raw = _call_perplexity(prompt)
            print(f"DEBUG: Perplexity raw response: {raw[:200]}...")
            data = _extract_json(raw)
            print(f"DEBUG: Perplexity parsed data: {data}")
            
            # Basic validation
            if not all(k in data for k in ("open_positions", "average_salary", "trending_employers")):
                raise ValueError("Missing required keys in Perplexity response")
            
            print(f"✅ Successfully fetched real-time job data via Perplexity")
            logging.info(f"✅ Successfully fetched real-time job data via Perplexity")
            return data
        except Exception as exc:
            print(f"ERROR: Perplexity failed: {exc}")
            logging.warning(f"Perplexity job-market fetch failed: {exc}. Using default snapshot.")

    return _DEFAULT_SNAPSHOT.copy()
