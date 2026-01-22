# Admin Filter Bypass - Analysis & Status

**Date:** January 22, 2026  
**File:** `backend/apps/documents/views.py`  
**Class:** `DocumentViewSet.get_queryset()` (lines 155-223)

---

## 🔍 **Current Implementation**

### **Admin Detection (Lines 161-167)**
```python
# ADMIN OVERRIDE: Superusers and system admins can see ALL documents
user = self.request.user
is_admin = (
    user.is_superuser or 
    user.groups.filter(name__in=['Document Admins', 'Senior Document Approvers']).exists() or
    user.user_roles.filter(role__name='Document Admin', is_active=True).exists()
)
```

**Admin users are identified as:**
- ✅ Superusers (`is_superuser=True`)
- ✅ Members of "Document Admins" group
- ✅ Members of "Senior Document Approvers" group
- ✅ Users with "Document Admin" role

---

## 📊 **Filter Bypass Status**

| View / Filter | Admin Bypass? | Current Behavior | Expected Behavior |
|---------------|---------------|------------------|-------------------|
| **Default (no filter)** | ✅ **YES** | Admin sees ALL documents | ✅ Correct |
| **Document Library** (`filter=library`) | ❌ **NO** | Admin sees only EFFECTIVE/APPROVED docs | ❌ Should see ALL |
| **My Tasks** (`filter=my_tasks`) | ❌ **NO** | Admin sees only their own tasks | ❌ Should see ALL tasks |
| **Obsolete Documents** (`filter=obsolete`) | ❌ **NO** | Admin sees only OBSOLETE docs | ✅ Correct (by design) |

---

## 🐛 **Issues Identified**

### **Issue 1: Document Library Filter (Lines 196-200)**

**Current Code:**
```python
elif filter_type == 'library':
    # Show ALL versions of active document families (frontend will group them)
    queryset = queryset.filter(
        status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE', 'SUPERSEDED']
    ).order_by('-updated_at')
```

**Problem:** No admin check - filters apply to everyone equally.

**Expected:** Admin should see ALL documents in library view, not just EFFECTIVE ones.

---

### **Issue 2: My Tasks Filter (Lines 172-181)**

**Current Code:**
```python
if filter_type == 'my_tasks':
    # Show documents where user has pending tasks
    from django.db import models
    queryset = queryset.filter(
        models.Q(author=self.request.user) |
        models.Q(reviewer=self.request.user) |
        models.Q(approver=self.request.user)
    ).filter(
        status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']
    ).order_by('-created_at')
```

**Problem:** Filters by `self.request.user` without checking if user is admin.

**Expected:** Admin should see ALL users' tasks for monitoring and oversight.

---

### **Issue 3: Obsolete Documents (Lines 191-194)**

**Current Code:**
```python
elif filter_type == 'obsolete':
    # Show ONLY latest version of obsolete document families
    queryset = self._get_latest_obsolete_documents()
```

**Status:** ✅ This is **correct by design** - obsolete documents are obsolete for everyone, including admins. The filter shows latest obsolete version of each family, which is appropriate.

---

## ✅ **What's Working**

### **Default View (Lines 202-221)**
```python
else:
    # Default: show all documents ordered by creation date
    if not is_admin:
        # Regular users: Filter based on role and document visibility rules
        queryset = queryset.filter(
            # Show if user is involved in the document
            Q(author=user) |
            Q(reviewer=user) |
            Q(approver=user) |
            # Show approved/effective documents to all authenticated users
            Q(status__in=[
                'APPROVED_AND_EFFECTIVE',
                'EFFECTIVE',
                'APPROVED_PENDING_EFFECTIVE',
                'SCHEDULED_FOR_OBSOLESCENCE',
                'SUPERSEDED'
            ])
        ).distinct()
    
    queryset = queryset.order_by('-created_at')
```

**✅ Correct:** Admin users skip the filter and see ALL documents.

---

## 🎯 **Recommended Fixes**

### **Fix 1: Document Library - Add Admin Bypass**

**Location:** Lines 196-200

**Current:**
```python
elif filter_type == 'library':
    queryset = queryset.filter(
        status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE', 'SUPERSEDED']
    ).order_by('-updated_at')
```

