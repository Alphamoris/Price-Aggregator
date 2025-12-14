# Asset Aggregator

A production-minded Crypto & Stock Market Data Aggregator built with FastAPI and Next.js.

## Overview

This system ingests real-time market data from two external sources (CoinGecko for crypto, Alpha Vantage for stocks), normalizes it into a unified schema, and exposes it through a REST API with a minimal frontend dashboard.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Docker Deployment

```bash
docker-compose up --build
```

## Architecture Decisions

### 1. Data Sources

| Source | Type | Rate Limit | Why |
|--------|------|------------|-----|
| CoinGecko | Crypto | 30/min, 10k/month | Free, reliable, no API key required |
| Alpha Vantage | Stocks | 5/min, 25/day | Free tier available, widely used |

### 2. Database: SQLite (dev) / PostgreSQL (prod)

- **Why SQLite for dev:** Zero configuration, single file, fast for small datasets
- **Why PostgreSQL for prod:** Connection pooling, concurrent writes, ACID compliance
- **Trade-off:** SQLite breaks at ~10-20 concurrent write operations due to file-level locking

### 3. Caching: In-Memory (cachetools)

- **Why not Redis:** For single-instance deployment, Redis adds operational complexity without proportional benefit
- **TTL:** 5 minutes matches data refresh interval
- **Trade-off:** Cache lost on restart; doesn't work with horizontal scaling

**When to switch to Redis:**
- Multiple application instances
- Cache persistence needed
- >10k requests/minute

### 4. Background Scheduler: APScheduler

- **Why not Celery:** No need for distributed task queue at this scale
- **Why not cron:** Integrated with application lifecycle, no external dependency
- **Trade-off:** Duplicate jobs if running multiple instances

### 5. Authentication: JWT with HS256

- **Why JWT:** Stateless, works with horizontal scaling, industry standard
- **Why HS256:** Symmetric encryption, simpler key management for single-service auth
- **Token expiry:** 30 minutes (balance between security and UX)

### 6. Structured Logging: structlog

- **Why:** JSON-formatted logs ready for ELK/Datadog/CloudWatch
- **Includes:** Request ID tracking, timestamps, log levels

## API Endpoints

### Authentication

```
POST /api/v1/auth/register
Body: { "username": "string", "email": "string", "password": "string" }
Response: { "id": 1, "username": "string", "email": "string", ... }

POST /api/v1/auth/login
Body: form-data { username, password }
Response: { "access_token": "jwt...", "token_type": "bearer" }

POST /api/v1/auth/token
Body: { "username": "string", "password": "string" }
Response: { "access_token": "jwt...", "token_type": "bearer" }
```

### Assets (Requires Authentication)

```
GET /api/v1/assets?page=1&page_size=20&asset_type=crypto
Headers: Authorization: Bearer <token>
Response: {
  "items": [...],
  "total": 55,
  "page": 1,
  "page_size": 20,
  "pages": 3
}

GET /api/v1/assets/crypto
GET /api/v1/assets/stocks
GET /api/v1/assets/{symbol}

POST /api/v1/assets/refresh  # Admin only
```

### Health

```
GET /api/v1/health           # Health check with database status
GET /api/v1/health/dependencies  # Full dependency check (DB, APIs, cache)
```

## Trade-offs & Limitations

### Current Limitations

| Component | Limit | Symptom | Solution |
|-----------|-------|---------|----------|
| SQLite | ~20 concurrent writes | Lock errors | PostgreSQL |
| In-memory cache | 1 instance | Cache misses across pods | Redis |
| APScheduler | 1 instance | Duplicate refresh jobs | Distributed lock |
| Alpha Vantage | 25 calls/day | Missing stock data | Paid API tier |

### What Scales Well

1. **Stateless JWT auth** - Horizontal scaling ready
2. **Normalized data model** - Easy to add new asset sources
3. **Service-oriented architecture** - Clear boundaries, testable
4. **Docker-ready** - Kubernetes deployment ready
5. **Structured logging** - Production observability ready

### Breaking Points (in order)

1. **SQLite concurrency** - First to fail under load
2. **In-memory cache** - Lost on each deployment/restart
3. **Scheduler duplication** - Multiple instances = multiple refreshes
4. **API rate limits** - External source bottleneck

## Error Handling Strategy

### Application Exceptions

```python
AppException          # Base exception
├── AuthenticationError   # 401 - Invalid credentials
├── AuthorizationError    # 403 - Insufficient permissions
├── NotFoundError         # 404 - Resource not found
├── ValidationError       # 422 - Invalid input
├── ExternalAPIError      # 502 - CoinGecko/AlphaVantage failure
├── RateLimitError        # 429 - Rate limit exceeded
└── DatabaseError         # 500 - Database operation failed
```

### Partial Failure Handling

The background scheduler continues even if one data source fails:

```
[Crypto Refresh] ✓ Success - 50 assets updated
[Stock Refresh]  ✗ Failed - Rate limit
[Result] Partial success - crypto data available, stocks stale
```

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v --cov=app
```

### Test Coverage

- `test_auth.py` - Registration, login, token validation
- `test_cache.py` - Cache operations, TTL, pattern invalidation
- `test_health.py` - Health endpoints
- `test_security.py` - Password hashing, JWT encode/decode

## CI/CD

GitHub Actions pipeline:

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Backend     │   │ Frontend    │   │ Docker      │
│ Lint + Test │   │ Lint + Build│   │ Build       │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                    All must pass
```

## What I'd Improve With More Time

### High Priority

1. **Database migrations** - Alembic for schema versioning
2. **Refresh tokens** - Better security with token rotation
3. **Rate limiting** - Protect API with slowapi
4. **Integration tests** - Testcontainers for full-stack testing

### Medium Priority

5. **WebSocket support** - Real-time price updates
6. **Prometheus metrics** - Request latency, error rates, cache hit rate
7. **API versioning** - /v1, /v2 support for breaking changes
8. **User preferences** - Watchlists, favorite assets

### Nice to Have

9. **Token blacklisting** - Proper logout invalidation
10. **Email verification** - Account security
11. **Admin dashboard** - Manual refresh, user management
12. **Historical data** - Price charts, trend analysis

---

<div align="center">
  <img src="frontend/public/pegasus1.jpg" alt="Alphamoris" width="50"/> &nbsp;&nbsp;<strong>|</strong>&nbsp;&nbsp; <em>Built by</em> &nbsp;<strong>ALPHAMORIS</strong>
</div>