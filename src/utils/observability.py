"""
Observability utilities for LLM monitoring and evaluation.
Provides centralized logging, tracing, and metrics tracking using LangSmith and W&B.
"""

import os
import time
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

# Import configuration
from src.utils.config import (
    LANGCHAIN_TRACING_V2,
    LANGCHAIN_API_KEY,
    LANGCHAIN_PROJECT,
    WANDB_API_KEY,
    WANDB_PROJECT,
    WANDB_ENTITY,
    WANDB_MODE
)

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """
    Centralized manager for observability tools (LangSmith + W&B).
    Handles initialization, tracing, and metrics logging.
    """
    
    def __init__(self):
        """Initialize observability tools."""
        self.langsmith_enabled = False
        self.wandb_enabled = False
        self.wandb_run = None
        
        # Initialize LangSmith
        self._init_langsmith()
        
        # Initialize Weights & Biases
        self._init_wandb()
    
    def _init_langsmith(self):
        """Initialize LangSmith tracing."""
        if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY:
            try:
                # Set environment variables for automatic LangChain tracing
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
                os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
                
                self.langsmith_enabled = True
                logger.info(f"✅ LangSmith tracing enabled for project: {LANGCHAIN_PROJECT}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize LangSmith: {e}")
                self.langsmith_enabled = False
        else:
            logger.info("ℹ️  LangSmith tracing disabled (set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY to enable)")
    
    def _init_wandb(self):
        """Initialize Weights & Biases."""
        if WANDB_API_KEY and WANDB_MODE != "disabled":
            try:
                import wandb
                
                # Initialize W&B run
                self.wandb_run = wandb.init(
                    project=WANDB_PROJECT,
                    entity=WANDB_ENTITY,
                    mode=WANDB_MODE,
                    config={
                        "framework": "langchain",
                        "application": "ai-learning-path-generator"
                    },
                    # Don't reinitialize if already running
                    reinit=False,
                    resume="allow"
                )
                
                self.wandb_enabled = True
                logger.info(f"✅ W&B tracking enabled for project: {WANDB_PROJECT}")
            except ImportError:
                logger.warning("⚠️  wandb package not installed. Run: pip install wandb")
                self.wandb_enabled = False
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize W&B: {e}")
                self.wandb_enabled = False
        else:
            logger.info("ℹ️  W&B tracking disabled (set WANDB_API_KEY to enable)")
    
    def log_llm_call(
        self,
        prompt: str,
        response: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        cost: Optional[float] = None
    ):
        """
        Log an LLM call to W&B Prompts.
        
        Args:
            prompt: The input prompt sent to the LLM
            response: The LLM's response
            model: Model name (e.g., 'gpt-4o-mini')
            metadata: Additional metadata (user_id, topic, etc.)
            latency_ms: Response time in milliseconds
            token_count: Total tokens used
            cost: Estimated cost in USD
        """
        if not self.wandb_enabled:
            return
        
        try:
            import wandb
            
            # Log to W&B Prompts table
            prompts_table = wandb.Table(
                columns=[
                    "timestamp", "model", "prompt", "response", 
                    "latency_ms", "token_count", "cost", "metadata"
                ]
            )
            
            prompts_table.add_data(
                datetime.utcnow().isoformat(),
                model,
                prompt[:500],  # Truncate for display
                response[:500],
                latency_ms,
                token_count,
                cost,
                str(metadata or {})
            )
            
            wandb.log({"llm_calls": prompts_table})
            
            # Also log metrics separately for easier aggregation
            if latency_ms:
                wandb.log({"llm_latency_ms": latency_ms})
            if token_count:
                wandb.log({"llm_tokens": token_count})
            if cost:
                wandb.log({"llm_cost_usd": cost})
                
        except Exception as e:
            logger.warning(f"Failed to log LLM call to W&B: {e}")
    
    def log_metric(self, name: str, value: float, metadata: Optional[Dict] = None):
        """
        Log a custom metric to W&B.
        
        Args:
            name: Metric name (e.g., 'path_generation_success')
            value: Metric value
            metadata: Additional context
        """
        if not self.wandb_enabled:
            return
        
        try:
            import wandb
            
            log_data = {name: value}
            if metadata:
                # Flatten metadata into the log
                for key, val in metadata.items():
                    log_data[f"{name}_{key}"] = val
            
            wandb.log(log_data)
        except Exception as e:
            logger.warning(f"Failed to log metric to W&B: {e}")
    
    def log_event(self, event_name: str, properties: Optional[Dict] = None):
        """
        Log a custom event to W&B.
        
        Args:
            event_name: Name of the event (e.g., 'path_generated', 'validation_failed')
            properties: Event properties
        """
        if not self.wandb_enabled:
            return
        
        try:
            import wandb
            
            wandb.log({
                "event": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                "properties": properties or {}
            })
        except Exception as e:
            logger.warning(f"Failed to log event to W&B: {e}")
    
    def finish(self):
        """Clean up and finish W&B run."""
        if self.wandb_enabled and self.wandb_run:
            try:
                import wandb
                wandb.finish()
                logger.info("✅ W&B run finished")
            except Exception as e:
                logger.warning(f"Failed to finish W&B run: {e}")


# Global observability manager instance
_observability_manager = None


def get_observability_manager() -> ObservabilityManager:
    """Get or create the global observability manager instance."""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager()
    return _observability_manager


def traceable(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    log_to_wandb: bool = True
):
    """
    Decorator to trace function execution with LangSmith and log to W&B.
    
    Usage:
        @traceable(name="generate_learning_path", metadata={"version": "v2"})
        def generate_path(topic: str) -> dict:
            ...
    
    Args:
        name: Custom name for the trace (defaults to function name)
        metadata: Additional metadata to attach to the trace
        log_to_wandb: Whether to also log execution metrics to W&B
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            obs_manager = get_observability_manager()
            trace_name = name or func.__name__
            
            # Start timing
            start_time = time.time()
            success = False
            error = None
            result = None
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                
                # Log to W&B if enabled
                if log_to_wandb and obs_manager.wandb_enabled:
                    obs_manager.log_metric(
                        f"{trace_name}_latency_ms",
                        latency_ms,
                        metadata={
                            "success": success,
                            "error": error,
                            **(metadata or {})
                        }
                    )
                    
                    obs_manager.log_metric(
                        f"{trace_name}_success",
                        1.0 if success else 0.0
                    )
        
        return wrapper
    return decorator


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate the cost of an LLM call based on token usage.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Estimated cost in USD
    """
    # Pricing per 1M tokens (as of 2024)
    pricing = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-4": {"input": 30.00, "output": 60.00},
    }
    
    # Default to gpt-4o-mini pricing if model not found
    model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
    
    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
    
    return input_cost + output_cost
