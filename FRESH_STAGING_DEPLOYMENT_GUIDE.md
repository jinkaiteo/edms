# Fresh Staging Server Deployment Guide

## Overview

This guide walks you through deploying EDMS to a fresh staging server with all optimizations applied:
- ✅ Optimized email configuration (no container restarts)
- ✅ Proper env_file directive (email settings work correctly)
- ✅ Removed redundant collectstatic (10-20s faster)
- ✅ All latest fixes and improvements

## Prerequisites

### Server Requirements
- Ubuntu 20.04+ / Debian 11+
- 2GB+ RAM
- 20GB+ disk space
- Docker & Docker Compose installed
- Git installed
- Ports available: 8001 (backend), 3001 (frontend)

### Access Requirements
- SSH access to staging server
- Sudo privileges
- Email credentials (Gmail app password or SMTP)

---

## Step-by-Step Deployment

### 1. Connect to Staging Server

```bash
ssh user@your-staging-server
```

### 2. Install Prerequisites (if not installed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install -y git

# Log out and back in for docker group to take effect
exit
```

### 3. Clone Repository

```bash
# SSH back in after logout
ssh user@your-staging-server

# Create deployment directory
mkdir -p ~/edms
cd ~/edms

# Clone repository
git clone https://github.com/jinkaiteo/edms.git .

# Verify you have latest changes
git pull origin main
git log --oneline -5

# Should show:
# a33caeb perf: Remove redundant collectstatic executions
# 7149860 fix: Use env_file directive to properly load email configuration
# e36b2af feat: Add optimized deployment script (deploy-interactive-fast.sh)
```

### 4. Run Deployment Script

```bash
# Use the stable, working deployment script
./deploy-interactive.sh

# Note: deploy-interactive-fast.sh exists but may have timing issues
# Use deploy-interactive.sh for reliable deployment
```

### 5. Deployment Script Prompts

The script will guide you through configuration:

#### A. Server Configuration
```
Server IP: [auto-detected]
Server hostname: your-staging-server.com (or leave blank)
Backend port: 8001 (press Enter)
Frontend port: 3001 (press Enter)
```

#### B. Application Configuration
```
Application title: EDMS (or customize)
Session timeout: 3600 (1 hour, press Enter)
```

#### C. Email Configuration (BEFORE Deployment - Optimized!)
```
Configure email notifications now? y

Select email provider:
  1) Gmail
  2) Microsoft 365
  3) Custom SMTP
  4) Skip

Choice: 1 (for Gmail)

Gmail address: your-email@gmail.com
Gmail app password: [16-character app password]

Send test email to: your-test-email@domain.com
```

**Note**: Email is configured BEFORE deployment starts (optimization), so no container restart needed!

#### D. HAProxy Configuration
```
Would you like to use HAProxy? N (for staging, direct access)
```

#### E. Admin User Creation
```
Create admin user now? y

Username: admin
Email: admin@yourcompany.com
Password: [secure password]
Password (again): [confirm]
```

#### F. Backup Automation
```
Set up automated backups now? y

(Script configures daily/weekly/monthly backups)
```

### 6. Wait for Deployment to Complete

The script will:
1. ✅ Create .env file with your configuration
2. ✅ Configure email settings (BEFORE deployment - fast!)
3. ✅ Build Docker images (~5-10 minutes first time)
4. ✅ Start containers (~10 seconds - optimized!)
5. ✅ Run database migrations
6. ✅ Create 7 roles, 6 groups, 32 placeholders
7. ✅ Create test users (author01, reviewer01, approver01)
8. ✅ Initialize workflows and scheduler
9. ✅ Test email configuration
10. ✅ Set up backup automation

**Total time**: 10-15 minutes (optimized!)

---

## Post-Deployment Verification

### 7. Verify Deployment

#### A. Check Container Status
```bash
docker compose -f docker-compose.prod.yml ps

