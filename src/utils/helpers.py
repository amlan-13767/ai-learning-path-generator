"""
Helper functions for the AI Learning Path Generator.
"""
import re
import json
import datetime
from typing import List, Dict, Any, Optional

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent any security issues.
    
    Args:
        text: The input text to sanitize
        
    Returns:
        Sanitized text string
    """
    # Remove any HTML or script tags
    text = re.sub(r'<[^>]*>', '', text)
    # Limit length
    return text.strip()[:1000]

def format_duration(minutes: int) -> str:
    """
    Format a duration in minutes to a human-readable string.
    
    Args:
        minutes: Number of minutes
        
    Returns:
        Formatted string (e.g., "2 hours 30 minutes")
    """
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours} hour{'s' if hours > 1 else ''} {mins} minute{'s' if mins > 1 else ''}"
    elif hours:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        return f"{mins} minute{'s' if mins > 1 else ''}"

def calculate_study_schedule(
    weeks: int, 
    hours_per_week: int, 
    topic_weights: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate a recommended study schedule based on topic weights.
    
    Args:
        weeks: Total duration in weeks
        hours_per_week: Hours available per week
        topic_weights: Dictionary of topics with their importance weights
        
    Returns:
        Dictionary with schedule information
    """
    total_hours = weeks * hours_per_week
    total_weight = sum(topic_weights.values())
    
    # Normalize weights to sum to 1
    normalized_weights = {
        topic: weight / total_weight for topic, weight in topic_weights.items()
    }
    
    # Calculate hours per topic
    hours_per_topic = {
        topic: round(weight * total_hours) for topic, weight in normalized_weights.items()
    }
    
    # Ensure minimum hours and adjust to match total
    min_hours = 1
    for topic in hours_per_topic:
        if hours_per_topic[topic] < min_hours:
            hours_per_topic[topic] = min_hours
    
    # Create schedule with start/end dates
    start_date = datetime.datetime.now()
    current_date = start_date
    
    schedule = {
        "total_hours": total_hours,
        "hours_per_week": hours_per_week,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": (start_date + datetime.timedelta(weeks=weeks)).strftime("%Y-%m-%d"),
        "topics": {}
    }
    
    for topic, hours in hours_per_topic.items():
        topic_days = hours / (hours_per_week / 7)  # Distribute across available days
        topic_end = current_date + datetime.timedelta(days=topic_days)
        
        schedule["topics"][topic] = {
            "hours": hours,
            "start_date": current_date.strftime("%Y-%m-%d"),
            "end_date": topic_end.strftime("%Y-%m-%d"),
            "percentage": round(hours / total_hours * 100, 1)
        }
        
        current_date = topic_end
    
    return schedule

def difficulty_to_score(difficulty: str) -> float:
    """
    Convert difficulty description to numeric score (0-1).
    
    Args:
        difficulty: String description of difficulty
        
    Returns:
        Numeric score between 0 and 1
    """
    difficulty = difficulty.lower()
    if "beginner" in difficulty or "easy" in difficulty:
        return 0.25
    elif "intermediate" in difficulty:
        return 0.5
    elif "advanced" in difficulty:
        return 0.75
    elif "expert" in difficulty:
        return 1.0
    else:
        return 0.5  # Default to intermediate

def match_resources_to_learning_style(
    resources: List[Any], 
    learning_style: str,
    resource_type_weights: Optional[Dict[str, Dict[str, int]]] = None
) -> List[Any]:
    """
    Sort resources based on learning style preference.
    
    Args:
        resources: List of resources (either dictionaries or Pydantic models)
        learning_style: User's learning style
        resource_type_weights: Optional custom weights for resource types
        
    Returns:
        Sorted list of resources
    """
    from src.utils.config import RESOURCE_TYPES
    
    weights = resource_type_weights or RESOURCE_TYPES
    
    # Create a copy of resources to avoid modifying the original objects
    resources_with_scores = []
    
    for resource in resources:
        # Handle both dictionary and Pydantic model (ResourceItem) objects
        if hasattr(resource, 'dict'):
            # It's a Pydantic model
            resource_dict = resource.dict()
            resource_type = resource.type if hasattr(resource, 'type') else 'article'
        else:
            # It's a dictionary
            resource_dict = resource
            resource_type = resource.get("type", "article")
        
        # Calculate style score
        style_score = 1  # Default score
        if resource_type in weights and learning_style in weights[resource_type]:
            style_score = weights[resource_type][learning_style]
        
        # Store the original resource and its score
        resources_with_scores.append((resource, style_score))
    
    # Sort by style score (higher is better)
    sorted_resources = [r[0] for r in sorted(resources_with_scores, key=lambda x: x[1], reverse=True)]
    return sorted_resources


