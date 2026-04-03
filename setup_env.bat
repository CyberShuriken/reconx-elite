@echo off
REM ReconX Elite Secure Environment Setup Script (Windows)
REM This script creates .env file from system environment variables

echo 🔐 ReconX Elite - Secure Environment Setup
echo.

REM Check if .env already exists
if exist ".env" (
    echo ⚠️  .env file already exists. Skipping creation.
    exit /b 0
)

REM Read API key from environment
if "%GEMINI_API_KEY%"=="" (
    echo ❌ GEMINI_API_KEY environment variable not found
    echo.
    echo Please set it first:
    echo CMD: set GEMINI_API_KEY=your-api-key-here
    echo PowerShell: $env:GEMINI_API_KEY = 'your-api-key-here'
    echo.
    echo Then run this script again.
    exit /b 1
)

REM Create .env file
echo # ReconX Elite Environment Configuration > .env
echo # Generated automatically from system environment variables >> .env
echo # NEVER commit this file to version control >> .env
echo. >> .env
echo # AI Integration >> .env
echo GEMINI_API_KEY=%GEMINI_API_KEY% >> .env
echo. >> .env

REM Copy base configuration from .env.example
if exist ".env.example" (
    for /f "usebackq tokens=* delims=" %%a in (".env.example") do (
        echo %%a >> .env
    )
)

echo ✅ .env file created successfully
echo 🔐 API key secured from environment variable
echo 📝 .env is already in .gitignore
echo.
echo You can now run: docker-compose up --build
pause
