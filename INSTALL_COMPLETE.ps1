# Complete Installation Script for AI Learning Path Generator
# This script fixes all Pydantic conflicts and installs dependencies

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Learning Path Generator - Complete Installation" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Uninstall ALL conflicting packages
Write-Host "`n[1/7] Removing conflicting packages..." -ForegroundColor Cyan
$packages = @(
    "pydantic",
    "pydantic-core", 
    "pydantic-settings",
    "langchain",
    "langchain-core",
    "langchain-openai",
    "langchain-community",
    "email-validator"
)

foreach ($pkg in $packages) {
    pip uninstall -y $pkg 2>$null | Out-Null
}
Write-Host "  Done!" -ForegroundColor Green

# Step 2: Clear pip cache
Write-Host "`n[2/7] Clearing pip cache..." -ForegroundColor Cyan
pip cache purge | Out-Null
Write-Host "  Done!" -ForegroundColor Green

# Step 3: Install Pydantic v1 FIRST
Write-Host "`n[3/7] Installing Pydantic v1.10.18..." -ForegroundColor Cyan
pip install --no-cache-dir pydantic==1.10.18 | Out-Null
Write-Host "  Done!" -ForegroundColor Green

# Step 4: Install email-validator
Write-Host "`n[4/7] Installing email-validator..." -ForegroundColor Cyan
pip install --no-cache-dir email-validator==2.1.0.post1 | Out-Null
Write-Host "  Done!" -ForegroundColor Green

# Step 5: Install LangChain
Write-Host "`n[5/7] Installing LangChain 0.0.267..." -ForegroundColor Cyan
pip install --no-cache-dir langchain==0.0.267 | Out-Null
Write-Host "  Done!" -ForegroundColor Green

# Step 6: Install remaining dependencies
Write-Host "`n[6/7] Installing remaining dependencies..." -ForegroundColor Cyan
pip install --no-cache-dir -r requirements.txt | Out-Null
Write-Host "  Done!" -ForegroundColor Green

# Step 7: Verify installation
Write-Host "`n[7/7] Verifying installation..." -ForegroundColor Cyan
$pydanticVersion = python -c "import pydantic; print(pydantic.VERSION)" 2>$null

if ($pydanticVersion -like "1.10.*") {
    Write-Host "  Pydantic: $pydanticVersion" -ForegroundColor Green
    
    # Test imports
    $testResult = python -c @"
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import Document
    from src.ml.model_orchestrator import ModelOrchestrator
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
"@ 2>&1
    
    if ($testResult -eq "OK") {
        Write-Host "  All imports: OK" -ForegroundColor Green
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "  SUCCESS! Installation complete." -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "`nNext steps:" -ForegroundColor Yellow
        Write-Host "  1. Run: python run_flask.py" -ForegroundColor White
        Write-Host "  2. Open: http://localhost:5000" -ForegroundColor White
    } else {
        Write-Host "  Import test failed: $testResult" -ForegroundColor Red
        Write-Host "`nPlease check the error above." -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: Pydantic version is $pydanticVersion" -ForegroundColor Red
    Write-Host "  Expected: 1.10.x" -ForegroundColor Red
}

Write-Host ""
