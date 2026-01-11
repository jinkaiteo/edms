# Document Creation Fix - Status Report

**Date:** 2026-01-11  
**Iterations Used:** 20  
**Primary Objective:** Fix "User ID not found in current user data" error  

---

## ✅ COMPLETED: Authentication API Fix

### Problem Solved
Frontend was unable to get user `id` field from authentication endpoints, causing document creation to fail with:
```
❌ Failed to get current user: Error: User ID not found in current user data
    handleCreateDocument DocumentCreateModal.tsx:526
```

### Solution Applied
Added missing `id` field to **ALL** authentication API responses across 3 files:

**Files Modified:**
1. ✅ `backend/apps/api/v1/auth_views.py`
   - `CurrentUserView.get()` - Added `id`, `is_active`
   - `LoginView.post()` - Added `id`, `is_active`

2. ✅ `backend/apps/api/v1/auth_views_simple.py`
   - `SimpleLoginView.post()` - Added `id`, `full_name`
   - `SimpleCurrentUserView.get()` - Added `id`, `full_name`, `is_active`

3. ✅ `backend/apps/api/v1/session_auth_views.py`
   - `session_login()` - Added `uuid`, `first_name`, `last_name`, `full_name`
   - `current_user()` - Added `uuid`, `first_name`, `last_name`, `full_name`

### Verification
```bash
✅ Login successful as admin
✅ /auth/profile/ returns complete user object:
   {
     "user": {
       "id": 1,                    ← ADDED
       "uuid": "...",
       "username": "admin",
       "email": "admin@example.com",
       "full_name": "",            ← ADDED (where missing)
       "is_active": true,          ← ADDED (where missing)
       ...
     }
   }
```

**Status:** ✅ **FULLY WORKING** - Frontend can now get user ID

---

## ⚠️ SECONDARY ISSUE: Document Creation API

### Problem Discovered
Even with user ID available, document creation via API returns 500 error:
```
RelatedObjectDoesNotExist: Document has no document_type
Location: backend/apps/documents/models.py:404 in generate_document_number()
```

### Root Cause Analysis
The Document model's `save()` method calls `generate_document_number()` which tries to access `self.document_type`, but the ForeignKey hasn't been set yet.

### Fixes Attempted

#### Fix #1: Added PrimaryKeyRelatedField to Serializer ✅
```python
# backend/apps/documents/serializers.py
class DocumentCreateSerializer(serializers.ModelSerializer):
    # Explicitly accept IDs and convert to objects
    document_type = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.filter(is_active=True),
        required=True
    )
    document_source = serializers.PrimaryKeyRelatedField(
        queryset=DocumentSource.objects.filter(is_active=True),
        required=True
    )
```

**Result:** ✅ Serializer correctly loads PrimaryKeyRelatedField (verified in Django shell)

#### Fix #2: Enhanced Serializer create() Method ✅
```python
def create(self, validated_data):
    # Don't override author if already set
    if 'author' not in validated_data:
        validated_data['author'] = user
    
    # Ensure FK fields are set
    if 'document_type' not in validated_data:
        raise ValidationError({'document_type': 'This field is required'})
    if 'document_source' not in validated_data:
        raise ValidationError({'document_source': 'This field is required'})
    
    document = super().create(validated_data)
    ...
```

**Result:** ✅ Code changes applied but error persists

### What's Working
- ✅ Manual document creation via Django shell **WORKS**
- ✅ Serializer has correct PrimaryKeyRelatedField configuration
- ✅ Authentication returns user ID
- ❌ API document creation still fails with 500 error

### Remaining Issue
The serializer may not be properly processing FormData. When data comes as FormData (multipart/form-data), Django REST Framework might not be converting the string IDs to objects despite PrimaryKeyRelatedField.

---

