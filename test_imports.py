"""
Test script to verify all imports work correctly
Run this before deploying to catch any import errors
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("Testing Imports for Hybrid Architecture")
print("=" * 60)

errors = []

# Test backend imports
print("\n📦 Testing Backend Imports...")
try:
    from backend import app
    print("✅ backend.app")
except Exception as e:
    print(f"❌ backend.app: {e}")
    errors.append(("backend.app", e))

try:
    from backend import routes
    print("✅ backend.routes")
except Exception as e:
    print(f"❌ backend.routes: {e}")
    errors.append(("backend.routes", e))

# Test worker imports
print("\n⚙️ Testing Worker Imports...")
try:
    from worker import celery_app
    print("✅ worker.celery_app")
except Exception as e:
    print(f"❌ worker.celery_app: {e}")
    errors.append(("worker.celery_app", e))

try:
    from worker import tasks
    print("✅ worker.tasks")
except Exception as e:
    print(f"❌ worker.tasks: {e}")
    errors.append(("worker.tasks", e))

# Test existing src imports
print("\n🔧 Testing Existing Src Imports...")
try:
    from src.learning_path import LearningPathGenerator
    print("✅ src.learning_path.LearningPathGenerator")
except Exception as e:
    print(f"❌ src.learning_path.LearningPathGenerator: {e}")
    errors.append(("src.learning_path", e))

try:
    from src.ml.model_orchestrator import ModelOrchestrator
    print("✅ src.ml.model_orchestrator.ModelOrchestrator")
except Exception as e:
    print(f"❌ src.ml.model_orchestrator: {e}")
    errors.append(("src.ml.model_orchestrator", e))

# Summary
print("\n" + "=" * 60)
if not errors:
    print("🎉 All imports successful!")
    print("\n✅ Ready for deployment!")
else:
    print(f"⚠️  {len(errors)} import error(s) found:")
    for module, error in errors:
        print(f"   - {module}: {error}")
    print("\n❌ Fix these errors before deploying")

print("=" * 60)
