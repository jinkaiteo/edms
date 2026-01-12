# Staging Server Deployment Execution Log

**Date:** 2026-01-12  
**Purpose:** Test updated deployment script with storage permissions and backup automation  
**Commits Deployed:** 197b597 (backup automation) + 3a3d3d2 (storage permissions)

---

## ✅ Pre-Deployment Checklist

- [x] Git conflict resolved
- [x] Latest code pulled (commit 197b597)
- [x] Script executable permissions verified
- [ ] System teardown completed
- [ ] Interactive deployment running
- [ ] Verification completed

---

## 📝 Execution Steps

Follow these commands on your staging server...

### STEP 1: Complete System Teardown

```bash
# SSH to staging server (if not already connected)
ssh user@<staging-ip>

# Navigate to EDMS directory
cd ~/edms

# Stop all running containers
docker compose -f docker-compose.prod.yml down

# Remove ALL volumes (THIS DELETES ALL DATA!)
docker compose -f docker-compose.prod.yml down -v

# Verify containers stopped
docker ps -a | grep edms

# Remove any orphaned volumes
docker volume prune -f

# Clean storage directories
sudo rm -rf storage/documents/*
sudo rm -rf storage/media/*
sudo rm -rf logs/*

# Remove existing .env files
rm -f .env
rm -f backend/.env

# Remove existing cron jobs (if any)
crontab -l | grep -v "backup-hybrid.sh" | crontab -

# VERIFICATION: Check clean state
echo "=== Containers ==="
docker ps -a | grep edms || echo "✓ No containers"

echo "=== Volumes ==="
docker volume ls | grep edms || echo "✓ No volumes"

echo "=== Storage ==="
ls -la storage/documents/ 2>/dev/null || echo "✓ Empty or doesn't exist"

echo "=== Cron Jobs ==="
crontab -l | grep "backup-hybrid.sh" || echo "✓ No backup jobs"

echo ""
echo "✅ System clean - ready for deployment"
```

**Expected Result:** All checks pass, system is clean slate

---

### STEP 2: Launch Interactive Deployment

```bash
cd ~/edms

# Launch the interactive deployment script
./deploy-interactive.sh
```

---

### STEP 3: Answer Configuration Prompts

**Note:** I'll provide example answers. Adjust based on your staging server details.

#### 3.1 Pre-flight Checks
```
✅ Checking Docker...
✅ Checking Docker Compose...
✅ Checking Python3...
✅ Checking Git...

All pre-flight checks passed!
```

Press Enter to continue...

---

#### 3.2 Server Configuration

```
? Server IP address [auto-detected: X.X.X.X]: 
```
**Action:** Press Enter to accept auto-detected IP, or type your staging server IP

```
? Server hostname: 
```
**Suggestion:** `edms-staging-test-20260112`

---

#### 3.3 Port Configuration

```
? Backend port [default: 8000]: 
```
**Suggestion:** `8001` (avoid conflicts)

```
? Frontend port [default: 3000]: 
```
**Suggestion:** `3001` (avoid conflicts)

```
? PostgreSQL port [default: 5432]: 
```
**Suggestion:** `5433` (avoid conflicts)

```
? Redis port [default: 6379]: 
```
**Suggestion:** `6380` (avoid conflicts)

---

#### 3.4 Database Configuration

```
? Database name [default: edms_db]: 
```
**Suggestion:** `edms_staging_reset`

```
? Database user [default: edms_user]: 
```
**Suggestion:** `edms_staging_user`

```
? Database password: 
```
**Action:** Enter a secure password (will be hidden)

```
? Confirm password: 
```
**Action:** Re-enter the same password

---

#### 3.5 Redis Configuration

```
? Redis password (leave empty for no password): 
```
**Suggestion:** Enter a password for security, or press Enter for none

---

#### 3.6 Django Configuration

```
? Django secret key [auto-generated]: 
```
**Action:** Press Enter (auto-generated is secure)

```
? Debug mode [yes/no]: 
```
**Suggestion:** `no` (use production settings even for staging)

```
? Allowed hosts (comma-separated) [default: localhost,127.0.0.1]: 
```
**Suggestion:** `<your-staging-ip>,localhost,127.0.0.1`

