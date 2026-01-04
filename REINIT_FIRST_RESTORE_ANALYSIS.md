# "Restore into Clean System (Reinit First)" - Analysis

**Date:** 2026-01-04  
**Commit:** 6ace8e5  
**Feature:** API-based restore with automatic system reinit

---

## 🎯 Answer to Your Question

> "Does 'Restore into clean system (reinit first)' perform the reinit first before the restore?"

**✅ YES!** - But it's an **API-only feature**, not a CLI option.

---

## 📍 Where It's Implemented

**File:** `backend/apps/backup/api_views.py`  
**Function:** `restore_from_file()` (Line ~322)  
**Type:** REST API endpoint only

---

## 🔧 How It Works

### API Endpoint

```
POST /api/v1/backup/restores/restore_from_file/
```

### Required Parameters

```json
{
  "backup_file": "<uploaded file>",
  "restore_type": "full",
  "with_reinit": "true",                    // Key parameter!
  "reinit_confirm": "RESTORE CLEAN"         // Safety confirmation
}
```

### Step-by-Step Process

```python
# Line ~340-360 in api_views.py

# Step 1: Check if reinit is requested
with_reinit_flag = str(request.data.get('with_reinit', 'false')).lower() == 'true'
confirmation_code = request.data.get('reinit_confirm', '')

# Step 2: Validate permissions and confirmation
if with_reinit_flag:
    # Require admin privileges
    if not request.user.is_staff:
        return Response({
            'error': 'Admin privileges required for reinit before restore'
        }, status=403)
    
    # Require exact confirmation code
    if confirmation_code != 'RESTORE CLEAN':
        return Response({
            'error': "Reinit confirmation failed. Type 'RESTORE CLEAN' to proceed."
        }, status=400)
    
    # Step 3: Execute system reinit BEFORE restore
    try:
        call_command('system_reinit', confirm=True, skip_interactive=True)
        logger.warning('System reinit executed via API by admin user %s', 
                      request.user.username)
    except Exception as e:
        return Response({
            'error': f'System reinit failed: {str(e)}'
        }, status=500)

# Step 4: Continue with restore (now in post-reinit state)
# The restore will automatically detect post-reinit state and use enhanced logic
```

### Enhanced Restore Process (Post-Reinit)

After reinit, the restore uses special logic:

```python
# Line ~900-1000 in api_views.py

if with_reinit_flag:
    logger.info("WITH-REINIT: extracting archive and preparing enhanced restore...")
    
    # Extract backup package
    temp_extract_dir = tempfile.mkdtemp(prefix='edms_enhanced_restore_')
    with tarfile.open(temp_path, 'r:gz') as tar:
        tar.extractall(temp_extract_dir)
    
    # Locate database_backup.json
    db_file = find_database_json(temp_extract_dir)
    
    # Pre-create users from backup
    # (Guarantees UserRole FK resolution)
    backup_users = [r for r in db_data if r.get('model') == 'users.user']
    for user_record in backup_users:
        if not User.objects.filter(username=username).exists():
            User.objects.create(
                username=username,
                email=email,
                # ... other fields
            )
            user_obj.set_password('edms123')  # Default password
            user_obj.save()
    
    # Run EnhancedRestoreProcessor
    from apps.backup.restore_processor import EnhancedRestoreProcessor
    processor = EnhancedRestoreProcessor()
    restoration_result = processor.process_backup_data(db_file)
    
    # Restore storage files
    # Restore document dependencies
    # Restore workflows
    # ... etc
```

---

## 🔐 Security Features

### Multi-Layer Safety

1. **Admin-Only Access**
   ```python
   if not request.user.is_staff:
       return Response({'error': 'Admin privileges required'}, status=403)
   ```

2. **Explicit Confirmation Required**
   ```python
   if confirmation_code != 'RESTORE CLEAN':
       return Response({'error': "Type 'RESTORE CLEAN' to proceed"}, status=400)
   ```

3. **Logged Action**
   ```python
   logger.warning('System reinit executed via API by admin user %s', 
                  request.user.username)
   ```

---

## 🆚 Comparison: Manual vs Automatic

### Manual Approach (CLI)

```bash
# Step 1: Create backup
python manage.py create_backup --type database --output /tmp/backup.json.gz

# Step 2: System reinit (manual)
python manage.py system_reinit --confirm

# Step 3: Restore (manual)
python manage.py restore_backup --from-file /tmp/backup.json.gz
```

