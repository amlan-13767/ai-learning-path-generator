# Set Fly.io secrets for the worker
# Run this script to configure all required environment variables

Write-Host "Setting Fly.io secrets..." -ForegroundColor Cyan

# Navigate to Fly CLI directory (adjust if needed)
$flyPath = "$env:USERPROFILE\.fly\bin\fly.exe"

if (-not (Test-Path $flyPath)) {
    Write-Host "Fly CLI not found at $flyPath" -ForegroundColor Red
    Write-Host "Trying to use 'fly' from PATH..." -ForegroundColor Yellow
    $flyPath = "fly"
}

# Set secrets (replace placeholders with your actual values from .env)
& $flyPath secrets set `
    REDIS_URL="redis://default:<PASSWORD>@<HOST>:<PORT>/0" `
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY" `
    SECRET_KEY="YOUR_FLASK_SECRET_KEY" `
    PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY" `
    LANGCHAIN_API_KEY="YOUR_LANGCHAIN_API_KEY" `
    WANDB_API_KEY="YOUR_WANDB_API_KEY" `
    DEFAULT_MODEL="gpt-4o-mini" `
    FLASK_ENV="production" `
    -a ai-learning-path-generator

Write-Host "`nSecrets set! Now listing them..." -ForegroundColor Green
& $flyPath secrets list -a ai-learning-path-generator

Write-Host "`nNow restart the machines:" -ForegroundColor Cyan
Write-Host "fly machines restart 48e37eea7d4228 -a ai-learning-path-generator" -ForegroundColor Yellow
Write-Host "fly machines restart 0801e02c2663e8 -a ai-learning-path-generator" -ForegroundColor Yellow
