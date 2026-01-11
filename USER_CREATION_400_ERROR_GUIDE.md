# User Creation 400 Error - Debugging Guide

**Date:** 2026-01-07  
**Issue:** 400 Bad Request when creating users from frontend  
**Status:** ⚠️ VALIDATION ERROR (Not related to the 404 fix)

---

## 🔍 Issue Analysis

### Error
```
XHR POST http://localhost:3001/api/v1/users/
[HTTP/1.1 400 Bad Request 40ms]
```

### Root Cause
**This is a DIFFERENT issue from the 404 role assignment error we just fixed.**

The 400 error indicates a **validation error** - the API endpoint works fine, but the data being sent doesn't pass validation.

---

## ✅ What's Working

1. ✅ **API endpoint exists** - `/api/v1/users/` resolves correctly
2. ✅ **Permissions work** - Superuser can create users
3. ✅ **Endpoint tested successfully** - Created test user with status 201

### Test Proof
```python
# This worked fine:
POST /api/v1/users/
{
  "username": "testuser123",
  "email": "test@example.com", 
  "password": "TestPass123!",
  "password_confirm": "TestPass123!",
  "first_name": "Test",
  "last_name": "User"
}
# Result: 201 Created ✅
```

---

## ❌ What's Failing

The **frontend form data** is likely:
- Missing `password` or `password_confirm` fields
- Passwords don't match
- Password doesn't meet strength requirements
- Missing required fields like `username` or `email`

### Required Fields (UserCreateSerializer)
```python
REQUIRED:
- username
- email
- password
- password_confirm

OPTIONAL:
- first_name
- last_name
- employee_id
- phone_number
- department
- position
- role_id
```

### Validation Rules
1. ✅ `password` and `password_confirm` must be provided
2. ✅ Both passwords must match
3. ✅ Password must meet Django's strength requirements:
   - At least 8 characters
   - Not too common (e.g., "password123")
   - Not too similar to username
   - Not entirely numeric

---

## 🐛 How to Debug

### Step 1: Check Browser Console
Open browser Developer Tools (F12) and look for the actual request:

**Network Tab:**
1. Find the failed `POST /api/v1/users/` request
2. Click on it
3. Look at **Request Payload** - What data was actually sent?
4. Look at **Response** - What error message did the API return?

**Expected Response (400 error):**
```json
{
  "password": ["This field is required."],
  "password_confirm": ["This field is required."]
}
```
OR
```json
{
  "non_field_errors": ["Passwords don't match"]
}
```
OR
```json
{
  "password": ["This password is too short. It must contain at least 8 characters."]
}
```

### Step 2: Check Frontend Form Component
Look at the user creation form in frontend:

**File to check:** `frontend/src/components/admin/UserManagement.tsx` or similar

**What to verify:**
1. Are all required fields in the form?
2. Is the form sending `password_confirm` field?
3. Are field names matching exactly (`password_confirm` not `confirmPassword`)?

### Step 3: Check API Service Call
**File:** `frontend/src/services/api.ts`

The `createUser` method expects:
```typescript
{
  username: string;
  email: string;
  password: string;
  password_confirm: string;  // ← Must be snake_case, not camelCase
  // ... optional fields
}
```

---

## 🔧 Common Issues & Fixes

### Issue 1: Password Confirm Field Missing
**Problem:** Form doesn't have a "Confirm Password" field

**Fix:** Add password confirmation input to the form
```tsx
<input
  type="password"
  name="password_confirm"
  placeholder="Confirm Password"
  required
/>
```

### Issue 2: Field Name Mismatch
**Problem:** Frontend sends `confirmPassword` but API expects `password_confirm`

**Fix:** Ensure field names use snake_case:
```typescript
// ❌ Wrong
{ confirmPassword: '...' }

// ✅ Correct
{ password_confirm: '...' }
```

### Issue 3: Weak Password
**Problem:** Password doesn't meet strength requirements

**Fix:** Add password requirements to form:
- Minimum 8 characters
- Mix of letters and numbers
- Not too common

### Issue 4: Empty Required Fields
**Problem:** Form allows submission with empty required fields

**Fix:** Add frontend validation:
```typescript
if (!username || !email || !password || !password_confirm) {
  alert('All fields are required');
  return;
}

if (password !== password_confirm) {
  alert('Passwords do not match');
  return;
}
```

---

## 📋 Quick Debugging Checklist

Run through this in the browser:

1. [ ] Open Developer Tools (F12)
2. [ ] Go to Network tab
3. [ ] Try to create a user
4. [ ] Find the failed POST request
5. [ ] Check **Request Payload** - Copy it
6. [ ] Check **Response** - Copy the error message
7. [ ] Compare with required fields above

**Then share:**
- What data was sent (Request Payload)
- What error was returned (Response)

---

## 🧪 Test API Directly

To verify the API works, test with curl:

```bash
# Login first to get session cookie
curl -X POST http://localhost:8001/api/v1/session/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin_password"}' \
  -c cookies.txt

# Then create user
curl -X POST http://localhost:8001/api/v1/users/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "username": "newuser",
    "email": "new@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "New",
    "last_name": "User"
  }'
```

If this works (201 response), the issue is in the frontend form.

---

## 🎯 Expected Behavior

**Successful User Creation:**
```
POST /api/v1/users/
Status: 201 Created
Response:
{
  "id": 5,
  "username": "newuser",
  "email": "new@example.com",
  "first_name": "New",
  "last_name": "User",
  ...
}
```

**Failed Validation:**
```
POST /api/v1/users/
Status: 400 Bad Request
Response:
{
  "password": ["This field is required."],
  "password_confirm": ["This field is required."]
}
```

---

## 📝 Summary

**The 400 error is NOT related to the 404 role assignment fix we just made.**

This is a **validation error** caused by:
- Missing required fields in the request
- Password validation failure
- Field name mismatch

**To fix:**
1. Check browser Developer Tools to see actual error
2. Verify frontend form has all required fields
3. Ensure field names match API expectations (snake_case)
4. Validate passwords match and meet requirements

---

**Status:** 🟡 **NEEDS FRONTEND DEBUGGING**  
**Related to 404 fix:** ❌ **NO** - This is a separate issue  
**Next Step:** Check browser console for actual validation error message

**Last Updated:** 2026-01-07 17:29 SGT
