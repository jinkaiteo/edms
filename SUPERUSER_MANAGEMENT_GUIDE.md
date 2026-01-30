# Superuser Management Guide

**Created:** 2026-01-30  
**Version:** 1.0  
**Critical Security Feature**

---

## 🔒 Overview

This guide covers the superuser protection and management features implemented to prevent accidentally locking yourself out of admin functions.

### Critical Protection Implemented

✅ **Cannot deactivate the last superuser**  
✅ **Cannot revoke superuser status from the last superuser**  
✅ **Only superusers can grant/revoke superuser status**  
✅ **Audit logging for all superuser status changes**

---

## 🚨 The Problem This Solves

**Before:** Users could deactivate the only superuser account, causing a complete lockout from admin functions. Recovery required direct database access or creating a new superuser via Django shell.

**After:** System prevents deactivation/revocation of the last superuser and provides safe methods to transfer superuser privileges.

---

## 📋 How It Works

### Protection Rules

1. **Last Superuser Protection**
   - System counts active superusers before allowing deactivation
   - If only 1 active superuser exists, deactivation is blocked
   - Clear error message explains the situation

2. **Privilege Escalation Control**
   - Only existing superusers can grant superuser status
   - Only existing superusers can revoke superuser status
   - Regular users cannot modify their own superuser status

3. **Safe Transfer Process**
   - Grant superuser to new user FIRST
   - Then deactivate/revoke from old user
   - System ensures at least 1 superuser always exists

---

## 🎯 Usage Examples

### Method 1: Using Django Shell (Terminal Access)

#### Grant Superuser Status

```bash
# SSH to server
ssh user@production-server

# Access Django shell
docker compose exec backend python manage.py shell

# Python commands:
from apps.users.models import User

# Find the user
user = User.objects.get(username='new_admin')

# Grant superuser status
user.is_superuser = True
user.is_staff = True
user.save()

print(f"✅ {user.username} is now a superuser")
```

#### Revoke Superuser Status (Safe)

```python
from apps.users.models import User

# Check current superusers
superusers = User.objects.filter(is_superuser=True, is_active=True)
print(f"Current superusers: {[u.username for u in superusers]}")

# Only proceed if there are 2+ superusers
if superusers.count() > 1:
    user = User.objects.get(username='old_admin')
    user.is_superuser = False
    user.save()
    print(f"✅ Superuser status revoked from {user.username}")
else:
    print("❌ Cannot revoke - only 1 superuser exists!")
```

---

### Method 2: Using API Endpoints (Frontend/Postman)

#### Grant Superuser Status

**Endpoint:** `POST /api/v1/users/{user_id}/grant_superuser/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "reason": "Promoting Alice to superuser for admin duties"
}
```

**Response (Success):**
```json
{
  "message": "Superuser status granted to alice",
  "username": "alice",
  "is_superuser": true,
  "granted_by": "admin"
}
```

**Response (Forbidden - Not a superuser):**
```json
{
  "error": "Only superusers can grant superuser status"
}
```

**Response (Already Superuser):**
```json
{
  "message": "alice is already a superuser"
}
```

---

#### Revoke Superuser Status

**Endpoint:** `POST /api/v1/users/{user_id}/revoke_superuser/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "reason": "Bob is leaving the admin team"
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

**Response (Last Superuser - Blocked):**
```json
{
  "error": "Cannot revoke superuser status from the last superuser",
  "detail": "Please grant superuser status to another user first."
}
```

---

### Method 3: Using cURL (Command Line)

#### Grant Superuser

```bash
# Get your auth token first
TOKEN="your_jwt_token_here"
USER_ID="uuid-of-user-to-promote"

curl -X POST \
  "http://your-domain/api/v1/users/${USER_ID}/grant_superuser/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Promoting to admin team"
  }'
```

#### Revoke Superuser

```bash
TOKEN="your_jwt_token_here"
USER_ID="uuid-of-user-to-demote"

curl -X POST \
  "http://your-domain/api/v1/users/${USER_ID}/revoke_superuser/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Leaving admin team"
  }'
```

---

## 📝 Safe Transfer Procedure

### Scenario: Replacing the Current Superuser

**Goal:** Transfer superuser privileges from `admin` to `alice`

**Steps:**

1. **Login as current superuser** (`admin`)

2. **Grant superuser to new user**
   ```bash
   POST /api/v1/users/{alice_id}/grant_superuser/
   {
     "reason": "Transferring admin duties to Alice"
   }
   ```

3. **Verify new superuser** (optional but recommended)
   - Logout
   - Login as `alice`
   - Check that admin functions are accessible

4. **Revoke from old user**
   ```bash
   POST /api/v1/users/{admin_id}/revoke_superuser/
   {
     "reason": "Transferred duties to Alice"
   }
   ```

5. **Or deactivate old user**
   ```bash
   PATCH /api/v1/users/{admin_id}/
   {
     "is_active": false
   }
   ```

**Result:** ✅ Alice is now the superuser, admin is revoked/deactivated

---

## 🛡️ Protection Scenarios

### Scenario 1: Trying to Deactivate Last Superuser

**Action:**
```json
PATCH /api/v1/users/{admin_id}/
{
  "is_active": false
}
```

**Response:**
```json
{
  "error": "Cannot deactivate the last superuser. This would lock you out of admin functions.",
  "detail": "Please assign superuser status to another user before deactivating this account."
}
```

**Status Code:** `403 Forbidden`

---

### Scenario 2: Regular User Trying to Grant Superuser

**Action:** User `bob` (not a superuser) tries to grant superuser to himself

```json
POST /api/v1/users/{bob_id}/grant_superuser/
{
  "reason": "I want admin access"
}
```

**Response:**
```json
{
  "error": "Only superusers can grant superuser status"
}
```

**Status Code:** `403 Forbidden`

---

### Scenario 3: Safe Multi-Admin Setup

**Goal:** Create 3 superusers for redundancy

```bash
# As current superuser, grant to 2 more users
POST /api/v1/users/{alice_id}/grant_superuser/
POST /api/v1/users/{bob_id}/grant_superuser/

