"""
Celery tasks for learning path generation
Wraps existing logic from src/
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# This file now contains a simple function for the RQ worker.

def generate_learning_path_for_worker(payload):
    """
    Worker function to generate a learning path. 
    This is the function that the RQ worker will execute.
    
    Args:
        payload (dict): A dictionary containing the necessary parameters like 
                        'topic', 'expertise_level', etc.
    """
    print(f"Worker received job with payload: {payload}")
    
    # Import necessary modules inside the function
    # This is a best practice for RQ tasks
    from src.learning_path import LearningPathGenerator

    # Extract parameters from the payload
    topic = payload.get('topic')
    expertise_level = payload.get('expertise_level', 'beginner')
    # duration_weeks may come as str/empty; coerce safely
    _dw = payload.get('duration_weeks', 4)
    try:
        duration_weeks = int(_dw) if _dw not in (None, "", []) else 4
    except Exception:
        duration_weeks = 4
    time_commitment = payload.get('time_commitment', 'moderate')
    # Normalize goals to a list or None so generator can apply defaults
    goals_raw = payload.get('goals')
    if isinstance(goals_raw, list):
        goals = goals_raw
    elif isinstance(goals_raw, str) and goals_raw.strip():
        goals = [goals_raw.strip()]
    else:
        goals = None
    ai_provider = payload.get('ai_provider', 'openai')
    ai_model = payload.get('ai_model')

    # Initialize the generator (constructor accepts optional api_key only)
    generator = LearningPathGenerator()

    # Generate the learning path
    # The result of this function will be stored in Redis by RQ
    learning_path = generator.generate_path(
        topic=topic,
        expertise_level=expertise_level,
        learning_style=None,
        time_commitment=time_commitment,
        duration_weeks=duration_weeks,
        goals=goals,
        ai_provider=ai_provider,
        ai_model=ai_model
    )

    # The learning_path object (likely a Pydantic model) will be pickled by RQ 
    # and stored in Redis. The API can then fetch this result.
    print(f"Successfully generated learning path for topic: {topic}")
    return learning_path.dict() if hasattr(learning_path, 'dict') else learning_path
