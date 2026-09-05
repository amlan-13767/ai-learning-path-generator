# Testing Observability Setup

## Quick Start

### 1. Run the Validation Script

```bash
python test_observability.py
```

This will:
- ✅ Check if API keys are set correctly
- ✅ Validate LangSmith connection
- ✅ Validate W&B connection  
- ✅ Test logging functionality
- ✅ Verify ModelOrchestrator integration

### 2. Expected Output

If everything is working, you should see:

```
============================================================
🔍 Testing Observability Setup
============================================================

1️⃣ Checking environment variables...
   LANGCHAIN_TRACING_V2: True
   LANGCHAIN_API_KEY: ✅ Set
   LANGCHAIN_PROJECT: ai-learning-path-generator
   WANDB_API_KEY: ✅ Set
   WANDB_PROJECT: ai-learning-path-generator
   WANDB_ENTITY: your-username
   WANDB_MODE: online

2️⃣ Initializing observability manager...
   LangSmith enabled: ✅ Yes
   W&B enabled: ✅ Yes

3️⃣ Testing LangSmith connection...
   ✅ LangSmith environment configured correctly
   📊 Project: ai-learning-path-generator
   🔗 Dashboard: https://smith.langchain.com

4️⃣ Testing W&B connection...
   ✅ W&B API key is valid
   📊 Project: ai-learning-path-generator
   👤 Entity: your-username
   🔗 Dashboard: https://wandb.ai/your-username/ai-learning-path-generator

5️⃣ Testing logging functionality...
   ✅ Metric logging works
   ✅ Event logging works
   ✅ LLM call logging works

6️⃣ Testing cost estimation...
   ✅ Cost estimation works
   💰 Example: 1000 input + 500 output tokens = $0.0004

7️⃣ Testing ModelOrchestrator integration...
   ✅ ModelOrchestrator has observability manager

============================================================
📊 Summary
============================================================
✅ LangSmith: Ready
✅ W&B: Ready

============================================================
🎉 All systems go! You're ready to generate learning paths.

Next steps:
1. Generate a learning path using your app
2. Check LangSmith dashboard: https://smith.langchain.com
3. Check W&B dashboard: https://wandb.ai

You should see:
  • Full LLM traces in LangSmith
  • Metrics and costs in W&B
============================================================
```

### 3. Generate a Test Learning Path

After validation passes, generate a learning path:

```python
from src.learning_path import LearningPathGenerator

generator = LearningPathGenerator()
path = generator.generate_path(
    topic="Python Programming",
    expertise_level="beginner",
    learning_style="hands-on",
    time_commitment="moderate"
)

print(f"✅ Generated path: {path.title}")
print(f"📊 Milestones: {len(path.milestones)}")
```

### 4. Check Your Dashboards

#### LangSmith Dashboard
1. Go to: https://smith.langchain.com
2. Select project: `ai-learning-path-generator`
3. You should see:
   - **Traces** tab: Full LLM interaction traces
   - Each trace shows: prompt, response, latency, tokens
   - Click any trace to see detailed breakdown

#### W&B Dashboard
1. Go to: https://wandb.ai/your-username/ai-learning-path-generator
2. You should see:
   - **Runs** tab: Your test run
   - **Charts**: Metrics like `llm_latency_ms`, `llm_cost_usd`, `llm_tokens`
   - **Tables**: LLM calls with full details

## What Gets Tracked

### Automatically (No Code Changes Needed)

✅ **Every LLM Call** - Logged to both LangSmith and W&B  
✅ **Token Usage** - Input and output tokens counted  
✅ **Cost** - Automatically calculated based on model pricing  
✅ **Latency** - Response time measured  
✅ **Prompts & Responses** - Full text logged (truncated for display)  

### Events Logged

✅ `path_generation_started` - When generation begins  
✅ `path_generation_completed` - When generation succeeds  
✅ Test events from validation script  

### Metrics Tracked

✅ `llm_latency_ms` - LLM response time  
✅ `llm_tokens` - Token usage per call  
✅ `llm_cost_usd` - Cost per call  
✅ `path_generation_success` - Success/failure tracking  
✅ `test_metric` - From validation script  

### Perplexity Metrics (New)
✅ `perplexity_latency_ms` - Time to return web resources  
✅ `perplexity_prompt_tokens` / `perplexity_completion_tokens` - Token usage when usage data is available  
✅ `perplexity_cost_usd` - Estimated cost per Perplexity call (requires setting per-1K token pricing in `.env`)  
✅ LangSmith trace: `perplexity_resource_search` (shows prompt, response, timings)

## Troubleshooting

### Issue: "LangSmith API key is missing"

**Fix:**
1. Check your `.env` file has:
   ```
   LANGCHAIN_API_KEY=your_actual_key_here
   ```
2. Restart your terminal/IDE
3. Run the test again

### Issue: "W&B API key is missing"

**Fix:**
1. Check your `.env` file has:
   ```
   WANDB_API_KEY=your_actual_key_here
   ```
2. Restart your terminal/IDE
3. Run the test again

### Issue: "LangSmith enabled: ❌ No"

**Fix:**
1. Ensure `LANGCHAIN_TRACING_V2=true` (lowercase "true")
2. Check API key is valid
3. Verify internet connection

### Issue: "W&B enabled: ❌ No"

**Fix:**
1. Ensure `WANDB_MODE` is not set to "disabled"
2. Check API key is valid
3. Try `wandb login` in terminal

### Issue: No traces showing in LangSmith

**Fix:**
1. Wait 10-30 seconds (traces can be delayed)
2. Refresh the dashboard
3. Check you're looking at the correct project
4. Verify `LANGCHAIN_TRACING_V2=true` in `.env`

### Issue: No metrics in W&B

**Fix:**
1. Check the run finished (not still running)
2. Refresh the dashboard
3. Look in the "Runs" tab, not "Sweeps"
4. Verify `WANDB_MODE=online` (not offline or disabled)

## Next Steps After Validation

1. ✅ Run `python test_observability.py`
2. ✅ Verify both dashboards are accessible
3. ✅ Generate a test learning path
4. ✅ Check LangSmith for traces
5. ✅ Check W&B for metrics
6. ✅ Review cost data in W&B
7. ✅ Set up alerts in LangSmith (optional)

## Cost Monitoring

After generating a few paths, check W&B to see:
- **Total cost** across all generations
- **Cost per topic** (which topics are expensive)
- **Cost per expertise level** (expert vs beginner)
- **Token usage patterns**

This helps you optimize prompts and reduce costs!

## Support

- **LangSmith Docs:** https://docs.smith.langchain.com
- **W&B Docs:** https://docs.wandb.ai
- **Setup Guide:** `docs/OBSERVABILITY_SETUP.md`
- **Implementation Details:** `OBSERVABILITY_IMPLEMENTATION.md`

---

**Ready?** Run `python test_observability.py` now! 🚀
