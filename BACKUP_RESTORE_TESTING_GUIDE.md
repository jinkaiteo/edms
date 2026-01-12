# Backup & Restore Testing Guide - Staging Server

**Date:** 2026-01-12  
**Server:** 172.25.222.103  
**Purpose:** Comprehensive testing of the hybrid backup/restore system  
**Estimated Time:** 30 minutes

---

## 📋 Overview

This guide will help you test the complete backup and restore workflow:

1. **Create test data** (documents, users, workflows)
2. **Create backup** (verify all data captured)
3. **Simulate disaster** (delete data)
4. **Restore backup** (verify complete recovery)
5. **Validate integrity** (confirm data matches)

---

## ⚠️ Safety Notice

**This test is SAFE for staging server:**
- ✅ All data will be backed up first
- ✅ Restore will bring data back
- ✅ Non-destructive if you follow steps
- ⚠️ DO NOT run on production without proper planning

---

## 🎯 Phase 1: Create Test Data (10 minutes)

### Step 1.1: Access Frontend

```bash
# Open browser to:
http://172.25.222.103:3001

# Login with admin credentials:
Username: admin
Password: [your admin password]
```

### Step 1.2: Create Test Documents

Create **3 test documents** with different statuses:

#### Document 1: Draft Status
1. Navigate to "My Documents"
2. Click "Create New Document"
3. Fill in:
   - **Document Number:** `TEST-BACKUP-001`
   - **Title:** `Backup Test - Draft Document`
   - **Document Type:** Select any type (e.g., SOP)
   - **Description:** `This document tests backup of DRAFT status`
4. **Upload file:** Use any test file (PDF, DOCX, TXT)
5. Click "Submit" (DO NOT submit for review yet)
6. **Expected Result:** Document created with status `DRAFT`

#### Document 2: Under Review Status
1. Click "Create New Document" again
2. Fill in:
   - **Document Number:** `TEST-BACKUP-002`
   - **Title:** `Backup Test - Under Review Document`
   - **Document Type:** Select any type
   - **Description:** `This document tests backup of UNDER_REVIEW status`
3. **Upload file:** Use a different test file
4. Click "Submit"
5. **Open the document** and click "Submit for Review"
6. **Expected Result:** Document status changes to `UNDER_REVIEW`

#### Document 3: With Version History
1. Click "Create New Document"
2. Fill in:
   - **Document Number:** `TEST-BACKUP-003`
   - **Title:** `Backup Test - Multi-version Document`
   - **Document Type:** Select any type
3. **Upload file:** Version 1
4. Submit and save
5. **Edit document** and upload a new version
6. **Expected Result:** Document with multiple versions

### Step 1.3: Create Test User (Optional)

```bash
# On staging server, create a test user via Django shell
cd ~/edms

docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# In Python shell:
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user
test_user = User.objects.create_user(
    username='testuser_backup',
    email='testuser@staging.test',
    password='TestPassword123!',
    first_name='Test',
    last_name='Backup User'
)
print(f"Created user: {test_user.username} (ID: {test_user.id})")

# Exit shell
exit()
```

### Step 1.4: Document Current State

```bash
# On staging server
cd ~/edms

# Count documents
echo "=== Document Count ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import Document
print(f'Total documents: {Document.objects.count()}')
for doc in Document.objects.all():
    print(f'  - {doc.document_number}: {doc.title} ({doc.status})')
"

# Count users
echo ""
echo "=== User Count ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Total users: {User.objects.count()}')
for user in User.objects.all():
    print(f'  - {user.username} ({user.email})')
"

# Count uploaded files
echo ""
echo "=== Uploaded Files ==="
ls -lh storage/documents/
echo "Total files:" $(find storage/documents/ -type f | wc -l)
```

**Save this output** - we'll compare it after restore!

---

## 💾 Phase 2: Create Backup (2 minutes)

### Step 2.1: Run Manual Backup

```bash
cd ~/edms

# Create backup
./scripts/backup-hybrid.sh

# Expected output:
# [timestamp] EDMS Hybrid Backup - Starting
# [timestamp] Database: edms_staging_reset (User: edms_staging_user)
# [timestamp] Step 1/4: Backing up database...
# [timestamp] ✅ Database backup complete: XXX K
# [timestamp] Step 2/4: Backing up media files...
# [timestamp] ✅ Media files backup complete: XXX K
# [timestamp] Step 3/4: Creating manifest...
# [timestamp] ✅ Manifest created
# [timestamp] Step 4/4: Creating final archive...
# [timestamp] ✅ Archive created: backup_YYYYMMDD_HHMMSS.tar.gz (XXX K)
# [timestamp] Backup completed successfully!
```

### Step 2.2: Verify Backup File