---

#### 3.7 HAProxy Configuration

```
? Use HAProxy reverse proxy [yes/no]: 
```
**Suggestion:** `no` (simpler for staging testing)

---

#### 3.8 Configuration Summary

The script will show a summary of all your settings:
```
═══════════════════════════════════════════════════════════════
  Configuration Summary
═══════════════════════════════════════════════════════════════

Server Configuration:
  IP Address:         X.X.X.X
  Hostname:           edms-staging-test-20260112

Port Configuration:
  Backend:            8001
  Frontend:           3001
  PostgreSQL:         5433
  Redis:              6380

Database Configuration:
  Database Name:      edms_staging_reset
  Database User:      edms_staging_user
  Database Password:  ********

[... more configuration ...]

═══════════════════════════════════════════════════════════════

? Proceed with deployment? [Y/n]: 
```

**Action:** Review carefully, then type `Y` and press Enter

---

### STEP 4: Watch Deployment Progress

The script will now execute these phases automatically:

#### Phase 1: Docker Container Deployment
```
═══════════════════════════════════════════════════════════════
  Phase 1: Deploying Docker Containers
═══════════════════════════════════════════════════════════════

Creating network...
Creating volumes...
Building images...
Starting containers...

✅ Docker containers deployed successfully
```

**Watch for:** All containers starting (db, redis, backend, frontend, celery_worker, celery_beat)

---

#### Phase 2: Storage Permissions Setup (NEW FEATURE!)
```
═══════════════════════════════════════════════════════════════
  Phase 2: Setting Up Storage Permissions
═══════════════════════════════════════════════════════════════

Detecting container UID...
Container UID: 995

Creating storage directories...
Setting ownership (995:995)...
Setting permissions (775)...

✅ Storage permissions configured successfully
```

**What to look for:**
- ✅ Container UID detected (usually 995)
- ✅ Directories created
- ✅ Ownership set automatically
- ✅ Permissions set to 775

---

#### Phase 3: Database Initialization
```
═══════════════════════════════════════════════════════════════
  Phase 3: Initializing Database
═══════════════════════════════════════════════════════════════

Running migrations...
Creating default groups...
Creating default roles...
Creating workflow types...

✅ Database initialized successfully
```

**Watch for:** No migration errors, all tables created

---

#### Phase 4: Admin User Creation
```
═══════════════════════════════════════════════════════════════
  Phase 4: Creating Admin User
═══════════════════════════════════════════════════════════════

? Admin username: 
```
**Suggestion:** `admin`

```
? Admin email: 
```
**Suggestion:** `admin@staging.test`

```
? Admin password (minimum 12 characters): 
```
**Action:** Enter a secure password (will be hidden)

```
? Confirm password: 
```
**Action:** Re-enter the same password

```
Creating admin user...
✅ Admin user created successfully
```

---

#### Phase 5: Deployment Testing
```
═══════════════════════════════════════════════════════════════
  Phase 5: Testing Deployment
═══════════════════════════════════════════════════════════════

Testing backend health...
Testing frontend accessibility...
Testing database connection...

✅ All deployment tests passed
```

**Watch for:** All tests passing

---

#### Phase 6: Backup Automation Setup (NEW FEATURE!)
```
═══════════════════════════════════════════════════════════════
  Phase 6: Backup Automation
═══════════════════════════════════════════════════════════════

? Set up automated backups now? [Y/n]: 
```

**Action:** Type `Y` and press Enter

```
Installing cron jobs...
  • Daily backup:   2:00 AM every day
  • Weekly backup:  3:00 AM every Sunday
  • Monthly backup: 4:00 AM on the 1st

Running test backup...
Creating backup archive...
Compressing files...

✅ Test backup successful!
Backup file: backup_20260112_153045.tar.gz (76K)

✅ Automated backups configured successfully!

Backup Schedule:
  • Daily:   2:00 AM every day
  • Weekly:  3:00 AM every Sunday
  • Monthly: 4:00 AM on the 1st

Backup location: /home/user/edms/backups/
Backup logs:     /home/user/edms/logs/backup.log
```

