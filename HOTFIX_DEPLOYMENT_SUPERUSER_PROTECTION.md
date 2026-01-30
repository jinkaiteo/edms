# Hotfix Deployment - Superuser Protection

**Date:** 2026-01-30  
**Version:** Hotfix for v1.3.0  
**Commit:** 0db0987  
**Severity:** CRITICAL  
**Type:** Security Fix  

---

## 🚨 Critical Issue Fixed

**Problem:** Users could deactivate the only superuser account, causing complete admin lockout.

**Solution:** Added protection to prevent deactivating/revoking the last superuser.

---

## 📋 Changes Summary

### Backend Changes Only ✅
- **Modified:** `backend/apps/users/views.py` (+155 lines)
  - Override `update()` method with superuser protection
  - Override `partial_update()` method with superuser protection
  - New action: `grant_superuser()` - Grant superuser to users
  - New action: `revoke_superuser()` - Revoke superuser from users

- **Added:** `SUPERUSER_MANAGEMENT_GUIDE.md` (comprehensive documentation)

### No Database Changes ❌
- No migrations required
- No schema changes
- No data migrations

### No Frontend Changes ❌
- No npm packages added
- No React component changes
- Frontend rebuild NOT required

---

## 🚀 Quick Deployment (Production)

### Estimated Time: 3-5 minutes
### Downtime: 30 seconds

```bash
# SSH to production server
ssh user@production-server

# Navigate to project
cd /path/to/edms

# Pull latest changes
git fetch origin main
git checkout main
git pull origin main

# Restart backend only (frontend unchanged)
docker compose restart backend

# Verify
docker compose ps backend
curl http://your-domain/api/v1/health/
```

---

## ✅ Post-Deployment Testing

### Test 1: Verify Protection Works

**Step 1:** Check current superusers
```bash
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
print('Active superusers:', User.objects.filter(is_superuser=True, is_active=True).count())
for u in User.objects.filter(is_superuser=True):
    print(f'  - {u.username} (active: {u.is_active})')
"
```

**Step 2:** Try to deactivate (should be blocked if only 1 exists)
- Login to frontend as superuser
- Go to User Management
- Try to deactivate your own account
- **Expected:** Error message: "Cannot deactivate the last superuser"

### Test 2: Grant Superuser (New Feature)

```bash
# Get user ID
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
user = User.objects.get(username='author01')  # Replace with actual username
print(f'User ID: {user.uuid}')
"

# Test API endpoint
curl -X POST \
  "http://your-domain/api/v1/users/{user_id}/grant_superuser/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Testing superuser grant feature"}'

# Expected: {"message": "Superuser status granted to author01", ...}
```

### Test 3: Safe Multi-Admin Setup

```bash
# Grant superuser to 2nd user
POST /api/v1/users/{user2_id}/grant_superuser/

# Now you should be able to deactivate the first superuser
PATCH /api/v1/users/{admin_id}/ {"is_active": false}

# Expected: SUCCESS (because 2+ superusers exist)
```

---

## 🛡️ What This Protects Against

### Before This Fix:
1. Admin deactivates their own account (last superuser)
2. System has no active superusers
3. **LOCKOUT** - No one can access admin functions
4. Recovery requires database access or Django shell

### After This Fix:
1. Admin tries to deactivate their account (last superuser)
2. System checks: "Is this the last active superuser?"
3. **BLOCKED** - Error message guides user to grant superuser to someone else first
4. No lockout possible

---

## 📊 Protection Rules

| Action | Last Superuser | 2+ Superusers | Result |
|--------|---------------|---------------|--------|
| Deactivate superuser | ❌ Blocked | ✅ Allowed | Protected |
| Revoke superuser | ❌ Blocked | ✅ Allowed | Protected |
| Grant superuser | ✅ Allowed | ✅ Allowed | Available |
| Modify non-superuser | ✅ Allowed | ✅ Allowed | Unchanged |

---

## 🔧 New API Endpoints

### Grant Superuser Status

**Endpoint:** `POST /api/v1/users/{user_id}/grant_superuser/`

**Permission:** Only superusers can call this

**Request:**
```json
{
  "reason": "Promoting Alice to admin team"
}
```

**Response:**
```json
{
  "message": "Superuser status granted to alice",
  "username": "alice",
  "is_superuser": true,
  "granted_by": "admin"
}
```

### Revoke Superuser Status

**Endpoint:** `POST /api/v1/users/{user_id}/revoke_superuser/`

**Permission:** Only superusers can call this

**Protection:** Cannot revoke from last superuser

**Request:**
```json
{
  "reason": "Bob leaving admin team"
}
```

**Response (Success):**
```json
{
  "message": "Superuser status revoked from bob",
  "username": "bob",
  "is_superuser": false,
  "revoked_by": "admin"
}
```

