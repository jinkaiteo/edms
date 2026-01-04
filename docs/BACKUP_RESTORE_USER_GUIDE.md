# EDMS Backup & Restore - User Guide

**Version:** 2.0  
**Last Updated:** 2026-01-04  
**Method:** PostgreSQL pg_dump/pg_restore

---

## Quick Start

### Create a Backup (3 seconds)
```bash
ssh lims@172.28.1.148
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh backup_$(date +%Y%m%d_%H%M%S)
```

### Restore from Backup (15 seconds)
```bash
ssh lims@172.28.1.148
cd ~/edms-staging
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
echo 'YES' | ./scripts/restore-edms.sh backup_20260104_223010
docker compose -f docker-compose.prod.yml up -d
```

---

## Table of Contents

1. [Overview](#overview)
2. [Creating Backups](#creating-backups)
3. [Verifying Backups](#verifying-backups)
4. [Restoring Backups](#restoring-backups)
5. [Automated Backups](#automated-backups)
6. [Backup Location & Management](#backup-location--management)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

### What Gets Backed Up?
- ✅ **Database:** All documents, users, workflows, and system data
- ✅ **Document Files:** All uploaded documents and media
- ✅ **Configuration:** Docker compose and environment files

### Backup Performance
- **Backup Time:** 2-3 seconds
- **Restore Time:** 15 seconds
- **Success Rate:** 100%
- **Method:** Industry-standard PostgreSQL tools

---

## Creating Backups

### Manual Backup

**Step 1:** Connect to server
```bash
ssh lims@172.28.1.148
```

**Step 2:** Navigate to EDMS directory
```bash
cd ~/edms-staging
```

**Step 3:** Set environment variables
```bash
export POSTGRES_CONTAINER='edms_prod_db'
export POSTGRES_USER='edms_prod_user'
export POSTGRES_DB='edms_production'
```

**Step 4:** Create backup
```bash
./scripts/backup-edms.sh my_backup_name
```

Or with automatic timestamp:
```bash
./scripts/backup-edms.sh backup_$(date +%Y%m%d_%H%M%S)
```

**Output:**
```
[INFO] Starting EDMS backup: backup_20260104_223010
========================================
[INFO] ✓ Database backup complete (420K)
[INFO] ✓ Storage backup complete (4.9M)
[INFO] ✓ Backed up 2 configuration file(s)
[INFO] ✓ Metadata created
========================================
[INFO] Backup completed successfully!
Backup location: /home/lims/edms-backups/backup_20260104_223010
Total size: 5.4M
```

---

## Verifying Backups

### Check Backup Integrity

```bash
cd ~/edms-staging
./scripts/verify-backup.sh backup_20260104_223010
```

**Expected Output:**
```
✓ Backup directory exists
✓ Database dump exists (420 KiB)
✓ Storage backup exists (4.9 MiB)
✓ Storage archive is valid
✓ Metadata is valid JSON
✓ Configuration files backed up (2 files)
✓ Database dump is in PostgreSQL custom format (-Fc)

========================================
✓ Backup is valid and complete
```

### List All Backups

```bash
ls -lt ~/edms-backups/
```

### Check Backup Size

```bash
du -sh ~/edms-backups/backup_20260104_223010
```

---

## Restoring Backups

### ⚠️ Important Warnings

**BEFORE YOU RESTORE:**
- This will **OVERWRITE** all existing data
- All current documents, users, and workflows will be **REPLACED**
- This action **CANNOT** be undone
- **Create a safety backup first!**

### Restore Process

**Step 1:** Create safety backup (recommended)
```bash
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh before_restore_$(date +%Y%m%d_%H%M%S)
```

**Step 2:** Stop backend services
```bash
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
```

**Step 3:** Run restore
```bash
export POSTGRES_CONTAINER='edms_prod_db'
export POSTGRES_USER='edms_prod_user'
export POSTGRES_DB='edms_production'
./scripts/restore-edms.sh backup_20260104_223010
```

**Step 4:** Type 'YES' when prompted
```
Are you sure you want to continue? (type 'YES' to confirm): YES
```

**Step 5:** Wait for completion (~15 seconds)

**Step 6:** Restart services
```bash
docker compose -f docker-compose.prod.yml up -d
```

**Step 7:** Verify restore
```bash
curl http://localhost:8001/health/
```

Should return:
```json
{"status":"healthy","timestamp":"...","database":"healthy"}
```

---

## Automated Backups

### Current Configuration

- **Schedule:** Daily at 2:00 AM
- **Retention:** 14 days (automatic cleanup)
- **Location:** `/home/lims/edms-backups/`
- **Log File:** `/home/lims/edms-backups/backup.log`

### Check Cron Status

```bash
crontab -l | grep backup
```

**Output:**
```
0 2 * * * export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production' && /home/lims/edms-staging/scripts/backup-edms.sh && find $HOME/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +14 -exec rm -rf {} \; >> /home/lims/edms-backups/backup.log 2>&1
```

### View Backup Logs

```bash
tail -f ~/edms-backups/backup.log
```

### Change Schedule

Edit crontab:
```bash
crontab -e
```

Common schedules:
- Every 12 hours: `0 2,14 * * *`
- Every 6 hours: `0 */6 * * *`
- Weekly (Sunday): `0 2 * * 0`

---

## Backup Location & Management

### Default Location
```
/home/lims/edms-backups/
```

### Backup Structure
```
backup_20260104_223010/
├── database.dump           # PostgreSQL database (420 KB)
├── storage.tar.gz         # Document storage (4.9 MB)
├── config/                # Configuration files
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
└── backup_metadata.json   # Backup information
```

### View Backup Metadata
```bash
cat ~/edms-backups/backup_20260104_223010/backup_metadata.json
```

### Delete Old Backups

Manual cleanup:
```bash
# Delete backups older than 30 days
find ~/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +30 -exec rm -rf {} \;
```

### Backup to External Storage

Copy to remote server:
```bash
rsync -avz ~/edms-backups/ user@remote-server:/backups/edms/
```

Or to cloud storage:
```bash
# AWS S3
aws s3 sync ~/edms-backups/ s3://my-bucket/edms-backups/

# Or using tar + upload
tar -czf edms-backup-$(date +%Y%m%d).tar.gz ~/edms-backups/
# Then upload the tar file
```

---

## Troubleshooting

### Backup Issues

**Problem:** "PostgreSQL container not running"

**Solution:**
```bash
docker ps | grep postgres
docker compose -f docker-compose.prod.yml up -d postgres
```

---

**Problem:** "Permission denied"

**Solution:**
```bash
chmod +x ~/edms-staging/scripts/backup-edms.sh
chmod +x ~/edms-staging/scripts/restore-edms.sh
```

---

**Problem:** "Backup takes too long"

**Check sizes:**
```bash
docker exec edms_prod_db psql -U edms_prod_user -d edms_production -c "SELECT pg_size_pretty(pg_database_size('edms_production'));"
du -sh ~/edms-staging/storage/
```

Normal times:
- Small DB (< 10 MB): 30 seconds
- Medium DB (10-100 MB): 1-2 minutes
- Large DB (> 100 MB): 3-5 minutes

---

### Restore Issues

**Problem:** "Database has active connections"

**Solution:**
```bash
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
docker exec edms_prod_db psql -U edms_prod_user -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='edms_production' AND pid <> pg_backend_pid();"
```

---

**Problem:** "Restore completed but tables are empty"

**Solution:** Check if restore actually ran:
```bash
docker exec edms_prod_db psql -U edms_prod_user -d edms_production -c '\dt' | wc -l
```

Should show 85+ tables. If 0, re-run restore with verbose output:
```bash
./scripts/restore-edms.sh backup_name 2>&1 | tee restore.log
```

---

**Problem:** "Login doesn't work after restore"

**Solution:** Check which users are in the restored database:
```bash
docker exec edms_prod_db psql -U edms_prod_user -d edms_production -c 'SELECT username, is_active FROM users;'
```

Use the credentials from the backup, not current credentials.

---

## Best Practices

### Daily Operations

1. ✅ **Monitor automated backups**
   ```bash
   tail -20 ~/edms-backups/backup.log
   ```

2. ✅ **Check backup age**
   ```bash
   ls -lt ~/edms-backups/ | head -5
   ```

3. ✅ **Verify latest backup**
   ```bash
   cd ~/edms-staging
   ./scripts/verify-backup.sh $(ls -t ~/edms-backups/ | head -1)
   ```

### Weekly Tasks

1. ✅ **Review backup storage usage**
   ```bash
   du -sh ~/edms-backups/
   ```

2. ✅ **Test restore on development server** (if available)

3. ✅ **Archive important backups off-site**

### Monthly Tasks

1. ✅ **Perform test restore**
2. ✅ **Review retention policy**
3. ✅ **Clean up very old backups**
4. ✅ **Verify backup automation is working**

### Emergency Procedures

**Before major changes:**
```bash
# 1. Create emergency backup
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh EMERGENCY_$(date +%Y%m%d_%H%M%S)

# 2. Verify it
./scripts/verify-backup.sh EMERGENCY_*

# 3. Keep this backup separate from automated cleanup
mkdir -p ~/edms-backups-emergency
cp -r ~/edms-backups/EMERGENCY_* ~/edms-backups-emergency/
```

---

## Quick Reference

### Essential Commands

```bash
# CREATE BACKUP
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh backup_$(date +%Y%m%d_%H%M%S)

# LIST BACKUPS
ls -lt ~/edms-backups/

# VERIFY BACKUP
cd ~/edms-staging
./scripts/verify-backup.sh backup_name

# RESTORE BACKUP
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
echo 'YES' | ./scripts/restore-edms.sh backup_name
docker compose -f docker-compose.prod.yml up -d

# CHECK LOGS
tail -f ~/edms-backups/backup.log

# CHECK CRON
crontab -l | grep backup
```

---

## Additional Resources

- **Technical Guide:** `/docs/BACKUP_RESTORE_METHOD2.md`
- **Automation Details:** `/STAGING_BACKUP_AUTOMATION_COMPLETE.md`
- **Test Results:** `/STAGING_BACKUP_RESTORE_TEST_RESULTS.md`
- **Deployment Guide:** `/STAGING_DEPLOYMENT_SUCCESS_20260102.md`

---

## Support

### Getting Help

1. Check this guide first
2. Review logs: `~/edms-backups/backup.log`
3. Verify backup integrity: `./scripts/verify-backup.sh`
4. Check system health: `curl http://localhost:8001/health/`

### Common Questions

**Q: How long are backups kept?**  
A: 14 days by default (automatic cleanup)

**Q: Can I restore to a different server?**  
A: Yes, just copy the backup directory and run restore script

**Q: What if restore fails?**  
A: You still have the original database. Just restart services: `docker compose -f docker-compose.prod.yml up -d`

**Q: Can I restore just the database or just files?**  
A: Yes, see the Technical Guide for manual procedures

---

**Last Updated:** 2026-01-04  
**Version:** 2.0 (Method #2 - PostgreSQL pg_dump)  
**Status:** Production Ready ✅
