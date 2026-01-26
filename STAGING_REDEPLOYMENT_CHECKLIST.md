# Staging Server Redeployment Checklist

## Issue Summary
Redis authentication error due to old .env file with password after env_file directive change.

## Pre-Deployment Steps

### 1. Connect to Staging Server
```bash
ssh lims@your-staging-server
cd /home/lims/edms
```

### 2. Backup Current State (Optional)
```bash
# Backup current .env
cp .env .env.backup.before-fix

# Check what's in current .env
grep REDIS .env
```

### 3. Pull Latest Code
```bash
git pull origin main
```

Expected commits:
- 80e2c99: Backend health check fix (start_period: 60s)
- 0a721cf: BuildKit enabled
- Plus diagnostic tools

---

## Deployment Steps

### Option 1: Clean Deployment (Recommended)

```bash
# Remove old .env file
rm .env

# Stop containers
docker compose -f docker-compose.prod.yml down

# Run deployment script (creates fresh .env)
./deploy-interactive.sh
```

**What to expect:**
- Script creates new .env with correct Redis URLs (no password)
- Backend starts successfully after ~60 seconds
- All containers become healthy

### Option 2: Fix Existing .env

```bash
# Use the fix script
./fix_redis_auth.sh

# Follow prompts to remove password from Redis URLs
```

---

## During Deployment

### Configuration Prompts

**Server Configuration:**
- Backend port: 8001 ✓
- Frontend port: 3001 ✓
- Database name: edms_prod_db ✓

**Email Configuration:**
- Configure if needed
- Test email will work correctly now (env_file fix applied)

**Expected Timeline:**
```
0-5 min:   Docker image build
5-6 min:   Container startup
6-7 min:   Database migrations + initialization
7-10 min:  Roles, users, placeholders setup
10-12 min: Complete

Total: 10-12 minutes
```

---

## Verification Steps

### 1. Check Container Status
```bash
docker compose -f docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                        STATUS
edms_prod_backend          Up (healthy)
edms_prod_db               Up (healthy)
edms_prod_redis            Up (healthy)
edms_prod_celery_worker    Up
edms_prod_celery_beat      Up
edms_prod_frontend         Up
```

### 2. Verify Redis Configuration
```bash
# Check .env has no password
grep REDIS .env

# Should show:
# REDIS_URL=redis://redis:6379/1
# CELERY_BROKER_URL=redis://redis:6379/0
# REDIS_PASSWORD=
```

### 3. Test Backend Health
```bash
curl http://localhost:8001/health/
# Should return: {"status":"healthy"}
```

### 4. Check Backend Logs (No Redis Errors)
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50 | grep -i redis
# Should show NO authentication errors
```

### 5. Test Frontend
```bash
curl http://localhost:3001/
# Should return HTML
```

### 6. Test Admin Login
```
http://your-server:8001/admin/
Login with admin credentials
```

### 7. Test User Login
```
http://your-server:3001/
Login with: author01 / Test@12345
```

---

## If Issues Occur

### Issue: Still getting Redis authentication error

**Diagnosis:**
```bash
./diagnose_backend_health.sh
```

**Fix:**
```bash
# Check .env again
cat .env | grep REDIS

# If still has password, manually fix:
sed -i 's|redis://:[^@]*@redis:|redis://redis:|g' .env

# Restart containers
docker compose down
docker compose up -d
```

### Issue: Backend still unhealthy after 60s

**Diagnosis:**
```bash
docker compose logs backend --tail=100
```

**Common causes:**
- Migrations failing → Check database connection
- SECRET_KEY missing → Check .env file
- Port conflict → Check `lsof -i :8001`

### Issue: Containers won't start

**Reset:**
```bash
docker compose down -v  # Remove volumes
docker compose up -d
```

---

## Success Criteria

✅ All containers showing "healthy" or "Up"
✅ No Redis authentication errors in logs
✅ Backend health endpoint returns 200
✅ Frontend accessible
✅ Can login to admin panel
✅ Can login as test user

---

## Post-Deployment

### 1. Test Document Creation
```
Login as author01
Create a test document
Verify workflow works
```

### 2. Monitor Logs
```bash
docker compose logs -f
# Watch for any errors
```

### 3. Verify Email (If Configured)
```
Check if test email was received
Try document workflow to trigger notification
```

---

## Rollback (If Needed)

If deployment fails completely:

```bash
# Restore old .env
cp .env.backup.before-fix .env

# Restart with old config
docker compose down
docker compose up -d
```

Then investigate the issue before retrying.

---

## Expected Result

After successful deployment:
- ✅ Backend responding in 5-10 seconds (not 120s timeout)
- ✅ No authentication errors
- ✅ All optimizations working (BuildKit, no collectstatic, email config)
- ✅ System fully functional

---

## Support

If you encounter issues:
1. Run: `./diagnose_backend_health.sh`
2. Check: `docker compose logs backend`
3. Share logs for analysis

---

**Date:** 2026-01-26
**Expected duration:** 10-15 minutes
**Risk:** Low (can rollback to old .env if needed)
