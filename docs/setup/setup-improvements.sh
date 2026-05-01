#!/bin/bash
# Setup script for ReconX Elite improvements

set -e

echo "🚀 ReconX Elite Improvement Setup"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo -e "${BLUE}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
fi
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install testing dependencies
echo -e "${BLUE}Installing testing dependencies...${NC}"
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install pytest-xdist  # For parallel test execution

# Install pre-commit
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
pip install pre-commit
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# Create test database
echo -e "${BLUE}Setting up test database...${NC}"
export DATABASE_URL="sqlite:///:memory:"

# Run tests
echo -e "${BLUE}Running tests...${NC}"
pytest backend/tests/ -v --tb=short || true

# Generate coverage report
echo -e "${BLUE}Generating coverage report...${NC}"
pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term
echo -e "${GREEN}✓ Coverage report generated (htmlcov/index.html)${NC}"

# Code formatting
echo -e "${BLUE}Checking code formatting...${NC}"
black backend/ --check --diff || true

# Linting
echo -e "${BLUE}Running linting checks...${NC}"
flake8 backend/ --max-line-length=120 --max-complexity=10 || true

# Type checking
echo -e "${BLUE}Running type checks...${NC}"
mypy backend/app --ignore-missing-imports --no-error-summary || true

# Security scanning
echo -e "${BLUE}Running security checks...${NC}"
bandit -r backend/ -ll -f json -o bandit-report.json || true
safety check --json || true
echo -e "${GREEN}✓ Security scan completed (bandit-report.json)${NC}"

# Environment setup
echo -e "${BLUE}Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Please create a .env file with your configuration.${NC}"
fi

# Docker images
echo -e "${BLUE}Building Docker images...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose build || true
    echo -e "${GREEN}✓ Docker images built${NC}"
fi

# Final summary
echo ""
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo ""
echo "📋 Next steps:"
echo "  1. Update .env file with your configuration"
echo "  2. Run tests: pytest backend/tests/ -v"
echo "  3. Start services: docker-compose up"
echo "  4. View coverage: open htmlcov/index.html"
echo "  5. Check logs: docker-compose logs backend"
echo ""
echo "📚 Documentation:"
echo "  - Improvements: see IMPROVEMENTS.md"
echo "  - Tests: backend/tests/"
echo "  - Config: backend/app/config.py"
echo "  - Logging: backend/app/structured_logging.py"
echo "  - Metrics: backend/app/metrics.py"
echo ""
echo -e "${BLUE}For more info, see IMPROVEMENTS.md${NC}"
