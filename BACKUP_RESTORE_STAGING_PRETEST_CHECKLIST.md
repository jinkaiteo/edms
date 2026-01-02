# Backup & Restore Pre-Test Checklist - Staging Server

**Date:** 2026-01-02  
**Server:** 172.28.1.148 (edms-staging)  
**Status:** Ready for testing with known issues documented

---

## ⚠️ **Known Issues & Anticipated Problems**

### **1. BACKUP_DIR Setting Not Configured ⚠️**

**Issue:**
```
BACKUP_DIR: Not set
```

**Impact:**
- Backups might save to default location: `/app/backups/` inside container
- If container is removed, backups are lost
- Not persisted to host filesystem

**Recommendation:**
Add to `docker-compose.prod.yml` environment or create volume mount:
```yaml
backend:
  volumes:
    - ./backups:/app/backups  # Persist backups to host
```

**Current Status:**
- Backups directory exists: `/home/lims/edms-staging/backups/`
- Has one backup: `20260101_130029`
- But may not be mounted to container

---

### **2. Database Service Name Mismatch**

**Configuration:**
- Docker service name: `db` ✅
- Container name: `edms_prod_db` ✅
- Port: `5433` (external) → `5432` (internal) ✅
- Database: PostgreSQL 18 ✅

**Status:** ✅ Correct - Database running and healthy

---

### **3. Timezone Impact on Backups**

**Consideration:**
- Backup timestamps use UTC
- Backup filenames: `20260101_130029` (UTC timestamp)
- Users in SGT see different date/time

**Example:**
- Backup created: `2026-01-01 13:00:29 UTC`
- Singapore time: `2026-01-01 21:00:29 SGT` (9 PM)
- Filename still shows UTC

**Impact:** ⚠️ Minor - Users might be confused by backup times

---

### **4. Storage Permissions**

**Potential Issue:**
- Container runs as specific user
- Host filesystem might have different permissions
- Backup files might not be readable/writable

**Check:**
```bash
ls -la /home/lims/edms-staging/backups/
# Should show lims:lims ownership
```

**Current Status:**
```
drwxrwxr-x  3 lims lims  4096 Jan  1 13:00 backups/
```
✅ Correct permissions

---

### **5. Database Backup Format**

**Important:**
- System uses Django fixtures (JSON format)
- NOT PostgreSQL pg_dump format
- Restore requires Django ORM, not psql

**Implication:**
- Cannot use standard PostgreSQL tools to restore
- Must use Django management commands
- Natural key dependencies matter

---

### **6. File Restoration**

**Media Files:**
- Location: `/app/storage/media` inside container
- Should be volume-mounted to host
- Check if files are actually backed up

**Configuration Files:**
- Settings might not be included in backup
- `.env` file not backed up (security)
- May need manual configuration after restore

---

### **7. Foreign Key Dependencies**

**Known Issue (from docs):**
- Restore order matters (users → documents → workflows)
- Natural keys must resolve correctly
- Missing dependencies cause restore failures

**From BACKUP_RESTORE_TROUBLESHOOTING.md:**
```
Common Issue: Foreign Key Constraint Violations
Solution: Ensure restore order respects dependencies
```

---

### **8. UUID vs ID Primary Keys**

**Potential Issue:**
- Some models use UUID primary keys
- Natural key resolution required
- Can cause "does not exist" errors during restore

**Models with UUIDs:**
- Document
- BackupJob
- RestoreJob
- Others

---

## ✅ **Pre-Test Verification Steps**

### **Step 1: Check Backup Directory**

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Check if backups directory exists and has correct permissions
ls -la backups/

# Check if directory is mounted in container
docker compose -f docker-compose.prod.yml exec backend ls -la /app/backups/
```

**Expected:** Directory exists in both host and container

---

### **Step 2: Verify Database Connection**

```bash
# Test database connection
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell -c "SELECT version();"
```

**Expected:** PostgreSQL version info

---

### **Step 3: Check Current Data**

```bash
# Count records before backup
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document
from apps.users.models import User
from apps.workflows.models import Workflow

print(f"Documents: {Document.objects.count()}")
print(f"Users: {User.objects.count()}")
print(f"Workflows: {Workflow.objects.count()}")
EOF
```

**Save these numbers** to compare after restore!

---

### **Step 4: Test Backup Creation**

```bash
# Create a test backup via Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'EOF'
from apps.backup.services import BackupService
from apps.backup.models import BackupConfiguration
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

# Get or create a backup config
config = BackupConfiguration.objects.first()
if not config:
    config = BackupConfiguration.objects.create(
        name="Test Backup",
        backup_type="DATABASE",
        created_by=admin
    )

# Try to create backup
service = BackupService()
try:
    job = service.execute_backup(config, admin)
    print(f"✅ Backup created: {job.backup_path}")
except Exception as e:
    print(f"❌ Backup failed: {e}")
EOF
```

**Expected:** Backup created successfully

---

### **Step 5: Check Backup File Exists**

```bash
# List backups
ls -lh /home/lims/edms-staging/backups/