```bash
# List backups
ls -lh backups/

# Get the latest backup filename
LATEST_BACKUP=$(ls -t backups/backup_*.tar.gz | head -1)
echo "Latest backup: $LATEST_BACKUP"

# Check backup size (should be > 100K if you uploaded files)
du -h "$LATEST_BACKUP"

# Verify backup contents
echo ""
echo "=== Backup Contents ==="
tar -tzf "$LATEST_BACKUP"

# Should show:
# tmp_YYYYMMDD_HHMMSS/
# tmp_YYYYMMDD_HHMMSS/database.dump
# tmp_YYYYMMDD_HHMMSS/storage.tar.gz
# tmp_YYYYMMDD_HHMMSS/manifest.json
```

### Step 2.3: Inspect Manifest

```bash
# Extract and view manifest
tar -xzOf "$LATEST_BACKUP" */manifest.json | python3 -m json.tool

# Should show:
# {
#   "timestamp": "2026-01-12T08:50:00+08:00",
#   "database": "database.dump",
#   "storage": "storage.tar.gz",
#   "version": "363f96a...",
#   "backup_type": "full",
#   "created_by": "backup-hybrid.sh"
# }
```

### Step 2.4: Save Backup Reference

```bash
# Save the backup filename for later
echo "$LATEST_BACKUP" > /tmp/test_backup_file.txt
echo "Backup saved: $LATEST_BACKUP"
```

---

## 🧨 Phase 3: Simulate Disaster (5 minutes)

**⚠️ WARNING:** This will delete data! We have a backup, so it's safe, but be aware.

### Step 3.1: Document Pre-Disaster State

```bash
cd ~/edms

# Take screenshots or save output
echo "=== PRE-DISASTER STATE ===" > /tmp/pre_disaster_state.txt
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import Document
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Documents: {Document.objects.count()}')
print(f'Users: {User.objects.count()}')
" >> /tmp/pre_disaster_state.txt

cat /tmp/pre_disaster_state.txt
```

### Step 3.2: Delete Database Data (Simulated Corruption)

```bash
# Stop containers
docker compose -f docker-compose.prod.yml down

# Remove database volume (SIMULATES DATA LOSS)
docker volume rm edms_postgres_prod_data

# Verify volume removed
docker volume ls | grep edms

# Remove uploaded files (SIMULATES FILE SYSTEM FAILURE)
sudo rm -rf storage/documents/*
sudo rm -rf storage/media/*

# Verify files removed
echo "Documents remaining:" $(find storage/documents/ -type f 2>/dev/null | wc -l)
echo "Media remaining:" $(find storage/media/ -type f 2>/dev/null | wc -l)
```

### Step 3.3: Restart Containers (Fresh Database)

```bash
# Start containers (this will create NEW empty database)
docker compose -f docker-compose.prod.yml up -d

# Wait for containers to be healthy
echo "Waiting for containers to start..."
sleep 30

# Check container status
docker compose -f docker-compose.prod.yml ps
```

### Step 3.4: Verify Data Loss

```bash
# Check database is empty (fresh migrations only)
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import Document
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Documents after disaster: {Document.objects.count()}')
print(f'Users after disaster: {User.objects.count()}')
"

# Expected output:
# Documents after disaster: 0
# Users after disaster: 0 (or maybe 1 if admin was recreated)

# Check files are gone
ls -la storage/documents/
# Should show empty directory
```

**✅ Disaster simulated successfully - all data is gone!**

---

## 🔄 Phase 4: Restore Backup (5 minutes)

Now let's restore everything from the backup!

### Step 4.1: Get Backup Filename

```bash
cd ~/edms

# Retrieve the backup filename we saved earlier
BACKUP_TO_RESTORE=$(cat /tmp/test_backup_file.txt)
echo "Restoring from: $BACKUP_TO_RESTORE"

# Verify backup file exists
if [ -f "$BACKUP_TO_RESTORE" ]; then
    echo "✅ Backup file found"
    ls -lh "$BACKUP_TO_RESTORE"
else
    echo "❌ Backup file not found! List available backups:"
    ls -lh backups/
    # Manually set BACKUP_TO_RESTORE to the correct file
fi
```

### Step 4.2: Run Restore

```bash
# Execute restore script
./scripts/restore-hybrid.sh "$BACKUP_TO_RESTORE"

# Expected output:
# [timestamp] ============================================
# [timestamp] EDMS Hybrid Restore - Starting
# [timestamp] ============================================
# [timestamp] Backup file: backups/backup_YYYYMMDD_HHMMSS.tar.gz
# [timestamp] Step 1/4: Extracting backup...
# [timestamp] ✅ Backup extracted
# [timestamp] Step 2/4: Restoring database...
# [timestamp] Database: edms_staging_reset (User: edms_staging_user)
# [timestamp] ✅ Database restored
# [timestamp] Step 3/4: Restoring media files...
# [timestamp] ✅ Media files restored
# [timestamp] Step 4/4: Restarting services...
# [timestamp] ✅ Services restarted
# [timestamp] ============================================
# [timestamp] Restore completed successfully!
# [timestamp] ============================================
```

