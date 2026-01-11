# Automated Backup Setup Guide

## ✅ Cron Job Configuration for EDMS Backups

This guide explains how to set up automated backups using host-level cron jobs.

---

## 📋 Prerequisites

- EDMS running in Docker containers
- Shell access to host system
- Sufficient disk space in `backups/` directory

---

## 🚀 Quick Setup

### Option 1: Automated Installation

Run the setup script:

```bash
cd /path/to/edms/project
./scripts/setup-backup-cron.sh
```

This will:
1. Detect your project directory
2. Create log directory if needed
3. Show proposed cron jobs
4. Ask for confirmation
5. Install cron jobs for you

### Option 2: Manual Installation

1. **Edit your crontab**:
   ```bash
   crontab -e
   ```

2. **Add these lines** (adjust path to your project):
   ```cron
   # EDMS Automated Backups
   0 2 * * * cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
   0 3 * * 0 cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
   0 4 1 * * cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
   ```

3. **Save and exit** (in vim: `:wq`, in nano: `Ctrl+X`, `Y`, `Enter`)

---

## 📅 Backup Schedule

| Frequency | Time | Day | Description |
|-----------|------|-----|-------------|
| **Daily** | 2:00 AM | Every day | Regular daily backup |
| **Weekly** | 3:00 AM | Sunday | Weekly backup (retention) |
| **Monthly** | 4:00 AM | 1st of month | Monthly backup (long-term) |

---

## 🔍 Verification

### Check Installed Cron Jobs
```bash
crontab -l | grep backup
```

Expected output:
```
0 2 * * * cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
0 3 * * 0 cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
0 4 1 * * cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
```

### Test Manual Backup
```bash
cd /path/to/edms/project
./scripts/backup-hybrid.sh
```

Expected output:
```
[2026-01-11 22:47:48] ============================================
[2026-01-11 22:47:48] EDMS Hybrid Backup - Starting
[2026-01-11 22:47:48] ============================================
[2026-01-11 22:47:48] Step 1/4: Backing up database...
[2026-01-11 22:47:48] ✅ Database backup complete: 388K
[2026-01-11 22:47:48] Step 2/4: Backing up media files...
[2026-01-11 22:47:48] ✅ Media files backup complete: 4.0K
[2026-01-11 22:47:48] Step 3/4: Creating manifest...
[2026-01-11 22:47:48] ✅ Manifest created
[2026-01-11 22:47:48] Step 4/4: Creating final archive...
[2026-01-11 22:47:48] ✅ Archive created: backup_20260111_224748.tar.gz (76K)
```

### Monitor Backup Logs
```bash
tail -f logs/backup.log
```

---

## 📁 Backup Storage

### Location
```
backups/
├── backup_20260111_222335.tar.gz  (680K)
├── backup_20260111_224748.tar.gz  (73K)
└── backup_20260112_020000.tar.gz  (scheduled)
```

### Retention Policy

Run the cleanup script to maintain retention:
```bash
./scripts/setup-backup-retention.sh
```

**Current Policy**:
- Keep last **7 daily** backups
- Keep last **4 weekly** backups  
- Keep last **12 monthly** backups

To automate cleanup, add to crontab:
```cron
0 5 * * * cd /home/jinkaiteo/Documents/QMS/QMS_04 && ./scripts/setup-backup-retention.sh >> logs/backup-cleanup.log 2>&1
```

---

## 🔧 Troubleshooting

### Cron Jobs Not Running

**Problem**: Backups not appearing in `backups/` directory

**Solutions**:
1. Check cron service is running:
   ```bash
   systemctl status cron  # or 'crond' on some systems
   ```

2. Check log file for errors:
   ```bash
   cat logs/backup.log
   ```

3. Verify script permissions:
   ```bash
   ls -lh scripts/backup-hybrid.sh
   # Should show: -rwxrwxr-x (executable)
   ```

4. Test script manually:
   ```bash
   cd /path/to/project && ./scripts/backup-hybrid.sh
   ```

### Permission Errors

**Problem**: `Permission denied` when running script

**Solution**:
```bash
chmod +x scripts/backup-hybrid.sh
chmod +x scripts/restore-hybrid.sh
```

### Docker Not Found

**Problem**: Cron job fails with "docker: command not found"

**Solution**: Add docker path to cron job:
```cron
0 2 * * * cd /path/to/project && PATH=/usr/local/bin:/usr/bin:/bin && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
```

### Disk Space Issues

**Problem**: Backups filling up disk

**Solutions**:
1. Implement retention policy (see above)
2. Compress older backups further
3. Move old backups to remote storage
4. Increase disk space

---

## 🔄 Restore Procedures

### Manual Restore

1. **List available backups**:
   ```bash
   ls -lh backups/backup_*.tar.gz
   ```

2. **Run restore script**:
   ```bash
   ./scripts/restore-hybrid.sh backups/backup_20260111_224748.tar.gz
   ```

3. **Confirm when prompted**:
   ```
   ⚠️  WARNING: This will overwrite the current database and media files!
   
   Are you sure you want to continue? (yes/no): yes
   ```

4. **Wait for completion**:
   ```
   [2026-01-11 22:51:17] ✅ Database restored
   [2026-01-11 22:51:21] ✅ Media files restored
   [2026-01-11 22:51:21] ✅ Services restarted
   ```

### Verify Restore

**Check database**:
```bash
docker compose exec db psql -U edms_user -d edms_db -c "SELECT COUNT(*) FROM users;"
```

**Check files**:
```bash
docker compose exec backend ls -lh /app/storage/
```

**Check application**:
```bash
curl http://localhost:8000/health/
```

---

## 📊 Backup Contents

Each backup archive contains:

```
backup_YYYYMMDD_HHMMSS.tar.gz
└── tmp_YYYYMMDD_HHMMSS/
    ├── database.dump       # PostgreSQL custom format dump
    ├── storage.tar.gz      # All uploaded files and media
    └── manifest.json       # Backup metadata
```

**Manifest Example**:
```json
{
    "timestamp": "2026-01-11T22:47:48+08:00",
    "database": "database.dump",
    "storage": "storage.tar.gz",
    "version": "49b0445578f2227b4244c57e92a2c3b5caaeb742",
    "backup_type": "full",
    "created_by": "backup-hybrid.sh"
}
```

---

## ⚡ Performance

- **Backup time**: ~1 second
- **Restore time**: ~9 seconds
- **Archive size**: 70K - 700K (depends on data)
- **CPU impact**: Minimal (runs during off-hours)
- **Disk I/O**: Low (compressed archives)

---

## 🔒 Security Considerations

### Backup File Permissions

Ensure backups are protected:
```bash
chmod 600 backups/backup_*.tar.gz
```

### Remote Backup Storage

For production, consider copying backups to remote storage:

```bash
# Add to crontab after backup
30 2 * * * rsync -avz backups/ user@remote:/backup/edms/
```

Or use cloud storage:
```bash
30 2 * * * aws s3 sync backups/ s3://your-bucket/edms-backups/
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `tail -f logs/backup.log`
2. Verify Docker services: `docker compose ps`
3. Test manual backup: `./scripts/backup-hybrid.sh`
4. Review this guide for common issues

---

## ✅ Checklist

- [ ] Cron jobs installed (`crontab -l`)
- [ ] Log directory created (`logs/`)
- [ ] Backup script executable (`chmod +x scripts/backup-hybrid.sh`)
- [ ] Manual backup tested successfully
- [ ] Restore procedure tested
- [ ] Retention policy configured
- [ ] Monitoring in place

---

**Last Updated**: January 11, 2026  
**Status**: Production Ready ✅
