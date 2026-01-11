# Staging Deployment - Ready to Deploy

**Date:** 2026-01-07 17:23 SGT  
**Server:** 172.28.1.148 (edms-staging)  
**Issue Fixed:** User role assignment 404 error  
**Commit:** `696fbac` - fix: Remove duplicate UserViewSet registration

---

## 🎯 Summary

**Fixed the 404 error preventing role assignment to users on staging server.**

### Problem
```
XHR POST http://172.28.1.148:3001/api/v1/users/4/assign_role/
[HTTP/1.1 404 Not Found]
```

### Root Cause
Duplicate `UserViewSet` registration:
- `/api/v1/users/` - Basic ViewSet without action methods → 404
- `/api/v1/users/users/` - Full ViewSet with actions → Would work but wrong URL

### Solution
1. Removed duplicate registration in `backend/edms/urls.py`
2. Imported full `UserViewSet` from `apps.users.views` in `apps/api/v1/views.py`
3. Now `/api/v1/users/{id}/assign_role/` works correctly

---

## ✅ Local Testing Results

All user endpoints now working:
```
✅ /api/v1/users/                     -> user-list
✅ /api/v1/users/1/                   -> user-detail  
✅ /api/v1/users/1/assign_role/       -> user-assign-role
✅ /api/v1/users/1/remove_role/       -> user-remove-role
✅ /api/v1/users/1/reset_password/    -> user-reset-password
✅ /api/v1/users/users/...            -> 404 (correctly removed)
```

---

## 📦 Changes Committed

**Commit:** `696fbac`  
**Branch:** `develop`  
**Files Changed:** 2

1. **backend/edms/urls.py**
   - Commented out duplicate users path registration
   - Added explanation comments

2. **backend/apps/api/v1/views.py**
   - Imported full UserViewSet from apps.users.views
   - Replaced basic ViewSet definition with full version

---

## 🚀 Deployment Instructions for Staging

### Step 1: SSH to Staging Server
```bash
ssh user@172.28.1.148
cd /path/to/edms/project
```

### Step 2: Pull Latest Changes
```bash
git pull origin develop
# Should show commit 696fbac
```

### Step 3: Rebuild Backend Container
```bash
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
```

### Step 4: Verify Services Running
```bash
docker compose -f docker-compose.prod.yml ps
# All services should show "Up" and "healthy"

docker compose -f docker-compose.prod.yml logs backend --tail 50
# Should show "Booting worker" messages, no errors
```

### Step 5: Test API Endpoint
```bash
# Test that users endpoint is accessible
curl http://localhost:8001/api/v1/users/
# Should return authentication error (401), not 404

# Verify assign_role endpoint exists (will need auth)
curl -X POST http://localhost:8001/api/v1/users/1/assign_role/ \
  -H "Content-Type: application/json" \
  -d '{"role_id": 1}'
# Should return 401 (needs auth), not 404
```

### Step 6: Browser Testing
1. Open browser to http://172.28.1.148:3001
2. Login with admin credentials
3. Navigate to **Admin** → **User Management**
4. Click on any user
5. Try to **Assign Role**
6. Open browser console (F12)
7. **Verify:** No 404 errors, role assignment succeeds

---

## 🧪 Testing Checklist

After deployment, verify:

- [ ] Backend container is healthy
- [ ] Frontend loads without errors
- [ ] Can login to admin interface
- [ ] User list displays correctly
- [ ] User detail page loads
- [ ] **Role assignment works (main fix)**
- [ ] Role removal works
- [ ] Password reset works
- [ ] No 404 errors in browser console for `/api/v1/users/*` paths

---

## 🔍 Other Similar Issues Checked

Scanned for similar duplicate registrations:

✅ **Documents** - `/api/v1/documents/documents/` is detail endpoint, not duplicate  
✅ **Workflows** - Multiple includes are intentional (base + enhanced)  
✅ **Scheduler** - Different paths (`/scheduler/` vs `/admin/scheduler/`)

**No other duplicate registration issues found.**

---

## 📊 Impact Assessment

**Risk Level:** 🟢 **LOW**
- Only affects user management endpoints
- No database schema changes
- No data migration required
- Backward compatible
- 2 files changed, well-tested locally

**Downtime:** ~5 minutes (container rebuild)

**Benefits:**
- ✅ Role assignment works
- ✅ Role removal works  
- ✅ Password reset works
- ✅ Cleaner URL structure
- ✅ No duplicate registrations

**Rollback Plan:**
If issues occur, rollback is simple:
```bash
git revert 696fbac
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

---

## 📝 Post-Deployment Verification

After deployment, document the results:

1. **Functional Test Results**
   - Role assignment: ✅/❌
   - Role removal: ✅/❌
   - Password reset: ✅/❌

2. **Console Errors**
   - Any 404 errors: Yes/No
   - Any other errors: Description

3. **User Feedback**
   - Admin can manage users: Yes/No
   - Any issues reported: Description

---

## 📞 Support Information

**Developer:** Rovo Dev  
**Date Fixed:** 2026-01-07  
**Documentation:** 
- `API_ROUTING_ISSUE_EXPLANATION.md` - Detailed technical explanation
- `API_FIX_DEPLOYMENT_SUMMARY.md` - Implementation summary
- This file - Deployment guide

**Related Files:**
- `backend/edms/urls.py`
- `backend/apps/api/v1/views.py`
- `backend/apps/users/views.py`

---

## ✨ Summary

**Status:** 🟢 **READY FOR STAGING DEPLOYMENT**

The fix is:
- ✅ Implemented and tested locally
- ✅ Committed to develop branch
- ✅ Pushed to repository
- ✅ Documented comprehensively
- ✅ Low risk, high benefit
- ✅ Easy rollback if needed

**Expected Result:** User role assignment will work correctly on staging server without 404 errors.

---

**Next Steps:**
1. Deploy to staging using instructions above
2. Test thoroughly
3. Document results
4. If successful, prepare for production deployment

**Estimated Time:** 30 minutes (deploy + test)

---

**Last Updated:** 2026-01-07 17:23 SGT  
**Status:** Ready to deploy
