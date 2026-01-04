# Backup, Reinit, and Restore - Dependency Analysis

**Date:** 2026-01-04  
**Commit:** 6ace8e5  
**Purpose:** Understand how these three functions interact

---

## 🎯 Executive Summary

### Key Finding: **They Are INDEPENDENT but AWARE of Each Other**

The three functions operate independently but the **restore function** detects and handles **post-reinit scenarios**:

```
Backup ──────────────────────────> Creates backup files
                                    (No dependency on others)

Reinit ──────────────────────────> Clears data, preserves config
                                    (No dependency on others)

Restore ─────> Detects Post-Reinit ──> Uses special logic
                                    (Aware of reinit state)
```

**Important:** Reinit does NOT call restore. Restore does NOT call reinit. They are separate operations that you chain manually.

---

## 📊 Three Functions Explained

### 1. Backup Function

**Purpose:** Create a snapshot of system data

**Location:** 
- `backend/apps/backup/services.py` - `BackupService._backup_database()`
- `backend/apps/backup/management/commands/create_backup.py`

**What It Does:**
1. Exports database using Django's `dumpdata` command
2. Uses natural keys for portability
3. Includes Django system tables (auth, contenttypes, permissions)
4. Includes EDMS apps (users, documents, workflows, audit, etc.)
5. Compresses to `.json.gz` file
6. Creates metadata file alongside
7. Records BackupJob in database

**Dependencies:**
- ❌ Does NOT depend on reinit
- ❌ Does NOT depend on restore
- ✅ Standalone operation

**Output:**
```
/storage/backups/database_backup_20260104_123456.json.gz
/storage/backups/database_backup_20260104_123456_metadata.json
```

---

### 2. System Reinit Function

**Purpose:** Reset system to clean state while preserving core configuration

**Location:**
- `backend/apps/admin_pages/management/commands/system_reinit.py`

**What It Does:**

#### Phase 1: Preservation (What It KEEPS)
```python
# These are preserved
- Document Types (POL, SOP, WI, etc.)
- Document Sources (Internal, External, etc.)
- Workflow Types (Review workflow definitions)
- Document States (DRAFT, REVIEWED, APPROVED, EFFECTIVE, etc.)
- Roles (Viewer, Author, Reviewer, Approver)
- Placeholders (Template placeholders like {{DOCUMENT_NUMBER}})
- Core system configuration
```

#### Phase 2: Deletion (What It REMOVES)
```python
# These are cleared
- All Users (except new admin)
- All Documents
- All Document Versions
- All Workflow Instances
- All Audit Trails
- All Backup Jobs
- Storage files (/storage/documents/*, /storage/versions/*)
```

#### Phase 3: Recreation
```python
# Creates fresh admin user
User.objects.create_superuser(
    username='admin',
    email='admin@edms.local',
    password='test123'
)
```

**Dependencies:**
- ❌ Does NOT call backup
- ❌ Does NOT call restore
- ✅ Standalone operation

**Result After Reinit:**
```
Users:              1 (admin only)
Documents:          0
Workflows:          0
Document Types:     6 (preserved)
Document Sources:   4 (preserved)
Workflow Types:     5 (preserved)
Document States:    19 (preserved)
Roles:              7 (preserved)
Placeholders:       32 (preserved)
```

---

### 3. Restore Function

**Purpose:** Load data from backup file into database

**Location:**
- `backend/apps/backup/services.py` - `RestoreService._restore_database_from_file()`
- `backend/apps/backup/management/commands/restore_backup.py`
- `backend/apps/backup/restore_processor.py` - `EnhancedRestoreProcessor`

**What It Does:**

#### Step 1: Load Backup File
```python
with gzip.open(backup_path, 'rt') as f:
    backup_data = json.load(f)  # Load Django fixture JSON
```