# ============================================
# TOKEN OPTIMIZATION UTILITIES
# Cost-saving functions to reduce API expenses
# ============================================

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in text for a specific model.
    This helps us avoid expensive API calls with huge prompts.
    
    Why this matters:
    - OpenAI charges per token (not per character)
    - Knowing token count helps us stay within budget
    - Prevents unexpected API costs
    
    Args:
        text: The text to count tokens for
        model: The model name to use for encoding
    
    Returns:
        Number of tokens
    
    Example:
        >>> count_tokens("Hello, world!")
        4
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base (used by GPT-4, GPT-3.5-turbo, text-embedding-ada-002)
            encoding = tiktoken.get_encoding("cl100k_base")
        
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough estimate if tiktoken not available
        # Approximate: 1 token ≈ 4 characters for English text
        return len(text) // 4


def truncate_text(text: str, max_tokens: int = 3000, model: str = "gpt-4o-mini") -> str:
    """
    Truncate text to fit within token limit while keeping the most important parts.
    
    Why: OpenAI charges per token. We want to send ONLY what's necessary.
    
    Strategy:
    - Keep first 70% (context and setup)
    - Keep last 30% (recent/relevant info)
    - This preserves both context and recency
    
    Args:
        text: Text to truncate
        max_tokens: Maximum tokens to allow
        model: Model to use for token counting
    
    Returns:
        Truncated text
    
    Example:
        >>> long_text = "..." * 10000
        >>> short_text = truncate_text(long_text, max_tokens=100)
        >>> count_tokens(short_text) <= 100
        True
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        tokens = encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # Keep first 70% and last 30% to preserve context
        first_part = int(max_tokens * 0.7)
        last_part = int(max_tokens * 0.3)
        
        truncated_tokens = tokens[:first_part] + tokens[-last_part:]
        return encoding.decode(truncated_tokens)
    except ImportError:
        # Fallback: character-based truncation
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        first_part = int(max_chars * 0.7)
        last_part = int(max_chars * 0.3)
        return text[:first_part] + "\n...[truncated]...\n" + text[-last_part:]


def optimize_prompt(prompt: str, context: Optional[List[str]] = None, max_tokens: int = 4000) -> str:
    """
    Optimize prompt by truncating context intelligently.
    
    How it works:
    1. Count tokens in main prompt (always kept intact)
    2. Calculate remaining tokens for context
    3. Truncate context if needed
    4. Combine prompt + optimized context
    
    This ensures:
    - Main prompt is never truncated (it's critical)
    - Context is added only if space allows
    - Total stays within budget
    
    Args:
        prompt: Main prompt (always kept)
        context: Additional context (can be truncated)
        max_tokens: Total token budget
    
    Returns:
        Optimized prompt with context
    
    Example:
        >>> prompt = "Generate a learning path for Python"
        >>> context = ["Python is a programming language...", "..."]
        >>> optimized = optimize_prompt(prompt, context, max_tokens=500)
        >>> count_tokens(optimized) <= 500
        True
    """
    prompt_tokens = count_tokens(prompt)
    
    if context:
        context_text = "\n\n".join(context)
        available_tokens = max_tokens - prompt_tokens - 100  # 100 token buffer for safety
        
        if available_tokens > 0:
            context_text = truncate_text(context_text, available_tokens)
            return f"{prompt}\n\nContext:\n{context_text}"
    
    return prompt


def estimate_api_cost(token_count: int, model: str = "gpt-4o-mini") -> float:
    """
    Estimate the cost of an API call based on token count.
    
    Pricing (as of 2024):
    - gpt-4o-mini: $0.15 per 1M input tokens, $0.60 per 1M output tokens
    - gpt-3.5-turbo: $0.50 per 1M input tokens, $1.50 per 1M output tokens
    - gpt-4: $30 per 1M input tokens, $60 per 1M output tokens
    
    Args:
        token_count: Number of tokens
        model: Model name
    
    Returns:
        Estimated cost in USD
    
    Example:
        >>> cost = estimate_api_cost(1000, "gpt-4o-mini")
        >>> print(f"${cost:.4f}")
        $0.0002
    """
    # Pricing per 1M tokens (input)
    pricing = {
        "gpt-4o-mini": 0.15,
        "gpt-4o": 2.50,
        "gpt-4": 30.00,
        "gpt-3.5-turbo": 0.50,
        "text-embedding-3-small": 0.02,
        "text-embedding-3-large": 0.13,
        "text-embedding-ada-002": 0.10,
    }
    
    # Get price per million tokens
    price_per_million = pricing.get(model, 0.15)  # Default to gpt-4o-mini pricing
    
    # Calculate cost
    cost = (token_count / 1_000_000) * price_per_million
    
    return cost
