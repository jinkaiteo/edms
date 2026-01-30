# Complete Deployment Guide - Superuser Management Feature

**Date:** 2026-01-30  
**Version:** v1.3.1 (Hotfix + UI Enhancement)  
**Commits:** 0db0987, d0a4d30, 7a0a703  
**Type:** Security Fix + Feature Enhancement  

---

## 🎯 What's Being Deployed

### 1. Backend Protection (CRITICAL) ✅
- **Commit:** 0db0987
- Prevents deactivating the last superuser
- Prevents revoking superuser from the last superuser
- New API endpoints for grant/revoke superuser

### 2. Frontend UI (Enhancement) ✅
- **Commit:** 7a0a703
- Visual superuser status indicator
- Grant/Revoke buttons in role management modal
- User-friendly error messages and confirmations

---

## 🚀 Quick Deployment Commands

### On Production Server:

```bash
# 1. Navigate to project
cd /path/to/edms

# 2. Backup current state
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Backup commit: $CURRENT_COMMIT" > /tmp/rollback_info.txt

# 3. Pull latest changes
git fetch origin main
git checkout main
git pull origin main

# 4. Restart services
docker compose restart backend
docker compose build frontend --no-cache
docker compose up -d frontend

# 5. Verify
docker compose ps
curl http://your-domain/api/v1/health/
```

### Expected Duration: 8-12 minutes
- Backend restart: 30 seconds
- Frontend rebuild: 5-8 minutes
- Frontend startup: 2-3 minutes
- Testing: 2-3 minutes

---

## 📋 Detailed Step-by-Step

### Step 1: Pre-Deployment Backup (CRITICAL)

```bash
# Backup database and media files
cd /path/to/edms
./scripts/backup-hybrid.sh

# Record current commit for rollback
git rev-parse HEAD > /tmp/current_commit.txt
echo "Backup commit: $(cat /tmp/current_commit.txt)"
```

### Step 2: Pull Latest Code

```bash
# Fetch and checkout
git fetch origin main
git checkout main
git pull origin main

# Verify new commits
git log --oneline -5
# Should show:
# 7a0a703 feat: Add frontend UI for superuser management
# d0a4d30 docs: Add hotfix deployment guide for superuser protection
# 0db0987 fix: Add critical superuser protection to prevent admin lockout
```

### Step 3: Deploy Backend (Quick - No Build Required)

```bash
# Backend has code-only changes, just restart
docker compose restart backend

# Wait for healthy status
sleep 10
docker compose ps backend

# Check logs for errors
docker compose logs backend --tail=50 | grep -i error
```

### Step 4: Deploy Frontend (Requires Rebuild)

```bash
# Frontend has component changes, needs rebuild
docker compose build frontend --no-cache

# Restart with new image
docker compose up -d frontend

# Check status
docker compose ps frontend
```

### Step 5: Health Verification

```bash
# API health check
curl http://your-domain/api/v1/health/

# Frontend loads
curl -I http://your-domain/ | head -1

# Backend logs
docker compose logs backend --tail=20

# Frontend logs
docker compose logs frontend --tail=20
```

---

## ✅ Post-Deployment Testing

### Test 1: Backend Protection Works

**Via Browser:**
1. Login as superuser
2. Go to User Management
3. Click "Manage Roles" on your own account
4. Click "Revoke Superuser" (red button)
5. **Expected:** Error message: "Cannot revoke superuser status from the last superuser"

**Via API:**
```bash
# Get your user ID
USER_ID="your-superuser-id"
TOKEN="your-jwt-token"

# Try to revoke (should fail if last superuser)
curl -X POST \
  "http://your-domain/api/v1/users/${USER_ID}/revoke_superuser/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"reason": "Testing protection"}'

# Expected response:
# {
#   "error": "Cannot revoke superuser status from the last superuser",
#   "detail": "Please grant superuser status to another user first."
# }
```

### Test 2: Grant Superuser UI Works

**Steps:**
1. Login as superuser
2. Go to User Management
3. Find a regular user (e.g., author01)
4. Click "Manage Roles" on that user
5. Check "Superuser Status" section at top of modal
6. Should show: "Regular User" with gray indicator
7. Click "Grant Superuser" (purple button)
8. Enter reason in prompt
9. **Expected:** Success message, user now shows "⭐ Superuser"

### Test 3: Revoke Superuser UI Works

**Steps:**
1. After Test 2, you should now have 2 superusers
2. Click "Manage Roles" on the newly created superuser
3. Click "Revoke Superuser" (red button)
4. Confirm in dialog
5. Enter reason in prompt
6. **Expected:** Success message, user returns to "Regular User"

### Test 4: Visual Indicators

**Check UI Elements:**
- ✅ Superuser status section appears at top of role modal
- ✅ Gradient purple/indigo background for superuser section
- ✅ Status indicator dot (purple for superuser, gray for regular)
- ✅ ⭐ emoji appears for superusers
- ✅ Descriptive text explains privileges
- ✅ Buttons are purple (grant) and red (revoke)
- ✅ Buttons disable during operations

---

## 🎨 UI Preview

### Before (No Superuser Management):
```
+------------------------------------------+
| Manage Roles: alice                      |
+------------------------------------------+
| Current Roles                            |
| [Role list...]                           |
|                                          |
| Available Roles                          |
| [Role list...]                           |
|                                          |
|                           [Close]        |
+------------------------------------------+
```

### After (With Superuser Management):
```
+------------------------------------------+
| Manage Roles: alice                      |
+------------------------------------------+
| Superuser Status                         |
| +--------------------------------------+ |
| | ● Regular User                       | |
| | Standard user permissions            | |
| |                  [Grant Superuser]   | |
| +--------------------------------------+ |
|                                          |
| Current Roles                            |
| [Role list...]                           |
|                                          |
| Available Roles                          |
| [Role list...]                           |
|                                          |
|                           [Close]        |
+------------------------------------------+
```

