# API Path Fix Analysis

## Issue

Frontend in commit 4f90489 has incorrect API endpoints:
- Calls: `/documents/documents/`
- Should call: `/documents/`

This causes 404 errors when creating documents or fetching document lists.

---

## Root Cause

The frontend source code has hardcoded paths with double endpoint names:
```typescript
// In DocumentCreateModal.tsx or similar
api.post('/documents/documents/', formData)
```

Combined with baseURL `/api/v1`, this becomes:
```
/api/v1/documents/documents/  ❌ Wrong
```

Should be:
```
/api/v1/documents/  ✅ Correct
```

---

## Investigation

Checked git history for commit 230b470 (mentioned earlier):
- **Result**: Commit 230b470 does NOT exist in this repository
- This was likely from a different context or misidentification

---

## Available Options

### Option 1: Fix Frontend Source Code (Proper Solution)

**Edit affected files**:
Find and replace `/documents/documents/` → `/documents/` in:
- `frontend/src/services/api.ts`
- `frontend/src/components/DocumentCreateModal.tsx`
- Any other components calling document APIs

**Steps**:
1. Fix source code on staging server
2. Rebuild frontend container
3. Restart frontend
4. Test

**Time**: 5-10 minutes

---

### Option 2: Add Backend URL Rewrite (Quick Workaround)

**Add to backend/edms/urls.py**:
```python
from django.urls import re_path
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect duplicate paths
    re_path(r'^api/v1/documents/documents/', 
            lambda request: redirect_to_single_documents(request)),
    ...
]
```

**Steps**:
1. Edit urls.py
2. Restart backend
3. Frontend works without rebuild

**Time**: 2-3 minutes

---

### Option 3: Deploy Latest Code from Repository

Check if there's a later commit in the repository (beyond 6ace8e5) that has:
- Working application
- Fixed API paths
- All features functional

**Risk**: May introduce new issues or changes

---

## Recommendation

**Use Option 1** (Fix frontend source code):
- Proper fix that addresses root cause
- Clean solution
- Future-proof
- Only requires frontend rebuild (not full deployment)

**Steps**:
1. Find and fix `/documents/documents/` in frontend source
2. Rebuild frontend
3. Test document creation
4. Commit changes

This ensures the system works correctly going forward.

---

## Current Workaround

For immediate testing, Option 2 (backend redirect) allows testing document creation while we fix the frontend properly.
