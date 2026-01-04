# GitHub Wiki Setup Guide for EDMS

**Repository:** https://github.com/jinkaiteo/edms  
**Wiki URL:** https://github.com/jinkaiteo/edms/wiki  
**Date:** 2026-01-04

---

## Step 1: Enable GitHub Wiki

1. Go to your repository: https://github.com/jinkaiteo/edms
2. Click **Settings** (top right)
3. Scroll down to **Features** section
4. Check the box next to **Wikis**
5. Click **Save** (if needed)

---

## Step 2: Access Wiki

1. Click the **Wiki** tab in your repository
2. You'll see "Create the first page" button
3. Click it to create the Home page

---

## Step 3: Create Home Page

Use this content for your Wiki home page:

```markdown
# EDMS Documentation

Welcome to the Electronic Document Management System (EDMS) documentation!

## Quick Links

### For Users
- [Backup & Restore Guide](Backup-and-Restore-Guide)
- [User Guide](User-Guide)
- [Troubleshooting](Troubleshooting)

### For Administrators
- [Deployment Guide](Deployment-Guide)
- [Configuration Guide](Configuration-Guide)
- [Automated Backups](Automated-Backups)

### For Developers
- [API Documentation](API-Documentation)
- [Development Setup](Development-Setup)
- [Architecture Overview](Architecture-Overview)

## Getting Help

- **System Version:** 2.0
- **Method #2 Backup:** PostgreSQL pg_dump (200-600x faster)
- **Support:** Create an issue on GitHub

## Recent Updates

- **2026-01-04:** Implemented Method #2 backup system
- **2026-01-04:** Removed Django backup app (8,000+ lines)
- **2026-01-04:** Setup automated backups (daily at 2 AM)

---

**Last Updated:** 2026-01-04  
**Maintained by:** EDMS Team
```

Click **Save Page**

---

## Step 4: Create Key Documentation Pages

### Page 1: Backup and Restore Guide

1. Click **New Page** button
2. Title: `Backup-and-Restore-Guide`
3. Copy content from: `docs/BACKUP_RESTORE_USER_GUIDE.md`
4. Click **Save Page**

### Page 2: Troubleshooting

1. Click **New Page**
2. Title: `Troubleshooting`
3. Content:

```markdown
# Troubleshooting Guide

## Backup Issues

### Problem: "PostgreSQL container not running"
**Solution:**
\`\`\`bash
docker ps | grep postgres
docker compose -f docker-compose.prod.yml up -d postgres
\`\`\`

### Problem: "Permission denied"
**Solution:**
\`\`\`bash
chmod +x ~/edms-staging/scripts/backup-edms.sh
\`\`\`

## Restore Issues

### Problem: "Database has active connections"
**Solution:**
\`\`\`bash
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
\`\`\`

## Common Questions

**Q: How long are backups kept?**  
A: 14 days by default (automatic cleanup)

**Q: Can I restore to a different server?**  
A: Yes, just copy the backup directory and run restore script

**Q: Where are backups stored?**  
A: `/home/lims/edms-backups/`

---

For more help, see [Backup & Restore Guide](Backup-and-Restore-Guide)
```

4. Click **Save Page**

### Page 3: Quick Reference

1. Click **New Page**
2. Title: `Quick-Reference`
3. Content:

```markdown
# Quick Reference

## Essential Commands

### Create Backup
\`\`\`bash
cd ~/edms-staging
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
./scripts/backup-edms.sh backup_$(date +%Y%m%d_%H%M%S)
\`\`\`

### List Backups
\`\`\`bash
ls -lt ~/edms-backups/
\`\`\`

### Verify Backup
\`\`\`bash
cd ~/edms-staging
./scripts/verify-backup.sh backup_name
\`\`\`

### Restore Backup
\`\`\`bash
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_production'
echo 'YES' | ./scripts/restore-edms.sh backup_name
docker compose -f docker-compose.prod.yml up -d
\`\`\`

### Check Logs
\`\`\`bash
tail -f ~/edms-backups/backup.log
\`\`\`

### Check Cron
\`\`\`bash
crontab -l | grep backup
\`\`\`

## Server Access

**Staging Server:**
- Host: 172.28.1.148
- User: lims
- Path: ~/edms-staging

**Connection:**
\`\`\`bash
ssh lims@172.28.1.148
\`\`\`

## Important Paths

- Backups: `~/edms-backups/`
- Application: `~/edms-staging/`
- Scripts: `~/edms-staging/scripts/`
- Logs: `~/edms-backups/backup.log`

## Configuration

**Database:**
- Container: edms_prod_db
- User: edms_prod_user
- Database: edms_production

**Automated Backups:**
- Schedule: Daily at 2:00 AM
- Retention: 14 days
- Cron: Active

---

For detailed instructions, see [Backup & Restore Guide](Backup-and-Restore-Guide)
```