#### Step 2: **DETECT POST-REINIT STATE**
```python
from django.contrib.auth import get_user_model
User = get_user_model()
user_count_before = User.objects.count()

if user_count_before <= 1:  # Only admin exists (post-reinit)
    logger.info("🔧 Post-reinit restoration detected")
    self._restore_with_conflict_resolution(temp_fixture_path, backup_data)
else:
    # Normal restoration
    call_command('loaddata', temp_fixture_path, verbosity=1)
```

**This is the KEY interaction point!**

#### Step 3: Choose Restore Strategy

**Normal Restore (user_count > 1):**
- Use Django's `loaddata` command
- Load all data directly
- Assumes clean database or compatible state

**Post-Reinit Restore (user_count <= 1):**
- Use `EnhancedRestoreProcessor`
- Handle UUID conflicts for preserved objects
- Skip admin user (already exists with different UUID)
- Map old Role UUIDs to new Role UUIDs
- Use name-based FK resolution instead of UUID

#### Step 4: Reset Sequences
```python
self._reset_postgresql_sequences()
# Prevents "duplicate key" errors on next insert
```

**Dependencies:**
- ✅ **AWARE** of reinit state (detects it)
- ❌ Does NOT call reinit
- ❌ Does NOT call backup
- ⚠️ Behavior changes based on reinit detection

---

## 🔄 How They Work Together

### Typical Workflow Sequences

#### Scenario A: Regular Backup and Restore

```
1. Create Backup
   └─> python manage.py create_backup --type database
   
2. (Later) Restore Backup
   └─> python manage.py restore_backup --from-file backup.json.gz
   
   Detection: user_count > 1 (normal state)
   Action: Standard restoration
```

#### Scenario B: System Reset with Data Recovery

```
1. Create Backup (BEFORE reinit)
   └─> python manage.py create_backup --type database
   
2. System Reinit (Clear data, keep config)
   └─> python manage.py system_reinit --confirm
   
   Result:
   - All users deleted except new admin
   - All documents deleted
   - Config preserved (DocumentTypes, Roles, etc.)
   
3. Restore Backup (Post-reinit restore)
   └─> python manage.py restore_backup --from-file backup.json.gz
   
   Detection: user_count = 1 (post-reinit state)
   Action: Enhanced restoration with conflict resolution
   - Skip new admin user
   - Map Role UUIDs (preserved roles have new UUIDs)
   - Restore users from backup
   - Restore documents from backup
```

#### Scenario C: Migration to New Server

```
1. On Old Server: Create Backup
   └─> python manage.py create_backup --type database
   
2. On New Server: Fresh Install
   └─> Migrations run, creates default DocumentTypes, Roles, etc.
   
3. On New Server: Restore
   └─> python manage.py restore_backup --from-file backup.json.gz
   
   Detection: May see as post-reinit (few users)
   Action: UUID mapping for default objects
```

---

## 🧩 Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │  Manual Decision: What to do?         │
         └───────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌────────┐         ┌─────────┐        ┌──────────┐
    │ BACKUP │         │ REINIT  │        │ RESTORE  │
    └────────┘         └─────────┘        └──────────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
  Creates backup       Clears data         Loads backup
     .json.gz          Preserves           Detects state
                       config              Adapts logic
         │                   │                   │
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  Database       │
                   │  Storage        │
                   └─────────────────┘

