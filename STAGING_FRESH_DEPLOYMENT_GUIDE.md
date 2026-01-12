# Staging Server Fresh Deployment Guide

**Date:** 2026-01-12  
**Purpose:** Reset staging server and deploy with all latest fixes  
**Includes:** Backup/restore fixes + UI improvements + customizable app title

---

## ✅ **What's Included in This Deployment**

### **Backend Fixes:**
1. ✅ Backup script reads credentials from `.env` (commit `363f96a`)
2. ✅ Restore script handles volume mounts correctly (commit `62ccf45`)
3. ✅ Improved error handling in restore (commit `ee83240`)
4. ✅ Storage permissions auto-setup (commit `3a3d3d2`)
5. ✅ Automated backup cron jobs (commit `197b597`)

### **Frontend Improvements:**
1. ✅ Create Document button only on My Tasks page (commit `29a3232`)
2. ✅ Last refresh timestamp indicator (commit `c7ed922`)
3. ✅ Rearranged header buttons for better UX (commit `7057a16`)
4. ✅ Customizable application title (commit `4c1cb78`)

### **Scripts Included:**
- ✅ `backup-hybrid.sh` - Fixed to use .env credentials
- ✅ `restore-hybrid.sh` - Fixed volume handling
- ✅ `document-system-state.sh` - State capture tool
- ✅ `validate-restore.sh` - Automated validation
- ✅ `deploy-interactive.sh` - Includes all fixes

---

## 🔄 **Quick Reset Instructions**

Run these commands on your **staging server**:

```bash
# Step 1: Navigate to EDMS directory
cd ~/edms

# Step 2: Stop all services
docker compose -f docker-compose.prod.yml down

# Step 3: Remove all volumes (DELETES ALL DATA!)
docker compose -f docker-compose.prod.yml down -v

# Step 4: Clean up orphaned volumes
docker volume prune -f

# Step 5: Remove storage files
sudo rm -rf storage/documents/*
sudo rm -rf storage/media/*
sudo rm -rf logs/*

# Step 6: Remove .env files
rm -f .env backend/.env

# Step 7: Remove existing cron jobs
crontab -l | grep -v "backup-hybrid.sh" | crontab -

# Step 8: Pull latest code (includes ALL fixes)
git pull origin develop

# Step 9: Verify latest commit
git log --oneline -1
# Should show: 4c1cb78 feat: Add customizable application title

# Step 10: Run interactive deployment
./deploy-interactive.sh
```

---

## 📋 **Deployment Prompts - What to Enter**

When the script prompts you:

### **1. Server Configuration**
```
? Server IP address [172.25.222.103]: <Press Enter>
? Server hostname: edms-staging-final
```

### **2. Application Branding** (NEW!)
```
? Application title [EDMS]: Tikva Quality Management System
```
*(Or press Enter to keep "EDMS")*

### **3. Port Configuration**
```
? Backend port [8001]: <Press Enter>
? Frontend port [3001]: <Press Enter>
? PostgreSQL port [5433]: <Press Enter>
? Redis port [6380]: <Press Enter>
```

### **4. Database Configuration**
```
? Database name: edms_final_test
? Database user: edms_final_user
? Database password: <enter secure 12+ char password>
? Confirm password: <re-enter password>
```

### **5. Security Configuration**
```
# SECRET_KEY and EDMS_MASTER_KEY auto-generated
? Session timeout (seconds) [3600]: <Press Enter>
```

### **6. HAProxy Configuration**
```
? Will you be using HAProxy? [y/N]: n
```

### **7. Monitoring**
```
? Enable Sentry error tracking? [y/N]: n
```

### **8. Configuration Summary**
- Review all settings
- Type `Y` to proceed

### **9. Admin User Creation**
```
? Admin username: admin
? Admin email: admin@staging.test
? Admin password: <enter 12+ char password>
? Confirm password: <re-enter password>
```

### **10. Backup Automation** (AUTOMATIC NOW!)
```
? Set up automated backups now? [Y/n]: Y
```

**The script will automatically:**
- ✅ Install 3 cron jobs (daily/weekly/monthly)
- ✅ Run test backup
- ✅ Show backup schedule and location

---

## ⏱️ **Expected Timeline**

| Phase | Time | What Happens |
|-------|------|--------------|
| Pre-flight checks | 10 seconds | Verify Docker, Python, Git |
| Configuration prompts | 2-3 minutes | Collect all settings |
| Docker deployment | 3-5 minutes | Build and start containers |
| Storage permissions | 10 seconds | Auto-detect UID and set permissions |
| Database initialization | 30-60 seconds | Migrations, defaults, workflows |
| Admin user creation | 30 seconds | Create admin account |
| Backup automation | 1-2 minutes | Install cron jobs + test backup |
| **Total Time** | **8-12 minutes** | Complete deployment |

---

## ✅ **Verification Steps**

After deployment completes:

### **1. Verify Containers**
```bash
docker compose -f docker-compose.prod.yml ps

# All should show "Up (healthy)":
# - edms_prod_backend
# - edms_prod_frontend
# - edms_prod_db
# - edms_prod_redis
# - edms_prod_celery_worker
# - edms_prod_celery_beat
```