## 📊 Overall Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Authentication `/auth/profile/`** | ✅ COMPLETE | Returns `id` field |
| **Authentication `/auth/token/`** | ✅ COMPLETE | Login returns `id` field |
| **Session auth endpoints** | ✅ COMPLETE | All fields added |
| **User endpoints consistency** | ✅ COMPLETE | All standardized |
| **DocumentCreateSerializer** | ✅ FIXED | PrimaryKeyRelatedField added |
| **Serializer create() method** | ✅ ENHANCED | Validation added |
| **Document creation via API** | ❌ FAILING | Still returns 500 error |
| **Frontend testing** | ⏸️ BLOCKED | Waiting for API fix |

---

## 🎯 Next Steps (Priority Order)

### Immediate (Critical Path)
1. **Debug why PrimaryKeyRelatedField isn't working with FormData**
   - Check if DRF parsers are correctly handling multipart/form-data
   - Verify that string IDs from FormData are being converted to integers
   - Add debug logging in serializer's `to_internal_value()` method

2. **Alternative: Override ViewSet.create()**
   - Manually convert document_type/document_source IDs to objects in view
   - This bypasses serializer field conversion issues with FormData

3. **Test FormData vs JSON**
   - Try sending JSON request body instead of FormData
   - If JSON works, issue is with FormData parsing

### Testing After Fix
4. Test document creation via API (curl/requests)
5. Test document creation via frontend UI
6. Verify author is correctly assigned
7. Verify document number is generated correctly

---

## 💡 Recommended Immediate Action

**Try the view-level fix:**

```python
# backend/apps/documents/views.py - DocumentViewSet
def create(self, request, *args, **kwargs):
    # Manual FK conversion for FormData
    if 'document_type' in request.data:
        try:
            doc_type_id = int(request.data['document_type'])
            request.data._mutable = True  # If QueryDict
            request.data['document_type'] = doc_type_id
            request.data._mutable = False
        except (ValueError, AttributeError):
            pass
    
    # Same for document_source
    if 'document_source' in request.data:
        try:
            doc_source_id = int(request.data['document_source'])
            request.data._mutable = True
            request.data['document_source'] = doc_source_id
            request.data._mutable = False
        except (ValueError, AttributeError):
            pass
    
    return super().create(request, *args, **kwargs)
```

This ensures IDs are integers before the serializer processes them.

---

## 📝 Commit Summary (When Complete)

```
fix: Add missing 'id' field to authentication API responses

COMPLETED:
- ✅ Added 'id' field to CurrentUserView (/auth/profile/)
- ✅ Added 'id' field to LoginView (/auth/token/)
- ✅ Added 'id' field to SimpleLoginView and SimpleCurrentUserView
- ✅ Added 'id', 'uuid', 'full_name' to session auth endpoints
- ✅ Standardized all authentication responses with complete user data
- ✅ Added PrimaryKeyRelatedField to DocumentCreateSerializer
- ✅ Enhanced serializer create() method with FK validation

IN PROGRESS:
- ⚠️ Document creation API still returns 500 error
- ⚠️ Investigating FormData parsing with PrimaryKeyRelatedField

IMPACT:
- Frontend can now successfully retrieve user ID
- Authentication responses are consistent across all endpoints
- Document creation via frontend will work once API issue resolved

Related Issues: Document creation error (line 526 in DocumentCreateModal.tsx)
Commit d2da690: Added author field requirement
```

---

## 🔍 Investigation Notes

The error occurs in the Document model's `save()` method when it tries to generate a document number. The `generate_document_number()` method accesses `self.document_type`, but this FK isn't set yet.

**Hypothesis:** The serializer's `super().create(validated_data)` is calling `Document.objects.create(**validated_data)`, but at some point between receiving the data and calling `model.save()`, the `document_type` FK is being lost or not properly set.

**Evidence:**
- Manual creation works: `Document(document_type=obj, ...).save()` ✅
- Serializer has correct field types: PrimaryKeyRelatedField ✅  
- API request fails: POST with FormData ❌

**Likely cause:** FormData string-to-integer conversion not happening before serializer validation.

