# Frontend Setup Script for Windows PowerShell
# Run this to set up the frontend for local development

Write-Host "🚀 Setting up AI Learning Path Generator Frontend..." -ForegroundColor Cyan
Write-Host ""

# Check Node.js version
Write-Host "Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Node.js installed: $nodeVersion" -ForegroundColor Green
    $major = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($major -lt 18) {
        Write-Host "⚠ Warning: Node.js 18+ recommended. You have $nodeVersion" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check if package.json exists
if (-not (Test-Path "package.json")) {
    Write-Host "✗ package.json not found. Are you in the frontend directory?" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    
    # Ask user for API URL
    Write-Host "Enter your backend API URL:" -ForegroundColor Cyan
    Write-Host "  [1] Local development (http://localhost:5000)" -ForegroundColor White
    Write-Host "  [2] Production API (https://ai-learning-path-api.onrender.com)" -ForegroundColor White
    Write-Host "  [3] Custom URL" -ForegroundColor White
    $choice = Read-Host "Select option (1-3)"
    
    switch ($choice) {
        "1" {
            $apiUrl = "http://localhost:5000"
        }
        "2" {
            $apiUrl = "https://ai-learning-path-api.onrender.com"
        }
        "3" {
            $apiUrl = Read-Host "Enter custom API URL"
        }
        default {
            $apiUrl = "http://localhost:5000"
        }
    }
    
    "VITE_API_URL=$apiUrl" | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ .env file created with VITE_API_URL=$apiUrl" -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Success message
Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start development server:  npm run dev" -ForegroundColor White
Write-Host "  2. Open browser:              http://localhost:3000" -ForegroundColor White
Write-Host "  3. Build for production:      npm run build" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation: See README.md for more details" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to start dev server
$start = Read-Host "Start development server now? (y/n)"
if ($start -eq "y" -or $start -eq "Y") {
    Write-Host ""
    Write-Host "Starting development server..." -ForegroundColor Cyan
    npm run dev
}
