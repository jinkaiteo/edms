# "With Reinit" Restore - Auth Impact Analysis

**Date:** 2026-01-04  
**Question:** Will "Restore into clean system (reinit first)" break auth on staging?  
**Answer:** ⚠️ **TEMPORARILY YES - But Recoverable**

---

## 🎯 Executive Summary

### Short Answer

The "with_reinit" restore **WILL cause auth issues**, but they are **temporary and by design**:

1. ✅ **During API call:** Admin user making the API call stays authenticated
2. ⚠️ **After reinit, before restore:** All users deleted except new admin (auth breaks for everyone else)
3. ✅ **After restore completes:** All users restored from backup (auth works again)
4. ❌ **Problem:** Brief window where auth is broken (~5-30 seconds depending on backup size)

### The Critical Issue

**The API caller will be deleted mid-operation!**

```
Timeline:
1. Admin user calls API: /restore_from_file/ with_reinit=true
2. System reinit executes: Deletes ALL users, creates new admin with password "test123"
3. Original admin user is DELETED (with their password/session)
4. Restore runs: Original users restored from backup
5. Original admin restored with their OLD password

Result: API call completes, but the user who initiated it was deleted/recreated!
```

---

## 🔍 Detailed Flow Analysis

### What Happens Step-by-Step

```python
# Line ~340 in api_views.py

# STEP 1: API receives request
POST /api/v1/backup/restores/restore_from_file/
Authorization: Bearer <admin_token>
User: admin (authenticated)

# STEP 2: Permission check passes
if not request.user.is_staff:
    # Admin user passes this check ✅

# STEP 3: Execute system_reinit
call_command('system_reinit', confirm=True, skip_interactive=True)

# What system_reinit does (from system_reinit.py):
# Line 469-477
User.objects.exclude(username='admin').delete()  # Delete all other users
# Then creates NEW admin user (Line 342-355)
final_admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@edms.local',
        'is_staff': True,
        'is_superuser': True,
    }
)
final_admin.set_password('test123')  # NEW password!
final_admin.save()

# CRITICAL: The admin user who called the API was just recreated!
# Their old password is gone
# Their session may be invalid

# STEP 4: Restore continues
# Enhanced restore processor runs
# Original users restored from backup
# Original admin restored with their ORIGINAL password

# STEP 5: API returns response
return Response({'status': 'success'})
```

---

## ⚠️ Auth Issues That WILL Occur

### Issue 1: Session Invalidation

**Problem:**
```python
# Before reinit:
admin_user.id = 123
admin_user.password = 'hashed_original_password'
session.user_id = 123

# After reinit:
admin_user.id = 1 (NEW ID!)
admin_user.password = 'hashed_test123'
session.user_id = 123 (points to deleted user!)

# Session is now invalid!
```

**Impact:**
- API call may complete successfully
- But subsequent API calls with same token will fail
- Frontend will show "Not authenticated"
- User must login again

### Issue 2: Password Change

**Problem:**
```python
# Original admin password: "admin_secure_password_123"
# After reinit: "test123"
# After restore: "admin_secure_password_123" (restored)

# During the operation:
# - Old password doesn't work
# - "test123" works briefly
# - Then old password works again
```

**Impact:**
- Confusing for users
- Password changed temporarily
- Login credentials unstable during operation

### Issue 3: JWT Token Invalidation

**Problem:**
```python
# JWT token contains:
{
  "user_id": 123,
  "username": "admin",
  "exp": ...
}

# After reinit:
# user_id 123 doesn't exist anymore!
# New admin has user_id = 1

# Token validation fails
```

**Impact:**
- All JWT tokens become invalid
- All authenticated sessions dropped
- Users must re-authenticate

### Issue 4: All Other Users Deleted

**Problem:**
```python
# Before reinit:
User.objects.count() = 7  # admin, author01, reviewer01, etc.

# After reinit, before restore:
User.objects.count() = 1  # Only new admin

# All other users temporarily don't exist!
```

**Impact:**
- No one can login (except new admin with "test123")
- All foreign keys to users are broken temporarily
- Workflow assignments have no users
- Document ownership points to non-existent users

---

## 🚨 Specific Staging Server Risks

### Current Staging Setup