INDEPENDENCE: Each function is standalone
AWARENESS: Restore detects post-reinit state
CHAINING: User manually chains: Backup → Reinit → Restore
```

---

## 🔍 Code-Level Dependencies

### Backup → Others

**Imports:**
```python
# backup/services.py
from django.core.management import call_command  # For dumpdata
from django.contrib.auth import get_user_model
# NO imports from reinit or restore
```

**Calls:**
- `call_command('dumpdata', ...)` - Django built-in
- Does NOT call reinit
- Does NOT call restore

**Conclusion:** ✅ Fully independent

---

### Reinit → Others

**Imports:**
```python
# admin_pages/management/commands/system_reinit.py
from apps.users.models import User, Role, UserRole
from apps.documents.models import Document, DocumentVersion
from apps.workflows.models import DocumentWorkflow
from apps.audit.models import AuditTrail
# NO imports from backup or restore modules
```

**Calls:**
- `User.objects.all().delete()` - Direct model operations
- `Document.objects.all().delete()` - Direct model operations
- Does NOT call backup
- Does NOT call restore

**Conclusion:** ✅ Fully independent

---

### Restore → Others

**Imports:**
```python
# backup/services.py - RestoreService
from django.core.management import call_command  # For loaddata
from django.contrib.auth import get_user_model
from .restore_processor import EnhancedRestoreProcessor
from .direct_restore_processor import DirectRestoreProcessor
# NO import of system_reinit command
```

**Detection Logic:**
```python
def _restore_database_from_file(self, backup_path):
    # Line 936-943 in services.py
    User = get_user_model()
    user_count_before = User.objects.count()
    
    if user_count_before <= 1:  # Post-reinit detection
        logger.info("🔧 Post-reinit restoration detected")
        self._restore_with_conflict_resolution(...)
    else:
        call_command('loaddata', ...)
```

**Calls:**
- Does NOT call `system_reinit` command
- Does NOT import reinit module
- Only **detects** post-reinit state by user count
- Does NOT call backup

**Conclusion:** ✅ Independent, but state-aware

---

## 🎭 Post-Reinit Detection Logic

### How Restore Detects Post-Reinit State

**Detection Method: User Count**

```python
user_count_before = User.objects.count()

if user_count_before <= 1:
    # Post-reinit state detected
    # After reinit, only 1 admin user exists
    post_reinit_mode = True
```

**Why User Count = 1 Indicates Post-Reinit:**

1. **Fresh Install:** Usually has 0 users (before any setup)
2. **After Reinit:** Has exactly 1 user (new admin created by reinit)
3. **Normal System:** Has multiple users (2+)

**False Positive Risk:** Low
- If system truly has only 1 user, worst case is it uses enhanced restore (no harm)

**False Negative Risk:** None
- If system has 2+ users, it's definitely not post-reinit

### What Changes in Post-Reinit Mode

**Normal Mode:**
```python
# Simple approach
call_command('loaddata', fixture_file)
# Load all data as-is, assuming PKs and UUIDs match
```

**Post-Reinit Mode:**
```python
# Enhanced approach
processor = EnhancedRestoreProcessor()
processor.process_backup_data(backup_file)

# Special handling:
# 1. Skip admin user (already exists with different UUID)
# 2. Map preserved object UUIDs:
#    - Roles: old UUID → new UUID (name-based match)
#    - DocumentTypes: old UUID → new UUID
#    - DocumentStates: old UUID → new UUID
# 3. Resolve FKs by natural keys (name/code) not UUIDs
# 4. Handle missing references gracefully
```

---

## 🧪 Test Scenarios

### Test 1: Independent Backup

**Commands:**
```bash
python manage.py create_backup --type database --output /tmp/test.json.gz
```

**Expected:**
- ✅ Creates backup file
- ✅ Records BackupJob
- ✅ No interaction with reinit or restore

**Verification:**
```bash
ls -lh /tmp/test.json.gz  # Should exist
gunzip -c /tmp/test.json.gz | head -20  # Should show JSON array
```

---

### Test 2: Independent Reinit

**Commands:**
```bash
python manage.py system_reinit --dry-run  # Safe preview
python manage.py system_reinit --confirm   # Actual execution
```

**Expected:**
- ✅ Clears all users except new admin
- ✅ Clears all documents
- ✅ Preserves DocumentTypes, Roles, etc.
- ✅ No interaction with backup or restore

**Verification:**
```bash
docker exec edms_backend python manage.py shell -c "
from apps.users.models import User
from apps.documents.models import Document, DocumentType
print(f'Users: {User.objects.count()}')  # Should be 1
print(f'Documents: {Document.objects.count()}')  # Should be 0
print(f'DocumentTypes: {DocumentType.objects.count()}')  # Should be 6
"
```

---

### Test 3: Restore Without Reinit (Normal)

**Setup:**
```bash
# Create backup of current state
python manage.py create_backup --type database --output /tmp/before.json.gz

