# Staging Server Reset Guide - Testing Updated Interactive Deployment

**Last Updated:** 2026-01-12  
**Purpose:** Reset staging server to clean state and test the updated `deploy-interactive.sh`  
**Recent Updates:** 
- ✅ Automatic storage permissions setup (commit `3a3d3d2`)
- ✅ Automated backup cron job installation (commit `197b597`)
- ✅ DB_HOST fix and improved error handling

---

## 📋 Overview

This guide helps you completely reset your staging server and test the latest interactive deployment script with:

1. **Storage Permissions Auto-Setup**: Detects container UID (995) and sets correct permissions automatically
2. **Backup Automation**: Installs daily/weekly/monthly cron jobs during deployment
3. **Improved Configuration**: Fixed DB_HOST, better error handling, comprehensive validation

---

## ⚠️ CRITICAL WARNING

**This procedure will DELETE ALL DATA on the staging server:**
- ✗ All documents
- ✗ All users (except new admin created during deployment)
- ✗ All workflows and workflow history
- ✗ Complete database wipe
- ✗ All uploaded files

**✅ Only perform on STAGING server - NEVER on production!**

---

## 🎯 Prerequisites

**Before Starting:**

1. **Backup current staging data** (if needed):
   ```bash
   # On staging server
   cd ~/edms
   ./scripts/backup-hybrid.sh
   
   # Copy backup to safe location
   cp backups/backup_$(date +%Y%m%d)_*.tar.gz ~/staging-backup-before-reset.tar.gz
   ```

2. **Verify you're on staging server**:
   ```bash
   # Check server IP (should be staging IP, NOT production)
   hostname -I
   
   # Should show staging server identifier
   hostname
   ```

3. **Have these details ready**:
   - Admin email and password (12+ characters)
   - Server IP address (e.g., 172.25.222.103)
   - Database credentials (can use defaults for testing)

---

## 🔄 Step 1: Complete System Teardown (5 minutes)

### 1.1 Stop All Services

```bash
# SSH to staging server
ssh user@<staging-ip>

# Navigate to EDMS directory
cd ~/edms

# Stop all containers
docker compose -f docker-compose.prod.yml down

# Verify containers stopped
docker ps -a | grep edms
```

### 1.2 Remove All Docker Resources

```bash
# Remove ALL volumes (THIS DELETES ALL DATA!)
docker compose -f docker-compose.prod.yml down -v

# Verify volumes removed
docker volume ls | grep edms

# Remove any orphaned volumes
docker volume prune -f

# Optional: Remove images to force rebuild
docker compose -f docker-compose.prod.yml down --rmi all
```

### 1.3 Clean Application Directories

```bash
# Remove storage files
sudo rm -rf storage/documents/*
sudo rm -rf storage/media/*
sudo rm -rf logs/*

# Remove any existing .env file
rm -f .env
rm -f backend/.env

# Verify directories are empty
ls -la storage/documents/
ls -la storage/media/
```

### 1.4 Remove Existing Cron Jobs

```bash
# Show current cron jobs
crontab -l

# Remove EDMS backup jobs if they exist
crontab -l | grep -v "backup-hybrid.sh" | crontab -

# Verify removal
crontab -l | grep -i edms
```

### 1.5 Verification

```bash
# Verify clean state
echo "=== Docker Containers ==="
docker ps -a | grep edms || echo "✓ No containers"

echo "=== Docker Volumes ==="
docker volume ls | grep edms || echo "✓ No volumes"

echo "=== Storage Files ==="
ls storage/documents/ | wc -l
ls storage/media/ | wc -l

echo "=== Cron Jobs ==="
crontab -l | grep -c "backup-hybrid.sh" || echo "✓ No backup jobs"

echo ""
echo "✅ System clean - ready for fresh deployment"
```

---

## 🚀 Step 2: Pull Latest Code (2 minutes)

### 2.1 Update Repository

