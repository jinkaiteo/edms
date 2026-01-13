# Staging Server Reset & Updated Script Testing Guide

## 🎯 Objective

Reset your staging server to a clean state and test the updated `deploy-interactive.sh` script with:
- ✅ Automatic storage permissions setup (UID 995)
- ✅ Automatic backup cron jobs installation
- ✅ DB_HOST fix (db instead of postgres)

---

## ⚠️ WARNING: Data Loss

**This will delete ALL data on staging server!**

- All documents will be deleted
- All users will be deleted  
- All workflows will be deleted
- Database will be wiped

**Only do this on staging server, NOT production!**

---

## 🔄 Phase 1: Backup Current State (Optional, 2 minutes)

If you want to preserve current staging data:

```bash
# On staging server
cd ~/edms

# Create backup
./scripts/backup-hybrid.sh

# Copy backup to safe location
cp backups/backup_*.tar.gz ~/edms-staging-backup-$(date +%Y%m%d).tar.gz

# Or copy to your local machine
# From local: scp user@172.25.222.103:~/edms/backups/backup_*.tar.gz ./
```

---

## 🧹 Phase 2: Complete System Reset (5 minutes)

### Step 1: Stop All Containers

```bash
# On staging server
cd ~/edms

# Stop all services
docker compose -f docker-compose.prod.yml down

# Verify all stopped
docker ps | grep edms_prod
# Should show nothing
```

### Step 2: Remove All Volumes

```bash
# Remove Docker volumes (deletes all data!)
docker compose -f docker-compose.prod.yml down -v

# Verify volumes removed
docker volume ls | grep edms
# Should show nothing or only old volumes
```

### Step 3: Clean Data Directories

```bash
# Remove storage files
sudo rm -rf storage/*

# Remove logs
sudo rm -rf logs/*

# Remove backups (optional - keep if you want)
# sudo rm -rf backups/*

# Remove environment file
rm -f backend/.env

# Remove any backup environment files
rm -f backend/.env.backup.*

# Verify clean
ls -la storage/
ls -la logs/
ls -la backend/.env
# All should show empty or "No such file"
```

### Step 4: Remove Docker Images (Optional)

```bash
# Remove built images to force complete rebuild
docker images | grep edms

# Remove each image
docker rmi edms-backend edms-frontend edms-celery_worker edms-celery_beat

# Or remove all unused images
docker image prune -a
```

### Step 5: Remove Cron Jobs

```bash
# Check current cron jobs
crontab -l

# If EDMS backup jobs exist, remove them
crontab -l | grep -v "backup-hybrid.sh" | crontab -

# Verify removed
crontab -l
# Should not show any EDMS backup jobs
```

---

## 📥 Phase 3: Update Deployment Script (2 minutes)

### Step 1: Pull Latest Changes

```bash
# On staging server
cd ~/edms

# Pull latest from GitHub
git pull origin develop

# Should see the latest commits:
# 197b597 - feat: Add automated backup setup
# 3a3d3d2 - fix: Add storage permissions setup
```

### Step 2: Verify Updates

```bash
# Check DB_HOST fix
grep "DB_HOST=db" deploy-interactive.sh
# Should show line 456: DB_HOST=db

# Check for new functions
grep "setup_storage_permissions" deploy-interactive.sh
grep "setup_backup_automation" deploy-interactive.sh
# Both should show results

# Verify script is executable
chmod +x deploy-interactive.sh
ls -la deploy-interactive.sh
```

### Step 3: Check Script Syntax

```bash
bash -n deploy-interactive.sh
# Should show no errors
```

---

## 🚀 Phase 4: Fresh Deployment Test (15-20 minutes)

### Step 1: Run Deployment Script

```bash
# On staging server
cd ~/edms

# Run the updated deployment script
./deploy-interactive.sh
```

### Step 2: Answer Prompts

**Recommended answers for testing:**

