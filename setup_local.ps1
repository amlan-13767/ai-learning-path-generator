# Setup script for local development
# Installs minimal dependencies needed for testing

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Setting up local development environment" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

Write-Host "`n📦 Installing Celery and Redis..." -ForegroundColor Yellow
pip install celery redis flask flask-cors

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`n📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Run: python test_imports.py" -ForegroundColor White
Write-Host "   2. If all tests pass, you're ready!" -ForegroundColor White
Write-Host "   3. To test with Docker: docker-compose -f docker-compose.dev.yml up" -ForegroundColor White
