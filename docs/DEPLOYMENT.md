# Deployment Guide

## Recommended Production Topology

The production deployment is split across hosted services:

- Vercel hosts only the React frontend.
- Railway runs FastAPI, Celery workers, and Alembic migrations from `backend/Dockerfile`.
- Supabase provides hosted Postgres and Supabase Auth.
- Upstash provides hosted Redis for cache, Celery broker, and Celery result backend.

See `docs/vercel-live-deployment.md` for frontend settings and
`docs/RAILWAY_PRODUCTION.md` for backend service setup.

## Production Deployment

### Environment Setup

1. **Server Requirements**
   - Docker & Docker Compose
   - Minimum 4GB RAM
   - 50GB+ storage
   - SSL certificates (for HTTPS)

2. **Environment Configuration**
```bash
# Edit .env with production values
```

**Critical Production Settings:**
- `JWT_SECRET_KEY` - Use a strong, unique secret
- `POSTGRES_PASSWORD` - Use a strong database password
- `HTTPS_BEHIND_PROXY=true` - Enable HSTS headers
- `METRICS_ENABLED=false` - Disable metrics in production (optional)

### SSL/TLS Setup

1. **Obtain SSL Certificates**
```bash
# Using Let's Encrypt (recommended)
certbot certonly --standalone -d yourdomain.com
```

2. **Configure Nginx**
```bash
# Enable TLS profile
docker compose --profile tls up -d
```

3. **Update Environment**
```bash
VITE_API_URL=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
HTTPS_BEHIND_PROXY=true
```

### Docker Compose Production

```bash
# Start production services
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Verify services
docker compose ps
curl https://yourdomain.com/health
```

## Monitoring

### Health Checks

- **Backend**: `GET /health`
- **System**: `GET /system/health`
- **Database**: PostgreSQL health check
- **Redis**: Redis ping

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
```

### Metrics (Optional)

Enable Prometheus monitoring:
```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

Access points:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Backup Strategy

### Database Backups

Automatic backups are configured via the `db-backup` service:
- **Frequency**: Every 24 hours (configurable)
- **Retention**: 7 days (configurable)
- **Location**: `/backups` volume

**Manual Backup:**
```bash
docker compose exec postgres pg_dump -U reconx reconx > backup.sql
```

**Restore Backup:**
```bash
docker compose exec -T postgres psql -U reconx reconx < backup.sql
```

### Configuration Backup

```bash
# Backup environment and configuration
tar -czf config-backup.tar.gz .env docker-compose.yml nginx/
```

## Scaling

### Horizontal Scaling

**Multiple Workers:**
```bash
# Scale worker services
docker compose up -d --scale worker=3
```

**Load Balancing:**
- Nginx handles load balancing for frontend
- Redis distributes tasks among workers
- PostgreSQL handles concurrent connections

### Resource Optimization

**Database Tuning:**
```bash
# Adjust PostgreSQL settings in docker-compose.yml
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

**Worker Optimization:**
```bash
# Adjust worker concurrency
WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

## Security

### Network Security

1. **Firewall Configuration**
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

2. **Docker Network Isolation**
- Services communicate via internal Docker network
- Only frontend and nginx exposed to internet
- Database and Redis not accessible externally

### Application Security

1. **Environment Variables**
- Never commit .env files to version control
- Use strong, unique secrets
- Rotate keys regularly

2. **Container Security**
```bash
# Run containers as non-root (already configured)
# Drop capabilities (already configured)
# Use read-only filesystems where possible
```

3. **Dependencies**
```bash
# Regularly update dependencies
docker compose pull
docker compose up -d
```

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check logs
docker compose logs service-name

# Check resource usage
docker stats

# Restart services
docker compose restart
```

**Database Connection Issues:**
```bash
# Check database health
docker compose exec postgres pg_isready -U reconx

# Test connection from backend
docker compose exec backend python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

**High Memory Usage:**
```bash
# Monitor resource usage
docker stats

# Adjust container limits
docker compose up -d --scale worker=1
```

### Performance Optimization

**Database Performance:**
```bash
# Check slow queries
docker compose exec postgres psql -U reconx -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Analyze tables
docker compose exec postgres psql -U reconx -c "ANALYZE;"
```

**Application Performance:**
```bash
# Monitor response times
curl -w "@curl-format.txt" https://yourdomain.com/health

# Check worker queue
docker compose exec worker celery -A app.tasks.celery_app.celery_app inspect active
```
