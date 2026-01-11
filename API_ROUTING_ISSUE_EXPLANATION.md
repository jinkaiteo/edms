# API Routing Issue - User Role Assignment 404 Error

**Date:** 2026-01-07  
**Issue:** Unable to assign roles to users via frontend (404 Not Found)  
**Staging Server:** 172.28.1.148

---

## 🔴 **Problem Statement**

When attempting to assign roles to users from the admin interface, the frontend receives a 404 error:

```
XHR POST http://172.28.1.148:3001/api/v1/users/4/assign_role/
[HTTP/1.1 404 Not Found 22ms]
```

---

## 🔍 **Root Cause Analysis**

### **The Issue: Duplicate User ViewSet Registration**

The application has **TWO separate registrations** of the `UserViewSet`, creating conflicting URL patterns:

#### **Registration #1: In `apps/api/v1/urls.py` (Line 68)**
```python
router.register(r'users', UserViewSet, basename='user')
```
**Creates URLs:**
- `/api/v1/users/` → ✅ Works
- `/api/v1/users/1/` → ✅ Works  
- `/api/v1/users/1/assign_role/` → ❌ **DOES NOT EXIST**

#### **Registration #2: In `backend/edms/urls.py` (Line 33)**
```python
path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),
```
Which includes `apps/users/urls.py` that registers:
```python
router.register(r'users', UserViewSet)
```
**Creates URLs:**
- `/api/v1/users/users/` → ✅ Works
- `/api/v1/users/users/1/` → ✅ Works
- `/api/v1/users/users/1/assign_role/` → ✅ **WORKS!**

---

## 🧪 **URL Resolution Test Results**

```
✅ /api/v1/users/               → Resolves to UserViewSet (Registration #1)
❌ /api/v1/users/1/assign_role/ → 404 Not Found (Registration #1 doesn't have actions)
✅ /api/v1/users/users/         → Resolves to UserViewSet (Registration #2)  
✅ /api/v1/users/users/1/assign_role/ → Works! (Registration #2 has full ViewSet with actions)
```

---

## 📊 **Why This Happens**

### **URL Pattern Priority**

Django resolves URLs **in order**. When a request comes for `/api/v1/users/1/assign_role/`:

1. **First Match:** `/api/v1/users/` pattern from Registration #1 matches
2. Django looks for `assign_role` action in that ViewSet
3. **Problem:** Registration #1's ViewSet instance doesn't have the action methods properly registered
4. Returns 404

The correct endpoint `/api/v1/users/users/1/assign_role/` works because Registration #2 has the full ViewSet with all action decorators properly registered.

---

## 🔧 **The Core Problem**

Looking at `backend/edms/urls.py` line 27-33:

```python
# Authentication endpoints
# Note: We don't include apps.users.urls here to avoid conflicts with apps.api.v1.urls
# apps.api.v1.urls contains all auth endpoints including JWT token endpoints
path('', include('apps.api.v1.urls')),  # ← Registers users at /api/v1/users/

# User management (direct access to users viewset only)
path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),  # ← Registers users at /api/v1/users/users/
```

**Result:** Two different `UserViewSet` instances registered at different paths.

---

## 📝 **Evidence from Backend Logs**

```
WARNING 2026-01-07 09:02:25,420 log Not Found: /api/v1/users/1/assign_role/
172.20.0.1 - - [07/Jan/2026:09:02:25 +0000] "POST /api/v1/users/1/assign_role/ HTTP/1.1" 404 179
```

The backend confirms the URL doesn't exist.

---

## 💡 **Solutions**

### **Option 1: Fix Frontend API Calls (Quick Fix)**

Update frontend to use the correct path:

**File:** `frontend/src/services/api.ts`

```typescript
// Current (WRONG):
async assignRole(userId: number, roleId: number, reason?: string): Promise<any> {
  const response = await this.client.post(`/users/${userId}/assign_role/`, {
    role_id: roleId,
    reason
  });
  return response.data;
}

// Fixed (CORRECT):
async assignRole(userId: number, roleId: number, reason?: string): Promise<any> {
  const response = await this.client.post(`/users/users/${userId}/assign_role/`, {
    role_id: roleId,
    reason
  });
  return response.data;
}
```

**Pros:** 
- Quick fix
- No backend changes needed
- Can deploy immediately

**Cons:**
- Unintuitive URL path (`/users/users/`)
- Doesn't fix root cause
- Other endpoints may have same issue

---

### **Option 2: Fix Backend URL Configuration (Proper Fix)**

Remove duplicate registration from `backend/edms/urls.py`:

```python
# BEFORE:
api_urlpatterns = [
    path('', include('apps.api.v1.urls')),  # Has users registration
    path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),  # Duplicate!
]

# AFTER:
api_urlpatterns = [
    path('', include('apps.api.v1.urls')),  # Keep this (has all viewsets)
    # Remove duplicate users registration
]
```

**Then ensure** `apps/api/v1/urls.py` imports the FULL `UserViewSet` from `apps.users.views`:

```python
# In apps/api/v1/urls.py
from apps.users.views import UserViewSet  # Import actual ViewSet with actions

# Then register it:
router.register(r'users', UserViewSet, basename='user')
```

**Pros:**
- Proper fix
- Clean URL structure
- Fixes all user-related endpoints
- Prevents future confusion

**Cons:**
- Requires backend rebuild
- Need to test all user endpoints
- May affect other code expecting `/users/users/` path

---

### **Option 3: Remove Registration #1, Keep Registration #2 (Alternative)**

Remove `UserViewSet` from `apps/api/v1/urls.py` router and keep only the one in `apps/users/urls.py`:

```python
# In apps/api/v1/urls.py - REMOVE this line:
# router.register(r'users', UserViewSet, basename='user')

# Keep the include in edms/urls.py:
path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),
```

Then update frontend to use `/users/users/` paths everywhere.

**Pros:**
- Single source of truth
- Full ViewSet functionality guaranteed
- Clear namespace

**Cons:**
- Awkward `/users/users/` URL pattern
- More frontend files to update
- Breaking change for existing API consumers

---

## 🎯 **Recommended Solution**

**Implement Option 2** - Remove duplicate registration and ensure proper import:

### **Step-by-step:**

1. **Verify the import** in `backend/apps/api/v1/urls.py`:
   ```python
   from apps.users.views import UserViewSet, RoleViewSet, UserRoleViewSet
   ```

2. **Check if ViewSet has proper actions:**
   ```python
   # In apps/users/views.py - Should have:
   @action(detail=True, methods=['post'])
   def assign_role(self, request, pk=None):
       # ... implementation
   ```

3. **Remove duplicate registration** from `backend/edms/urls.py`:
   ```python
   # Comment out or remove:
   # path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),
   ```

4. **Rebuild backend container:**
   ```bash
   docker compose -f docker-compose.prod.yml build backend
   docker compose -f docker-compose.prod.yml up -d backend
   ```

5. **Test endpoints:**
   ```bash
   # Should work:
   curl http://localhost:8001/api/v1/users/
   curl http://localhost:8001/api/v1/users/1/
   curl -X POST http://localhost:8001/api/v1/users/1/assign_role/ -H "Content-Type: application/json" -d '{"role_id":1}'
   
   # Should return 404:
   curl http://localhost:8001/api/v1/users/users/
   ```

6. **Verify frontend works** without any changes needed.

---

## 🔍 **How to Verify Which ViewSet Registration is Used**

```python
# Django shell
from django.urls import get_resolver

resolver = get_resolver()
match = resolver.resolve('/api/v1/users/1/assign_role/')
print(f"View: {match.view_name}")
print(f"Func: {match.func}")
```

If it shows `users-api:user-assign-role`, it's using Registration #2 (the `/users/users/` path).
If it shows `user-assign-role`, it's using Registration #1 (the `/users/` path).

---

## 📚 **Related Issues**

This same pattern might affect other endpoints:

- `POST /api/v1/users/{id}/remove_role/`
- `POST /api/v1/users/{id}/reset_password/`
- Any custom actions on UserViewSet

Check frontend service files for any endpoints calling `/users/{id}/` with custom actions.

---

## 📝 **Documentation Updates Needed**

After fix:
1. Update API documentation with correct endpoint paths
2. Update frontend service layer documentation
3. Add URL routing tests to prevent regression
4. Document the single UserViewSet registration pattern

---

## ✅ **Testing Checklist**

After implementing fix:

- [ ] User list retrieval works
- [ ] User detail retrieval works  
- [ ] User creation works
- [ ] User update works
- [ ] Role assignment works
- [ ] Role removal works
- [ ] Password reset works
- [ ] Frontend admin user management functional
- [ ] No 404 errors in browser console
- [ ] All user-related E2E tests pass

---

## 🚀 **Deployment Impact**

**Backend Changes:**
- Requires backend container rebuild
- No database migrations needed
- No data loss
- Downtime: ~2-3 minutes for container rebuild

**Frontend Changes:**
- **Option 1:** Frontend needs updates if using quick fix
- **Option 2:** No frontend changes needed (recommended)

**Testing Required:**
- User management functionality
- Role assignment/removal
- User creation/editing
- Admin interface user operations

---

## 📞 **Summary**

The 404 error occurs because:
1. Frontend calls `/api/v1/users/4/assign_role/`
2. This URL doesn't exist due to ViewSet registration at `/api/v1/users/` not having actions
3. The working URL is `/api/v1/users/users/4/assign_role/` from the second registration

**Best fix:** Remove duplicate registration, ensure single UserViewSet at `/api/v1/users/` with all actions.

**Impact:** Low risk, high benefit - fixes not just this issue but prevents future similar issues.

**Time to fix:** 30 minutes (code change + rebuild + testing)

---

**Status:** 🔴 **IDENTIFIED - AWAITING FIX**  
**Priority:** 🔥 **HIGH** - Blocks admin functionality  
**Last Updated:** 2026-01-07 17:03 SGT
