#!/usr/bin/env bash
set -euo pipefail

REQUIRED_VARS=(
  DATABASE_URL
  REDIS_URL
  JWT_SECRET_KEY
  JWT_ALGORITHM
  ACCESS_TOKEN_EXPIRE_MINUTES
  REFRESH_TOKEN_EXPIRE_MINUTES
  CORS_ALLOWED_ORIGINS
  SUPABASE_URL
  SUPABASE_PUBLISHABLE_KEY
  OPENROUTER_KEY
  OR_KEY_NEMOTRON_NANO
  OR_KEY_NEMOTRON_SUPER
  OR_KEY_QWEN_CODER
  OR_KEY_GLM_45
  OPENROUTER_API_KEY_SECONDARY
  OPENROUTER_API_KEY_TERTIARY
  OR_KEY_MINIMAX
  OR_KEY_GPT_OSS_120B
  OR_KEY_GPT_OSS_20B
  OR_KEY_NEMOTRON_SUPER_ALT
  GEMINI_API_KEY
)

missing=()
for name in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Missing required production variables:"
  printf '  - %s\n' "${missing[@]}"
  exit 1
fi

if [[ "$DATABASE_URL" != postgresql+psycopg2://* ]]; then
  echo "DATABASE_URL must start with postgresql+psycopg2://"
  exit 1
fi

if [[ "$REDIS_URL" != redis://* && "$REDIS_URL" != rediss://* ]]; then
  echo "REDIS_URL must start with redis:// or rediss://"
  exit 1
fi

if [[ "$JWT_SECRET_KEY" == "change-me-in-production" || ${#JWT_SECRET_KEY} -lt 32 ]]; then
  echo "JWT_SECRET_KEY must be changed and at least 32 characters long"
  exit 1
fi

if [[ "$JWT_ALGORITHM" != "HS256" ]]; then
  echo "JWT_ALGORITHM must be HS256"
  exit 1
fi

if [[ "$CORS_ALLOWED_ORIGINS" == "*" || "$CORS_ALLOWED_ORIGINS" != https://* ]]; then
  echo "CORS_ALLOWED_ORIGINS must be the exact https:// Vercel frontend origin"
  exit 1
fi

echo "Production environment validation passed."
