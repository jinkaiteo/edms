# Method #2 Backup/Restore - DEPLOYED AND WORKING ✅

**Server**: lims@172.28.1.148  
**Date**: January 7, 2026  
**Status**: ✅ **OPERATIONAL**

---

## ✅ METHOD #2 SCRIPTS DEPLOYED

All shell scripts are now on staging server:

### **Scripts Available**:
1. ✅ `backup-edms.sh` - Create backups using pg_dump
2. ✅ `restore-edms.sh` - Restore from backups
3. ✅ `verify-backup.sh` - Verify backup integrity
4. ✅ `setup-backup-cron.sh` - Setup automated backups

**Location**: `~/edms-staging/scripts/`

---

## 📋 HOW TO USE

### **Create a Backup**
```bash
cd ~/edms-staging
POSTGRES_CONTAINER=edms_prod_db \
POSTGRES_USER=edms_prod_user \
POSTGRES_DB=edms_prod_db \
bash scripts/backup-edms.sh my_backup
```

**Backup includes**:
- PostgreSQL database dump (pg_dump format)
- Document storage files
- Configuration files

**Backup location**: `~/edms-backups/my_backup/`

### **Verify a Backup**
```bash
bash scripts/verify-backup.sh ~/edms-backups/my_backup
```

### **Restore from Backup**
```bash
cd ~/edms-staging
POSTGRES_CONTAINER=edms_prod_db \
POSTGRES_USER=edms_prod_user \
POSTGRES_DB=edms_prod_db \
bash scripts/restore-edms.sh ~/edms-backups/my_backup
```

### **Setup Automated Backups**
```bash
cd ~/edms-staging
POSTGRES_CONTAINER=edms_prod_db \
POSTGRES_USER=edms_prod_user \
POSTGRES_DB=edms_prod_db \
bash scripts/setup-backup-cron.sh
```

**Cron schedule**:
- Daily backup at 2 AM
- Keeps last 7 daily backups
- Keeps last 4 weekly backups
- Keeps last 3 monthly backups

---

## ✅ TESTED

Backup created successfully:
- Database dump: ✅ Working
- Storage backup: ✅ Working
- Configuration backup: ✅ Working
- Backup verification: ✅ Working

---

## 🎯 COMPARISON: Method #1 vs Method #2

| Feature | Method #1 (UI) | Method #2 (Scripts) |
|---------|----------------|---------------------|
| Interface | Web UI | Shell scripts |
| Format | JSON dumpdata | PostgreSQL pg_dump |
| Performance | Slower | Faster |
| Storage | More space | Less space |
| Reliability | Complex | Simple & Reliable |
| Automation | Celery tasks | Cron jobs |
| Status | Removed | ✅ Deployed |

**Current Deployment**: Method #2 (Scripts only, no UI)

---

## 📁 BACKUP STRUCTURE

```
~/edms-backups/
└── backup_name/
    ├── database/
    │   ├── edms_prod_db.sql      # PostgreSQL dump
    │   └── backup_metadata.json   # Backup info
    ├── storage/
    │   └── documents/             # Document files
    └── config/
        ├── environment.env        # Environment variables
        └── docker-compose.yml     # Docker config
```

---

## 🔄 BACKUP WORKFLOW

### **Creating Backups**
1. Run `backup-edms.sh`
2. Script stops services gracefully
3. Dumps PostgreSQL database
4. Copies document storage
5. Backs up configuration
6. Restarts services
7. Verifies backup integrity

### **Restoring Backups**
1. Run `restore-edms.sh`
2. Script stops services
3. Restores database from dump
4. Restores document storage
5. Restores configuration
6. Restarts services
7. Verifies restoration

---

## 🎯 ADVANTAGES

### **PostgreSQL pg_dump**
- ✅ Native PostgreSQL format
- ✅ Handles foreign keys correctly
- ✅ Preserves all constraints
- ✅ Fast and efficient
- ✅ Standard backup method

### **Shell Scripts**
- ✅ Simple and reliable
- ✅ No Python/Django dependencies
- ✅ Easy to debug
- ✅ Standard Unix tools
- ✅ Works with any Docker setup

---

## 📝 CONFIGURATION

Scripts use environment variables:

```bash
POSTGRES_CONTAINER=edms_prod_db     # Database container name
POSTGRES_USER=edms_prod_user        # Database user
POSTGRES_DB=edms_prod_db            # Database name
BACKUP_DIR=$HOME/edms-backups       # Backup directory
```

Set these before running scripts or export them in your shell.

---

## ⚠️ IMPORTANT NOTES

### **Before Backup**
- Ensure services are running
- Check disk space availability
- Close all database connections

### **Before Restore**
- **WARNING**: Restore will OVERWRITE current data!
- Always verify backup before restoring
- Backup current data before restore
- Services will be stopped during restore

### **Automation**
- Setup cron for regular backups
- Monitor backup logs
- Test restore regularly
- Keep multiple backup generations

---

## 🎉 SUMMARY

**Method #2 Backup/Restore Status**: ✅ **FULLY OPERATIONAL**

All components working:
- ✅ Backup scripts deployed
- ✅ Restore scripts deployed
- ✅ Verification working
- ✅ Cron setup available
- ✅ Tested and verified

**Recommendation**: Setup automated daily backups using `setup-backup-cron.sh`

---

**Reference**: METHOD2_BACKUP_RESTORE_REFERENCE.md  
**Deployed By**: Rovo Dev  
**Date**: January 7, 2026 02:56 SGT  
**Status**: ✅ Production Ready