```
Server: lims@172.28.1.148:3001
Deployment: Production mode (nginx + docker)
Users: Multiple (admin, test users)
```

### What Will Break

1. **All Active Sessions**
   ```
   Before: 5 active user sessions
   After reinit: 0 active sessions (all invalidated)
   After restore: Users exist but must re-login
   ```

2. **Frontend Authentication**
   ```
   Frontend stores JWT token in localStorage/cookies
   Token becomes invalid when users are deleted
   Frontend shows "Not authenticated" errors
   Users see login screen
   ```

3. **API Integrations**
   ```
   Any external systems with saved tokens
   All tokens become invalid
   Must re-authenticate
   ```

4. **Background Jobs**
   ```
   Celery tasks running as users
   User references become invalid
   Tasks may fail
   ```

---

## 📊 Timeline of Auth State

```
Time: T+0s (API call starts)
├─ Admin user authenticated ✅
├─ JWT token valid ✅
└─ Session active ✅

Time: T+1s (reinit executes)
├─ All users deleted ❌
├─ New admin created (id=1, password="test123") ⚠️
├─ All JWT tokens invalid ❌
├─ All sessions invalid ❌
└─ Only new admin can login (with "test123") ⚠️

Time: T+2s-30s (restore running)
├─ Users being restored from backup...
├─ Original admin being recreated (with original password)
└─ Auth still broken during this window ❌

Time: T+30s+ (restore complete)
├─ All users restored ✅
├─ Original admin password restored ✅
├─ But all tokens still invalid ❌
├─ But all sessions still invalid ❌
└─ Users must re-authenticate to get new tokens 🔄
```

---

## 💡 Why This Happens

### Root Cause: User ID Changes

```python
# Before reinit:
admin.id = 5  # Auto-incremented from previous users

# After reinit:
admin.id = 1  # First user in fresh database

# Database sequence was reset!
```

Django doesn't preserve user IDs during recreation. The new admin gets a fresh ID.

### Foreign Key References

```python
# Document.author_id = 5 (original admin)
# After reinit: user_id 5 doesn't exist
# After restore: user_id 5 is restored

# But during the window, FK is broken!
```

---

## 🛡️ Mitigation Strategies

### Option 1: Accept Temporary Downtime

**Approach:**
```bash
# Schedule maintenance window
# Notify all users to logout
# Run with_reinit restore
# Wait for completion
# Notify users to login again
```

**Pros:**
- ✅ Simple
- ✅ Safe
- ✅ No unexpected behavior

**Cons:**
- ❌ Requires coordination
- ❌ Downtime required
- ❌ Manual process

### Option 2: Manual Process (Safer)

**Approach:**
```bash
# Step 1: Create backup
python manage.py create_backup --type database

# Step 2: Notify users, wait for them to logout
# Schedule maintenance window

# Step 3: Reinit
python manage.py system_reinit --confirm

# Step 4: Restore
python manage.py restore_backup --from-file backup.json.gz

# Step 5: Notify users they can login
```

**Pros:**
- ✅ Full control
- ✅ Can verify each step
- ✅ Can pause between steps
- ✅ CLI commands more stable

**Cons:**
- ❌ Multiple steps
- ❌ Manual coordination

### Option 3: Modify with_reinit Logic (Advanced)

**Approach:**
```python
# Enhance api_views.py to:
# 1. Store original admin password hash
# 2. After reinit, restore original admin immediately
# 3. Keep original admin ID intact

# This requires code changes to preserve the calling user
```

**Pros:**
- ✅ No session interruption for admin
- ✅ Seamless for API caller

**Cons:**
- ❌ Requires code modification
- ❌ Complex to implement
- ❌ May have edge cases

---

## 📋 Recommended Approach for Staging

### Best Practice: Manual Process

**For your staging server, I recommend:**

