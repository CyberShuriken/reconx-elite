# ReconX Elite Secure Environment Setup Script
# This script creates .env file from system environment variables

Write-Host "🔐 ReconX Elite - Secure Environment Setup" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"

# Check if .env already exists
if (Test-Path $envFile) {
    Write-Host "⚠️  .env file already exists. Skipping creation." -ForegroundColor Yellow
    exit 0
}

# Read API key from environment
$apiKey = $env:GEMINI_API_KEY

if (-not $apiKey) {
    Write-Host "❌ GEMINI_API_KEY environment variable not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set it first:" -ForegroundColor White
    Write-Host "PowerShell: `$env:GEMINI_API_KEY = 'your-api-key-here'" -ForegroundColor Gray
    Write-Host "CMD: set GEMINI_API_KEY=your-api-key-here" -ForegroundColor Gray
    Write-Host "Then run this script again." -ForegroundColor Gray
    exit 1
}

try {
    # Create .env file with the API key
    $envContent = @"
# ReconX Elite Environment Configuration
# Generated automatically from system environment variables
# NEVER commit this file to version control

# AI Integration
GEMINI_API_KEY=$apiKey
"@
    
    # Copy base configuration from .env.example
    $envExampleFile = Join-Path $projectRoot ".env.example"
    if (Test-Path $envExampleFile) {
        $baseConfig = Get-Content $envExampleFile | Where-Object { $_ -notmatch "^GEMINI_API_KEY=" }
        $envContent = $envContent + "`r`n" + ($baseConfig -join "`r`n")
    }
    
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    
    Write-Host "✅ .env file created successfully" -ForegroundColor Green
    Write-Host "🔐 API key secured from environment variable" -ForegroundColor Green
    Write-Host "📝 .env is already in .gitignore" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run: docker-compose up --build" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed to create .env file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