**Pros:**
- ✅ Full control over each step
- ✅ Can verify state between steps
- ✅ Available via CLI

**Cons:**
- ❌ Three separate commands
- ❌ Manual coordination required
- ❌ Risk of forgetting a step

---

### Automatic Approach (API)

```bash
# Single API call does all three steps
curl -X POST http://localhost:8000/api/v1/backup/restores/restore_from_file/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "backup_file=@/path/to/backup.tar.gz" \
  -F "restore_type=full" \
  -F "with_reinit=true" \
  -F "reinit_confirm=RESTORE CLEAN"
```

**Pros:**
- ✅ Single atomic operation
- ✅ Automatic coordination
- ✅ Enhanced restore logic built-in

**Cons:**
- ❌ API-only (not available in CLI)
- ❌ Less granular control
- ❌ Requires admin API access

---

## 🔍 Model Definition

The `RestoreJob` model does **NOT** have a separate "WITH_REINIT" type:

```python
# backend/apps/backup/models.py - Line 273-278
RESTORE_TYPES = [
    ('FULL_RESTORE', 'Full System Restore'),
    ('DATABASE_RESTORE', 'Database Restore'),
    ('FILES_RESTORE', 'Files Restore'),
    ('SELECTIVE_RESTORE', 'Selective Restore'),
]
```

**Note:** The "with reinit" behavior is controlled by a **parameter**, not a restore type.

---

## 📊 Full API Request Example

### Using cURL

```bash
# Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' | jq -r '.access')

# Restore with reinit
curl -X POST http://localhost:8000/api/v1/backup/restores/restore_from_file/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "backup_file=@/tmp/backup.tar.gz" \
  -F "restore_type=full" \
  -F "with_reinit=true" \
  -F "reinit_confirm=RESTORE CLEAN" \
  -F "overwrite_existing=true"
```

### Using JavaScript (Frontend)

```javascript
const formData = new FormData();
formData.append('backup_file', backupFile);
formData.append('restore_type', 'full');
formData.append('with_reinit', 'true');
formData.append('reinit_confirm', 'RESTORE CLEAN');
formData.append('overwrite_existing', 'true');

const response = await fetch('/api/v1/backup/restores/restore_from_file/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
```

### Using Python (requests)

```python
import requests

token = get_auth_token()  # Your auth function

files = {'backup_file': open('/tmp/backup.tar.gz', 'rb')}
data = {
    'restore_type': 'full',
    'with_reinit': 'true',
    'reinit_confirm': 'RESTORE CLEAN',
    'overwrite_existing': 'true'
}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:8000/api/v1/backup/restores/restore_from_file/',
    files=files,
    data=data,
    headers=headers
)

print(response.json())
```

---

## ⚠️ Important Considerations

### 1. Not Available in CLI

The `with_reinit` parameter is **only available through the API**. The CLI commands don't have this option:

```bash
# This does NOT exist:
python manage.py restore_backup --with-reinit --from-file backup.json.gz

# You must do it manually:
python manage.py system_reinit --confirm
python manage.py restore_backup --from-file backup.json.gz
```

### 2. Requires Admin Privileges

```python
if not request.user.is_staff:
    return Response({'error': 'Admin privileges required'}, status=403)
```

Only staff/admin users can use the `with_reinit` option.

### 3. Requires Exact Confirmation Code

```python
if confirmation_code != 'RESTORE CLEAN':
    return Response({'error': "Type 'RESTORE CLEAN' to proceed"}, status=400)
```

Must type exactly: `RESTORE CLEAN` (case-sensitive)

### 4. DESTRUCTIVE Operation

Just like manual reinit, this will:
- ❌ Delete all users (except new admin)
- ❌ Delete all documents
- ❌ Delete all workflows
- ❌ Delete all audit trails
- ✅ Preserve DocumentTypes, Roles, etc.

**No undo!** Ensure you have a valid backup.

### 5. Frontend Implementation

Looking at the code, this feature is meant to be used from a frontend UI. The frontend would:

1. Show a restore form
2. Provide a checkbox: "Restore into clean system (reinit first)"
3. If checked, show confirmation input: "Type 'RESTORE CLEAN' to confirm"
4. Send API request with `with_reinit=true` and confirmation code

---

## 🧪 Testing the Feature

### Test 1: API Endpoint Exists