# All containers should show "Up" and "healthy"
```

#### B. Verify Static Files (New!)
```bash
./verify_static_files.sh

# Should show all checks passed
```

#### C. Test Backend Health
```bash
curl http://localhost:8001/health/

# Should return: {"status": "healthy"}
```

#### D. Test Frontend
```bash
curl http://localhost:3001/

# Should return HTML (React app)
```

#### E. Test Django Admin
```bash
# Open in browser:
http://your-staging-server:8001/admin/

# Login with admin credentials
# Verify styling loads correctly (static files working)
```

#### F. Test Email (if configured)
```bash
# Email test already ran during deployment
# Check the inbox you specified
# Should have "EDMS Email Test - Deployment Verification" message
```

### 8. Create Test Documents

```bash
# Access frontend
http://your-staging-server:3001/

# Login as:
Username: author01
Password: Test@12345

# Create a test document to verify workflow
```

---

## Verification Checklist

Print this checklist and verify each item:

- [ ] All containers running and healthy
- [ ] Backend health check passes (http://localhost:8001/health/)
- [ ] Frontend accessible (http://your-staging-server:3001/)
- [ ] Django admin accessible and styled correctly
- [ ] Can login with admin user
- [ ] Can login with test users (author01, reviewer01, approver01)
- [ ] Static files verification passed (./verify_static_files.sh)
- [ ] Email test received (if configured)
- [ ] Can create a document
- [ ] Can submit document for review
- [ ] Workflow notifications work
- [ ] No errors in logs

---

## Performance Verification

### Test Container Restart Speed (Optimized!)

```bash
# Time a container restart
time docker compose -f docker-compose.prod.yml restart backend

# Should take 5-10 seconds (optimized)
# Old: 15-20 seconds
```

### Test Full Deployment Time

```bash
# Run comprehensive test
./test_optimized_deployment.sh

# Verifies:
# - Static files work without runtime collection
# - Container startup is fast
# - All services functional
```

---

## Common Issues & Solutions

### Issue 1: Email Test Fails with "Connection refused"

**Old behavior**: Email config failed even after fixes

**Current behavior**: Should work! Email is properly loaded via env_file.

**Verify**:
```bash
# Check container has correct email settings
docker compose exec backend env | grep EMAIL

# Should show:
# EMAIL_HOST=smtp.gmail.com (not localhost!)
# EMAIL_PORT=587
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

**If still fails**:
```bash
# Check .env file
grep EMAIL .env

# Recreate containers to reload .env
docker compose down
docker compose up -d
```

### Issue 2: Django Admin Has No Styling

**Old behavior**: Sometimes static files missing

**Current behavior**: Should always work! Files baked into image.

**Verify**:
```bash
./verify_static_files.sh

# Check specific CSS
curl -I http://localhost:8001/static/admin/css/base.css
# Should return: 200 OK
```

**If fails**:
```bash
# Rebuild image with static files
docker compose build backend
docker compose up -d
```

### Issue 3: Containers Start Slowly

**Expected**: First build takes 5-10 minutes, startup ~10 seconds
**Optimized**: Container restarts now 5-10 seconds (not 15-20s)

**If slower**:
```bash
# Check what's running during startup
docker compose logs backend --tail=50
```

### Issue 4: Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8001

# Stop conflicting service or change port in .env
```

---

## Environment Configuration

### .env File Location

After deployment, your `.env` file is at:
```
/home/user/edms/.env
```

### Key Settings to Verify

```bash
cat .env | grep -E "EMAIL|SECRET|DB_|BACKEND_PORT|FRONTEND_PORT"