```bash
# 1. Test on local first (you have working local deployment)
docker exec edms_backend python manage.py create_backup \
  --type database --output /tmp/staging_test.json.gz

docker exec edms_backend python manage.py system_reinit --dry-run
# Review what will be deleted

docker exec edms_backend python manage.py system_reinit --confirm

docker exec edms_backend python manage.py restore_backup \
  --from-file /tmp/staging_test.json.gz

# Verify users restored
docker exec edms_backend python manage.py shell -c "
from apps.users.models import User
print(f'Users: {User.objects.count()}')
for u in User.objects.all():
    print(f'  - {u.username}')
"

# 2. After verifying locally, apply to staging
ssh lims@172.28.1.148
cd ~/edms-staging

# Create backup
docker exec edms_prod_backend python manage.py create_backup \
  --type database --output /tmp/staging_backup.json.gz

# Schedule downtime (5-10 minutes)
# Put up maintenance page or notify users

# Reinit
docker exec edms_prod_backend python manage.py system_reinit --confirm

# Restore
docker exec edms_prod_backend python manage.py restore_backup \
  --from-file /tmp/staging_backup.json.gz

# Verify
docker exec edms_prod_backend python manage.py shell -c "
from apps.users.models import User
from apps.documents.models import Document
print(f'Users: {User.objects.count()}')
print(f'Documents: {Document.objects.count()}')
"

# Users can login with their original passwords
```

---

## ⚠️ Critical Warnings

### DO NOT Use with_reinit API in Production Without:

1. **Scheduled Maintenance Window**
   - All users notified
   - All users logged out
   - No active sessions

2. **Understanding Auth Break**
   - All tokens invalidated
   - All sessions invalidated
   - Users must re-login

3. **Testing First**
   - Test on local environment
   - Test on staging with test users
   - Verify complete workflow

### The API Feature is Designed For:

- ✅ Automated testing environments
- ✅ CI/CD pipelines
- ✅ Development environments
- ❌ Production with active users

---

## 🧪 Test Plan Before Using on Staging

### Local Test First

```bash
# Terminal 1: Monitor logs
docker logs -f edms_backend

# Terminal 2: Create test backup
docker exec edms_backend python manage.py create_backup \
  --type database --output /tmp/test_backup.json.gz

# Terminal 3: Test with_reinit via API
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' | jq -r '.access')

curl -X POST http://localhost:8000/api/v1/backup/restores/restore_from_file/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "backup_file=@/tmp/test_backup.json.gz" \
  -F "restore_type=full" \
  -F "with_reinit=true" \
  -F "reinit_confirm=RESTORE CLEAN"

# Terminal 4: Try to use same token (will fail!)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/profile/
# Expected: 401 Unauthorized

# Terminal 5: Login again with original password
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}'
# Should work with restored password
```

### Staging Test Checklist

- [ ] Create backup of current staging state
- [ ] Schedule maintenance window (off-hours)
- [ ] Notify all users (if any active)
- [ ] Test with_reinit on local first
- [ ] Apply to staging during maintenance window
- [ ] Verify all users restored
- [ ] Verify all passwords work
- [ ] Test login for multiple users
- [ ] Verify document access
- [ ] Check audit trails

---

## ✅ Conclusion

### Will it Break Auth?

**YES** - Temporarily and by design:

1. ✅ **API call completes** (admin stays authenticated during call)
2. ❌ **All sessions invalidated** (including admin)
3. ❌ **All JWT tokens invalidated**
4. ⚠️ **Brief window** where only new admin can login with "test123"
5. ✅ **All users restored** from backup
6. ✅ **Original passwords restored**
7. 🔄 **Users must re-login** with their original credentials

### Recommended Approach

**For Staging Server:**
1. Use **manual CLI commands** (3 steps)
2. Schedule **maintenance window**
3. **Test on local first**
4. Have **backup plan** (keep backup file safe)

**Avoid:**
- ❌ Using with_reinit API with active users
- ❌ Running without maintenance window
- ❌ Testing directly on staging first time

### Safe Alternative

```bash
# Safest approach for staging:
# 1. Backup
# 2. Notify users (logout + wait)
# 3. Reinit (manual command)
# 4. Restore (manual command)
# 5. Notify users (login)

# Total time: 5-10 minutes
# Predictable: Yes
# Safe: Yes
# Tested: Can test on local first
```

---

**Status:** ⚠️ **WILL BREAK AUTH TEMPORARILY**  
**Severity:** 🟡 **MEDIUM** (Temporary, recoverable)  
**Mitigation:** ✅ **Manual process recommended**  
**Last Updated:** 2026-01-04