```yaml
═══════════════════════════════════════════════════════════════
Pre-flight Checks
═══════════════════════════════════════════════════════════════
# Should all pass ✓

═══════════════════════════════════════════════════════════════
Configuration Collection
═══════════════════════════════════════════════════════════════

Server Configuration:
  ? Server IP address [172.25.222.103]: <Enter>
  ? Server hostname [edms-server]: edms-staging-reset <Enter>

Docker Port Configuration:
  ? Backend port [8001]: <Enter>
  ? Frontend port [3001]: <Enter>
  ? PostgreSQL port [5433]: <Enter>
  ? Redis port [6380]: <Enter>

Database Configuration:
  ? Database name [edms_production]: edms_staging_test <Enter>
  ? Database user [edms_prod_user]: edms_staging_user <Enter>
  ? Database password: <create-strong-password>
  ? Confirm password: <same-password>

Security Configuration:
  # SECRET_KEY and EDMS_MASTER_KEY auto-generated
  ? Session timeout (seconds) [3600]: <Enter>

HAProxy Configuration:
  ? Will you be using HAProxy? [Y/n]: n <Enter>
  # Keep it simple for testing

Optional: Monitoring
  ? Enable Sentry error tracking? [y/N]: <Enter>

═══════════════════════════════════════════════════════════════
Configuration Summary
═══════════════════════════════════════════════════════════════
# Review all settings

? Proceed with deployment? [Y/n]: y <Enter>

═══════════════════════════════════════════════════════════════
Environment File Creation
═══════════════════════════════════════════════════════════════
✓ .env file created

═══════════════════════════════════════════════════════════════
Docker Deployment
═══════════════════════════════════════════════════════════════
# Building images (3-5 minutes)
# Starting containers

═══════════════════════════════════════════════════════════════
Storage Directory Setup ⭐ NEW!
═══════════════════════════════════════════════════════════════
▶ Creating storage directories...
✓ Storage directories created

▶ Detecting container user ID...
ℹ Backend container runs as UID: 995

▶ Setting storage permissions for UID 995...
✓ Storage permissions configured
ℹ Ownership: UID 995
ℹ Permissions: 775 (rwxrwxr-x)

▶ Verifying storage structure...
# Should show correct ownership

═══════════════════════════════════════════════════════════════
Database Initialization
═══════════════════════════════════════════════════════════════
# Migrations, defaults, test users, etc.

═══════════════════════════════════════════════════════════════
Admin User Creation
═══════════════════════════════════════════════════════════════
? Create admin user now? [Y/n]: y <Enter>
  Username: admin
  Email: admin@staging.test
  Password: <admin-password>
  Password (again): <admin-password>

═══════════════════════════════════════════════════════════════
System Testing
═══════════════════════════════════════════════════════════════
# Health checks, container logs

═══════════════════════════════════════════════════════════════
Backup Automation Setup ⭐ NEW!
═══════════════════════════════════════════════════════════════
ℹ EDMS includes a hybrid backup system with:
  • Daily backups at 2:00 AM
  • Weekly backups on Sunday at 3:00 AM
  • Monthly backups on the 1st at 4:00 AM

ℹ Backup features:
  • 1-second backup time (pg_dump + tar)
  • 9-second restore time
  • Automatic retention (keeps last 7 backups)
  • Stored in: /home/lims/edms/backups/

? Set up automated backups now? [Y/n]: y <Enter>

▶ Setting up automated backup cron jobs...
✓ Automated backups configured successfully!

ℹ Backup Schedule:
  • Daily:   2:00 AM every day
  • Weekly:  3:00 AM every Sunday
  • Monthly: 4:00 AM on the 1st

ℹ Backup location: /home/lims/edms/backups/
ℹ Backup logs:     /home/lims/edms/logs/backup.log

▶ Testing manual backup...
✓ Manual backup test successful!
ℹ Latest backup: backup_20260112_065234.tar.gz (76K)

═══════════════════════════════════════════════════════════════
HAProxy Setup
═══════════════════════════════════════════════════════════════
# Skipped (we chose 'n')

═══════════════════════════════════════════════════════════════
Deployment Complete! 🎉
═══════════════════════════════════════════════════════════════
```