# Should show:
# EMAIL_HOST=smtp.gmail.com (or your SMTP)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# SECRET_KEY=[generated key]
# DB_NAME=edms_prod_db
# BACKEND_PORT=8001
# FRONTEND_PORT=3001
```

---

## Accessing the Application

### Frontend (User Interface)
```
URL: http://your-staging-server:3001/
```

### Backend API
```
URL: http://your-staging-server:8001/api/v1/
```

### Django Admin
```
URL: http://your-staging-server:8001/admin/
Username: [your admin username]
Password: [your admin password]
```

### Test Users

| Username | Password | Role |
|----------|----------|------|
| author01 | Test@12345 | Author |
| reviewer01 | Test@12345 | Reviewer |
| approver01 | Test@12345 | Approver |

---

## Maintenance Commands

### View Logs
```bash
# All containers
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery_worker
```

### Restart Services
```bash
# All services
docker compose restart

# Specific service (fast - 5-10s!)
docker compose restart backend
```

### Update Code
```bash
cd ~/edms
git pull origin main

# Rebuild if needed
docker compose build backend
docker compose up -d
```

### Backup Database
```bash
./scripts/backup-hybrid.sh

# Backups stored in: ./backups/
```

### Restore Database
```bash
./scripts/restore-hybrid.sh

# Lists available backups, choose one to restore
```

---

## Performance Metrics

### Expected Performance (Optimized)

| Operation | Time | Notes |
|-----------|------|-------|
| First deployment | 10-15 min | Includes Docker image build |
| Container startup | 5-10s | Optimized (no collectstatic) |
| Container restart | 5-10s | Optimized (no collectstatic) |
| Code update deploy | 2-3 min | Rebuild + restart |
| Email test | <5s | No container restart |

### Savings from Optimizations

| Optimization | Time Saved | Frequency |
|--------------|------------|-----------|
| Email config order | 15s | Per deployment |
| Removed collectstatic | 10-20s | Per restart |
| env_file directive | 0s | Reliability fix |
| **Total per restart** | **25-35s** | **10x/week = 4.3h/year** |

---

## What's Different in This Deployment

### Compared to Old Deployment Scripts

✅ **Email configured BEFORE deployment** - No container restart after email config
✅ **env_file directive** - Email settings properly loaded from .env
✅ **No redundant collectstatic** - Static files only collected once (in image build)
✅ **Faster container startup** - 5-10s instead of 15-20s
✅ **Comprehensive verification** - Built-in testing scripts

### Scripts Available

```bash
deploy-interactive-fast.sh       # Optimized deployment (recommended)
deploy-interactive.sh            # Standard deployment (also optimized)
verify_static_files.sh          # Verify static files work
test_optimized_deployment.sh    # Full deployment test
diagnose_email_root_cause.sh    # Email troubleshooting
check_email_config.sh           # Check email settings
quick_test_collectstatic.sh     # Verify optimization applied
```

---

## Next Steps After Deployment

1. **Configure Production Settings**
   - Update ALLOWED_HOSTS in .env
   - Set up SSL/TLS certificates
   - Configure firewall rules

2. **Set Up Monitoring**
   - Configure Sentry (if using)
   - Set up log aggregation
   - Enable backup notifications

3. **User Training**
   - Create user documentation
   - Train document authors
   - Train reviewers/approvers

4. **Production Deployment**
   - Use same process on production server
   - Switch to production email SMTP
   - Configure HAProxy for load balancing

---

## Support

### Documentation Files

- `COLLECTSTATIC_OPTIMIZATION.md` - Static files optimization details
- `EMAIL_CONFIGURATION_ROOT_CAUSE_FIX.md` - Email configuration fix
- `DEPLOYMENT_OPTIMIZATION_SUMMARY.md` - All optimizations summary
- `README.md` - Project overview

### Diagnostic Scripts

```bash
./verify_static_files.sh          # 10-point static files check
./diagnose_email_root_cause.sh    # Email configuration check
./check_email_config.sh           # Email settings verification
```

### Getting Help

1. Check container logs: `docker compose logs -f`
2. Run verification scripts
3. Review documentation files
4. Check recent commits: `git log --oneline -10`

---

## Date
2026-01-24

## Version
Deployment Guide v1.1 (Optimized)