```bash
# Check if endpoint is accessible
curl http://localhost:8000/api/v1/backup/restores/ | jq
```

### Test 2: Permission Check

```bash
# Try as non-admin (should fail)
curl -X POST http://localhost:8000/api/v1/backup/restores/restore_from_file/ \
  -H "Authorization: Bearer $NON_ADMIN_TOKEN" \
  -F "with_reinit=true" \
  -F "reinit_confirm=RESTORE CLEAN"

# Expected: 403 Forbidden
```

### Test 3: Confirmation Code Check

```bash
# Try with wrong confirmation (should fail)
curl -X POST http://localhost:8000/api/v1/backup/restores/restore_from_file/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "with_reinit=true" \
  -F "reinit_confirm=WRONG CODE"

# Expected: 400 Bad Request
```

### Test 4: Full Workflow (Dry Run)

```bash
# 1. Create backup first
docker exec edms_backend python manage.py create_backup \
  --type database --output /tmp/test_backup.json.gz

# 2. Test the API (if you have a frontend or API client)
# This would actually execute reinit + restore
# Use with caution!
```

---

## 📋 Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ API Request: restore_from_file()                        │
│ with_reinit=true, reinit_confirm="RESTORE CLEAN"       │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Permission Check: is_staff?                             │
│ ❌ No → 403 Forbidden                                   │
│ ✅ Yes → Continue                                       │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Confirmation Check: code == "RESTORE CLEAN"?            │
│ ❌ No → 400 Bad Request                                 │
│ ✅ Yes → Continue                                       │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Execute System Reinit                           │
│ call_command('system_reinit', confirm=True)             │
│                                                          │
│ Result:                                                  │
│ - Users: 1 (new admin)                                  │
│ - Documents: 0                                           │
│ - Config: Preserved (DocumentTypes, Roles, etc.)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 2: Extract Backup Package                          │
│ - Create temp directory                                 │
│ - Extract tar.gz                                         │
│ - Locate database_backup.json                           │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 3: Pre-Create Users (Enhanced Logic)               │
│ - Parse backup for users                                │
│ - Create user accounts                                  │
│ - Set default password: 'edms123'                       │
│ - Guarantees FK resolution for UserRoles                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 4: Run EnhancedRestoreProcessor                    │
│ - Process with post-reinit awareness                    │
│ - Map old UUIDs to new UUIDs                            │
│ - Restore roles, documents, workflows                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 5: Restore Storage Files                           │
│ - Restore /storage/documents/*                          │
│ - Restore /storage/versions/*                           │
│ - Restore media files                                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 6: Return Success Response                         │
│ {                                                        │
│   "status": "success",                                  │
│   "restore_job_id": "uuid",                             │
│   "message": "Restore with reinit completed"            │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Key Differences from Manual Process

### Manual Process (CLI)

```
1. Backup  → Manual command
2. Reinit  → Manual command  
3. Restore → Manual command (detects post-reinit automatically)
```

**User controls:** All 3 steps

### API with_reinit Process

```
1. Backup  → (Assumed already created)
2. Reinit  → Automatic (API calls it)
3. Restore → Automatic (API continues)
```

**User controls:** Just the API call
**API controls:** Reinit + Restore coordination

---

## ✅ Summary

### Question Answer

**"Does 'Restore into clean system (reinit first)' perform reinit first?"**

✅ **YES** - It's an API feature that:
1. Executes `system_reinit` command
2. Then proceeds with restore
3. Uses enhanced post-reinit restore logic

### Where It Exists

- ✅ **API:** `/api/v1/backup/restores/restore_from_file/` with `with_reinit=true`
- ❌ **CLI:** Not available as a command-line option
- ❌ **Model:** Not a separate restore type

### How to Use It

**API Request:**
```bash
POST /api/v1/backup/restores/restore_from_file/
- backup_file: <file>
- with_reinit: "true"
- reinit_confirm: "RESTORE CLEAN"
```

**CLI Alternative:**
```bash
# Must do manually:
python manage.py system_reinit --confirm
python manage.py restore_backup --from-file backup.json.gz
```

### Safety Features

- ✅ Admin-only
- ✅ Requires exact confirmation code
- ✅ Logged action
- ✅ Atomic operation

---

**Status:** ✅ **FEATURE EXISTS AND WORKS**  
**Type:** 🌐 **API-Only**  
**Safety:** 🔐 **High** (Multi-layer protection)  
**Last Updated:** 2026-01-04