# Make some changes (create test document)
# ...

# Restore to previous state
python manage.py restore_backup --from-file /tmp/before.json.gz
```

**Expected:**
- ✅ Detects user_count > 1 (normal mode)
- ✅ Uses standard loaddata
- ✅ Restores all data
- ✅ No post-reinit handling

**Verification:**
```bash
# Check logs for "Post-reinit restoration detected"
# Should NOT see this message
```

---

### Test 4: Restore After Reinit (Post-Reinit Mode)

**Full Workflow:**
```bash
# Step 1: Create backup
python manage.py create_backup --type database --output /tmp/backup_pre_reinit.json.gz

echo "Backup created with:"
echo "- Users: 7"
echo "- Documents: 4"
echo "- DocumentTypes: 6 (with UUIDs: xxx, yyy, zzz)"

# Step 2: System reinit
python manage.py system_reinit --confirm

echo "After reinit:"
echo "- Users: 1 (new admin)"
echo "- Documents: 0"
echo "- DocumentTypes: 6 (PRESERVED but with NEW UUIDs: aaa, bbb, ccc)"

# Step 3: Restore
python manage.py restore_backup --from-file /tmp/backup_pre_reinit.json.gz
```

**Expected:**
- ✅ Detects user_count = 1 (post-reinit mode)
- ✅ Uses EnhancedRestoreProcessor
- ✅ Maps old Role UUIDs to new Role UUIDs
- ✅ Skips new admin user (prevents conflict)
- ✅ Restores users from backup
- ✅ Restores documents from backup

**Verification:**
```bash
docker exec edms_backend python manage.py shell -c "
from apps.users.models import User
from apps.documents.models import Document
from apps.users.models import Role

print(f'Users after restore: {User.objects.count()}')  # Should be 7
print(f'Documents after restore: {Document.objects.count()}')  # Should be 4
print(f'Roles: {Role.objects.count()}')  # Should be 7 (preserved)

# Check if role assignments work
user = User.objects.get(username='author01')
print(f'author01 roles: {list(user.roles.values_list(\"name\", flat=True))}')
"
```

---

## ⚠️ Important Considerations

### 1. Restore Does NOT Clear Data First

**Behavior:**
```python
# Restore adds/updates data, does NOT delete existing data
call_command('loaddata', fixture_file)
# This merges backup data with existing data
```

**Implications:**
- If you restore to a non-empty database, you get a MERGE
- Old data stays, backup data is added
- May cause conflicts if objects with same natural keys exist

**Best Practice:**
```bash
# For clean restore, either:
# Option A: Restore to empty database
# Option B: Use reinit first, then restore
```

### 2. Reinit is DESTRUCTIVE and IRREVERSIBLE

**Warning:**
```python
# system_reinit.py line 200-250
User.objects.exclude(username='admin').delete()
Document.objects.all().delete()
DocumentVersion.objects.all().delete()
# ... all user data deleted
```

**Safety Measures:**
- Requires `--confirm` flag
- Shows dry-run preview with `--dry-run`
- Interactive confirmation prompt
- Cannot be undone without backup

**Best Practice:**
```bash
# ALWAYS backup before reinit
python manage.py create_backup --type database --output /tmp/safety_backup.json.gz
python manage.py system_reinit --dry-run  # Preview first
python manage.py system_reinit --confirm   # Execute only if sure
```

### 3. UUID Conflicts in Post-Reinit

**The Problem:**
```
Before Reinit:
- Role "Reviewer" has UUID: 550e8400-e29b-41d4-a716-446655440000

