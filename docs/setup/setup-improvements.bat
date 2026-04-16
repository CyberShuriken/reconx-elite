@echo off
REM Setup script for ReconX Elite improvements (Windows)

echo.
echo ==================================
echo ReconX Elite Improvement Setup
echo ==================================
echo.

REM Check Python version
echo [*] Checking Python version...
python --version

REM Create virtual environment
echo [*] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

REM Install dependencies
echo [*] Installing dependencies...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

REM Install testing dependencies
echo [*] Installing testing dependencies...
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist

REM Install pre-commit
echo [*] Installing pre-commit hooks...
pip install pre-commit
pre-commit install
echo [+] Pre-commit hooks installed

REM Set test database
set DATABASE_URL=sqlite:///:memory:

REM Run tests
echo [*] Running tests...
pytest backend\tests\ -v --tb=short

REM Generate coverage report
echo [*] Generating coverage report...
pytest backend\tests\ --cov=backend --cov-report=html --cov-report=term
echo [+] Coverage report generated (htmlcov\index.html)

REM Code formatting
echo [*] Checking code formatting...
black backend\ --check --diff

REM Linting
echo [*] Running linting checks...
flake8 backend\ --max-line-length=120 --max-complexity=10

REM Type checking
echo [*] Running type checks...
mypy backend\app --ignore-missing-imports --no-error-summary

REM Security scanning
echo [*] Running security checks...
bandit -r backend\ -ll -f json -o bandit-report.json
safety check --json

REM Environment setup
echo [*] Checking environment configuration...
if not exist ".env" (
    echo [!] .env file not found
    if exist ".env.example" (
        copy .env.example .env
        echo [!] Please update .env with your configuration
    )
)

REM Docker images
echo [*] Building Docker images...
docker-compose build

REM Final summary
echo.
echo ==================================
echo [+] Setup completed successfully!
echo ==================================
echo.
echo Next steps:
echo   1. Update .env file with your configuration
echo   2. Run tests: pytest backend\tests\ -v
echo   3. Start services: docker-compose up
echo   4. View coverage: start htmlcov\index.html
echo   5. Check logs: docker-compose logs backend
echo.
echo Documentation:
echo   - Improvements: see IMPROVEMENTS.md
echo   - Tests: backend\tests\
echo   - Config: backend\app\config.py
echo   - Logging: backend\app\structured_logging.py
echo   - Metrics: backend\app\metrics.py
echo.

pause