**What to look for:**
- ✅ 3 cron jobs installed
- ✅ Test backup runs successfully
- ✅ Backup file created (~50-100KB for empty system)
- ✅ Schedule displayed

---

### STEP 5: Deployment Completion

```
═══════════════════════════════════════════════════════════════
  🎉 Deployment Successful!
═══════════════════════════════════════════════════════════════

Access URLs:
  Frontend:    http://X.X.X.X:3001
  Backend API: http://X.X.X.X:8001/api/v1/
  Admin Panel: http://X.X.X.X:8001/admin/

Admin Credentials:
  Username: admin
  Password: [as entered]

Container Status:
  ✅ edms_prod_db
  ✅ edms_prod_redis
  ✅ edms_prod_backend
  ✅ edms_prod_frontend
  ✅ edms_prod_celery_worker
  ✅ edms_prod_celery_beat

Next Steps:
  1. Access frontend at http://X.X.X.X:3001
  2. Login with admin credentials
  3. Test document creation
  4. Verify backup automation: crontab -l

For support, check logs:
  docker compose -f docker-compose.prod.yml logs -f

═══════════════════════════════════════════════════════════════
```

---

## 🔍 Post-Deployment Verification

Once deployment completes, run these checks:

### Check 1: Container Status
```bash
docker ps

# Expected: 6 containers running
# edms_prod_backend, edms_prod_frontend, edms_prod_db, 
# edms_prod_redis, edms_prod_celery_worker, edms_prod_celery_beat
```

### Check 2: Storage Permissions (NEW FEATURE)
```bash
ls -la storage/

# Expected output:
# drwxrwxr-x 2 995 995 4096 Jan 12 15:30 documents/
# drwxrwxr-x 2 995 995 4096 Jan 12 15:30 media/
```

### Check 3: Backup Automation (NEW FEATURE)
```bash
crontab -l

# Expected: 3 lines with backup-hybrid.sh
# 0 2 * * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 3 * * 0 cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
# 0 4 1 * * cd ~/edms && ./scripts/backup-hybrid.sh >> logs/backup.log 2>&1
```

### Check 4: Backup File Created
```bash
ls -lh backups/

# Expected: At least 1 backup file
# backup_20260112_153045.tar.gz (50K-100K)
```

### Check 5: Backend Health
```bash
curl -f http://localhost:8001/health/

# Expected: {"status":"healthy"}
```

### Check 6: Frontend Accessibility
```bash
curl -I http://localhost:3001

# Expected: HTTP/1.1 200 OK
```

---

## 📊 Deployment Success Criteria

Mark these as you verify:

- [ ] All 6 containers running
- [ ] Storage owned by UID 995
- [ ] Storage permissions 775
- [ ] 3 cron jobs installed
- [ ] Test backup file exists
- [ ] Backend health responds
- [ ] Frontend loads
- [ ] No errors in logs

---

## 🌐 Browser Testing

After CLI verification passes, test in browser:

### 1. Access Frontend
- URL: `http://<staging-ip>:3001`
- **Expected:** Login page loads

### 2. Login
- Username: `admin`
- Password: `[as entered]`
- **Expected:** Dashboard loads successfully

### 3. Create Test Document
- Navigate to "My Documents"
- Click "Create New Document"
- Fill in:
  - Document Number: TEST-001
  - Title: Staging Deployment Test
  - Upload: Any test file
- Submit
- **Expected:** Document created, file uploaded successfully (proves storage permissions work)

### 4. Test Workflow
- Open TEST-001
- Submit for Review
- **Expected:** Status changes, no errors

---

## 📝 Notes & Observations

[Document any issues, warnings, or observations during deployment]

### Issues Encountered:


### Warnings Observed:


### Performance Notes:


### New Features Verified:
- [ ] Storage permissions auto-configured
- [ ] Backup cron jobs installed
- [ ] Test backup successful
- [ ] No manual permission fixes needed

---

## ✅ Final Status

**Deployment Status:** [ ] Success / [ ] Partial / [ ] Failed

**Time Taken:** ___ minutes

**Overall Assessment:**


---

**Deployment completed by:** ___________  
**Date/Time:** 2026-01-12 15:30 SGT