---

## ✅ Phase 5: Verify Automated Features (10 minutes)

### 1. Check Storage Permissions

```bash
# On staging server
cd ~/edms

# Check storage directory ownership
ls -la storage/
ls -la storage/documents/
ls -la storage/media/

# Should show UID 995 or user 'edms'
# drwxrwxr-x  995 995  storage/
# drwxrwxr-x  995 995  storage/documents/
# drwxrwxr-x  995 995  storage/media/
```

**✅ Expected**: Owned by UID 995 (container user)

### 2. Check Cron Jobs

```bash
# View installed cron jobs
crontab -l

# Should show:
# EDMS Automated Backups
# 0 2 * * * cd /home/lims/edms && ./scripts/backup-hybrid.sh >> /home/lims/edms/logs/backup.log 2>&1
# 0 3 * * 0 cd /home/lims/edms && ./scripts/backup-hybrid.sh >> /home/lims/edms/logs/backup.log 2>&1
# 0 4 1 * * cd /home/lims/edms && ./scripts/backup-hybrid.sh >> /home/lims/edms/logs/backup.log 2>&1
```

**✅ Expected**: 3 cron jobs installed

### 3. Check Test Backup

```bash
# Check backup was created during deployment
ls -lh backups/

# Should show at least one backup file
# backup_20260112_065234.tar.gz  (76K or similar)
```

**✅ Expected**: At least 1 backup file

### 4. Check Backup Logs

```bash
# View backup log
cat logs/backup.log

# Should show successful backup execution
```

**✅ Expected**: Log shows successful backup

### 5. Check All Services

```bash
docker compose -f docker-compose.prod.yml ps
```

**✅ Expected**: All 6 containers "Up" and healthy

---

## 🧪 Phase 6: Test Document Creation (5 minutes)

### Critical Test: Storage Permissions

**This is the test that failed before!**

1. **Open browser**: `http://172.25.222.103:3001`

2. **Login**: 
   - Username: `admin`
   - Password: [your admin password]

3. **Create Document**:
   - Click "Create New Document"
   - Fill in details:
     - Title: "Test Document After Reset"
     - Description: "Testing storage permissions"
     - Document Type: Policy
     - Document Source: Internal
   - Upload file: Any DOCX file
   - Click "Create"

4. **Expected Result**: 
   - ✅ **SUCCESS!** Document created
   - ✅ No permission errors
   - ✅ File uploaded successfully

**This should work now without manual permission fixes!**

---

## 📊 Phase 7: Verification Checklist

### Automated Features Verification

- [ ] **Storage Permissions**: 
  - `ls -la storage/` shows UID 995 ownership ✅
  - `storage/documents/` exists with correct permissions ✅
  - `storage/media/` exists with correct permissions ✅

- [ ] **Backup Automation**:
  - `crontab -l` shows 3 EDMS backup jobs ✅
  - `ls backups/` shows test backup file ✅
  - `cat logs/backup.log` shows successful execution ✅

- [ ] **Document Creation**:
  - Can create document without errors ✅
  - Can upload file without permission issues ✅
  - File appears in `storage/documents/` or `storage/media/` ✅

- [ ] **All Services**:
  - 6 containers running and healthy ✅
  - Backend health check passes ✅
  - Frontend accessible ✅

---

## 🎯 Expected Improvements

### Before (Manual Fix Required):
```bash
# Deploy
./deploy-interactive.sh

# ❌ Document creation fails with Permission denied

# Manual fix needed:
sudo chown -R 995:995 storage/
sudo chmod -R 775 storage/
docker compose restart backend

# ✅ Now document creation works
```

### After (Automated):
```bash
# Deploy
./deploy-interactive.sh

# ✅ Document creation works immediately!
# No manual permission fixes needed
```

---

## 🔧 Troubleshooting During Test

### Issue: Storage Permissions Still Wrong

**Check**:
```bash
ls -la storage/
```

