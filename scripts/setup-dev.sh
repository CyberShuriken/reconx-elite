#!/bin/bash
# Development setup script for ReconX-Elite

set -e

echo "Setting up ReconX-Elite development environment..."

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before continuing."
    echo "Press Enter to continue after editing .env..."
    read -r
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p backup logs

# Stop any existing services
echo "Stopping existing services..."
docker compose down 2>/dev/null || true

# Build and start services
echo "Building and starting services..."
docker compose up --build -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "Backend is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "WARNING: Backend health check failed after 30 attempts"
    fi
    sleep 2
done

# Run database migrations
echo "Running database migrations..."
docker compose run --rm migrate

echo "Setup complete!"
echo ""
echo "Access points:"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: docker compose down"
echo "To restart services: docker compose restart"