# Result: 3 active superusers (original + alice + bob)
```

**Benefit:** Now any one of them can be safely deactivated/revoked

---

## 🔍 Verification Commands

### Check Current Superusers (Django Shell)

```python
from apps.users.models import User

# All superusers
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    status = "ACTIVE" if user.is_active else "INACTIVE"
    print(f"{user.username} - {status}")

# Active superusers only
active = User.objects.filter(is_superuser=True, is_active=True).count()
print(f"\nTotal active superusers: {active}")
```

### Check Via API

**Endpoint:** `GET /api/v1/users/?is_superuser=true&is_active=true`

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid-1",
      "username": "admin",
      "is_superuser": true,
      "is_active": true
    },
    {
      "id": "uuid-2", 
      "username": "alice",
      "is_superuser": true,
      "is_active": true
    }
  ]
}
```

---

## 🚑 Recovery Procedures

### Emergency: All Superusers Deactivated (Should Never Happen Now!)

**If it somehow happens:**

1. **Access server via SSH**
   ```bash
   ssh user@production-server
   cd /path/to/edms
   ```

2. **Activate a superuser via Django shell**
   ```bash
   docker compose exec backend python manage.py shell
   ```

   ```python
   from apps.users.models import User
   
   # Find the deactivated superuser
   admin = User.objects.get(username='admin')
   
   # Reactivate
   admin.is_active = True
   admin.save()
   
   print(f"✅ {admin.username} reactivated")
   ```

3. **Or create a new superuser**
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

---

## 📊 Audit Trail

All superuser status changes are logged:

**Log Format:**
```
AUDIT: Superuser status granted to alice by admin. Reason: Promoting to admin team
AUDIT: Superuser status revoked from bob by admin. Reason: Leaving admin team
```

**Where to Find Logs:**
```bash
# Backend logs
docker compose logs backend | grep "AUDIT: Superuser"

# Or real-time monitoring
docker compose logs -f backend | grep "AUDIT"
```

---

## ⚠️ Important Notes

### DO's ✅

- ✅ Always have at least 2 active superusers for redundancy
- ✅ Grant superuser to replacement BEFORE revoking from original
- ✅ Document the reason when granting/revoking superuser status
- ✅ Verify new superuser can login before revoking old one
- ✅ Regularly audit who has superuser status

### DON'Ts ❌

- ❌ Don't try to deactivate the only superuser (system blocks this now)
- ❌ Don't grant superuser status unnecessarily
- ❌ Don't forget to revoke superuser when someone leaves
- ❌ Don't modify superuser status directly in database (use API/shell)
- ❌ Don't share superuser credentials

---

## 🧪 Testing the Protection

### Test 1: Try to Deactivate Last Superuser

```bash
# Setup: Ensure only 1 active superuser exists
# Try to deactivate via API
curl -X PATCH \
  "http://localhost:8000/api/v1/users/{admin_id}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"is_active": false}'

# Expected: 403 Forbidden with error message
```

### Test 2: Safe Transfer

```bash
# 1. Grant to new user (should succeed)
curl -X POST \
  "http://localhost:8000/api/v1/users/{alice_id}/grant_superuser/" \
  -H "Authorization: Bearer ${TOKEN}"

# Expected: 200 OK

# 2. Now deactivate original (should succeed - 2 superusers exist)
curl -X PATCH \
  "http://localhost:8000/api/v1/users/{admin_id}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"is_active": false}'

# Expected: 200 OK
```

---

## 🔧 Technical Implementation

### Code Location
- **File:** `backend/apps/users/views.py`
- **Class:** `UserViewSet`
- **Methods:**
  - `update()` - Overridden with protection
  - `partial_update()` - Overridden with protection
  - `grant_superuser()` - New action
  - `revoke_superuser()` - New action

### Protection Logic
```python
# Check if last active superuser
active_superusers = User.objects.filter(
    is_superuser=True,
    is_active=True
).exclude(id=instance.id).count()

if active_superusers == 0:
    return Response({'error': '...'}, status=403)
```

---

## 📞 Support

**If you need help:**
- Review this guide thoroughly
- Check audit logs for recent changes
- Use Django shell verification commands
- Contact system administrator if locked out

**For feature requests:**
- Create GitHub issue with "[Superuser Management]" prefix

---

## 📚 Related Documentation

- **User Management API:** See API documentation
- **Security Best Practices:** See SECURITY.md
- **Audit Trail Guide:** See audit logging documentation

---

**Remember:** The system is designed to prevent lockouts. If you encounter a "cannot deactivate" error, it's protecting you from losing admin access! ✅

---

*Last Updated: 2026-01-30*  
*Version: 1.0*  
*Status: Production Ready*
