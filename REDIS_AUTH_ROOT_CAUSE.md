# Redis Authentication Error - Root Cause Analysis

## Issue
After env_file directive change (commit 7149860), Redis authentication started failing.

## Root Cause

### Before env_file Change
```yaml
environment:
  - REDIS_URL=redis://:${REDIS_PASSWORD:-change_me_redis_password}@redis:6379/1
```

- Used shell variable interpolation
- `${REDIS_PASSWORD:-fallback}` syntax
- If REDIS_PASSWORD not set, used default password in URL
- **Redis container had no auth, but password in URL was tolerated**

### After env_file Change  
```yaml
env_file:
  - .env
```

- Reads REDIS_URL directly from .env file
- deploy-interactive.sh creates .env with: `REDIS_URL=redis://redis:6379/1` (no password)
- **BUT**: If .env already exists from old deployment, it might have password

## Why Old Setup "Worked"

The old hardcoded URLs had passwords, but Redis container never enforced them:
```yaml
redis:
  image: redis:7-alpine
  # No requirepass command = authentication disabled
```

Django-redis was sending password, Redis ignored it. Everything worked.

## Why New Setup Fails

When env_file loads from .env:
- If .env has `REDIS_URL=redis://:password@redis:6379/1`
- Django-redis sends AUTH command
- Redis (with no password) rejects with "Authentication required"

## Solution

Ensure .env file has Redis URLs WITHOUT passwords:
```bash
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
REDIS_PASSWORD=
```

## Prevention

Update deploy-interactive.sh to check and fix Redis URLs after creation.

