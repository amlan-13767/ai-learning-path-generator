"""
Configuration utilities for the AI Learning Path Generator.
Loads environment variables and provides configuration settings across the application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Load environment variables from .env file, expecting it at project root (2 levels up from this file).
# This ensures changes in .env are picked up correctly.
# Load .env file only if not on Render
if not os.environ.get('RENDER'):
    dotenv_path = Path(__file__).resolve().parents[2] / '.env'
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path)
        print(f"--- Successfully loaded .env from: {dotenv_path} ---")
    else:
        # Fallback to default python-dotenv behavior (searches current dir and parents)
        # This can be helpful if the script is run from an unexpected location.
        print(f"--- .env not found at {dotenv_path}, attempting default load_dotenv() search. ---")
        loaded_by_default = load_dotenv()
        if loaded_by_default:
            print(f"--- Successfully loaded .env from default location (e.g., {os.getcwd()}/.env or parent). ---")
        else:
            print("--- WARNING: .env file not found by explicit path or default search. Environment variables may not be set. ---")

# Development mode flag - checked before raising key errors
DEV_MODE = os.getenv('DEV_MODE', 'False').lower() == 'true'

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# Deprecated - kept for backward compatibility but not used
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
# Perplexity pricing (cost per 1K tokens) - default 0 so users can opt-in
PERPLEXITY_PROMPT_COST_PER_1K = float(os.getenv("PERPLEXITY_PROMPT_COST_PER_1K", "0"))
PERPLEXITY_COMPLETION_COST_PER_1K = float(os.getenv("PERPLEXITY_COMPLETION_COST_PER_1K", "0"))

# Ensure OpenAI API key is available (unless in DEV_MODE)
if not DEV_MODE and not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY environment variable is required (unless DEV_MODE=true).")

# Default model provider (can be 'openai' or 'deepseek')
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai").lower()

# Model configuration
# Using GPT-4o-mini: 3x cheaper than GPT-3.5-turbo, better quality!
# Cost: $0.15/1M input tokens vs $0.50 for GPT-3.5
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # Cheaper embeddings
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Alternative models for different use cases
REASONING_MODEL = os.getenv("REASONING_MODEL", "gpt-4o-mini")  # For complex reasoning
SIMPLE_MODEL = os.getenv("SIMPLE_MODEL", "gpt-4o-mini")  # For simple tasks

# (Deprecated) Perplexity settings – retained for legacy tests but not used by the app.
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "pplx-7b-online")  # noqa: E501

# Vector database settings
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")

# Region settings
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "North America")

# LangSmith Configuration (LLM Tracing & Debugging)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-learning-path-generator")

# Weights & Biases Configuration (Metrics & Experiment Tracking)
WANDB_API_KEY = os.getenv("WANDB_API_KEY")
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "ai-learning-path-generator")
WANDB_ENTITY = os.getenv("WANDB_ENTITY")  # Your W&B username or team name
WANDB_MODE = os.getenv("WANDB_MODE", "online")  # 'online', 'offline', or 'disabled'

# ============================================
# ADVANCED RAG PIPELINE CONFIGURATION
# ============================================

# Redis Configuration (Semantic Caching)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = os.getenv("REDIS_URL")  # Alternative: full connection URL
SEMANTIC_CACHE_TTL = int(os.getenv("SEMANTIC_CACHE_TTL", "3600"))
SEMANTIC_CACHE_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.95"))
ENABLE_SEMANTIC_CACHE = os.getenv("ENABLE_SEMANTIC_CACHE", "True").lower() == "true"

# Cohere Reranking API
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_RERANK_MODEL = os.getenv("COHERE_RERANK_MODEL", "rerank-english-v3.0")
USE_LOCAL_RERANKER = os.getenv("USE_LOCAL_RERANKER", "False").lower() == "true"
LOCAL_RERANKER_MODEL = os.getenv("LOCAL_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# Hybrid Search Configuration
BM25_K1 = float(os.getenv("BM25_K1", "1.5"))
BM25_B = float(os.getenv("BM25_B", "0.75"))
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.5"))
HYBRID_TOP_K = int(os.getenv("HYBRID_TOP_K", "20"))

# Query Rewriting
QUERY_REWRITE_ENABLED = os.getenv("QUERY_REWRITE_ENABLED", "True").lower() == "true"
QUERY_REWRITE_MODEL = os.getenv("QUERY_REWRITE_MODEL", "gpt-3.5-turbo")
QUERY_REWRITE_MAX_TOKENS = int(os.getenv("QUERY_REWRITE_MAX_TOKENS", "100"))

# Contextual Compression
CONTEXTUAL_COMPRESSION_ENABLED = os.getenv("CONTEXTUAL_COMPRESSION_ENABLED", "True").lower() == "true"
COMPRESSION_MODEL = os.getenv("COMPRESSION_MODEL", "gpt-3.5-turbo")
COMPRESSION_MAX_TOKENS = int(os.getenv("COMPRESSION_MAX_TOKENS", "500"))

# Reranking Configuration
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "True").lower() == "true"

# Web app settings
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
PORT = int(os.getenv("PORT", "5000"))

# Learning paths configuration
LEARNING_STYLES = {
    "visual": "Learns best through images, diagrams, and spatial understanding",
    "auditory": "Learns best through listening and speaking",
    "reading": "Learns best through written materials and note-taking",
    "kinesthetic": "Learns best through hands-on activities and physical interaction"
}

EXPERTISE_LEVELS = {
    "beginner": "No prior knowledge in the subject",
    "intermediate": "Some familiarity with basic concepts",
    "advanced": "Solid understanding of core principles",
    "expert": "Deep knowledge and specialization"
}

TIME_COMMITMENTS = {
    "minimal": "1-2 hours per week",
    "moderate": "3-5 hours per week",
    "substantial": "6-10 hours per week",
    "intensive": "10+ hours per week"
}

# Resource types with weights for learning styles (higher = more relevant)
RESOURCE_TYPES = {
    "video": {"visual": 5, "auditory": 4, "reading": 2, "kinesthetic": 3},
    "article": {"visual": 3, "reading": 5, "auditory": 2, "kinesthetic": 1},
    "book": {"reading": 5, "visual": 3, "auditory": 2, "kinesthetic": 1},
    "interactive": {"kinesthetic": 5, "visual": 4, "auditory": 3, "reading": 3},
    "course": {"visual": 4, "auditory": 4, "reading": 4, "kinesthetic": 3},
    "documentation": {"reading": 5, "visual": 3, "auditory": 1, "kinesthetic": 1},
    "podcast": {"auditory": 5, "reading": 2, "visual": 1, "kinesthetic": 1},
    "project": {"kinesthetic": 5, "visual": 3, "reading": 3, "auditory": 2}
}
