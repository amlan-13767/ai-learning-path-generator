"""
Quick test script to verify setup is working correctly.
Run this after installing dependencies.
"""

import sys
import os

def test_imports():
    """Test that all critical imports work."""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("  ✅ Flask")
    except ImportError as e:
        print(f"  ❌ Flask: {e}")
        return False
    
    try:
        import pydantic
        print(f"  ✅ Pydantic (version {pydantic.VERSION})")
        if pydantic.VERSION.startswith("2"):
            print("  ⚠️  WARNING: Pydantic v2 detected, should be v1.10.18")
    except ImportError as e:
        print(f"  ❌ Pydantic: {e}")
        return False
    
    try:
        from langchain.chat_models import ChatOpenAI
        print("  ✅ LangChain ChatOpenAI")
    except ImportError as e:
        print(f"  ❌ LangChain ChatOpenAI: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✅ python-dotenv")
    except ImportError as e:
        print(f"  ❌ python-dotenv: {e}")
        return False
    
    try:
        from flask_sqlalchemy import SQLAlchemy
        print("  ✅ Flask-SQLAlchemy")
    except ImportError as e:
        print(f"  ❌ Flask-SQLAlchemy: {e}")
        return False
    
    return True


def test_env_file():
    """Test that .env file exists and has required keys."""
    print("\n🔍 Testing environment configuration...")
    
    from dotenv import load_dotenv
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        print("  ❌ .env file not found!")
        print("  📝 Create .env file and add OPENAI_API_KEY")
        return False
    
    print(f"  ✅ .env file exists at: {env_path}")
    
    load_dotenv(env_path)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("  ❌ OPENAI_API_KEY not set in .env")
        return False
    
    if openai_key.startswith('sk-'):
        print("  ✅ OPENAI_API_KEY is set")
    else:
        print("  ⚠️  OPENAI_API_KEY format looks incorrect")
    
    return True


def test_database():
    """Test database connection."""
    print("\n🔍 Testing database...")
    
    db_path = os.path.join(os.path.dirname(__file__), 'learning_path.db')
    
    if os.path.exists(db_path):
        print(f"  ✅ Database exists at: {db_path}")
        return True
    else:
        print("  ⚠️  Database not found (will be created on first run)")
        print("  💡 Run: python -m migrations.add_chatbot_tables")
        return True


def test_project_structure():
    """Test that key files and directories exist."""
    print("\n🔍 Testing project structure...")
    
    required_paths = [
        'src',
        'src/learning_path.py',
        'src/ml',
        'src/ml/model_orchestrator.py',
        'src/services',
        'web_app',
        'run_flask.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for path in required_paths:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} not found")
            all_exist = False
    
    return all_exist


def test_few_shot_prompting():
    """Test that few-shot prompting code is in place."""
    print("\n🔍 Testing few-shot prompting implementation...")
    
    learning_path_file = os.path.join(os.path.dirname(__file__), 'src', 'learning_path.py')
    
    try:
        with open(learning_path_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '=== EXAMPLE 1:' in content and '=== EXAMPLE 2:' in content:
            print("  ✅ Few-shot prompting examples found")
            return True
        else:
            print("  ❌ Few-shot prompting examples not found")
            return False
    except Exception as e:
        print(f"  ❌ Error reading learning_path.py: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 AI Learning Path Generator - Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_env_file()))
    results.append(("Database", test_database()))
    results.append(("Project Structure", test_project_structure()))
    results.append(("Few-Shot Prompting", test_few_shot_prompting()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\n📝 Next steps:")
        print("   1. Run: python run_flask.py")
        print("   2. Open: http://localhost:5000")
        print("   3. Test the application")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n📚 See LOCAL_SETUP_GUIDE.md for detailed instructions")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
