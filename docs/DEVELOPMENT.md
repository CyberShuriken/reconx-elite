# Development Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Python 3.8+ (for local development)
- Node.js & npm (for frontend development)

### Setup

1. **Clone and configure environment**
```bash
git clone <repository-url>
cd reconx-elite
# Edit .env with your configuration
```

2. **Start all services**
```bash
docker compose up --build
```

3. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

**Backend Development:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend Development:**
```bash
cd frontend
npm install
npm run dev
```

**Worker (Background Tasks):**
```bash
cd backend
.venv\Scripts\activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

## Project Structure

```
reconx-elite/
|-- backend/                 # FastAPI backend application
|   |-- app/                # Main application code
|   |-- alembic/            # Database migrations
|   |-- tests/              # Backend tests
|   |-- Dockerfile          # Backend Docker configuration
|   `-- requirements.txt    # Python dependencies
|-- frontend/               # React frontend application
|   |-- src/               # Frontend source code
|   |-- Dockerfile         # Frontend Docker configuration
|   `-- package.json        # Node.js dependencies
|-- docs/                   # Project documentation
|   |-- archive/           # Historical documentation
|   |-- setup/             # Setup scripts and guides
|   `-- technical/         # Technical documentation
|-- worker/                 # Celery worker configuration
|-- nginx/                  # Nginx configuration
|-- monitoring/             # Monitoring configuration
|-- docker-compose.yml      # Main Docker orchestration
`-- README.md              # Main project documentation
```

## Environment Configuration

Key environment variables:

**Database:**
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `DATABASE_URL` - Full database connection string

**Redis:**
- `REDIS_URL` - Redis connection string

**Security:**
- `JWT_SECRET_KEY` - JWT signing secret (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token lifetime
- `REFRESH_TOKEN_EXPIRE_MINUTES` - Refresh token lifetime

**AI Features (Optional):**
- `GEMINI_API_KEY` - Google Gemini API key for AI features
- `OPENROUTER_KEY` - OpenRouter API key for multi-model AI

## Testing

**Backend Tests:**
```bash
cd backend
python -m unittest discover -s tests
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

**Integration Tests:**
```bash
python run_backend_tests.py
```

## Troubleshooting

**Docker Issues:**
- Ensure Docker is running and has sufficient resources
- Check `docker compose logs` for service-specific errors
- Use `docker compose down && docker compose up --build` for full rebuild

**Database Issues:**
- Run migrations manually: `alembic upgrade head`
- Check database connection in .env file
- Verify PostgreSQL container is healthy

**AI Features Not Working:**
- Ensure API keys are properly set in .env
- Check rate limits and quotas
- Review backend logs for AI-related errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Security Notes

- Never commit API keys or secrets to version control
- Use strong, unique secrets in production
- Enable HTTPS in production environments
- Regularly update dependencies
