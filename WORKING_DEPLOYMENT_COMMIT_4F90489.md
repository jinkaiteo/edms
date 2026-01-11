# Working Deployment - Commit 4f90489 ✅

## Date: 2026-01-06 14:30 UTC
## Status: WORKING - Username displays correctly

---

## Successful Configuration

### Commit Information
- **Commit**: 4f90489
- **Date**: January 2, 2026 16:53:48 +0800
- **Message**: "test: Verify timezone consistency fix with comprehensive tests"
- **Source**: Identified from STAGING_DEPLOYMENT_SUCCESS_20260102.md

---

## Container Setup

### Docker Compose File
**File**: `docker-compose.prod.yml`

### Container Configuration

| Container Name | Image | Port Mapping | Status |
|----------------|-------|--------------|--------|
| edms_prod_frontend | edms-staging-frontend | 3001→80 | ✅ Healthy |
| edms_prod_backend | edms-staging-backend | 8001→8000 | ✅ Healthy |
| edms_prod_db | postgres:18 | 5433→5432 | ✅ Healthy |
| edms_prod_redis | redis:7-alpine | 6380→6379 | ✅ Healthy |
| edms_prod_celery_worker | edms-staging-celery_worker | - | ✅ Healthy |
| edms_prod_celery_beat | edms-staging-celery_beat | - | ✅ Running |

---

## Critical Configuration Change

### The Key Fix: REACT_APP_API_URL

**Problem**: Frontend was calling wrong API URL
- Frontend was calling: `http://172.28.1.148:3001/api/v1/...` ❌
- Should call: `http://172.28.1.148:8001/api/v1/...` ✅

**Solution**: Added environment variable before building frontend

### .env File Configuration

```bash
# Django Settings
DJANGO_ENV=production
SECRET_KEY=staging-secret-key-4f90489
DEBUG=False
ALLOWED_HOSTS=172.28.1.148,localhost

# Database
POSTGRES_DB=edms_db
POSTGRES_USER=edms_user
POSTGRES_PASSWORD=edms_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://172.28.1.148:3001,http://localhost:3001

# Time Zone
DISPLAY_TIMEZONE=Asia/Singapore

# Frontend API Configuration - CRITICAL!
REACT_APP_API_URL=http://172.28.1.148:8001/api/v1
```

**Key Addition**: `REACT_APP_API_URL=http://172.28.1.148:8001/api/v1`

---

## Deployment Steps That Worked

### 1. Prepare Code
```bash
git reset --hard 4f90489
```

### 2. Create Deployment Package
```bash
./create-deployment-package.sh
```

### 3. Deploy to Server
```bash
# Copy package to server
rsync -avz edms-deployment-*/ lims@172.28.1.148:~/edms-staging/

# SSH to server
ssh lims@172.28.1.148
cd ~/edms-staging
```

### 4. Configure Environment
```bash
# Create .env with REACT_APP_API_URL
cat > .env << 'ENVFILE'
# ... all settings ...
REACT_APP_API_URL=http://172.28.1.148:8001/api/v1
ENVFILE
```

### 5. Build and Start
```bash
# Build all containers
docker compose -f docker-compose.prod.yml build

# Start all containers
docker compose -f docker-compose.prod.yml up -d

# Wait for containers to start (30 seconds)
```

### 6. Initialize Database
```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create admin user
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@edms-staging.local', 'AdminPassword123')
PYEOF
```

---

## What Was Changed From Previous Attempts

### Previous Attempts (Failed)
1. ❌ Used commit 6ace8e5 (only documentation changes, not actual code)
2. ❌ Missing `REACT_APP_API_URL` configuration
3. ❌ Frontend calling wrong port (3001 instead of 8001)
4. ❌ Mixed old/new containers (11-hour-old DB with 30-minute-old frontend)

### This Attempt (Success)
1. ✅ Used commit 4f90489 (actual working deployment from Jan 2)
2. ✅ Added `REACT_APP_API_URL=http://172.28.1.148:8001/api/v1` to `.env`
3. ✅ Rebuilt frontend with correct API URL
4. ✅ All containers built and started together at same time
5. ✅ Admin password simplified: `AdminPassword123`

---

## Verification

### Working Features
- ✅ Login works (admin / AdminPassword123)
- ✅ Username "admin" displays in top-right corner
- ✅ JWT authentication functional
- ✅ Dashboard loads
- ✅ No console errors for authentication

### Known Issues (To Be Fixed)
- ⚠️ Document types not populated
- ⚠️ Document sources not populated
- ⚠️ Roles not populated

These require initialization scripts to be run (see next section).

---

## Access Information

**URL**: http://172.28.1.148:3001

**Credentials**:
- Username: `admin`
- Password: `AdminPassword123`

---

## Container Details

### Build Information
- **All containers created**: 2026-01-06 05:49:16 UTC
- **Frontend build**: Contains correct API URL configuration
- **Backend**: Running with Gunicorn WSGI
- **Database**: Fresh PostgreSQL 18 with migrations applied

### Health Checks
- All containers passing health checks
- Frontend: Nginx serving React production build
- Backend: Gunicorn responding on port 8001
- Database: PostgreSQL healthy
- Redis: Cache operational
- Celery: Worker and Beat scheduler running

---

## Critical Success Factors

1. **Correct Commit**: Using 4f90489 (not 6ace8e5)
2. **API URL Configuration**: `REACT_APP_API_URL` must be set before building frontend
3. **Fresh Build**: All containers built from scratch at same time
4. **Correct Ports**: Frontend 3001, Backend 8001 (not 3000/8000)
5. **Environment File**: Complete `.env` with all required variables

---

## Next Steps

1. ✅ Deployment working - username displays
2. ⚠️ Run initialization scripts for:
   - Document types
   - Document sources  
   - Roles
3. 🔄 Add Method #2 backup/restore (from `backup-restore-method2-work` branch)

---

## Backup Work Preservation

The Method #2 backup/restore work is preserved in:
- **Branch**: `backup-restore-method2-work`
- **Status**: Complete and ready to merge
- **Action**: Deploy on top of this working baseline after initializing data

---

**This configuration is confirmed working. Username displays correctly in top-right corner after login.**
