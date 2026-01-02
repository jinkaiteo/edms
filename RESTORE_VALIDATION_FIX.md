# Restore Validation Fix

**Date:** 2026-01-02  
**Issue:** `'str' object has no attribute 'get'` error during restore  
**Status:** ✅ **FIXED**

---

## 🔍 **Issue**

**Error Message:**
```
Restore strict validation failed: 'str' object has no attribute 'get'
```

**User Action:**
- Uploaded backup file: `edms_migration_package_20260102_162557.tar.gz`
- Triggered restore operation
- Got 400 Bad Request error

**Root Cause:**
The restore validation code assumed `rec['fields']` is always a dictionary, but in some backup formats it can be a string, causing the `.get()` method to fail.

**Location:** `backend/apps/backup/api_views.py` lines 798-802

---

## 🔧 **Fix Applied**

### **Changed Lines:**

**Line 798:** Workflow state validation
```python
# Before
state_codes.add(rec['fields'].get('code'))

# After
fields = rec.get('fields', {})
if isinstance(fields, dict):
    state_codes.add(fields.get('code'))
```

**Line 801:** Document type validation
```python
# Before
type_codes = {rec.get('fields', {}).get('code') if isinstance(rec.get('fields', {}), dict) else None for rec in db_data if rec.get('model') == 'documents.documenttype'}

# After
type_codes = {rec.get('fields', {}).get('code') for rec in db_data if rec.get('model') == 'documents.documenttype' and isinstance(rec.get('fields', {}), dict)}
```

**Line 802:** Document source validation
```python
# Before
source_names = {rec.get('fields', {}).get('name') if isinstance(rec.get('fields', {}), dict) else None for rec in db_data if rec.get('model') == 'documents.documentsource'}

# After
source_names = {rec.get('fields', {}).get('name') for rec in db_data if rec.get('model') == 'documents.documentsource' and isinstance(rec.get('fields', {}), dict)}
```

---

## 📝 **Git Commits**

```bash
8445006 fix: Cleanup restore validation - remove None values from sets
adc3064 fix: Properly handle line 798 restore validation
```

**Pushed to:** `develop` branch ✅

---

## 🚀 **Deploy to Staging**

```bash
# 1. SSH to staging
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# 2. Pull the fix
git pull origin develop

# 3. Rebuild backend (REQUIRED for Python changes)
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# 4. Wait for backend
sleep 15

# 5. Verify
docker compose -f docker-compose.prod.yml ps backend
```

**After deployment, try your restore operation again!**

---

## ✅ **Expected Result**

After the fix, the restore validation should:
- ✅ Safely handle string fields
- ✅ Safely handle dict fields
- ✅ Not crash with AttributeError
- ✅ Proceed with restore or give meaningful error

**Note:** The restore might still fail for other reasons, but at least you'll get a proper error message instead of a Python exception!

---

**Status:** ✅ Fix committed and ready for deployment
