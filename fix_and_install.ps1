# Fix Pydantic Conflicts and Install Dependencies
# Run this script to completely fix the Pydantic version conflict

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🔧 Fixing Pydantic Conflicts and Installing Dependencies" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

# Step 1: Uninstall ALL conflicting packages
Write-Host "`n📦 Step 1: Removing conflicting packages..." -ForegroundColor Cyan
pip uninstall -y pydantic pydantic-core pydantic-settings langchain langchain-core langchain-openai langchain-community email-validator 2>$null

# Step 2: Clear pip cache
Write-Host "`n🧹 Step 2: Clearing pip cache..." -ForegroundColor Cyan
pip cache purge

# Step 3: Install Pydantic v1 FIRST (to lock it in)
Write-Host "`n📌 Step 3: Installing Pydantic v1 (locked)..." -ForegroundColor Cyan
pip install --no-cache-dir pydantic==1.10.18

# Step 4: Install email-validator compatible with Pydantic v1
Write-Host "`n📧 Step 4: Installing email-validator..." -ForegroundColor Cyan
pip install --no-cache-dir email-validator==2.1.0.post1

# Step 5: Install LangChain (old version compatible with Pydantic v1)
Write-Host "`n🔗 Step 5: Installing LangChain..." -ForegroundColor Cyan
pip install --no-cache-dir langchain==0.0.267

# Step 6: Install remaining dependencies
Write-Host "`n📦 Step 6: Installing remaining dependencies..." -ForegroundColor Cyan
pip install --no-cache-dir -r requirements.txt

# Step 7: Verify installation
Write-Host "`n✅ Step 7: Verifying installation..." -ForegroundColor Cyan
python -c "import pydantic; print(f'Pydantic version: {pydantic.VERSION}')"

$pydanticVersion = python -c "import pydantic; print(pydantic.VERSION)" 2>$null

if ($pydanticVersion -like "1.10.*") {
    Write-Host "`n🎉 SUCCESS! Pydantic v1 is installed correctly." -ForegroundColor Green
    Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Run: python run_flask.py" -ForegroundColor White
    Write-Host "   2. Open: http://localhost:5000" -ForegroundColor White
} else {
    Write-Host "`n⚠️  WARNING: Pydantic version is $pydanticVersion (should be 1.10.x)" -ForegroundColor Red
    Write-Host "   Please run this script again or contact support." -ForegroundColor Red
}

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
