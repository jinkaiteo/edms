# ⚡ Quick Start: Backup & Restore

**For**: Production deployment  
**Time**: 5 minutes  

---

## 🚀 Setup Automated Backups (3 steps)

### 1. Test Manual Backup
```bash
cd /home/jinkaiteo/Documents/QMS/QMS_04
./scripts/backup-hybrid.sh
```
✅ Should complete in ~1 second

### 2. Install Cron Jobs
```bash
./scripts/setup-backup-cron.sh
```
✅ Answer "yes" when prompted

### 3. Verify Installation
```bash
crontab -l | grep backup
```
✅ Should show 3 cron jobs (daily, weekly, monthly)

**Done!** Backups will run automatically at:
- 🌙 2:00 AM daily
- 🌙 3:00 AM Sunday (weekly)
- 🌙 4:00 AM 1st of month (monthly)

---

## 🔄 Restore from Backup (2 steps)

### 1. Choose Backup
```bash
ls -lh backups/backup_*.tar.gz
```

### 2. Run Restore
```bash
./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```
✅ Type "yes" when prompted  
✅ Wait ~9 seconds  
✅ Done!

---

## 📊 Monitor & Maintain

### View Logs
```bash
tail -f logs/backup.log
```

### List Backups
```bash
ls -lh backups/
```

### Cleanup Old Backups
```bash
./scripts/setup-backup-retention.sh
```

---

## 📞 Need Help?

**Full documentation**:
- `BACKUP_RESTORE_FINAL_SUMMARY.md` - Complete overview
- `CRON_BACKUP_SETUP_GUIDE.md` - Detailed setup guide
- `RESTORE_TEST_RESULTS.md` - Test results

**Common commands**:
```bash
# Manual backup
./scripts/backup-hybrid.sh

# Manual restore
./scripts/restore-hybrid.sh backups/[FILE]

# Check services
docker ps

# View logs
tail -f logs/backup.log
```

---

✅ **System Ready**: All tests passed, production-ready!
