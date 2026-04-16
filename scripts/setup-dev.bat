@echo off
REM Development setup script for ReconX-Elite (Windows)

echo Setting up ReconX-Elite development environment...

REM Check prerequisites
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration before continuing.
    echo Press Enter to continue after editing .env...
    pause
)

REM Create necessary directories
echo Creating directories...
if not exist backup mkdir backup
if not exist logs mkdir logs

REM Stop any existing services
echo Stopping existing services...
docker-compose down 2>nul

REM Build and start services
echo Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo Checking service health...
set /a counter=0
:health_check
set /a counter+=1
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if %counter% geq 30 (
        echo WARNING: Backend health check failed after 30 attempts
        goto continue_setup
    )
    timeout /t 2 /nobreak >nul
    goto health_check
)
echo Backend is healthy!

:continue_setup
REM Run database migrations
echo Running database migrations...
docker-compose run --rm migrate

echo Setup complete!
echo.
echo Access points:
echo   Frontend: http://localhost:5173
echo   Backend API: http://localhost:8000
echo   API Documentation: http://localhost:8000/docs
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down
echo To restart services: docker-compose restart
pause