---

## 🔄 Rollback Plan

If issues arise:

### Quick Rollback (Backend Only)

```bash
# Get previous commit
ROLLBACK_COMMIT=$(cat /tmp/current_commit.txt)

# Rollback
git checkout $ROLLBACK_COMMIT
docker compose restart backend
```

### Full Rollback (Backend + Frontend)

```bash
# Get previous commit
ROLLBACK_COMMIT=$(cat /tmp/current_commit.txt)

# Rollback
git checkout $ROLLBACK_COMMIT
docker compose build backend frontend
docker compose up -d
```

---

## 📊 Change Summary

### Backend Changes
- **File:** `backend/apps/users/views.py`
- **Lines Added:** 155
- **New Methods:**
  - `update()` - Override with protection
  - `partial_update()` - Override with protection
  - `grant_superuser()` - New action
  - `revoke_superuser()` - New action

### Frontend Changes
- **File:** `frontend/src/components/users/UserManagement.tsx`
- **Lines Added:** 117
- **New Functions:**
  - `handleGrantSuperuser()` - API call to grant
  - `handleRevokeSuperuser()` - API call to revoke
- **UI Additions:**
  - Superuser status section in role modal
  - Visual indicators and buttons

### Documentation
- `SUPERUSER_MANAGEMENT_GUIDE.md` (532 lines)
- `HOTFIX_DEPLOYMENT_SUPERUSER_PROTECTION.md` (415 lines)
- `DEPLOY_HOTFIX_NOW.sh` (automated deployment script)

---

## 🎯 Recommended Post-Deployment Actions

### 1. Create Backup Superuser (Highly Recommended)

Having 2+ superusers provides redundancy:

```bash
# Via Django shell
docker compose exec backend python manage.py shell
```

```python
from apps.users.models import User

# Choose a trusted user
backup_admin = User.objects.get(username='alice')
backup_admin.is_superuser = True
backup_admin.is_staff = True
backup_admin.save()

print(f"✅ {backup_admin.username} is now a superuser")
```

**Or via UI:**
1. Login as superuser
2. Go to User Management
3. Click "Manage Roles" on trusted user
4. Click "Grant Superuser"
5. Enter reason: "Creating backup superuser for redundancy"

### 2. Document Superusers

```bash
# Create a record of who has superuser access
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
print('Current Superusers:')
for u in User.objects.filter(is_superuser=True, is_active=True):
    print(f'  - {u.username} ({u.email})')
" > /tmp/superusers_$(date +%Y%m%d).txt

cat /tmp/superusers_$(date +%Y%m%d).txt
```

### 3. Test Protection with Team

Have your team try to:
- Deactivate the last superuser (should fail)
- Grant superuser to themselves (should fail if not superuser)
- Revoke from last superuser (should fail)

All should show appropriate error messages.

---

## 📞 Support & Troubleshooting

### Issue: Frontend Not Showing Superuser Section

**Cause:** Browser cache showing old JavaScript

**Solution:**
```bash
# Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
# Or hard refresh in incognito mode
```

### Issue: "Only superusers can grant superuser status"

**Cause:** Logged-in user is not a superuser

**Solution:**
```bash
# Check your user status
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
user = User.objects.get(username='your_username')
print(f'Is superuser: {user.is_superuser}')
"

# If false, grant superuser via shell
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
user = User.objects.get(username='your_username')
user.is_superuser = True
user.is_staff = True
user.save()
print('✅ Superuser granted')
"
```

### Issue: Button Doesn't Respond

**Check:**
1. Browser console for errors (F12)
2. Network tab for API call failures
3. Backend logs: `docker compose logs backend --tail=50`

---

## 📚 Complete Documentation

- **User Guide:** `SUPERUSER_MANAGEMENT_GUIDE.md`
- **Deployment Guide:** `HOTFIX_DEPLOYMENT_SUPERUSER_PROTECTION.md`
- **Deployment Script:** `DEPLOY_HOTFIX_NOW.sh`
- **This Guide:** `DEPLOY_COMPLETE_SUPERUSER_FEATURE.md`

---

## ✅ Deployment Checklist

**Pre-Deployment:**
- [x] Code committed and pushed to main
- [x] Documentation created
- [ ] Production backup completed
- [ ] Team notified of deployment

**Deployment:**
- [ ] Pull latest code
- [ ] Restart backend (30 seconds)
- [ ] Rebuild frontend (5-8 minutes)
- [ ] Verify health checks pass

**Post-Deployment:**
- [ ] Test backend protection (try to revoke last superuser)
- [ ] Test grant superuser UI
- [ ] Test revoke superuser UI
- [ ] Verify visual indicators display correctly
- [ ] Create backup superuser for redundancy
- [ ] Document current superusers
- [ ] Notify team deployment complete

---

## 🎉 Summary

**What You're Getting:**
- ✅ Protection against admin lockout (backend)
- ✅ Beautiful UI for superuser management (frontend)
- ✅ Comprehensive documentation
- ✅ Automated deployment script
- ✅ Easy rollback if needed

**Total Development Time:** ~4 hours  
**Total Deployment Time:** ~10-15 minutes  
**Risk Level:** Low (backward compatible, protection-only)  

---

**Ready to deploy?** Follow the Quick Deployment Commands at the top of this guide!

---

*Prepared by: Rovo Dev AI Assistant*  
*Last Updated: 2026-01-30*  
*Status: Production Ready*
