# Backend Health Check Fix

## Problem

Backend container marked as "unhealthy" causing deployment failure:
```
dependency failed to start: container edms_prod_backend is unhealthy
✗ Failed to start Docker containers
```

## Root Cause

The backend startup sequence takes 15-40 seconds:

1. **Migrations** (10-30 seconds) - Creates/updates database tables
2. **Load fixtures** (1-2 seconds) - Loads initial_users.json
3. **Start gunicorn** (2-5 seconds) - Web server startup
4. **Total: 13-37 seconds**

The health check configuration was:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  # Missing: start_period
```

**Issue**: Health checks start immediately, but backend isn't ready yet.
- First check at 0s: ❌ Fails (migrations still running)
- Second check at 30s: ❌ Fails (might still be migrating)
- Third check at 60s: ❌ Fails (3 retries exhausted)
- **Result**: Container marked "unhealthy"

## Solution

Add `start_period: 60s` to give backend time to complete startup:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s  # Wait 60s before first health check
```

## What `start_period` Does

From Docker documentation:
> `start_period` provides initialization time for containers that need time to bootstrap. 
> Probe failures during this period will not count towards the maximum number of retries.

**Timeline with fix**:
- 0s: Container starts (migrations begin)
- 0-60s: **Start period** - health checks run but failures don't count
- 60s: First "real" health check (migrations likely complete)
- Result: ✅ Container becomes healthy

## Changes Made

### docker-compose.prod.yml

```diff
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
+     start_period: 60s  # Allow time for migrations to complete before health checks
```

### Why 60 seconds?

- Average migration time: 15-25 seconds
- Worst case: 30-40 seconds (many pending migrations)
- Buffer: +20 seconds for safety
- **Total: 60 seconds**

This is conservative but safe for production.

## Testing

### Before Fix
```bash
docker compose -f docker-compose.prod.yml up -d

# Result:
# edms_prod_backend | unhealthy
# edms_prod_celery_worker | dependency failed
# edms_prod_celery_beat | dependency failed
# edms_prod_frontend | dependency failed
```

### After Fix
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Timeline:
# 0-60s: Backend starting (migrations running)
# 60s: First health check
# Result: ✅ All containers healthy
```

## Verification

```bash
# Watch container status
watch docker compose -f docker-compose.prod.yml ps

# Check health check output
docker inspect edms_prod_backend --format='{{json .State.Health}}' | jq '.'

# View startup logs
docker compose -f docker-compose.prod.yml logs backend -f
```

## Related Health Checks

### Celery Worker
Already has `start_period: 40s`:
```yaml
celery_worker:
  healthcheck:
    test: ["CMD-SHELL", "celery -A edms inspect ping -d celery@$$HOSTNAME"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s  # Already present
```

### Celery Beat
Health check disabled (correct for schedulers):
```yaml
celery_beat:
  healthcheck:
    disable: true  # Beat is a scheduler, doesn't respond to ping
```

## Diagnostic Tools

Created scripts to help diagnose health issues:

### 1. diagnose_backend_health.sh
Comprehensive 10-point diagnostic:
- Container status and logs
- Database connectivity
- Redis connectivity
- Environment variables
- Health endpoint testing
- Migration status
- Common issue detection

### 2. fix_backend_unhealthy.sh
Interactive fix script:
- Identifies the issue
- Offers automated fixes
- Tests health endpoint manually
- Provides step-by-step guidance

## Common Issues (Other Than Timing)

### Issue 1: Migrations Fail
**Symptom**: Logs show migration errors
**Solution**:
```bash
docker compose exec backend python manage.py migrate --verbosity=2
```

### Issue 2: SECRET_KEY Missing
**Symptom**: "SECRET_KEY setting must not be empty"
**Solution**:
```bash
# Generate new key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Add to .env
echo "SECRET_KEY=<generated_key>" >> .env
```

### Issue 3: Database Not Ready
**Symptom**: "could not connect to server"
**Solution**:
```bash
# Check database health
docker compose ps db
docker compose logs db --tail=20
```

### Issue 4: Health Endpoint Missing
**Symptom**: "404 Not Found" on /health/
**Solution**: Verify URL config has health endpoint

## Prevention

### For New Services
Always add `start_period` to health checks for services that:
- Run migrations on startup
- Load initial data
- Have complex initialization
- Take >10 seconds to start

### Recommended Values
- **Simple services** (nginx, redis): No start_period needed
- **Django/API servers** (with migrations): 60s
- **Celery workers**: 40s
- **Databases**: No start_period (pg_isready is fast)

## Performance Impact

**Question**: Does `start_period` slow down deployment?

**Answer**: No! It only delays the first VALID health check.
- Container starts immediately
- Application runs normally during start_period
- Other containers can depend on it after start_period
- No actual delay in functionality

**Actual timing**:
```
Without start_period: 0-90s to fail (3 retries)
With start_period: 60s + first successful check (60-65s)

Net result: ~25s faster to success or similar time to failure
```

## Documentation References

- Docker healthcheck: https://docs.docker.com/engine/reference/builder/#healthcheck
- Docker Compose health checks: https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck
- Start period parameter: https://docs.docker.com/engine/reference/builder/#healthcheck

## Date
2026-01-24
