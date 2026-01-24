# Email Configuration Root Cause Fix

## Problem Statement

Email test consistently fails with `Connection refused` to `localhost:587` even after:
- Configuring Gmail SMTP in deployment script
- Updating .env file with correct settings
- Recreating backend container with `--force-recreate`

**Error**: `ConnectionRefusedError: [Errno 111] Connection refused`
**Shows**: `SMTP Host: localhost:587` instead of `smtp.gmail.com:587`

## Root Cause Analysis

### The Issue

**docker-compose.prod.yml** hardcoded environment variables with fallback defaults:

```yaml
backend:
  environment:
    - EMAIL_HOST=${EMAIL_HOST:-localhost}  # ← Fallback to localhost!
    - EMAIL_PORT=${EMAIL_PORT:-587}
    - EMAIL_BACKEND=${EMAIL_BACKEND:-django.core.mail.backends.console.EmailBackend}
```

### Why This Failed

1. **Deployment script updates .env file** with correct values:
   ```bash
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   ```

2. **Docker Compose doesn't auto-read .env changes** even with `--force-recreate`
   - Docker reads .env **only on initial `docker compose up`**
   - `--force-recreate` rebuilds containers but **environment variables are cached**
   - The hardcoded defaults in docker-compose.yml take precedence

3. **${VAR:-default} syntax problem**:
   - If `EMAIL_HOST` not found in shell environment → uses `localhost`
   - .env file variables need explicit `env_file:` directive to be loaded

4. **Why recreate didn't work**:
   ```bash
   docker compose up -d --force-recreate --no-deps backend
   ```
   - This recreates the container
   - BUT: Still uses the same environment spec from docker-compose.yml
   - .env file is never re-read unless you restart the entire compose stack

## The Solution

### Changed: Use `env_file` Directive

**Before** (hardcoded with defaults):
```yaml
backend:
  environment:
    - SECRET_KEY=${SECRET_KEY:-generate_a_secure_secret_key_here}
    - DB_NAME=${DB_NAME:-edms_prod_db}
    - EMAIL_HOST=${EMAIL_HOST:-localhost}  # ← Always defaults to localhost
    - EMAIL_PORT=${EMAIL_PORT:-587}
    # ... 20+ more variables
```

**After** (load from .env file):
```yaml
backend:
  env_file:
    - .env  # ← Load ALL variables from .env file
  environment:
    - DEBUG=False
    - DJANGO_SETTINGS_MODULE=edms.settings.production
    - DB_HOST=db  # Container-specific overrides only
    - DB_PORT=5432
    - ENVIRONMENT=production
```

### Benefits

1. ✅ **Dynamic configuration**: .env changes are picked up on container recreate
2. ✅ **Simpler docker-compose.yml**: No need to list all variables
3. ✅ **No fallback conflicts**: .env values take precedence
4. ✅ **Email configuration works**: SMTP settings properly loaded
5. ✅ **Easier maintenance**: One source of truth (.env file)

## Technical Details

### Docker Compose Variable Priority

1. **Highest**: `environment:` in docker-compose.yml (explicit values)
2. **Medium**: `env_file:` directive (loads from file)
3. **Lowest**: `${VAR:-default}` syntax (shell interpolation with fallback)

**Old approach** used priority #3 (lowest), which meant:
- If shell doesn't have `EMAIL_HOST` → use `localhost`
- .env file was ignored because variables weren't in shell environment

**New approach** uses priority #2 (medium):
- `env_file: .env` loads all variables into container
- Values from .env file are used directly
- No fallback defaults needed

### What Changed in docker-compose.prod.yml

**Services modified**:
- `backend` (lines 57-99)
- `celery_worker` (lines 114-147)
- `celery_beat` (lines 165-211)

**Added to each**:
```yaml
env_file:
  - .env
```

**Removed from each**:
- All `${VAR:-default}` style environment variables
- Kept only container-specific settings (DEBUG, DJANGO_SETTINGS_MODULE, DB_HOST)

## Testing

### Before Fix
```bash
# Configure email in deployment script
# .env has: EMAIL_HOST=smtp.gmail.com
docker compose up -d --force-recreate --no-deps backend

# Check what container sees:
docker compose exec backend env | grep EMAIL_HOST
# Output: EMAIL_HOST=localhost  # ← WRONG!
```

### After Fix
```bash
# Configure email in deployment script
# .env has: EMAIL_HOST=smtp.gmail.com
docker compose up -d --force-recreate --no-deps backend

# Check what container sees:
docker compose exec backend env | grep EMAIL_HOST
# Output: EMAIL_HOST=smtp.gmail.com  # ← CORRECT!
```

## Deployment Impact

### On Existing Deployments

If you have an existing deployment, you need to recreate containers:

```bash
cd /home/lims/edms
git pull origin main

# IMPORTANT: Recreate with new docker-compose.yml
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Verify email configuration loaded:
docker compose -f docker-compose.prod.yml exec backend env | grep EMAIL
```

### On New Deployments

The deployment scripts will work correctly:
- `deploy-interactive.sh` - Email test will work
- `deploy-interactive-fast.sh` - Email test will work

## Why This Kept Happening

This issue was **systematic**, not a one-time error:

1. **Script updated .env** ✅ (worked correctly)
2. **Script tried to reload** ✅ (used --force-recreate)
3. **Docker Compose didn't read .env** ❌ (no env_file directive)
4. **Container used hardcoded defaults** ❌ (localhost fallback)

Every deployment had the same pattern:
- Email config looked correct in .env
- Container restart appeared to work
- But runtime still used localhost
- **Because .env file was never loaded into container**

## Files Changed

1. **docker-compose.prod.yml**
   - Added `env_file: - .env` to backend, celery_worker, celery_beat
   - Removed hardcoded environment variable defaults
   - Simplified to container-specific settings only

2. **diagnose_email_root_cause.sh** (new diagnostic script)
   - Checks .env file contents
   - Checks container environment
   - Compares expected vs actual values

## Verification Commands

```bash
# 1. Check .env file has correct settings
grep EMAIL .env

# 2. Check container environment matches
docker compose exec backend env | grep EMAIL

# 3. Test email sending
docker compose exec backend python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
print(f'EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'EMAIL_PORT: {settings.EMAIL_PORT}')
"

# 4. Send actual test email
docker compose exec backend python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Test email', 'from@example.com', ['to@example.com'])
"
```

## Related Issues Fixed

This fix also resolves:
- ✅ Celery email notifications not working
- ✅ Periodic review reminders not sent
- ✅ Task assignment notifications failing
- ✅ Any other email-based features

All these features depend on EMAIL_HOST being correctly set in the backend container.

## Date
2026-01-24