### Step 4.3: Monitor Restore Progress

If restore takes time, you can monitor in another terminal:

```bash
# Watch container logs
docker compose -f docker-compose.prod.yml logs -f backend

# Check database activity
docker compose -f docker-compose.prod.yml exec db psql -U edms_staging_user -d edms_staging_reset -c "SELECT COUNT(*) FROM django_migrations;"
```

### Step 4.4: Wait for Services

```bash
# Wait for services to stabilize after restart
echo "Waiting for services to restart..."
sleep 20

# Check container status
docker compose -f docker-compose.prod.yml ps

# All should show "Up"
```

---

## ✅ Phase 5: Validate Restoration (8 minutes)

Now verify that ALL data was restored correctly!

### Step 5.1: Check Document Count

```bash
cd ~/edms

echo "=== POST-RESTORE STATE ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import Document
from django.contrib.auth import get_user_model
User = get_user_model()

print('Documents after restore:', Document.objects.count())
print('Users after restore:', User.objects.count())
print('')
print('Documents:')
for doc in Document.objects.all():
    print(f'  - {doc.document_number}: {doc.title} ({doc.status})')
print('')
print('Users:')
for user in User.objects.all():
    print(f'  - {user.username} ({user.email})')
"
```

**Compare with Phase 1 output** - should match exactly!

### Step 5.2: Check Uploaded Files

```bash
# Check files restored
echo ""
echo "=== Restored Files ==="
ls -lh storage/documents/
echo "Total files:" $(find storage/documents/ -type f | wc -l)

# Compare with Phase 1 count
```

### Step 5.3: Check File Permissions

```bash
# Verify permissions restored correctly
ls -la storage/

# Expected:
# drwxrwxr-x 2 995 995 ... documents/
# drwxrwxr-x 2 995 995 ... media/
```

### Step 5.4: Browser Verification

```bash
# Access frontend
# http://172.25.222.103:3001

# Login with admin credentials
# Password should work (it was restored!)
```

**In browser, verify:**
1. ✅ Login successful (credentials restored)
2. ✅ Navigate to "My Documents"
3. ✅ See all 3 test documents:
   - TEST-BACKUP-001 (Draft)
   - TEST-BACKUP-002 (Under Review)
   - TEST-BACKUP-003 (Multiple versions)
4. ✅ Open each document - should show correct details
5. ✅ Download uploaded files - should work
6. ✅ Check document status matches
7. ✅ Check version history on TEST-BACKUP-003

### Step 5.5: Advanced Validation

```bash
# Check workflow states
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.workflows.models import WorkflowInstance
print(f'Workflow instances: {WorkflowInstance.objects.count()}')
for wf in WorkflowInstance.objects.all():
    print(f'  - Document {wf.document.document_number}: {wf.current_state.name if wf.current_state else \"N/A\"}')
"

# Check document versions
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import DocumentVersion
print(f'Document versions: {DocumentVersion.objects.count()}')
for ver in DocumentVersion.objects.all():
    print(f'  - {ver.document.document_number} v{ver.version_major}.{ver.version_minor}')
"

# Check audit trail
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.documents.models import AuditTrail
print(f'Audit trail entries: {AuditTrail.objects.count()}')
print('Recent entries:')
for entry in AuditTrail.objects.order_by('-timestamp')[:5]:
    print(f'  - {entry.action} on {entry.document.document_number} by {entry.user.username}')
"
```

---

## 📊 Validation Checklist

Mark each as you verify:

### Data Integrity
- [ ] Document count matches (should be 3 or more)
- [ ] User count matches (admin + test users)
- [ ] All document numbers present (TEST-BACKUP-001, 002, 003)
- [ ] Document titles match
- [ ] Document statuses correct (DRAFT, UNDER_REVIEW, etc.)
- [ ] Uploaded files exist in storage/documents/
- [ ] File count matches pre-disaster count

### Functionality
- [ ] Can login with restored credentials
- [ ] Documents visible in "My Documents"
- [ ] Can open and view documents
- [ ] Can download uploaded files
- [ ] Document details display correctly
- [ ] Version history shows (for TEST-BACKUP-003)
- [ ] Workflow states preserved

### System Integrity
- [ ] Workflow instances restored
- [ ] Document versions restored
- [ ] Audit trail entries restored
- [ ] File permissions correct (995:995, 775)
- [ ] No error messages in logs
- [ ] All containers running
- [ ] Backend health check passes
- [ ] Frontend loads without errors

### Performance
- [ ] Backup completed in <5 seconds
- [ ] Restore completed in <30 seconds
- [ ] No significant downtime
- [ ] System responsive after restore

---