### **2. Verify Backup System**
```bash
# Check cron jobs installed
crontab -l | grep backup-hybrid.sh
# Should show 3 lines

# Check backup files
ls -lh backups/
# Should show at least 1 backup file

# Test manual backup
./scripts/backup-hybrid.sh
# Should complete in <1 second
```

### **3. Verify Storage Permissions**
```bash
ls -la storage/
# Should show:
# drwxrwxr-x 2 995 995 ... documents/
# drwxrwxr-x 2 995 995 ... media/
```

### **4. Verify App Title** (if customized)
Open browser to `http://172.25.222.103:3001`
- Login page should show your custom title
- Sidebar should show your custom title
- When collapsed, should show first letter

### **5. Verify UI Improvements**
Navigate to different pages:
- **My Tasks** - Should have "📝 Create Document" button
- **Document Library** - No Create button
- **All pages** - Should show "🕐 Last refreshed: HH:MM:SS" after first refresh

---

## 🎯 **Post-Deployment Quick Test**

```bash
cd ~/edms

# 1. Create test state
./scripts/document-system-state.sh

# 2. Create backup
./scripts/backup-hybrid.sh

# 3. List backups
ls -lh backups/

# 4. Verify backup contents
LATEST=$(ls -t backups/backup_*.tar.gz | head -1)
tar -tzf "$LATEST"

# Should show:
# - database.dump
# - storage.tar.gz
# - manifest.json
```

---

## 📊 **Comparison: Old vs New**

### **What's Fixed Since Last Deployment**

| Issue | Before | After |
|-------|--------|-------|
| Backup credentials | Hardcoded `edms_user` | Reads from `.env` ✅ |
| Storage restore | "Device busy" error | Clears contents ✅ |
| Storage permissions | Manual setup needed | Auto-configured ✅ |
| Backup automation | Manual cron setup | Automatic installation ✅ |
| Create button | All pages | My Tasks only ✅ |
| Refresh indicator | None | Shows timestamp ✅ |
| Button layout | Confusing order | Logical flow ✅ |
| App title | Hardcoded "EDMS" | Customizable ✅ |

---

## 🔧 **Troubleshooting**

### **Issue: Git pull conflicts**
```bash
# Stash any local changes
git stash

# Pull latest
git pull origin develop

# If needed, drop stash
git stash drop
```

### **Issue: Docker build fails**
```bash
# Clean Docker cache
docker system prune -af

# Rebuild without cache
docker compose -f docker-compose.prod.yml build --no-cache
```

### **Issue: Backup test fails**
```bash
# Check .env has correct credentials
grep -E "DB_NAME|DB_USER" .env

# Manually test database connection
docker compose -f docker-compose.prod.yml exec db psql -U <your-db-user> -d <your-db-name> -c "SELECT 1;"
```

### **Issue: Storage permissions wrong**
```bash
# Get container UID
CONTAINER_UID=$(docker compose -f docker-compose.prod.yml exec backend id -u)

# Set permissions manually
sudo chown -R $CONTAINER_UID:$CONTAINER_UID storage/
sudo chmod -R 775 storage/
```

---

## 📝 **What to Test After Deployment**

### **Priority 1: Core Functionality**
- [ ] Login with admin credentials
- [ ] Navigate to My Tasks
- [ ] Click "Create Document" button (should work)
- [ ] Create a test document with file upload
- [ ] Verify file uploaded successfully

### **Priority 2: UI Improvements**
- [ ] Verify custom app title appears (if set)
- [ ] Click Refresh button
- [ ] Verify "Last refreshed" timestamp appears
- [ ] Navigate to Document Library
- [ ] Verify NO "Create Document" button
- [ ] Check button order: Refresh → Create → Views

### **Priority 3: Backup System**
- [ ] Run manual backup: `./scripts/backup-hybrid.sh`
- [ ] Verify backup file created
- [ ] Check cron jobs: `crontab -l`
- [ ] Test restore (optional): `./scripts/restore-hybrid.sh <backup-file>`

---

## 🎊 **Success Criteria**

Your deployment is successful when:

1. ✅ All 6 containers are running and healthy
2. ✅ Storage permissions are 995:995 with 775
3. ✅ 3 backup cron jobs are installed
4. ✅ Test backup completed successfully
5. ✅ Can login and create documents
6. ✅ UI improvements are visible
7. ✅ Custom app title appears (if configured)
8. ✅ No errors in logs

---

## 📚 **Related Documentation**

- `STAGING_SERVER_RESET_GUIDE.md` - Detailed reset procedure
- `BACKUP_RESTORE_TESTING_GUIDE.md` - Comprehensive backup testing
- `BACKUP_RESTORE_TEST_SUCCESS_REPORT.md` - Previous test results
- `STAGING_DEPLOYMENT_SUCCESS_REPORT.md` - Deployment documentation

---

## 🚀 **Quick Command Summary**

```bash
# Complete reset and deploy in one go:
cd ~/edms && \
docker compose -f docker-compose.prod.yml down -v && \
docker volume prune -f && \
sudo rm -rf storage/documents/* storage/media/* logs/* && \
rm -f .env backend/.env && \
crontab -l | grep -v "backup-hybrid.sh" | crontab - && \
git pull origin develop && \
./deploy-interactive.sh
```

---

**Ready to deploy? Run the commands and let me know if you encounter any issues!** 🎯
