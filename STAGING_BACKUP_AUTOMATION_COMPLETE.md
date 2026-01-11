# EDMS Staging - Automated Backup Setup Complete

**Date:** 2026-01-04  
**Server:** lims@172.28.1.148 (staging-server-ubuntu-20)  
**Status:** ✅ OPERATIONAL

---

## Automated Backup Configuration

### Schedule
- **Frequency:** Daily at 2:00 AM
- **Retention:** 14 days (automatic cleanup)
- **Cron:** `0 2 * * *`

### Backup Details
- **Container:** edms_prod_db
- **Database:** edms_production
- **User:** edms_prod_user
- **Location:** ~/edms-backups/
- **Log File:** ~/edms-backups/backup.log

### Expected Backup Size
- **Database:** ~400 KB
- **Storage:** ~5 MB (documents)
- **Total:** ~5.5 MB per backup
- **14 backups:** ~77 MB total storage

---

## Cron Configuration

```bash
# EDMS Automated Backup - Daily at 2 AM, Keep 14 days
0 2 * * * export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production' && /home/lims/edms-staging/scripts/backup-edms.sh && find $HOME/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +14 -exec rm -rf {} \; >> /home/lims/edms-backups/backup.log 2>&1
```

---

## Monitoring

### Check Backup Logs
```bash
ssh lims@172.28.1.148
tail -f ~/edms-backups/backup.log
```

### List Backups
```bash
ssh lims@172.28.1.148
ls -lth ~/edms-backups/ | head -15
```

### Verify Last Backup
```bash
ssh lims@172.28.1.148
cd ~/edms-staging
LATEST=$(ls -t ~/edms-backups/ | head -1)
./scripts/verify-backup.sh $LATEST
```

### Check Cron Status
```bash
ssh lims@172.28.1.148
crontab -l | grep backup
```

---

## Manual Backup

To create a backup manually at any time:

```bash
ssh lims@172.28.1.148
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db'
export POSTGRES_USER='edms_prod_user'
export POSTGRES_DB='edms_production'
./scripts/backup-edms.sh manual_backup_$(date +%Y%m%d_%H%M%S)
```

---

## Restore Procedure

### Emergency Restore

```bash
# 1. SSH to server
ssh lims@172.28.1.148

# 2. Navigate to directory
cd ~/edms-staging

# 3. List available backups
ls -lt ~/edms-backups/

# 4. Restore specific backup
export POSTGRES_CONTAINER='edms_prod_db'
export POSTGRES_USER='edms_prod_user'
export POSTGRES_DB='edms_production'
./scripts/restore-edms.sh <backup_name>

# 5. Restart services
docker restart edms_prod_backend

# 6. Verify
curl http://localhost:8000/health/
```

---

## Maintenance

### Adjust Retention Period

To change retention from 14 days to 30 days:

```bash
ssh lims@172.28.1.148

# Edit crontab
crontab -e

# Change: -mtime +14
# To:     -mtime +30
```

### Adjust Backup Schedule

Common schedules:

```bash
# Every 12 hours
0 2,14 * * *

# Every 6 hours  
0 */6 * * *

# Weekly (Sunday at 2 AM)
0 2 * * 0

# Twice daily (2 AM and 2 PM)
0 2,14 * * *
```

### Disable Automated Backups

```bash
ssh lims@172.28.1.148
crontab -l | grep -v 'backup-edms.sh' | crontab -
```

---

## Alerts & Notifications

### Setup Email Alerts (Optional)

```bash
# Install mailutils
sudo apt-get install mailutils

# Edit crontab and add email
crontab -e

# Add at top:
MAILTO=admin@example.com

# Cron will email on backup failures
```

### Monitoring Script

Create monitoring script to check backup age:

```bash
cat > ~/check_backup_age.sh << 'SCRIPT'
#!/bin/bash
LATEST=$(ls -t ~/edms-backups/ | head -1)
AGE=$(find ~/edms-backups/$LATEST -maxdepth 0 -mmin +1500 2>/dev/null)

if [ -n "$AGE" ]; then
    echo "WARNING: Last backup is older than 25 hours!"
    exit 1
fi

echo "OK: Recent backup found"
exit 0
SCRIPT

chmod +x ~/check_backup_age.sh

# Add to cron (check every hour)
(crontab -l; echo "0 * * * * ~/check_backup_age.sh") | crontab -
```

---

## Backup Storage Estimates

### Current State
- Backups created: Daily
- Retention: 14 days
- Expected total: ~77 MB

### Growth Projections
Assuming document storage grows 10 MB/month:

| Month | Backup Size | 14-Day Total |
|-------|-------------|--------------|
| Now | 5.5 MB | 77 MB |
| +3 months | 8.5 MB | 119 MB |
| +6 months | 11.5 MB | 161 MB |
| +1 year | 17.5 MB | 245 MB |

### Disk Space Check
```bash
ssh lims@172.28.1.148
df -h ~
du -sh ~/edms-backups/
```

---

## Testing

### Test Backup Notification

```bash
# Force backup to run now
ssh lims@172.28.1.148
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh test_notification
```

### Test Cron Execution

```bash
# Wait for next scheduled run (2 AM)
# Or manually trigger:
ssh lims@172.28.1.148
/bin/bash -c "export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production' && /home/lims/edms-staging/scripts/backup-edms.sh && find \$HOME/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +14 -exec rm -rf {} \; >> /home/lims/edms-backups/backup.log 2>&1"
```

---

## Troubleshooting

### Cron Not Running

```bash
# Check cron service
ssh lims@172.28.1.148
sudo systemctl status cron

# Check cron logs
sudo grep CRON /var/log/syslog | tail -20

# Verify crontab
crontab -l
```

### Backup Failures

```bash
# Check backup log
tail -50 ~/edms-backups/backup.log

# Test backup manually
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh test_debug
```

### Disk Space Issues

```bash
# Check disk space
df -h ~

# List large backups
du -sh ~/edms-backups/* | sort -h

# Manually clean old backups
find ~/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +30 -exec rm -rf {} \;
```

---

## Success Criteria

✅ **All criteria met:**

- [x] Cron job installed and active
- [x] Daily backup schedule (2 AM)
- [x] 14-day retention configured
- [x] Logging enabled
- [x] Manual backup tested successfully
- [x] Automated backup script tested
- [x] Verification script validated
- [x] Restore procedure documented

---

## Next Review

- **Date:** 2026-01-18 (2 weeks)
- **Check:** Verify 14 backups exist
- **Verify:** Total storage < 100 MB
- **Test:** Perform test restore

---

**Status:** ✅ AUTOMATED BACKUPS ACTIVE AND OPERATIONAL