**If not owned by 995**:
```bash
# The script should have done this, but verify:
docker compose -f docker-compose.prod.yml exec backend id
# Note the UID (should be 995)

# Check if script ran
docker compose -f docker-compose.prod.yml logs backend | grep -i permission
```

### Issue: Cron Jobs Not Installed

**Check**:
```bash
crontab -l | grep backup
```

**If missing**:
- Did you answer 'y' to "Set up automated backups"?
- Check if scripts/backup-hybrid.sh exists
- Try manual installation: `./scripts/setup-backup-cron.sh`

### Issue: Test Backup Failed

**Check**:
```bash
# Try manual backup
./scripts/backup-hybrid.sh

# Check for errors
cat logs/backup.log
```

---

## 📋 Quick Reset Commands (Copy-Paste)

```bash
# ==============================================================================
# STAGING SERVER COMPLETE RESET - RUN ON STAGING SERVER
# ==============================================================================

cd ~/edms

# 1. Stop containers
docker compose -f docker-compose.prod.yml down -v

# 2. Clean directories
sudo rm -rf storage/* logs/* backend/.env backend/.env.backup.*

# 3. Optional: Remove images for complete rebuild
docker rmi edms-backend edms-frontend edms-celery_worker edms-celery_beat 2>/dev/null || true

# 4. Remove cron jobs
crontab -l | grep -v "backup-hybrid.sh" | crontab - 2>/dev/null || true

# 5. Pull latest code
git pull origin develop

# 6. Verify updates
grep "DB_HOST=db" deploy-interactive.sh
grep "setup_storage_permissions" deploy-interactive.sh
grep "setup_backup_automation" deploy-interactive.sh

# 7. Deploy fresh
./deploy-interactive.sh

# ==============================================================================
# Follow the prompts and answer:
# - HAProxy: n
# - Backups: y
# - Create admin: y
# ==============================================================================
```

---

## ✅ Post-Test Verification Script

After deployment completes, run this verification script:

```bash
cat > verify-deployment.sh << 'VERIFY_EOF'
#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  Deployment Verification Script"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check containers
echo "1. Checking containers..."
CONTAINERS=$(docker compose -f docker-compose.prod.yml ps | grep "Up" | wc -l)
echo "   Running containers: $CONTAINERS/6"
if [ "$CONTAINERS" -eq 6 ]; then
    echo "   ✅ All containers running"
else
    echo "   ❌ Some containers not running"
fi
echo ""

# Check storage permissions
echo "2. Checking storage permissions..."
STORAGE_UID=$(stat -c '%u' storage/ 2>/dev/null)
echo "   Storage owned by UID: $STORAGE_UID"
if [ "$STORAGE_UID" = "995" ] || [ "$STORAGE_UID" = "1000" ]; then
    echo "   ✅ Storage permissions correct"
else
    echo "   ❌ Storage permissions incorrect (expected 995 or 1000)"
fi
echo ""

# Check cron jobs
echo "3. Checking cron jobs..."
CRON_COUNT=$(crontab -l 2>/dev/null | grep "backup-hybrid.sh" | wc -l)
echo "   Backup cron jobs: $CRON_COUNT"
if [ "$CRON_COUNT" -eq 3 ]; then
    echo "   ✅ All 3 cron jobs installed"
else
    echo "   ❌ Cron jobs missing (expected 3, found $CRON_COUNT)"
fi
echo ""

# Check backup files
echo "4. Checking backups..."
BACKUP_COUNT=$(ls -1 backups/backup_*.tar.gz 2>/dev/null | wc -l)
echo "   Backup files: $BACKUP_COUNT"
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo "   ✅ Test backup created"
    ls -lh backups/backup_*.tar.gz | tail -1
else
    echo "   ❌ No backup files found"
fi
echo ""

# Check backend health
echo "5. Checking backend health..."
HEALTH=$(curl -s http://localhost:8001/health/ | grep -o '"status":"healthy"')
if [ -n "$HEALTH" ]; then
    echo "   ✅ Backend healthy"
else
    echo "   ❌ Backend not healthy"
fi
echo ""

# Check frontend
echo "6. Checking frontend..."
FRONTEND=$(curl -s -I http://localhost:3001/ | grep "HTTP" | grep "200")
if [ -n "$FRONTEND" ]; then
    echo "   ✅ Frontend accessible"
else
    echo "   ❌ Frontend not accessible"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "  Verification Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Access URLs:"
echo "  Frontend:    http://172.25.222.103:3001"
echo "  Backend API: http://172.25.222.103:8001/api/"
echo "  Admin Panel: http://172.25.222.103:8001/admin/"
echo ""
echo "Next: Test document creation in browser"
echo "═══════════════════════════════════════════════════════════════"
VERIFY_EOF

chmod +x verify-deployment.sh
./verify-deployment.sh
```