4. Click **Save Page**

---

## Step 5: Organize Wiki Sidebar

1. Click **Edit Sidebar** (if available)
2. Add navigation structure:

```markdown
### User Documentation
- [Home](Home)
- [Backup & Restore](Backup-and-Restore-Guide)
- [Troubleshooting](Troubleshooting)
- [Quick Reference](Quick-Reference)

### Admin Documentation
- [Deployment](Deployment-Guide)
- [Configuration](Configuration-Guide)

### Developer Documentation
- [API Docs](API-Documentation)
- [Architecture](Architecture-Overview)
```

---

## Step 6: Upload Documentation Files

You can either:

### Option A: Copy-Paste (Easy)
- Copy content from markdown files in `docs/` folder
- Paste into Wiki pages manually
- Good for initial setup

### Option B: Clone Wiki Repo (Advanced)
```bash
git clone https://github.com/jinkaiteo/edms.wiki.git
cd edms.wiki
# Copy markdown files
cp ~/edms/docs/BACKUP_RESTORE_USER_GUIDE.md Backup-and-Restore-Guide.md
# Edit to fix any formatting
git add .
git commit -m "Add backup/restore documentation"
git push
```

---

## Step 7: Verify Help Icon Works

1. Push changes to GitHub:
   ```bash
   git push origin develop
   ```

2. Deploy to staging:
   ```bash
   ssh lims@172.28.1.148
   cd ~/edms-staging
   git pull origin develop
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d frontend
   ```

3. Test:
   - Login to EDMS: http://172.28.1.148:3001
   - Look for **?** icon in top right
   - Click it - should open Wiki in new tab

---

## Wiki Page Naming Convention

GitHub Wiki converts page titles to URL-friendly names:

- "Backup & Restore Guide" → `Backup-and-Restore-Guide`
- "Quick Reference" → `Quick-Reference`
- "API Documentation" → `API-Documentation`

Use hyphens for multi-word pages.

---

## Documentation Files to Upload

From your repository, create Wiki pages from these files:

| File | Wiki Page Name |
|------|----------------|
| `docs/BACKUP_RESTORE_USER_GUIDE.md` | Backup-and-Restore-Guide |
| `docs/BACKUP_RESTORE_METHOD2.md` | Technical-Backup-Documentation |
| `docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md` | Deployment-Guide |
| `STAGING_BACKUP_AUTOMATION_COMPLETE.md` | Automated-Backups |
| `README.md` | System-Overview |

---

## Maintenance

### Update Wiki Content
1. Go to Wiki page
2. Click **Edit** button
3. Make changes
4. Click **Save Page**

### Version Control
GitHub Wiki has its own git repository:
```bash
git clone https://github.com/jinkaiteo/edms.wiki.git
```

All Wiki changes are version controlled!

---

## Quick Setup Checklist

- [ ] Enable Wiki in repository settings
- [ ] Create Home page with navigation
- [ ] Create Backup & Restore Guide page
- [ ] Create Troubleshooting page
- [ ] Create Quick Reference page
- [ ] Test Help icon in EDMS app
- [ ] Add more pages as needed

---

## Next Steps

1. **Enable Wiki** (5 minutes)
2. **Create Home page** (5 minutes)
3. **Create 3-5 key pages** (30 minutes)
4. **Test Help icon** (2 minutes)
5. **Deploy to staging** (10 minutes)

Total time: ~1 hour for complete setup

---

**Wiki URL:** https://github.com/jinkaiteo/edms/wiki  
**Repository:** https://github.com/jinkaiteo/edms  
**Help Icon:** Already configured in `frontend/src/components/common/Layout.tsx`

---

**Ready to go! Enable the Wiki and start adding documentation!**
