# API Documentation

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

#### Targets
- `GET /targets` - List all targets
- `POST /targets` - Create new target
- `GET /targets/{id}` - Get target details
- `PUT /targets/{id}` - Update target
- `DELETE /targets/{id}` - Delete target

#### Scans
- `POST /scan/{target_id}` - Start scan
- `POST /scan/{target_id}/config` - Configure scan
- `GET /scans/{scan_id}` - Get scan status
- `GET /scans/{scan_id}/results` - Get scan results

#### Vulnerabilities
- `GET /vulnerabilities` - List vulnerabilities
- `GET /vulnerabilities/{id}` - Get vulnerability details
- `PUT /vulnerabilities/{id}` - Update vulnerability
- `POST /vulnerabilities/{id}/verify` - Verify vulnerability

#### Reports
- `GET /reports/{target_id}/json` - Get JSON report
- `GET /reports/{target_id}/pdf` - Get PDF report
- `POST /reports/generate` - Generate new report

#### Advanced Reconnaissance
- `POST /advanced-recon/stealth-config/{target_id}` - Create stealth config
- `GET /advanced-recon/stealth-config/{target_id}` - Get stealth config
- `POST /advanced-recon/parameter-discovery` - Start parameter discovery
- `POST /advanced-recon/content-fuzzing` - Start content fuzzing
- `GET /advanced-recon/parameters/{target_id}` - Get discovered parameters
- `GET /advanced-recon/fuzzed-endpoints/{target_id}` - Get fuzzed endpoints

#### System
- `GET /health` - Health check
- `GET /system/health` - System health check
- `GET /system/validation/admin` - Admin system validation

## WebSocket

Real-time updates are available via WebSocket connection:

```
ws://localhost:8000/ws
```

### WebSocket Events
- `scan_started` - Scan has started
- `scan_progress` - Scan progress update
- `scan_completed` - Scan completed
- `vulnerability_found` - New vulnerability discovered
- `notification` - System notification

## Rate Limits

The API implements rate limiting:

- **Register**: 10 requests/minute
- **Login**: 20 requests/minute
- **Token Refresh**: 30 requests/minute
- **Read Operations**: 120 requests/minute
- **Write Operations**: 60 requests/minute
- **Scan Operations**: 12 requests/minute
- **Report Generation**: 30 requests/minute

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details"
  }
}
```

### Common Error Codes

- `UNAUTHORIZED` - Invalid or missing authentication
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Invalid request data
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

## Examples

### Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### Create Target

```bash
curl -X POST http://localhost:8000/targets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "description": "Test target",
    "enable_ai_processing": true
  }'
```

### Start Scan

```bash
curl -X POST http://localhost:8000/scan/123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_type": "comprehensive",
    "config": {
      "enable_aggressive_scanning": false,
      "max_endpoints": 100
    }
  }'
```

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Data Models

### Target
```json
{
  "id": "uuid",
  "domain": "example.com",
  "description": "Target description",
  "status": "active|inactive|archived",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "enable_ai_processing": true,
  "scan_count": 5,
  "vulnerability_count": 2
}
```

### Scan
```json
{
  "id": "uuid",
  "target_id": "uuid",
  "status": "pending|running|completed|failed",
  "scan_type": "basic|comprehensive|custom",
  "progress": 75,
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": null,
  "findings_count": 10,
  "config": {}
}
```

### Vulnerability
```json
{
  "id": "uuid",
  "target_id": "uuid",
  "scan_id": "uuid",
  "title": "Vulnerability title",
  "description": "Detailed description",
  "severity": "low|medium|high|critical",
  "cwe_id": "CWE-79",
  "cvss_score": 6.1,
  "status": "open|confirmed|false_positive|mitigated",
  "discovered_at": "2024-01-01T00:00:00Z",
  "details": {}
}
```