**Fixed:**
```python
elif filter_type == 'library':
    # Show ALL versions of active document families (frontend will group them)
    if not is_admin:
        # Regular users see only active/approved documents
        queryset = queryset.filter(
            status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE', 'SUPERSEDED']
        )
    # Admin users see ALL documents in library (no status filter)
    queryset = queryset.order_by('-updated_at')
```

---

### **Fix 2: My Tasks - Add Admin Bypass**

**Location:** Lines 172-181

**Current:**
```python
if filter_type == 'my_tasks':
    queryset = queryset.filter(
        models.Q(author=self.request.user) |
        models.Q(reviewer=self.request.user) |
        models.Q(approver=self.request.user)
    ).filter(
        status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']
    ).order_by('-created_at')
```

**Fixed:**
```python
if filter_type == 'my_tasks':
    # Show documents where user has pending tasks
    from django.db import models
    
    if is_admin:
        # Admin sees ALL tasks from ALL users for oversight
        queryset = queryset.filter(
            status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']
        )
    else:
        # Regular users see only their own tasks
        queryset = queryset.filter(
            models.Q(author=self.request.user) |
            models.Q(reviewer=self.request.user) |
            models.Q(approver=self.request.user)
        ).filter(
            status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']
        )
    
    queryset = queryset.order_by('-created_at')
```

---

## 📋 **Summary**

### **Current Status:**
- ✅ Admin bypass works for **default view**
- ❌ Admin bypass **missing** for **Document Library**
- ❌ Admin bypass **missing** for **My Tasks**
- ✅ Obsolete Documents filter is **correct by design**

### **Required Changes:**
1. Add `if not is_admin:` check before Document Library status filter
2. Add `if is_admin:` / `else:` branches for My Tasks filter
3. No change needed for Obsolete Documents filter

### **Impact:**
- **Admin users** will be able to see ALL documents in Document Library (for oversight)
- **Admin users** will be able to see ALL users' tasks in My Tasks (for monitoring)
- **Regular users** behavior remains unchanged

---

## 🧪 **Testing Plan**

### **Test 1: Admin in Document Library**
```bash
# Login as admin user
curl -X GET "http://localhost:8000/api/v1/documents/?filter=library" \
  -H "Authorization: Token <admin_token>"

# Expected: Should see ALL documents (DRAFT, PENDING_REVIEW, EFFECTIVE, etc.)
# Actual (before fix): Only sees EFFECTIVE/APPROVED documents
```

### **Test 2: Admin in My Tasks**
```bash
# Login as admin user
curl -X GET "http://localhost:8000/api/v1/documents/?filter=my_tasks" \
  -H "Authorization: Token <admin_token>"

# Expected: Should see ALL users' pending tasks
# Actual (before fix): Only sees admin's own tasks
```

### **Test 3: Regular User in Document Library**
```bash
# Login as author01
curl -X GET "http://localhost:8000/api/v1/documents/?filter=library" \
  -H "Authorization: Token <user_token>"

# Expected: Should see only EFFECTIVE/APPROVED documents
# Should remain unchanged after fix
```

### **Test 4: Regular User in My Tasks**
```bash
# Login as author01
curl -X GET "http://localhost:8000/api/v1/documents/?filter=my_tasks" \
  -H "Authorization: Token <user_token>"

# Expected: Should see only their own tasks
# Should remain unchanged after fix
```

---

## 📝 **Code Location Reference**

**File:** `backend/apps/documents/views.py`

**Method:** `DocumentViewSet.get_queryset()`

**Lines to modify:**
- Line 172-181: My Tasks filter
- Line 196-200: Document Library filter

**Admin check defined at:** Line 161-167

---

## ✅ **Verification Checklist**

After implementing fixes:

- [ ] Admin can see ALL documents in Document Library
- [ ] Admin can see ALL users' tasks in My Tasks
- [ ] Admin can see ALL documents in default view (already working)
- [ ] Regular users still see only their filtered documents in Library
- [ ] Regular users still see only their own tasks in My Tasks
- [ ] Regular users' default view behavior unchanged
- [ ] No unauthorized access for regular users
- [ ] Audit trail logs admin access appropriately

---

**Status:** ⏳ **Awaiting Implementation**  
**Priority:** Medium (Admin oversight feature)  
**Breaking Changes:** None - only adds admin capabilities
