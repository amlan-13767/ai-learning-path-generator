"""Perplexity-powered resource search helper.

This module queries the Perplexity chat completion endpoint to retrieve
real, high-quality learning resources (videos, articles, docs) that a user
can click to continue learning. It returns a simple list of dictionaries so
upstream code can map them into `ResourceItem` Pydantic objects.

If the `PERPLEXITY_API_KEY` environment variable is missing, or the API call
fails, we fall back to a deterministic set of real educational resources for
that topic instead of using placeholder URLs.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, List
from urllib.parse import urlparse

import requests
from langsmith import traceable as langsmith_traceable

from src.utils.observability import get_observability_manager
from src.utils.config import (
    PERPLEXITY_PROMPT_COST_PER_1K,
    PERPLEXITY_COMPLETION_COST_PER_1K,
)

FALLBACK_RESOURCE_LIBRARY = (
    ("python", "https://docs.python.org/3/tutorial/", "Python Tutorial"),
    ("python", "https://docs.python.org/3/", "Python Documentation"),
    ("javascript", "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "JavaScript Guide"),
    ("html", "https://developer.mozilla.org/en-US/docs/Learn/HTML", "HTML Guide"),
    ("css", "https://developer.mozilla.org/en-US/docs/Learn/CSS", "CSS Guide"),
    ("react", "https://react.dev/learn", "React Learn"),
    ("postgresql", "https://www.postgresql.org/docs/", "PostgreSQL Documentation"),
    ("sql", "https://www.postgresql.org/docs/current/sql.html", "SQL Language Reference"),
    ("redis", "https://redis.io/docs/", "Redis Documentation"),
    ("docker", "https://docs.docker.com/", "Docker Documentation"),
    ("git", "https://git-scm.com/doc", "Git Documentation"),
    ("flask", "https://flask.palletsprojects.com/", "Flask Documentation"),
    ("scikit", "https://scikit-learn.org/stable/user_guide.html", "scikit-learn User Guide"),
    ("pytorch", "https://pytorch.org/tutorials/", "PyTorch Tutorials"),
    ("tensorflow", "https://www.tensorflow.org/tutorials", "TensorFlow Tutorials"),
    ("pandas", "https://pandas.pydata.org/docs/", "pandas Documentation"),
    ("numpy", "https://numpy.org/doc/stable/", "NumPy Documentation"),
    ("ml", "https://scikit-learn.org/stable/tutorial/index.html", "Machine Learning Tutorials"),
    ("data", "https://pandas.pydata.org/docs/user_guide/index.html", "pandas User Guide"),
    ("api", "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Client-side_web_APIs", "Web APIs Guide"),
)


def _normalize_url(value: str) -> str:
    """Return a normalized absolute URL or an empty string."""
    if not isinstance(value, str):
        return ""
    candidate = value.strip()
    if not candidate:
        return ""
    if not candidate.startswith(("http://", "https://")):
        return ""
    parsed = urlparse(candidate)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return candidate


def _is_placeholder_resource(url: str, title: str = "") -> bool:
    """Reject placeholder and malformed learning-resource values."""
    lowered_url = (url or "").lower()
    lowered_title = (title or "").lower()
    return (
        "example.com" in lowered_url
        or "placeholder-resource" in lowered_url
        or "placeholder" in lowered_title
        or "configure perplexity" in lowered_title
        or "example.com" in lowered_title
        or not lowered_url.startswith(("http://", "https://"))
    )


def _fallback_resources_for_query(query: str, k: int = 3) -> List[Dict[str, str]]:
    """Return deterministic real resources for a topic using authoritative docs."""
    normalized_query = (query or "").lower()
    out: List[Dict[str, str]] = []
    seen: set[str] = set()

    for keyword, url, title in FALLBACK_RESOURCE_LIBRARY:
        if keyword in normalized_query:
            cleaned_url = _normalize_url(url)
            if not cleaned_url or cleaned_url.lower() in seen:
                continue
            if _is_placeholder_resource(cleaned_url, title):
                continue
            out.append({"type": "article", "url": cleaned_url, "description": title})
            seen.add(cleaned_url.lower())
            if len(out) >= k:
                break

    if not out:
        candidate_url = "https://developer.mozilla.org/"
        out.append({
            "type": "article",
            "url": candidate_url,
            "description": "Developer documentation"
        })

    return out[:k]


def sanitize_resources(resources: List[Dict[str, str]], query: str, k: int = 3) -> List[Dict[str, str]]:
    """Validate, deduplicate, and trim resource entries before returning them."""
    sanitized: List[Dict[str, str]] = []
    seen_urls: set[str] = set()

    for item in resources or []:
        if not isinstance(item, dict):
            continue
        raw_url = item.get("url", "")
        raw_title = item.get("description") or item.get("title") or ""
        url = _normalize_url(raw_url)
        title = str(raw_title).strip()

        if not url or _is_placeholder_resource(url, title):
            continue
        if not title:
            title = "Official documentation"
        if _is_placeholder_resource("", title):
            continue
        if url.lower() in seen_urls:
            continue

        seen_urls.add(url.lower())
        sanitized.append({
            "type": item.get("type", "article") or "article",
            "url": url,
            "description": title,
        })
        if len(sanitized) >= k:
            break

    if sanitized:
        return sanitized
    return _fallback_resources_for_query(query, k)


def _extract_keywords(query: str) -> List[str]:
    """Collect meaningful keywords from the query for simple relevance filtering."""
    tokens = re.findall(r"[\w']+", query.lower())
    stopwords = {
        "the",
        "with",
        "your",
        "from",
        "this",
        "that",
        "about",
        "topic",
        "learn",
        "learning",
        "skill",
        "skills",
        "path",
        "guide",
        "study",
        "course",
        "for",
        "into",
        "using",
        "based",
        "mastery",
        "introduction",
        "advanced",
        "beginner",
        "intermediate",
    }
    keywords = [tok for tok in tokens if len(tok) > 3 and tok not in stopwords]

    if ":" in query:
        parts = query.split(":")
        main_topic = parts[0].strip().lower()
        main_tokens = re.findall(r"[\w']+", main_topic)
        keywords.extend([tok for tok in main_tokens if len(tok) > 3 and tok not in stopwords])

    return list(set(keywords))


def _filter_by_keywords(resources: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
    """Filter out resources that do not mention any significant query keywords."""
    keywords = _extract_keywords(query)
    if not keywords:
        return resources

    main_topic = query.split(":")[0].strip().lower() if ":" in query else query.split()[0].lower()

    filtered: List[Dict[str, str]] = []
    for item in resources:
        haystack = " ".join(
            [item.get("url", ""), item.get("description", ""), item.get("type", "")]
        ).lower()

        if main_topic not in haystack:
            logging.info(f"⚠️  Filtered out resource (missing main topic '{main_topic}'): {item.get('description', '')[:50]}")
            continue

        if any(keyword in haystack for keyword in keywords):
            filtered.append(item)

    if not filtered:
        logging.warning(f"All resources filtered out for query '{query}'. Keeping originals.")
    return filtered or resources


@langsmith_traceable(name="perplexity_resource_search")
def search_resources(query: str, k: int = 3, timeout: int = 45, trusted_sources: Dict[str, List[str]] = None) -> List[Dict[str, str]]:
    """Search for learning resources using Perplexity.

    Each dict has keys: `type`, `url`, `description`.
    """
    source_instruction = ""
    if trusted_sources:
        youtube_channels = trusted_sources.get('youtube', [])
        websites = trusted_sources.get('websites', [])

        if youtube_channels or websites:
            source_instruction = "\n\n🎯 CRITICAL - SEARCH ONLY IN THESE CURATED SOURCES:\n"
            if youtube_channels:
                source_instruction += f"✅ APPROVED YouTube Channels (search ONLY these): {', '.join(youtube_channels)}\n"
                source_instruction += "   - Go to each channel's videos page\n"
                source_instruction += "   - Find videos that match the query topic\n"
                source_instruction += "   - Return DIRECT video watch URLs (youtube.com/watch?v=...)\n"
            if websites:
                source_instruction += f"✅ APPROVED Websites (search ONLY these): {', '.join(websites)}\n"
                source_instruction += "   - Search within these domains for relevant content\n"
                source_instruction += "   - Return direct article/tutorial URLs, not homepages\n"
            source_instruction += "\n❌ FORBIDDEN: Do NOT search or suggest content from ANY other sources\n"
            source_instruction += "❌ FORBIDDEN: Do NOT make up or hallucinate URLs\n"
            source_instruction += "✅ REQUIRED: Every URL must be from the approved list above\n"
            source_instruction += "✅ REQUIRED: Every URL must be a real, existing page you found by searching\n"

    prompt = (
        f"Search the web and find {k} real, working FREE learning resources SPECIFICALLY for: '{query}'. "
        "\n"
        "🎯 CRITICAL REQUIREMENTS:\n"
        "1. PRIORITIZE FREE CONTENT: YouTube videos, free tutorials, open documentation\n"
        "2. AVOID PAID COURSES: Do NOT suggest Udemy, Coursera, or any paid platforms unless they have free content\n"
        "3. DIRECT VIDEO LINKS ONLY: For YouTube, provide DIRECT VIDEO LINKS (youtube.com/watch?v=...), NOT:\n"
        "   - Channel homepages\n"
        "   - Playlist pages\n"
        "   - Search result pages\n"
        "4. SPECIFIC ARTICLES: For websites, link to the SPECIFIC PAGE/ARTICLE, not homepages\n"
        "5. EXACT TOPIC MATCH: Every resource MUST be directly about the EXACT topic in the query\n"
        "6. VERIFY RELEVANCE: The resource title/description must explicitly mention the main topic\n"
        "7. PREFER COMPREHENSIVE CONTENT: Look for 'full course', 'complete tutorial', 'crash course'\n"
        f"{source_instruction}"
        "\n"
        "📺 YOUTUBE PRIORITY: At least 60% of resources should be YouTube videos with direct watch links\n"
        "\n"
        "Return ONLY valid JSON array (no markdown, no code blocks) with format: "
        '[{"type": "video", "url": "https://youtube.com/watch?v=...", "description": "Full Course Title by Channel Name"}, ...]'
        "\n"
        "✅ VALIDATION: Each URL must be:\n"
        "- A real, working link that exists right now\n"
        "- Directly clickable and accessible\n"
    )

    obs_manager = get_observability_manager()
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    if not perplexity_key:
        logging.info("PERPLEXITY_API_KEY not set; returning deterministic fallback resources.")
        return _fallback_resources_for_query(query, k)

    try:
        logging.info("Searching for resources using Perplexity (web search)...")
        start_time = time.time()
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that searches the web for real learning resources. Always return valid JSON with actual, working URLs.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        completion = response.json()
        latency_ms = (time.time() - start_time) * 1000
        content = completion["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        resources: List[Dict[str, str]] = json.loads(content)
        cleaned: List[Dict[str, str]] = []
        for item in resources[:k]:
            cleaned.append({
                "type": item.get("type", "article"),
                "url": item.get("url", ""),
                "description": item.get("description", "") or item.get("title", ""),
            })

        if cleaned:
            cleaned = _filter_by_keywords(cleaned, query)
            cleaned = sanitize_resources(cleaned, query, k)
            if cleaned:
                logging.info(f"✅ Found {len(cleaned)} resources via Perplexity")

                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

                usage = getattr(completion, "usage", None)
                if usage:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0)
                    completion_tokens = getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0)
                    total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
                else:
                    usage_payload = None
                    if hasattr(completion, "model_dump") and callable(completion.model_dump):
                        usage_payload = completion.model_dump().get("usage")
                    elif isinstance(completion, dict):
                        usage_payload = completion.get("usage")

                    if usage_payload:
                        prompt_tokens = usage_payload.get("prompt_tokens", usage_payload.get("input_tokens", 0))
                        completion_tokens = usage_payload.get("completion_tokens", usage_payload.get("output_tokens", 0))
                        total_tokens = usage_payload.get("total_tokens", prompt_tokens + completion_tokens)

                perplexity_cost = 0.0
                if PERPLEXITY_PROMPT_COST_PER_1K > 0 or PERPLEXITY_COMPLETION_COST_PER_1K > 0:
                    perplexity_cost = (
                        (prompt_tokens / 1000.0) * PERPLEXITY_PROMPT_COST_PER_1K
                        + (completion_tokens / 1000.0) * PERPLEXITY_COMPLETION_COST_PER_1K
                    )

                obs_manager.log_llm_call(
                    prompt=prompt,
                    response=content,
                    model="perplexity-sonar-pro",
                    metadata={
                        "provider": "perplexity",
                        "query": query,
                        "trusted_sources": trusted_sources or {},
                    },
                    latency_ms=latency_ms,
                    token_count=total_tokens or None,
                    cost=perplexity_cost or None,
                )

                obs_manager.log_metric(
                    "perplexity_latency_ms",
                    float(latency_ms),
                    {"query": query, "result_count": len(cleaned)},
                )

                if prompt_tokens:
                    obs_manager.log_metric("perplexity_prompt_tokens", float(prompt_tokens), {"query": query})
                if completion_tokens:
                    obs_manager.log_metric("perplexity_completion_tokens", float(completion_tokens), {"query": query})
                if perplexity_cost:
                    obs_manager.log_metric("perplexity_cost_usd", perplexity_cost, {"query": query})

                return cleaned
    except Exception as exc:
        logging.warning(f"Perplexity resource search failed for query '{query}': {exc}. Falling back to real educational resources.")

    return _fallback_resources_for_query(query, k)

