# Frontend API Issue Analysis

## Problem

After deploying the correct production containers (docker-compose.prod.yml), the frontend is still calling wrong API endpoints:

**Frontend calls**: `/api/v1/documents/documents/?filter=library`
**Correct endpoint**: `/api/v1/documents/?filter=library`

**Result**: HTTP 404 errors, documents don't load, username not displayed

---

## Root Cause

The frontend source code has hardcoded API paths that include duplicate endpoint names:

```typescript
// In DocumentList.tsx or similar
const response = await api.get('/documents/documents/?filter=library');
// This becomes: /api/v1/documents/documents/?filter=library (WRONG)
```

The API service class in `frontend/src/services/api.ts` uses `baseURL = /api/v1`, and then the component adds `/documents/documents/` which creates the duplicate.

---

## Why Frontend Rebuild Didn't Fix It

The frontend was rebuilt with `REACT_APP_API_URL=/api/v1` correctly set, BUT:
- The source code itself has the wrong paths
- The JavaScript bundle still contains `/documents/documents/`
- Environment variables only set the base URL, not fix the paths in code

---

## Solution Options

### Option 1: Fix Frontend Source Code (Proper Fix)
Edit the frontend source files to use correct paths:

```typescript
// Change from:
api.get('/documents/documents/?filter=library')

// To:
api.get('/documents/?filter=library')
```

**Files to check**:
- `frontend/src/components/DocumentList.tsx`
- `frontend/src/services/api.ts`
- Any component calling document endpoints

### Option 2: Add URL Rewrite in Backend (Workaround)
Add URL rewriting in Django or Nginx to redirect `/api/v1/documents/documents/` → `/api/v1/documents/`

**Django urls.py**:
```python
path('api/v1/documents/documents/', redirect_to_documents_view),
```

### Option 3: Check Git History for Working Frontend
The deployment at commit 6ace8e5 was working. Check if that commit has different frontend code with correct API paths.

---

## Verification Needed

1. Check frontend source code for API endpoint paths
2. Compare with git commit 6ace8e5 to see what changed
3. Verify if the production build should have different API service configuration

---

## Current Status

- ✅ Backend API working correctly (`/api/v1/documents/` returns 200)
- ✅ Production containers running correctly
- ✅ Database initialized
- ❌ Frontend calling wrong endpoints
- ❌ Username not displayed (likely because profile API also fails)

---

## Next Steps

1. Check git commit 6ace8e5 for working frontend code
2. Compare API service configuration
3. Either fix frontend source code or add backend URL rewrite
4. Rebuild frontend with corrected code