**Response (Blocked - Last Superuser):**
```json
{
  "error": "Cannot revoke superuser status from the last superuser",
  "detail": "Please grant superuser status to another user first."
}
```

---

## 📝 How to Use After Deployment

### Scenario: Make Alice a Superuser

**Option 1: Using Django Shell (Recommended for First Setup)**

```bash
docker compose exec backend python manage.py shell
```

```python
from apps.users.models import User

alice = User.objects.get(username='alice')
alice.is_superuser = True
alice.is_staff = True
alice.save()

print(f"✅ {alice.username} is now a superuser")
```

**Option 2: Using API (After You Have Superuser)**

```bash
curl -X POST \
  "http://your-domain/api/v1/users/{alice_id}/grant_superuser/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"reason": "Adding Alice to admin team"}'
```

### Scenario: Safe Admin Transition

**Goal:** Replace admin with alice

```bash
# 1. Grant superuser to alice (as admin)
POST /api/v1/users/{alice_id}/grant_superuser/

# 2. Verify alice can login and access admin functions
# (Login as alice, test admin features)

# 3. Revoke from admin (now safe - 2 superusers exist)
POST /api/v1/users/{admin_id}/revoke_superuser/

# OR deactivate admin
PATCH /api/v1/users/{admin_id}/ {"is_active": false}
```

---

## 🚑 Rollback Plan

If issues arise (unlikely - backward compatible):

```bash
# Rollback to previous commit
git checkout b9f4834
docker compose restart backend
```

**Note:** This is a safety-only change. Rollback only needed if unexpected errors occur.

---

## 📊 Impact Analysis

### Risk Level: **LOW** ✅
- No database changes
- No frontend changes
- Backward compatible
- Only adds protection, doesn't change existing behavior for normal operations

### Breaking Changes: **NONE** ✅
- Existing API calls work unchanged
- Only blocks unsafe operations (which should not have been possible)

### User Impact: **POSITIVE** ✅
- Prevents accidental lockouts
- Adds new management features
- Clear error messages guide safe transitions

---

## 🔍 Verification Commands

### Check Superuser Count
```bash
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
print(User.objects.filter(is_superuser=True, is_active=True).count())
"
```

### List All Superusers
```bash
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
for user in User.objects.filter(is_superuser=True):
    status = 'ACTIVE' if user.is_active else 'INACTIVE'
    print(f'{user.username}: {status}')
"
```

### Check Audit Logs
```bash
docker compose logs backend | grep "AUDIT: Superuser"
```

---

## 📚 Complete Documentation

See `SUPERUSER_MANAGEMENT_GUIDE.md` for:
- Detailed usage examples
- All API endpoints
- Safe transfer procedures
- Recovery procedures
- Testing scenarios
- Security best practices

---

## ✅ Deployment Checklist

**Pre-Deployment:**
- [x] Code reviewed and tested locally
- [x] Documentation created
- [x] Commit pushed to GitHub
- [ ] Production backup completed

**Deployment:**
- [ ] SSH to production server
- [ ] Pull latest code
- [ ] Restart backend container
- [ ] Verify health check passes

**Post-Deployment:**
- [ ] Test protection (try to deactivate last superuser)
- [ ] Verify existing features work
- [ ] Check backend logs for errors
- [ ] Document current superusers
- [ ] Consider granting superuser to 2nd user for redundancy

---

## 🎯 Recommended Post-Deployment Actions

### 1. Create Redundant Superuser (Highly Recommended)

Having 2+ superusers provides redundancy:

```bash
docker compose exec backend python manage.py shell
```

```python
from apps.users.models import User

# Find a trusted user
backup_admin = User.objects.get(username='alice')

# Grant superuser
backup_admin.is_superuser = True
backup_admin.is_staff = True
backup_admin.save()

print(f"✅ Redundant superuser created: {backup_admin.username}")
```

### 2. Audit Current Superusers

```bash
# Document who currently has superuser access
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
print('=== Current Superusers ===')
for u in User.objects.filter(is_superuser=True):
    print(f'{u.username} - Active: {u.is_active}')
"
```

### 3. Test the Protection

Try to deactivate the last superuser to verify protection works.

---

## 📞 Support

**If issues arise:**
1. Check backend logs: `docker compose logs backend --tail=100`
2. Verify backend is running: `docker compose ps backend`
3. Review error messages (they guide you to correct actions)
4. Consult `SUPERUSER_MANAGEMENT_GUIDE.md`

**Emergency contact:** System Administrator

---

**This hotfix addresses a critical security vulnerability. Deploy as soon as possible.** 🚨

---

*Prepared by: Rovo Dev AI Assistant*  
*Last Updated: 2026-01-30*  
*Status: Ready for Production Deployment*