## 🎯 Success Criteria

**Backup/Restore is successful if:**

1. ✅ **Backup completed** - Archive created with database + files
2. ✅ **Data loss simulated** - Database and files deleted
3. ✅ **Restore completed** - No errors during restore
4. ✅ **Data integrity** - All documents, users, files restored
5. ✅ **Functionality** - Can login, view docs, download files
6. ✅ **System health** - All services running, no errors
7. ✅ **Performance** - Backup <5s, Restore <30s

---

## 📈 Test Results Template

Document your test results:

```
=== BACKUP/RESTORE TEST RESULTS ===
Date: 2026-01-12
Server: 172.25.222.103
Tester: [Your name]

PRE-BACKUP STATE:
- Documents: ___
- Users: ___
- Files: ___

BACKUP:
- Time taken: ___ seconds
- Backup size: ___ KB
- Status: ✅ Success / ❌ Failed

DISASTER SIMULATION:
- Data deleted: ✅ Yes
- Containers restarted: ✅ Yes
- Fresh database: ✅ Yes

RESTORE:
- Time taken: ___ seconds
- Status: ✅ Success / ❌ Failed
- Errors: None / [describe]

POST-RESTORE STATE:
- Documents: ___
- Users: ___
- Files: ___
- Match: ✅ Yes / ❌ No

VALIDATION:
- Login works: ✅ / ❌
- Documents visible: ✅ / ❌
- Files downloadable: ✅ / ❌
- Workflows intact: ✅ / ❌

OVERALL RESULT: ✅ PASS / ❌ FAIL

NOTES:
[Any observations, issues, or recommendations]
```

---

## 🔍 Troubleshooting

### Issue: Restore fails with "database does not exist"

**Solution:**
```bash
# Create database manually
docker compose -f docker-compose.prod.yml exec db createdb -U edms_staging_user edms_staging_reset

# Then retry restore
./scripts/restore-hybrid.sh [backup-file]
```

### Issue: Files not restored

**Solution:**
```bash
# Check if storage.tar.gz exists in backup
tar -tzf [backup-file] | grep storage.tar.gz

# If present, manually extract:
TEMP_DIR=$(mktemp -d)
tar -xzf [backup-file] -C $TEMP_DIR
cat $TEMP_DIR/*/storage.tar.gz | docker compose -f docker-compose.prod.yml exec -T backend tar -xzf - -C /app
```

### Issue: Permission denied after restore

**Solution:**
```bash
# Fix storage permissions
sudo chown -R 995:995 storage/
sudo chmod -R 775 storage/

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

### Issue: Login fails after restore

**Solution:**
```bash
# Check if admin user exists
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(username='admin').first()
if admin:
    print(f'Admin exists: {admin.username}')
    # Reset password if needed
    admin.set_password('your-new-password')
    admin.save()
    print('Password reset')
else:
    print('Admin user not found - restore may have failed')
"
```

---

## 🎓 What You're Testing

This test validates:

1. **Complete data capture** - Database + files in single backup
2. **Fast backup** - <5 second backup time
3. **Fast restore** - <30 second restore time  
4. **Data integrity** - All data restored exactly
5. **Functional recovery** - System fully operational after restore
6. **Automated process** - No manual intervention needed
7. **Production readiness** - Reliable for real disaster recovery

---

## 📚 Next Steps After Testing

### If Test PASSED ✅
1. Document results in test log
2. Schedule regular backup testing (monthly)
3. Verify automated cron backups working
4. Plan production backup strategy
5. Create disaster recovery procedures

### If Test FAILED ❌
1. Document failure details
2. Check logs: `docker compose -f docker-compose.prod.yml logs`
3. Review backup file integrity
4. Test individual components (DB restore, file restore)
5. Report issues for investigation

---

## 🔄 Automated Backup Verification

After manual testing, verify cron jobs:

```bash
# Check cron schedule
crontab -l

# Expected:
# 0 2 * * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 3 * * 0 cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 4 1 * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1

# Monitor backup logs
tail -f logs/backup.log

# Check when next backup will run
echo "Next daily backup: Tonight at 2:00 AM"
echo "Next weekly backup: Next Sunday at 3:00 AM"
echo "Next monthly backup: 1st of next month at 4:00 AM"
```

---

## 📞 Support

**Questions or Issues?**

Check documentation:
- `scripts/backup-hybrid.sh` - Backup script source
- `scripts/restore-hybrid.sh` - Restore script source
- `STAGING_DEPLOYMENT_SUCCESS_REPORT.md` - Deployment details

Check logs:
```bash
# Backup logs
cat logs/backup.log

# Container logs
docker compose -f docker-compose.prod.yml logs backend db

# System logs
journalctl -u docker -n 100
```

---

**Happy Testing! 🎉**

This comprehensive test will give you confidence that your backup/restore system is production-ready!
