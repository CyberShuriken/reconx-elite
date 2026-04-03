#!/bin/bash

# ReconX Elite - Advanced Bug Bounty Platform Setup Script
# This script sets up the complete advanced system with all new features

set -e

echo "🚀 RECONX ELITE - ADVANCED SETUP"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Setup environment
setup_environment() {
    print_step "Setting up environment..."
    
    # Copy .env.example to .env if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        
        print_warning "Please edit .env file and set your GEMINI_API_KEY for AI features"
        print_warning "Current .env file created with default settings"
    else
        print_status ".env file already exists"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    print_status "Environment setup completed!"
}

# Build and start services
build_services() {
    print_step "Building and starting services..."
    
    # Build the services
    print_status "Building Docker images..."
    docker-compose build
    
    # Start the services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    print_status "Services built and started!"
}

# Run database migrations
run_migrations() {
    print_step "Running database migrations..."
    
    # Wait for database to be ready
    print_status "Waiting for database..."
    sleep 5
    
    # Run migrations
    docker-compose exec backend alembic upgrade head
    
    print_status "Database migrations completed!"
}

# Validate system
validate_system() {
    print_step "Running system validation..."
    
    # Run the validation script
    python3 validate_docker_system.py
    
    if [ $? -eq 0 ]; then
        print_status "System validation passed!"
    else
        print_warning "System validation completed with warnings/errors"
    fi
}

# Show final setup information
show_final_info() {
    print_step "Setup completed!"
    
    echo ""
    echo "🎉 RECONX ELITE ADVANCED SETUP COMPLETED!"
    echo "=========================================="
    echo ""
    echo "📋 SERVICES STATUS:"
    echo "  • Backend API: http://localhost:8000"
    echo "  • Frontend: http://localhost:5173"
    echo "  • Database: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo ""
    echo "🚀 NEW ADVANCED FEATURES:"
    echo "  • ✅ Exploit Validation Engine"
    echo "  • ✅ Out-of-Band Interaction Tracking"
    echo "  • ✅ Manual Testing with Payload Injection"
    echo "  • ✅ Intelligence Learning System"
    echo "  • ✅ Custom Nuclei Template Engine"
    echo "  • ✅ AI Security Hardening"
    echo "  • ✅ Elite Report Generation (CVSS/CWE/OWASP)"
    echo "  • ✅ Centralized Logging & Validation"
    echo ""
    echo "🔧 MANAGEMENT COMMANDS:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart: docker-compose restart"
    echo "  • Validate system: python3 validate_docker_system.py"
    echo ""
    echo "📚 DOCUMENTATION:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • System Status: http://localhost:8000/api/system/health"
    echo "  • Admin Validation: http://localhost:8000/api/system/validation/admin"
    echo ""
    echo "🔒 SECURITY NOTES:"
    echo "  • Default JWT secret is for development only"
    echo "  • Configure GEMINI_API_KEY in .env for AI features"
    echo "  • Review CORS settings for production"
    echo "  • Enable HTTPS in production"
    echo ""
    echo "🎯 NEXT STEPS:"
    echo "  1. Edit .env file with your configuration"
    echo "  2. Set GEMINI_API_KEY for AI features"
    echo "  3. Create admin user via API"
    echo "  4. Start your first scan"
    echo ""
    echo "🌟 ENJOY YOUR ADVANCED BUG BOUNTY PLATFORM!"
}

# Main execution
main() {
    echo "Starting ReconX Elite Advanced Setup..."
    echo ""
    
    check_prerequisites
    setup_environment
    build_services
    run_migrations
    validate_system
    show_final_info
    
    echo ""
    print_status "Setup script completed successfully!"
}

# Handle script interruption
trap 'print_error "Setup interrupted"; exit 1' INT

# Run main function
main