After Reinit:
- Role "Reviewer" preserved but NEW UUID: 9b59b42f-3c8a-4e87-8f41-2c7e5e8d3f1a

Backup Data:
- User "reviewer01" has role FK: 550e8400-e29b-41d4-a716-446655440000
```

**The Solution:**
```python
# Enhanced Restore Processor
# Line 100-150 in restore_processor.py

role_mapping = {}
for role_name in ['Viewer', 'Author', 'Reviewer', 'Approver']:
    old_role = backup_data.get_role(role_name)
    new_role = Role.objects.get(name=role_name)
    
    if old_role.uuid != new_role.uuid:
        role_mapping[old_role.uuid] = new_role.uuid

# When restoring user role assignments
for user_role_record in backup_data:
    old_role_uuid = user_role_record['fields']['role']
    new_role_uuid = role_mapping.get(old_role_uuid, old_role_uuid)
    UserRole.objects.create(user=user, role_uuid=new_role_uuid)
```

### 4. Natural Key Requirements

**For portability, models must define natural keys:**

```python
# Example from users/models.py
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def natural_key(self):
        return (self.name,)
    
    class Meta:
        natural_key_fields = ['name']
```

**Used in backup:**
```json
{
  "model": "users.userrole",
  "fields": {
    "user": ["author01"],  // Natural key: username
    "role": ["Author"]     // Natural key: role name
  }
}
```

---

## 📊 Summary Table

| Aspect | Backup | Reinit | Restore |
|--------|--------|--------|---------|
| **Purpose** | Save data | Clear data | Load data |
| **Calls Other Functions** | ❌ No | ❌ No | ❌ No |
| **Called By Others** | ❌ No | ❌ No | ❌ No |
| **Aware of Others** | ❌ No | ❌ No | ✅ Yes (detects reinit) |
| **Independence** | ✅ Standalone | ✅ Standalone | ✅ Standalone |
| **Side Effects** | Creates files | Deletes data | Inserts data |
| **Reversible** | N/A | ❌ No | ⚠️ Partial |
| **Requires Auth** | ✅ Yes | ✅ Yes | ✅ Yes |
| **API Available** | ✅ Yes | ✅ Yes | ✅ Yes |
| **CLI Available** | ✅ Yes | ✅ Yes | ✅ Yes |

---

## ✅ Conclusion

### Key Takeaways

1. **Three Independent Operations**
   - Backup, Reinit, and Restore are separate commands
   - No function calls another
   - Each can run standalone

2. **State-Aware Restore**
   - Restore detects post-reinit state
   - Changes behavior automatically
   - Handles UUID conflicts intelligently

3. **Manual Chaining**
   - User must chain operations manually
   - Common pattern: Backup → Reinit → Restore
   - Each step is explicit and controlled

4. **Clean Restore Pattern**
   ```bash
   # For truly clean restoration:
   create_backup → reinit → restore
   
   # NOT:
   restore alone (merges with existing data)
   ```

5. **UUID Mapping is Critical**
   - Post-reinit creates new UUIDs for preserved objects
   - Restore must map old UUIDs to new UUIDs
   - Name-based matching resolves this

### Answer to Your Question

> "Does clean restore use the reinit function?"

**Answer:** ❌ **NO**

- Restore does NOT call reinit
- Restore does NOT import reinit
- They are separate operations
- **BUT:** Restore detects if reinit was run and adapts

**"Clean Restore" means:**
1. You manually run `system_reinit` first (clears data)
2. Then you run `restore_backup` (loads backup)
3. Restore detects the post-reinit state and uses special logic

It's a **manual two-step process**, not an integrated function.

---

**Status:** ✅ **ANALYSIS COMPLETE**  
**Complexity:** 🟡 **MEDIUM** - Independent but state-aware  
**Risk Level:** 🟢 **LOW** - Well-designed separation of concerns  
**Last Updated:** 2026-01-04
