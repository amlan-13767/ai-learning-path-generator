# Observability Stack Setup Guide

## Overview

This guide walks you through setting up LangSmith and Weights & Biases (W&B) for comprehensive LLM monitoring, debugging, and evaluation.

## What We've Implemented

### 1. Core Infrastructure

**Files Created:**
- `src/utils/observability.py` - Central observability manager
- Updated `src/utils/config.py` - Added LangSmith and W&B configuration
- Updated `src/ml/model_orchestrator.py` - Integrated LLM call logging
- Updated `.env.example` - Added observability environment variables
- Updated `requirements.txt` - Added `langsmith` and `wandb` packages

### 2. Key Features

✅ **Automatic LangChain Tracing** - All LangChain calls automatically traced to LangSmith  
✅ **LLM Call Logging** - Every OpenAI API call logged with prompt, response, latency, tokens, and cost  
✅ **Custom Metrics** - Track business metrics like path generation success rate  
✅ **Event Tracking** - Log important events (generation started, completed, failed)  
✅ **Cost Estimation** - Automatic cost calculation based on token usage  
✅ **Graceful Degradation** - Observability failures don't break the app  

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install langsmith wandb
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Step 2: Get API Keys

#### LangSmith

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy the key

#### Weights & Biases

1. Go to [wandb.ai](https://wandb.ai)
2. Sign up or log in
3. Go to User Settings → API keys
4. Copy your API key

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai-learning-path-generator

# Weights & Biases Configuration
WANDB_API_KEY=your_wandb_api_key_here
WANDB_PROJECT=ai-learning-path-generator
WANDB_ENTITY=your_wandb_username_or_team
WANDB_MODE=online  # or 'offline' or 'disabled'
```

### Step 4: Verify Setup

Run this test script:

```python
from src.utils.observability import get_observability_manager

# Initialize observability
obs_manager = get_observability_manager()

# Check if enabled
print(f"LangSmith enabled: {obs_manager.langsmith_enabled}")
print(f"W&B enabled: {obs_manager.wandb_enabled}")

# Test logging
obs_manager.log_metric("test_metric", 1.0, {"source": "setup_test"})
obs_manager.log_event("setup_test_completed", {"status": "success"})

print("✅ Observability setup successful!")
```

## Usage Examples

### 1. Automatic LLM Tracing (LangSmith)

All LangChain calls are automatically traced. No code changes needed!

```python
from src.learning_path import LearningPathGenerator

generator = LearningPathGenerator()
path = generator.generate_path(
    topic="Machine Learning",
    expertise_level="intermediate",
    learning_style="hands-on"
)

# Check LangSmith dashboard to see the full trace!
```

### 2. Manual Logging (W&B)

```python
from src.utils.observability import get_observability_manager

obs_manager = get_observability_manager()

# Log an LLM call
obs_manager.log_llm_call(
    prompt="Generate a learning path for Python",
    response="Here's your path...",
    model="gpt-4o-mini",
    latency_ms=1234.5,
    token_count=500,
    cost=0.0015,
    metadata={"user_id": "user123", "topic": "Python"}
)

# Log a custom metric
obs_manager.log_metric(
    "resource_validation_rate",
    0.85,  # 85% valid
    metadata={"topic": "Python", "milestone_count": 5}
)

# Log an event
obs_manager.log_event("path_shared", {
    "path_id": "abc123",
    "user_id": "user123",
    "share_method": "email"
})
```

### 3. Using the @traceable Decorator

```python
from src.utils.observability import traceable

@traceable(name="custom_function", metadata={"version": "v2"})
def my_expensive_function(param1, param2):
    # Your code here
    result = do_something(param1, param2)
    return result

# Automatically logs execution time and success/failure
result = my_expensive_function("test", 123)
```

## What Gets Tracked

### LangSmith Traces

Every LLM interaction creates a trace showing:
- **Input Prompt** - Exact prompt sent to the LLM
- **Output Response** - Complete LLM response
- **Latency** - Time taken for each step
- **Chain Structure** - Visual hierarchy of LangChain components
- **Errors** - Full stack trace if something fails
- **Metadata** - Custom tags (user_id, topic, etc.)

### W&B Metrics

Automatically logged metrics:
- `llm_latency_ms` - Response time for each LLM call
- `llm_tokens` - Total tokens used
- `llm_cost_usd` - Estimated cost in USD
- `path_generation_success` - 1.0 for success, 0.0 for failure
- `path_generation_latency_ms` - Time to generate a path
- `resource_validation_rate` - Percentage of valid resources

### W&B Events

Key events tracked:
- `path_generation_started` - When generation begins
- `path_generation_completed` - Successful generation
- `path_generation_failed` - Failed generation with error details

## Dashboards & Monitoring

### LangSmith Dashboard

Access at: [smith.langchain.com](https://smith.langchain.com)

**Key Views:**
1. **Traces** - See all LLM interactions in real-time
2. **Playground** - Replay and modify prompts
3. **Datasets** - Create test sets from production traces
4. **Monitoring** - Track latency, error rate, feedback scores
5. **Evaluations** - Run automated evals on datasets

**Useful Filters:**
- Filter by `user_id` to debug a specific user's issue
- Filter by `status:error` to see all failures
- Filter by `topic` to analyze performance per subject

### W&B Dashboard

Access at: [wandb.ai](https://wandb.ai)

**Key Views:**
1. **Runs** - See all experiment runs
2. **Charts** - Visualize metrics over time
3. **Tables** - View LLM calls in tabular format
4. **Reports** - Create shareable reports

**Useful Charts:**
- **Cost Over Time** - Track your OpenAI spend
- **Success Rate** - Monitor path generation reliability
- **Latency P99** - Track worst-case performance
- **Token Usage** - Identify expensive queries

## Debugging Workflow

### Scenario: User reports slow generation

1. **Find the trace in LangSmith**
   - Filter by `user_id` or timestamp
   - Click on the slow trace

2. **Analyze the bottleneck**
   - Look at the latency breakdown
   - Identify which step is slow (prompt generation, LLM call, parsing)

3. **Check W&B for patterns**
   - Is this topic consistently slow?
   - Is it a specific expertise level?
   - Compare token counts with faster generations

4. **Fix and validate**
   - Make code changes
   - Run test generations
   - Compare metrics in W&B before/after

### Scenario: High OpenAI costs

1. **Open W&B dashboard**
   - Sort LLM calls by `cost`
   - Identify the most expensive queries

2. **Analyze token usage**
   - Check if certain topics use more tokens
   - Look for unnecessarily long prompts

3. **Optimize**
   - Reduce prompt length
   - Use cheaper models for simple tasks
   - Implement better caching

4. **Monitor impact**
   - Track `llm_cost_usd` metric over time
   - Verify cost reduction

## Advanced Features

### Creating Datasets in LangSmith

```python
# Automatically create a dataset from failed generations
# 1. Go to LangSmith dashboard
# 2. Filter traces by status:error
# 3. Select traces
# 4. Click "Add to Dataset"
# 5. Name it "failed_generations"
```

### Custom Evaluators

Create a file `src/evals/custom_evaluators.py`:

```python
def is_json_valid(outputs: dict) -> dict:
    """Check if LLM output is valid JSON."""
    try:
        import json
        json.loads(outputs.get("output", ""))
        return {"score": 1.0, "reason": "Valid JSON"}
    except:
        return {"score": 0.0, "reason": "Invalid JSON"}

def has_sufficient_milestones(outputs: dict) -> dict:
    """Check if path has at least 3 milestones."""
    try:
        import json
        data = json.loads(outputs.get("output", "{}"))
        milestone_count = len(data.get("milestones", []))
        
        if milestone_count >= 3:
            return {"score": 1.0, "reason": f"{milestone_count} milestones"}
        else:
            return {"score": 0.0, "reason": f"Only {milestone_count} milestones"}
    except:
        return {"score": 0.0, "reason": "Could not parse"}
```

Register in LangSmith and run on datasets.

### Alerting

Set up alerts in LangSmith:

1. Go to Monitoring → Alerts
2. Create alert for:
   - `P99 latency > 15 seconds`
   - `Error rate > 5%`
   - `Feedback score < 3.5`
3. Configure Slack/email notifications

## Cost Estimation

The system automatically estimates costs based on:

```python
# Pricing per 1M tokens (as of 2024)
pricing = {
    "gpt-4o-mini": {"input": $0.15, "output": $0.60},
    "gpt-4o": {"input": $5.00, "output": $15.00},
    "gpt-3.5-turbo": {"input": $0.50, "output": $1.50},
}
```

View total costs in W&B dashboard under `llm_cost_usd` metric.

## Troubleshooting

### Issue: LangSmith not showing traces

**Solution:**
1. Check `.env` has `LANGCHAIN_TRACING_V2=true`
2. Verify API key is correct
3. Check logs for initialization errors
4. Restart the application

### Issue: W&B not logging metrics

**Solution:**
1. Check `WANDB_API_KEY` is set
2. Verify `WANDB_MODE` is not `disabled`
3. Check internet connection (if mode is `online`)
4. Look for errors in application logs

### Issue: High memory usage

**Solution:**
- W&B buffers data before syncing
- Set `WANDB_MODE=offline` to reduce memory
- Call `obs_manager.finish()` periodically

## Best Practices

1. **Tag Everything** - Add user_id, topic, expertise_level to all logs
2. **Monitor Costs** - Set up weekly cost alerts
3. **Review Failures** - Check failed traces daily
4. **Create Datasets** - Build test sets from production data
5. **Run Evals Regularly** - Automate quality checks
6. **Share Dashboards** - Make metrics visible to the team

## Next Steps

1. ✅ Complete the integration in `src/learning_path.py` (see code comments)
2. ✅ Add user feedback collection in the UI
3. ✅ Create custom evaluators for your use cases
4. ✅ Set up alerting for critical metrics
5. ✅ Build W&B reports for stakeholders

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com)
- [W&B Documentation](https://docs.wandb.ai)
- [LangChain Tracing Guide](https://python.langchain.com/docs/langsmith/walkthrough)
- [W&B Prompts Guide](https://docs.wandb.ai/guides/prompts)

---

**Status**: ✅ Core infrastructure complete. Manual integration needed for `src/learning_path.py` due to indentation complexity.