```bash
# Ensure you're in the EDMS directory
cd ~/edms

# Fetch latest changes
git fetch origin

# Check current branch
git branch

# Pull latest code (adjust branch name as needed)
git pull origin develop
# OR for main branch:
# git pull origin main

# Verify latest commits
git log --oneline -5
```

**Expected recent commits:**
- `197b597` - feat: Add automated backup setup to deployment script
- `3a3d3d2` - fix: Add storage permissions setup to deployment script
- `484b7c5` - feat: Implement Hybrid Backup System with Automated Scheduling

### 2.2 Verify Script

```bash
# Check deployment script exists and is executable
ls -la deploy-interactive.sh

# Make executable if needed
chmod +x deploy-interactive.sh

# Verify backup scripts
ls -la scripts/backup-hybrid.sh
ls -la scripts/restore-hybrid.sh
chmod +x scripts/backup-hybrid.sh scripts/restore-hybrid.sh
```

---

## 🎬 Step 3: Run Interactive Deployment (15-20 minutes)

### 3.1 Launch Deployment

```bash
cd ~/edms
./deploy-interactive.sh
```

### 3.2 Configuration Prompts

Answer the prompts as follows (example for staging):

#### Pre-flight Checks
- All checks should pass ✅
- Docker, Docker Compose, Python3, Git verified

#### Server Configuration
```
? Server IP address [auto-detected]: <Press Enter to accept>
? Server hostname: edms-staging-test
```

#### Port Configuration (use non-standard to avoid conflicts)
```
? Backend port: 8001
? Frontend port: 3001
? PostgreSQL port: 5433
? Redis port: 6380
```

#### Database Configuration
```
? Database name: edms_staging_reset
? Database user: edms_staging_user
? Database password: <enter secure password>
? Confirm password: <re-enter password>
```

#### Redis Configuration
```
? Redis password: <enter secure password>
```

#### Django Configuration
```
? Django secret key: <auto-generated - press Enter>
? Debug mode: no  (use production settings)
? Allowed hosts: <staging-ip>,localhost,127.0.0.1
```

#### HAProxy Configuration
```
? Use HAProxy: no  (for staging, direct access is simpler)
```

#### Configuration Summary
- Review all settings
- Confirm: `y`

#### Deployment Execution
- Watch for successful completion of each phase:
  1. ✅ Docker container deployment
  2. ✅ **Storage permissions setup** (NEW - should detect UID 995)
  3. ✅ Database initialization
  4. ✅ Admin user creation
  5. ✅ Deployment testing
  6. ✅ **Backup automation setup** (NEW - installs cron jobs)

#### Admin User Creation
```
? Admin username: admin
? Admin email: admin@staging.test
? Admin password: <enter 12+ character password>
? Confirm password: <re-enter password>
```

#### Backup Automation (NEW FEATURE)
```
? Set up automated backups now? [Y/n]: y
```

**What happens:**
- Creates cron jobs for daily/weekly/monthly backups
- Runs test backup to verify functionality
- Shows backup schedule and locations

**Expected output:**
```
✅ Automated backups configured successfully!

Backup Schedule:
  • Daily:   2:00 AM every day
  • Weekly:  3:00 AM every Sunday
  • Monthly: 4:00 AM on the 1st

Backup location: /home/user/edms/backups/
Backup logs:     /home/user/edms/logs/backup.log

Testing manual backup...
✅ Manual backup test successful!
Latest backup: backup_20260112_152314.tar.gz (76K)
```

### 3.3 Deployment Completion

The script will display a final summary with:
- ✅ All services running
- ✅ Access URLs (frontend, backend API, admin panel)
- ✅ Test results
- ✅ Next steps

---

## ✅ Step 4: Verification (10 minutes)

### 4.1 Verify Container Status

```bash
# Check all containers are running
docker ps

# Expected output: 6 containers running
# - edms_prod_backend
# - edms_prod_frontend
# - edms_prod_db
# - edms_prod_redis
# - edms_prod_celery_worker
# - edms_prod_celery_beat
```

### 4.2 Verify Storage Permissions (NEW)