---

## 🎯 Expected Test Results

### ✅ All Should Pass:

```
═══════════════════════════════════════════════════════════════
  Deployment Verification Script
═══════════════════════════════════════════════════════════════

1. Checking containers...
   Running containers: 6/6
   ✅ All containers running

2. Checking storage permissions...
   Storage owned by UID: 995
   ✅ Storage permissions correct

3. Checking cron jobs...
   Backup cron jobs: 3
   ✅ All 3 cron jobs installed

4. Checking backups...
   Backup files: 1
   ✅ Test backup created
   backup_20260112_065234.tar.gz  76K

5. Checking backend health...
   ✅ Backend healthy

6. Checking frontend...
   ✅ Frontend accessible

═══════════════════════════════════════════════════════════════
  Verification Summary
═══════════════════════════════════════════════════════════════

Access URLs:
  Frontend:    http://172.25.222.103:3001
  Backend API: http://172.25.222.103:8001/api/
  Admin Panel: http://172.25.222.103:8001/admin/

Next: Test document creation in browser
═══════════════════════════════════════════════════════════════
```

---

## 🎊 Final Manual Test

### Document Creation Test

1. **Open**: `http://172.25.222.103:3001`
2. **Login**: admin / [your password]
3. **Create Document**: Upload a DOCX file
4. **Expected**: ✅ **SUCCESS!** No permission errors!

---

## 📊 Success Criteria

Your reset and retest is successful when:

- [x] All containers running (6/6)
- [x] Storage owned by UID 995
- [x] 3 cron jobs installed
- [x] Test backup created
- [x] Backend healthy
- [x] Frontend accessible
- [x] **Document creation works without manual fixes** ⭐
- [x] File upload works
- [x] No permission errors

---

## 🚀 Timeline

```
Phase 1: Backup current state      →  2 minutes
Phase 2: Complete reset            →  5 minutes
Phase 3: Update script             →  2 minutes
Phase 4: Fresh deployment          → 15-20 minutes
Phase 5: Verification              →  10 minutes
                                    ───────────────
Total estimated time:                 35-40 minutes
```

---

## ✨ What You're Testing

### Core Improvements:
1. ✅ **Storage permissions auto-setup** (UID detection + chown)
2. ✅ **Backup cron jobs auto-install** (3 schedules)
3. ✅ **Test backup execution** (verifies scripts work)
4. ✅ **DB_HOST fix** (db not postgres)
5. ✅ **Complete automation** (no manual fixes needed)

### Expected Outcome:
**One-command deployment** with everything working:
```bash
./deploy-interactive.sh
# Answer prompts
# 20 minutes later: Fully functional EDMS with automated backups!
```

---

## 📞 Need Help?

**During reset/test, if you encounter issues:**
1. Take screenshot
2. Copy error messages
3. Share with me
4. I'll help troubleshoot!

---

## 🎉 Ready to Test?

**Run the quick reset commands** (copy-paste block from above)  
**Then deploy fresh** with `./deploy-interactive.sh`

This will verify that the deployment script is now **truly automated** and **production-ready**! 🚀

**Let me know when you're ready to start, or if you have any questions!** 😊