# Check inside container
docker compose -f docker-compose.prod.yml exec backend ls -lh /app/backups/
```

**Expected:** New backup file visible

---

### **Step 6: Verify Backup Content**

```bash
# If backup is ZIP, check contents
cd /home/lims/edms-staging/backups/
unzip -l <backup-filename>.zip
```

**Expected:** Should contain:
- `database_backup.json` (Django fixture)
- `metadata.json` (backup info)
- Possibly `media/` directory (if files included)

---

## 🎯 **Recommended Test Plan**

### **Test 1: Simple Backup (Low Risk)**

1. Create backup of current system
2. Verify backup file created
3. Check backup contains data
4. **DO NOT RESTORE YET**

**Risk:** ✅ Low - Just reading data

---

### **Test 2: Backup Verification (Low Risk)**

1. Download backup file
2. Extract and inspect JSON
3. Verify all models included
4. Check natural keys exist

**Risk:** ✅ Low - Just reading files

---

### **Test 3: Restore to SEPARATE Database (Medium Risk)**

**NOT RECOMMENDED ON STAGING YET**

Create a separate test database first:
1. Create new database: `edms_test_restore`
2. Configure Django to use test database
3. Restore backup to test database
4. Verify data integrity
5. If successful, then try on staging

**Risk:** 🔶 Medium - Could overwrite data if misconfigured

---

### **Test 4: Full Restore on Staging (HIGH RISK)**

**⚠️ ONLY AFTER Test 1-3 SUCCEED**

1. **BACKUP CURRENT DATA FIRST!**
2. Create fresh backup of current state
3. Test restore from old backup
4. Verify all data restored correctly
5. If problems, restore from fresh backup

**Risk:** ⚠️ HIGH - Could lose data if restore fails

---

## 🚨 **Critical Warnings**

### **Before Testing Restore:**

1. ⚠️ **CREATE FRESH BACKUP FIRST**
   - Backup current staging data before any restore tests
   - Keep multiple backup copies
   - Test backup is valid before proceeding

2. ⚠️ **UNDERSTAND RESTORE IS DESTRUCTIVE**
   - Restore REPLACES current database
   - All current data will be lost
   - Cannot undo without a backup

3. ⚠️ **CHECK BACKUP FILE INTEGRITY**
   - Verify backup file is not corrupted
   - Check JSON is valid
   - Ensure all required data is present

4. ⚠️ **CONSIDER DOWNTIME**
   - Users cannot access system during restore
   - Plan for maintenance window
   - Notify users in advance

---

## 📋 **Known Issues from Documentation**

### **From BACKUP_RESTORE_TROUBLESHOOTING.md:**

#### **Issue 1: Foreign Key Constraint Violations**
**Symptom:** `IntegrityError: violates foreign key constraint`  
**Cause:** Wrong restore order  
**Solution:** Restore in dependency order (users → documents → workflows)

#### **Issue 2: Natural Key Resolution Failures**
**Symptom:** `DoesNotExist` errors during restore  
**Cause:** Referenced objects don't exist yet  
**Solution:** Ensure all dependencies restored first

#### **Issue 3: UUID Conflicts**
**Symptom:** `duplicate key value violates unique constraint`  
**Cause:** UUIDs already exist in database  
**Solution:** Clear database before restore, or use `--update` flag

#### **Issue 4: Missing Media Files**
**Symptom:** Documents restored but files 404  
**Cause:** Media files not included in backup  
**Solution:** Ensure `include_files=True` in backup config

#### **Issue 5: Permission Errors**
**Symptom:** `PermissionError: [Errno 13]`  
**Cause:** Container cannot write to backup directory  
**Solution:** Fix directory permissions on host

---

## ✅ **Recommended Approach**

### **Phase 1: Non-Destructive Testing (TODAY)**

1. ✅ Create a backup
2. ✅ Verify backup file exists
3. ✅ Check backup content
4. ✅ Count records in backup
5. ❌ **DO NOT RESTORE YET**

**Risk:** ✅ ZERO - No data modification

---

### **Phase 2: Restore Testing (FUTURE)**

**Prerequisites:**
- Fresh backup of current data ✅
- Backup file validated ✅
- Maintenance window scheduled ✅
- Users notified ✅

**Steps:**
1. Create current state backup
2. Attempt restore from old backup
3. Verify data integrity
4. If problems, restore from fresh backup

**Risk:** 🔶 Medium - Can recover with fresh backup

---

## 🎯 **Immediate Next Steps**

### **Safe Actions (Do Now):**

1. **Create a backup:**
   ```bash
   # Via Django admin at http://172.28.1.148:3001/admin/backup/
   # Or via API
   ```

2. **Check backup created:**
   ```bash
   ls -lh /home/lims/edms-staging/backups/
   ```

3. **Document current state:**
   - Number of documents
   - Number of users
   - Number of workflows
   - Current database size

### **Risky Actions (Wait):**

- ❌ **DO NOT** test restore yet
- ❌ **DO NOT** run restore commands
- ❌ **DO NOT** clear database

**Wait until backup is verified and you have a solid rollback plan!**

---

## 📞 **If Something Goes Wrong**

### **During Backup:**
- Check logs: `docker compose logs backend`
- Check permissions: `ls -la backups/`
- Check disk space: `df -h`

### **During Restore:**
- **STOP IMMEDIATELY**
- Check what data still exists
- Restore from fresh backup if needed
- Check error logs for root cause

### **Recovery Plan:**
1. Restore from fresh backup created before testing
2. Restart all containers
3. Verify database integrity
4. Notify users of any data loss

---

## 🎉 **Current Status**

### **✅ Ready for:**
- Backup creation testing
- Backup verification
- Non-destructive operations

### **⚠️ NOT Ready for:**
- Full restore testing
- Database replacement
- Destructive operations

### **🔧 Recommended Setup Before Restore Testing:**

1. Add explicit backup volume mount:
   ```yaml
   # docker-compose.prod.yml
   backend:
     volumes:
       - ./backups:/app/backups
   ```

2. Configure BACKUP_DIR in settings:
   ```python
   # settings/production.py
   BACKUP_DIR = '/app/backups'
   ```

3. Test on separate database first

---

**Ready to proceed with Phase 1 (non-destructive backup testing)?**

**Answer:** ✅ YES - Safe to test backup creation and verification  
**Restore testing:** ⚠️ Wait until backup validated and rollback plan ready
