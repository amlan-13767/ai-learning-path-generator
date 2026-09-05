"""OpenAI-powered resource search helper.

This module queries the OpenAI Chat Completion endpoint to retrieve
real, high-quality learning resources (videos, articles, docs) that a user
can click to continue learning. It returns a simple list of dictionaries so
upstream code can map them into `ResourceItem` Pydantic objects.

If the `OPENAI_API_KEY` environment variable is missing, or the API call
fails, we fall back to a single placeholder so the rest of the app
continues to work.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, List

from openai import OpenAI
from langsmith import traceable as langsmith_traceable

from src.utils.observability import get_observability_manager
from src.utils.config import (
    PERPLEXITY_PROMPT_COST_PER_1K,
    PERPLEXITY_COMPLETION_COST_PER_1K,
)

# Initialize OpenAI client
client = None


def _stub_resources() -> List[Dict[str, str]]:
    """Return a static placeholder when real search is unavailable."""
    return [
        {
            "type": "article",
            "url": "https://example.com/placeholder-resource",
            "description": "Add your OpenAI API key to see real learning resources.",
        }
    ]

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
    # Extract keywords, prioritizing the first word (usually the main topic)
    keywords = [tok for tok in tokens if len(tok) > 3 and tok not in stopwords]
    
    # If query has a colon (e.g., "Mandarin: Pronunciation"), extract both parts
    if ":" in query:
        parts = query.split(":")
        main_topic = parts[0].strip().lower()
        # Main topic is critical - add all its words
        main_tokens = re.findall(r"[\w']+", main_topic)
        keywords.extend([tok for tok in main_tokens if len(tok) > 3 and tok not in stopwords])
    
    return list(set(keywords))  # Remove duplicates


def _filter_by_keywords(resources: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
    """Filter out resources that do not mention any significant query keywords."""
    keywords = _extract_keywords(query)
    if not keywords:
        return resources

    # Extract main topic (first word or word before colon)
    main_topic = query.split(":")[0].strip().lower() if ":" in query else query.split()[0].lower()
    
    filtered: List[Dict[str, str]] = []
    for item in resources:
        haystack = " ".join(
            [item.get("url", ""), item.get("description", ""), item.get("type", "")]
        ).lower()
        
        # STRICT: Main topic MUST be present
        if main_topic not in haystack:
            logging.info(f"⚠️  Filtered out resource (missing main topic '{main_topic}'): {item.get('description', '')[:50]}")
            continue
            
        # Also check if any other keyword matches
        if any(keyword in haystack for keyword in keywords):
            filtered.append(item)

    # If everything was filtered out, keep the originals to avoid empty lists
    if not filtered:
        logging.warning(f"All resources filtered out for query '{query}'. Keeping originals.")
    return filtered or resources


@langsmith_traceable(name="perplexity_resource_search")
def search_resources(query: str, k: int = 3, timeout: int = 45, trusted_sources: Dict[str, List[str]] = None) -> List[Dict[str, str]]:
    """Search for learning resources using Perplexity (with OpenAI fallback).

    Each dict has keys: `type`, `url`, `description`.
    
    Args:
        query: The search query/milestone title
        k: Number of resources to return
        timeout: API timeout in seconds
        trusted_sources: Dict with 'youtube' and 'websites' lists of trusted sources
    """
    # Build source-specific instructions
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

    # Try Perplexity first (real-time web search)
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if perplexity_key:
        try:
            logging.info("Searching for resources using Perplexity (web search)...")
            client = OpenAI(
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai"
            )

            start_time = time.time()
            completion = client.chat.completions.create(
                model="sonar-pro",  # Online search model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that searches the web for real learning resources. Always return valid JSON with actual, working URLs.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
                timeout=timeout,
            )
            latency_ms = (time.time() - start_time) * 1000
            content = completion.choices[0].message.content.strip()

            # Remove markdown code blocks if present
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
                    "description": item.get("description", ""),
                })

            if cleaned:
                cleaned = _filter_by_keywords(cleaned, query)
                logging.info(f"✅ Found {len(cleaned)} resources via Perplexity")

                # Extract usage (token counts) if provided
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

                usage = getattr(completion, "usage", None)
                if usage:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0)
                    completion_tokens = getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0)
                    total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
                else:
                    # Fallback: some clients expose model_dump / dict style
                    usage_payload = None
                    if hasattr(completion, "model_dump") and callable(completion.model_dump):
                        usage_payload = completion.model_dump().get("usage")
                    elif isinstance(completion, dict):
                        usage_payload = completion.get("usage")

                    if usage_payload:
                        prompt_tokens = usage_payload.get("prompt_tokens", usage_payload.get("input_tokens", 0))
                        completion_tokens = usage_payload.get("completion_tokens", usage_payload.get("output_tokens", 0))
                        total_tokens = usage_payload.get("total_tokens", prompt_tokens + completion_tokens)

                # Estimate cost using configured pricing (per 1K tokens)
                perplexity_cost = 0.0
                if PERPLEXITY_PROMPT_COST_PER_1K > 0 or PERPLEXITY_COMPLETION_COST_PER_1K > 0:
                    perplexity_cost = (
                        (prompt_tokens / 1000.0) * PERPLEXITY_PROMPT_COST_PER_1K
                        + (completion_tokens / 1000.0) * PERPLEXITY_COMPLETION_COST_PER_1K
                    )

                # Log to observability platforms
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
                    {
                        "query": query,
                        "result_count": len(cleaned),
                    },
                )

                if prompt_tokens:
                    obs_manager.log_metric(
                        "perplexity_prompt_tokens",
                        float(prompt_tokens),
                        {"query": query},
                    )
                if completion_tokens:
                    obs_manager.log_metric(
                        "perplexity_completion_tokens",
                        float(completion_tokens),
                        {"query": query},
                    )
                if perplexity_cost:
                    obs_manager.log_metric(
                        "perplexity_cost_usd",
                        perplexity_cost,
                        {"query": query},
                    )

                return cleaned
        except Exception as exc:
            logging.warning(f"Perplexity resource search failed: {exc}. Falling back to OpenAI...")

    # Fallback to OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.info("OPENAI_API_KEY not set; returning stub resources")
        return _stub_resources()

    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    try:
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant that provides real, working URLs to learning resources."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=400,
            timeout=timeout,
        )
        content = completion.choices[0].message.content.strip()

        # Remove markdown code blocks if present
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
                "description": item.get("description", ""),
            })
        cleaned = _filter_by_keywords(cleaned, query)
        return cleaned or _stub_resources()
    except Exception as exc:
        logging.warning("OpenAI resource search failed: %s", exc)
        return _stub_resources()