```bash
# Check storage directory ownership
ls -la storage/

# Should show UID 995 (or container user)
ls -la storage/documents/
ls -la storage/media/

# Permissions should be 775 (rwxrwxr-x)
stat -c "%a %U:%G" storage/documents/
```

**Expected:**
```
drwxrwxr-x 995 995 documents/
drwxrwxr-x 995 995 media/
775 995:995
```

### 4.3 Verify Backup Automation (NEW)

```bash
# Check cron jobs installed
crontab -l | grep backup-hybrid.sh

# Expected: 3 lines
# 0 2 * * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 3 * * 0 cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 4 1 * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1

# Verify backup was created during deployment
ls -lh backups/

# Should show at least 1 backup file
# backup_20260112_152314.tar.gz
```

### 4.4 Test Backup/Restore Functionality

```bash
# Run manual backup
./scripts/backup-hybrid.sh

# List backups
ls -lh backups/

# Verify backup contents
tar -tzf backups/backup_*.tar.gz | head -20

# Expected files:
# - tmp_*/database.dump
# - tmp_*/storage.tar.gz
# - tmp_*/manifest.json
```

### 4.5 Check Backend Health

```bash
# Test backend health endpoint
curl -f http://localhost:8001/health/

# Expected: {"status": "healthy"}

# Check API documentation
curl -f http://localhost:8001/api/v1/

# Should return API root response
```

### 4.6 Check Database Connection

```bash
# Access database
docker compose -f docker-compose.prod.yml exec db psql -U edms_staging_user -d edms_staging_reset -c "\dt"

# Should show Django tables created

# Check admin user exists
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(f'Admin users: {User.objects.filter(is_superuser=True).count()}')"

# Expected: Admin users: 1
```

---

## 🌐 Step 5: Browser Testing (10 minutes)

### 5.1 Access Frontend

1. **Open browser**: `http://<staging-ip>:3001`
2. **Login** with admin credentials you created
3. **Verify**:
   - ✅ Login successful
   - ✅ Dashboard loads
   - ✅ Navigation menu appears

### 5.2 Test Document Creation

1. **Navigate to**: My Documents
2. **Click**: "Create New Document"
3. **Fill in**:
   - Document Number: TEST-001
   - Title: Staging Test Document
   - Document Type: Select any type
   - Upload: Upload a test file
4. **Submit**
5. **Verify**:
   - ✅ Document created successfully
   - ✅ File uploaded (confirms storage permissions work)
   - ✅ Document appears in list

### 5.3 Test Workflow

1. **Open document**: TEST-001
2. **Submit for Review**: Click "Submit for Review"
3. **Verify**:
   - ✅ Status changes to "UNDER_REVIEW"
   - ✅ Workflow progresses
   - ✅ No permission errors

### 5.4 Test Admin Panel

1. **Access**: `http://<staging-ip>:8001/admin/`
2. **Login**: with admin credentials
3. **Verify**:
   - ✅ Admin interface loads
   - ✅ Can view users
   - ✅ Can view documents
   - ✅ Static files load correctly

---

## 📊 Step 6: Automated Verification Script

Create and run this comprehensive verification script:

```bash
cat > ~/verify-deployment.sh << 'VERIFY_EOF'
#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  EDMS Staging Deployment Verification"
echo "═══════════════════════════════════════════════════════════════"
echo ""

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
        ((PASS++))
    else
        echo "❌ $1"
        ((FAIL++))
    fi
}

# 1. Container Status
echo "1. Checking containers..."
RUNNING=$(docker ps --filter "name=edms_prod" | grep -c "Up")
echo "   Running containers: $RUNNING/6"
[ $RUNNING -eq 6 ]
check "All containers running"
echo ""

# 2. Storage Permissions
echo "2. Checking storage permissions..."
STORAGE_UID=$(stat -c "%u" storage/documents/)
echo "   Storage owned by UID: $STORAGE_UID"
[ "$STORAGE_UID" = "995" ] || [ "$STORAGE_UID" = "1000" ]
check "Storage permissions configured"
echo ""

# 3. Cron Jobs
echo "3. Checking backup automation..."
CRON_COUNT=$(crontab -l 2>/dev/null | grep -c "backup-hybrid.sh" || echo 0)
echo "   Backup cron jobs: $CRON_COUNT"
[ $CRON_COUNT -eq 3 ]
check "Backup automation configured (3 jobs)"
echo ""

# 4. Backup Files
echo "4. Checking backups..."
BACKUP_COUNT=$(ls -1 backups/backup_*.tar.gz 2>/dev/null | wc -l)
echo "   Backup files: $BACKUP_COUNT"
[ $BACKUP_COUNT -ge 1 ]
check "Test backup created"
if [ $BACKUP_COUNT -ge 1 ]; then
    ls -lh backups/backup_*.tar.gz | tail -3
fi
echo ""

# 5. Backend Health
echo "5. Checking backend health..."
curl -sf http://localhost:8001/health/ > /dev/null
check "Backend health endpoint responds"
echo ""

# 6. Frontend
echo "6. Checking frontend..."
curl -sf http://localhost:3001 > /dev/null
check "Frontend accessible"
echo ""

# 7. Database Connection
echo "7. Checking database..."
docker compose -f docker-compose.prod.yml exec -T db pg_isready -U edms_staging_user > /dev/null 2>&1
check "Database connection OK"
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "  Verification Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 All checks passed! Deployment successful."
    echo ""
    echo "Access URLs:"
    echo "  Frontend:    http://$(hostname -I | awk '{print $1}'):3001"
    echo "  Backend API: http://$(hostname -I | awk '{print $1}'):8001/api/v1/"
    echo "  Admin Panel: http://$(hostname -I | awk '{print $1}'):8001/admin/"
    echo ""
    echo "Next Steps:"
    echo "1. Test document creation in browser"
    echo "2. Verify workflow functionality"
    echo "3. Monitor backup logs: tail -f logs/backup.log"
else
    echo "⚠️  Some checks failed. Review errors above."
fi

echo "═══════════════════════════════════════════════════════════════"
VERIFY_EOF

chmod +x ~/verify-deployment.sh
~/verify-deployment.sh
```

---

## 🎯 Expected Results Summary

### ✅ What Should Work After Reset

| Feature | Status | Notes |
|---------|--------|-------|
| Container deployment | ✅ | 6 containers running |
| Storage permissions | ✅ | **AUTO-CONFIGURED** to UID 995 |
| Database initialization | ✅ | Tables created, migrations applied |
| Admin user | ✅ | Can login and access admin panel |
| Document creation | ✅ | Files upload successfully |
| Workflow system | ✅ | Submit/Review/Approve works |
| Backup automation | ✅ | **3 CRON JOBS INSTALLED** |
| Test backup | ✅ | Created during deployment |
| Frontend access | ✅ | Loads at port 3001 |
| Backend API | ✅ | Responds at port 8001 |

### 🆕 New Features Verified

1. **Automatic Storage Permissions** (commit `3a3d3d2`):
   - ✅ Detects container UID automatically
   - ✅ Sets ownership to UID 995:995
   - ✅ Sets permissions to 775
   - ✅ No manual intervention needed

2. **Automated Backup Setup** (commit `197b597`):
   - ✅ Prompts to install cron jobs
   - ✅ Daily backup at 2:00 AM
   - ✅ Weekly backup at 3:00 AM Sunday
   - ✅ Monthly backup at 4:00 AM on 1st
   - ✅ Runs test backup during deployment
   - ✅ Shows backup size and location

---

## 🔍 Troubleshooting

### Issue: Storage Permission Denied

**Symptom:** Document upload fails with "Permission denied"

**Solution:**
```bash
# Check current ownership
ls -la storage/documents/

# Get container UID
docker compose -f docker-compose.prod.yml exec backend id -u

# Set permissions manually
sudo chown -R 995:995 storage/
sudo chmod -R 775 storage/
```

### Issue: Cron Jobs Not Installed

