"""
Quick test script to verify Phase 1 structure
Run this to check if everything is set up correctly
"""
import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} NOT FOUND")
        return False

def check_directory(path, description):
    """Check if a directory exists"""
    if Path(path).is_dir():
        print(f"✅ {description}: {path}/")
        return True
    else:
        print(f"❌ {description}: {path}/ NOT FOUND")
        return False

def main():
    print("=" * 60)
    print("Phase 1 Structure Verification")
    print("=" * 60)
    
    checks = []
    
    print("\n📁 Directory Structure:")
    checks.append(check_directory("backend", "Backend directory"))
    checks.append(check_directory("worker", "Worker directory"))
    checks.append(check_directory("shared", "Shared directory"))
    checks.append(check_directory("src", "Existing src directory"))
    
    print("\n🔧 Backend Files:")
    checks.append(check_file("backend/app.py", "Backend Flask app"))
    checks.append(check_file("backend/routes.py", "Backend routes"))
    checks.append(check_file("backend/requirements.txt", "Backend requirements"))
    checks.append(check_file("backend/Procfile", "Backend Procfile"))
    checks.append(check_file("backend/Dockerfile", "Backend Dockerfile"))
    
    print("\n⚙️ Worker Files:")
    checks.append(check_file("worker/celery_app.py", "Celery app"))
    checks.append(check_file("worker/tasks.py", "Worker tasks"))
    checks.append(check_file("worker/requirements.txt", "Worker requirements"))
    checks.append(check_file("worker/Procfile", "Worker Procfile"))
    checks.append(check_file("worker/Dockerfile", "Worker Dockerfile"))
    
    print("\n🐳 Docker & Docs:")
    checks.append(check_file("docker-compose.dev.yml", "Docker Compose"))
    checks.append(check_file("HYBRID_DEPLOYMENT_GUIDE.md", "Deployment guide"))
    checks.append(check_file("PHASE1_README.md", "Phase 1 README"))
    
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 All checks passed! ({passed}/{total})")
        print("\n✅ Phase 1 structure is complete!")
        print("\n📝 Next steps:")
        print("   1. Test locally: docker-compose -f docker-compose.dev.yml up")
        print("   2. Deploy backend to Render")
        print("   3. Deploy worker to Render")
        print("   4. Read HYBRID_DEPLOYMENT_GUIDE.md for details")
    else:
        print(f"⚠️  Some checks failed ({passed}/{total} passed)")
        print("\nPlease review the missing files above.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
