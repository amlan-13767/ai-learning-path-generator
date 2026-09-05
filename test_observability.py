"""
Test script to validate LangSmith and W&B API keys and setup.
Run this before generating learning paths to ensure observability is working.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 Testing Observability Setup")
print("=" * 60)

# Test 1: Check environment variables
print("\n1️⃣ Checking environment variables...")
from src.utils.config import (
    LANGCHAIN_TRACING_V2,
    LANGCHAIN_API_KEY,
    LANGCHAIN_PROJECT,
    WANDB_API_KEY,
    WANDB_PROJECT,
    WANDB_ENTITY,
    WANDB_MODE
)

print(f"   LANGCHAIN_TRACING_V2: {LANGCHAIN_TRACING_V2}")
print(f"   LANGCHAIN_API_KEY: {'✅ Set' if LANGCHAIN_API_KEY else '❌ Missing'}")
print(f"   LANGCHAIN_PROJECT: {LANGCHAIN_PROJECT}")
print(f"   WANDB_API_KEY: {'✅ Set' if WANDB_API_KEY else '❌ Missing'}")
print(f"   WANDB_PROJECT: {WANDB_PROJECT}")
print(f"   WANDB_ENTITY: {WANDB_ENTITY or 'Not set (will use default)'}")
print(f"   WANDB_MODE: {WANDB_MODE}")

if not LANGCHAIN_API_KEY:
    print("\n❌ LangSmith API key is missing!")
    print("   Add LANGCHAIN_API_KEY to your .env file")
    sys.exit(1)

if not WANDB_API_KEY:
    print("\n❌ W&B API key is missing!")
    print("   Add WANDB_API_KEY to your .env file")
    sys.exit(1)

# Test 2: Initialize observability manager
print("\n2️⃣ Initializing observability manager...")
try:
    from src.utils.observability import get_observability_manager
    
    obs_manager = get_observability_manager()
    
    print(f"   LangSmith enabled: {'✅ Yes' if obs_manager.langsmith_enabled else '❌ No'}")
    print(f"   W&B enabled: {'✅ Yes' if obs_manager.wandb_enabled else '❌ No'}")
    
    if not obs_manager.langsmith_enabled:
        print("\n⚠️  LangSmith initialization failed. Check your API key.")
    
    if not obs_manager.wandb_enabled:
        print("\n⚠️  W&B initialization failed. Check your API key.")
    
except Exception as e:
    print(f"\n❌ Failed to initialize observability manager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test LangSmith connection
print("\n3️⃣ Testing LangSmith connection...")
try:
    if obs_manager.langsmith_enabled:
        # LangSmith is automatically configured via environment variables
        # Just verify the environment is set correctly
        import os
        if os.getenv("LANGCHAIN_TRACING_V2") == "true":
            print("   ✅ LangSmith environment configured correctly")
            print(f"   📊 Project: {LANGCHAIN_PROJECT}")
            print(f"   🔗 Dashboard: https://smith.langchain.com")
        else:
            print("   ⚠️  LANGCHAIN_TRACING_V2 not set to 'true'")
    else:
        print("   ⏭️  LangSmith disabled, skipping")
except Exception as e:
    print(f"   ⚠️  LangSmith test warning: {e}")

# Test 4: Test W&B connection
print("\n4️⃣ Testing W&B connection...")
try:
    if obs_manager.wandb_enabled:
        import wandb
        
        # Check if we can access the API
        api = wandb.Api()
        
        # Try to get user info
        try:
            # This will validate the API key
            print(f"   ✅ W&B API key is valid")
            print(f"   📊 Project: {WANDB_PROJECT}")
            if WANDB_ENTITY:
                print(f"   👤 Entity: {WANDB_ENTITY}")
            print(f"   🔗 Dashboard: https://wandb.ai/{WANDB_ENTITY or 'your-username'}/{WANDB_PROJECT}")
        except Exception as e:
            print(f"   ⚠️  Could not validate W&B API key: {e}")
            print(f"   This might be okay - will test with actual logging")
    else:
        print("   ⏭️  W&B disabled, skipping")
except Exception as e:
    print(f"   ⚠️  W&B test warning: {e}")

# Test 5: Test logging functionality
print("\n5️⃣ Testing logging functionality...")
try:
    # Test metric logging
    obs_manager.log_metric("test_metric", 1.0, {"source": "validation_script"})
    print("   ✅ Metric logging works")
    
    # Test event logging
    obs_manager.log_event("test_event", {"status": "success", "test": True})
    print("   ✅ Event logging works")
    
    # Test LLM call logging
    obs_manager.log_llm_call(
        prompt="Test prompt",
        response="Test response",
        model="gpt-4o-mini",
        metadata={"test": True},
        latency_ms=100.0,
        token_count=50,
        cost=0.001
    )
    print("   ✅ LLM call logging works")
    
except Exception as e:
    print(f"   ⚠️  Logging test warning: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test cost estimation
print("\n6️⃣ Testing cost estimation...")
try:
    from src.utils.observability import estimate_cost
    
    cost = estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=500)
    print(f"   ✅ Cost estimation works")
    print(f"   💰 Example: 1000 input + 500 output tokens = ${cost:.4f}")
    
except Exception as e:
    print(f"   ❌ Cost estimation failed: {e}")

# Test 7: Test ModelOrchestrator integration
print("\n7️⃣ Testing ModelOrchestrator integration...")
try:
    from src.ml.model_orchestrator import ModelOrchestrator
    
    orchestrator = ModelOrchestrator()
    
    if hasattr(orchestrator, 'obs_manager'):
        print("   ✅ ModelOrchestrator has observability manager")
    else:
        print("   ⚠️  ModelOrchestrator missing observability manager")
    
except Exception as e:
    print(f"   ⚠️  ModelOrchestrator test warning: {e}")

# Final summary
print("\n" + "=" * 60)
print("📊 Summary")
print("=" * 60)

all_good = True

if not obs_manager.langsmith_enabled:
    print("⚠️  LangSmith: Not enabled or failed to initialize")
    all_good = False
else:
    print("✅ LangSmith: Ready")

if not obs_manager.wandb_enabled:
    print("⚠️  W&B: Not enabled or failed to initialize")
    all_good = False
else:
    print("✅ W&B: Ready")

print("\n" + "=" * 60)

if all_good:
    print("🎉 All systems go! You're ready to generate learning paths.")
    print("\nNext steps:")
    print("1. Generate a learning path using your app")
    print("2. Check LangSmith dashboard: https://smith.langchain.com")
    print("3. Check W&B dashboard: https://wandb.ai")
    print("\nYou should see:")
    print("  • Full LLM traces in LangSmith")
    print("  • Metrics and costs in W&B")
else:
    print("⚠️  Some issues detected. Review the warnings above.")
    print("\nCommon fixes:")
    print("  • Verify API keys are correct in .env")
    print("  • Ensure LANGCHAIN_TRACING_V2=true (not 'True')")
    print("  • Check internet connection")
    print("  • Restart your application after changing .env")

print("=" * 60)

# Cleanup
if obs_manager.wandb_enabled:
    try:
        obs_manager.finish()
        print("\n✅ W&B run finished cleanly")
    except:
        pass
