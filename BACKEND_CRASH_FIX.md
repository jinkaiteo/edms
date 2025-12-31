# Backend Crash Fix - Middleware Class Name Error

## ✅ Issue Fixed!

**Problem:** Backend container was crashing on startup with:
```
ImportError: Module "apps.audit.middleware_api_fix" does not define a "ComprehensiveAuditMiddleware" attribute/class
```

**Root Cause:** Incorrect middleware class name in `production.py`
- Production settings referenced: `ComprehensiveAuditMiddleware`
- Actual class name in file: `EnhancedAuditMiddleware`

**Fix Applied:** Changed line 18 in `backend/edms/settings/production.py`
```python
# Before (wrong):
'apps.audit.middleware_api_fix.ComprehensiveAuditMiddleware',

# After (correct):
'apps.audit.middleware_api_fix.EnhancedAuditMiddleware',
```

---

## 🚀 Deploy the Fix

On your staging server:

```bash
# Pull the fix
cd /home/lims/edms-staging
git pull origin develop

# Restart backend container
docker compose -f docker-compose.prod.yml restart backend

# Watch logs to see it start successfully
docker compose -f docker-compose.prod.yml logs backend -f

# Wait for: "Booting worker" or "Listening at" messages
```

Once backend starts successfully:
1. ✅ Backend will be accessible on port 8001
2. ✅ HAProxy will route API calls correctly
3. ✅ Login should work at http://172.28.1.148

---

## 🔍 Verify Backend is Running

```bash
# Check container status (should show "healthy")
docker compose -f docker-compose.prod.yml ps backend

# Test backend directly
curl http://localhost:8001/health
# Should return 200

# Test through HAProxy
curl http://localhost/health
# Should return 200

# Try login in browser
# http://172.28.1.148
```

---

## 📋 Complete Recovery Steps

```bash
# 1. Pull fix
git pull origin develop

# 2. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 3. Wait 30 seconds for startup
sleep 30

# 4. Verify backend is healthy
docker compose -f docker-compose.prod.yml ps backend

# 5. Test login in browser
# Open: http://172.28.1.148
```

---

**This should fix the 503 error and allow login to work!** 🎉