**Symptom:** `crontab -l` shows no backup jobs

**Solution:**
```bash
# Install manually
./scripts/setup-backup-cron.sh

# Or add manually
crontab -e
# Add these lines:
# 0 2 * * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 3 * * 0 cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 4 1 * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
```

### Issue: Containers Not Starting

**Symptom:** `docker ps` shows fewer than 6 containers

**Solution:**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs --tail=50

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend

# Full restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Issue: Database Connection Failed

**Symptom:** Backend logs show database connection errors

**Solution:**
```bash
# Verify database is running
docker compose -f docker-compose.prod.yml ps db

# Check database logs
docker compose -f docker-compose.prod.yml logs db --tail=50

# Verify credentials in .env
cat .env | grep DB_

# Test connection manually
docker compose -f docker-compose.prod.yml exec db psql -U edms_staging_user -d edms_staging_reset -c "SELECT 1;"
```

### Issue: Frontend Shows Blank Page

**Symptom:** Browser shows white screen or loading spinner

**Solution:**
```bash
# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend --tail=50

# Check browser console (F12)
# Look for API connection errors

# Verify backend is accessible
curl http://localhost:8001/api/v1/

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend
```

---

## 📝 Post-Reset Checklist

Use this checklist to ensure complete verification:

- [ ] All 6 Docker containers running
- [ ] Storage owned by UID 995 (or correct container user)
- [ ] Storage permissions set to 775
- [ ] 3 cron jobs installed for backups
- [ ] At least 1 backup file created
- [ ] Backend health endpoint responds
- [ ] Frontend loads in browser
- [ ] Admin login works
- [ ] Can create new document
- [ ] Can upload file successfully
- [ ] Workflow submission works
- [ ] Admin panel accessible
- [ ] No permission errors in logs

---

## 🎊 Success Criteria

**Deployment is successful when:**

1. ✅ **All containers running** - 6/6 containers up
2. ✅ **Storage configured** - Automatic UID detection and permission setup
3. ✅ **Backups automated** - 3 cron jobs installed and working
4. ✅ **Test backup created** - Backup file exists and is valid
5. ✅ **Application accessible** - Frontend and backend respond
6. ✅ **Admin access** - Can login and manage system
7. ✅ **Document operations** - Create, upload, workflow all work
8. ✅ **No errors** - Clean logs, no permission issues

---

## 📚 Related Documentation

- **Deployment Script Source**: `deploy-interactive.sh`
- **Backup System**: `scripts/backup-hybrid.sh` and `scripts/restore-hybrid.sh`
- **Recent Changes**: 
  - `STAGING_RESET_AND_TEST_GUIDE.md` - Previous reset guide
  - `DEPLOYMENT_QUICK_START.md` - Quick deployment reference
  - Git commits: `197b597`, `3a3d3d2`, `484b7c5`

---

## 🔄 Rolling Back (If Needed)

If deployment fails and you need to restore previous state:

```bash
# Stop new deployment
docker compose -f docker-compose.prod.yml down -v

# Restore from backup (if you created one in Prerequisites)
./scripts/restore-hybrid.sh ~/staging-backup-before-reset.tar.gz

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

---

## 🎯 Next Steps After Successful Reset

1. **Document Results**: Note any issues or improvements
2. **Test Workflows**: Create test documents and run through approval workflow
3. **Monitor Backups**: Check logs after first scheduled backup runs
4. **Performance Test**: Create multiple documents, test concurrent users
5. **Prepare for Production**: If staging successful, plan production deployment

---

**Questions or Issues?**

Check the logs:
```bash
# Container logs
docker compose -f docker-compose.prod.yml logs -f

# Backup logs
tail -f logs/backup.log

# Application logs
tail -f logs/edms.log
```

---

**Last Updated:** 2026-01-12 15:32 SGT  
**Script Version:** 1.0 (with storage permissions + backup automation)  
**Tested On:** Ubuntu 20.04 LTS, Docker 24.x, Docker Compose 2.x
