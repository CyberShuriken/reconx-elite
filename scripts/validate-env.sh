#!/bin/bash
set -e

# Validate required environment variables for docker-compose
REQUIRED_VARS=(
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "JWT_SECRET_KEY"
)

echo "Validating environment variables..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Load .env file
export "$(cat .env | grep -v '^#' | xargs)"

# Check required variables
missing=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        missing+=("$var")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "ERROR: Missing required environment variables:"
    printf '  - %s\n' "${missing[@]}"
    echo ""
    echo "Please set these variables in your .env file."
    exit 1
fi

# Warn about critical variables with default values
if [ "$JWT_SECRET_KEY" = "change-me-in-production" ]; then
    echo "WARNING: JWT_SECRET_KEY is set to the default value. This is insecure for production."
fi

echo "Environment validation passed."
