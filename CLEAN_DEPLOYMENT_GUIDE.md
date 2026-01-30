# Clean Deployment Guide - Start Fresh

**Purpose:** Complete clean deployment to resolve any configuration issues  
**Use When:** Experiencing persistent errors, port conflicts, or state issues  
**Duration:** 15-20 minutes  
**Downtime:** 5-10 minutes  

---

## 🎯 What is a Clean Deployment?

A clean deployment:
- ✅ Stops all containers
- ✅ Removes old containers and networks
- ✅ Rebuilds all images from scratch
- ✅ Clears any cached/stale configurations
- ✅ Starts fresh with latest code

**Does NOT:**
- ❌ Delete your database data
- ❌ Delete uploaded documents
- ❌ Delete backups
- ❌ Affect user accounts

---

## ⚠️ Pre-Deployment Backup (CRITICAL)

**ALWAYS backup before clean deployment!**

```bash
cd /path/to/edms

# Create backup
./scripts/backup-hybrid.sh

# Verify backup exists
ls -lh backups/ | tail -5

# Record backup filename
BACKUP_FILE=$(ls -t backups/backup_*.tar.gz | head -1)
echo "Backup: $BACKUP_FILE" > /tmp/clean_deploy_backup.txt
echo "Created: $(date)" >> /tmp/clean_deploy_backup.txt
```

**Checklist:**
- [ ] Backup completed successfully
- [ ] Backup file exists and has reasonable size
- [ ] Backup filename recorded

---

## 🧹 Step 1: Clean Shutdown (5 minutes)

### Stop All Services

```bash
cd /path/to/edms

# Stop services gracefully
docker compose -f docker-compose.prod.yml down

# Wait a moment
sleep 5

# Force stop any remaining containers
docker ps -a | grep edms | awk '{print $1}' | xargs -r docker stop

# Remove containers
docker ps -a | grep edms | awk '{print $1}' | xargs -r docker rm

# Check nothing is running
docker ps | grep edms
# Should return nothing
```

**Checklist:**
- [ ] All containers stopped
- [ ] All containers removed
- [ ] No edms containers in `docker ps`

---

## 🗑️ Step 2: Clean Old Images (Optional but Recommended)

```bash
# See current images
docker images | grep edms

# Remove old edms images (keeps volumes/data safe)
docker images | grep edms | awk '{print $3}' | xargs -r docker rmi -f

# Or clean all dangling images
docker image prune -f
```

**Checklist:**
- [ ] Old images removed
- [ ] Disk space freed

---

## 📥 Step 3: Get Latest Code

```bash
cd /path/to/edms

# Record current commit (for rollback)
git rev-parse HEAD > /tmp/pre_clean_deploy_commit.txt

# Ensure we're on main
git checkout main

# Pull latest
git fetch origin main
git pull origin main

# Verify we have latest commits
git log --oneline -7

# Should show:
# e62ccbc docs: Add comprehensive production deployment checklist
# 0e39704 fix: Correct docker-compose file references and add port diagnostics
# 9d241ec docs: Add complete deployment guide for superuser feature
# 7a0a703 feat: Add frontend UI for superuser management
# d0a4d30 docs: Add hotfix deployment guide for superuser protection
# 0db0987 fix: Add critical superuser protection to prevent admin lockout
# b9f4834 docs: Add production deployment guide for v1.3.0
```

**Checklist:**
- [ ] On main branch
- [ ] Code pulled successfully
- [ ] All 7 commits present
- [ ] No merge conflicts

---

## ⚙️ Step 4: Verify Configuration

### Check .env File

```bash
cd /path/to/edms

# Verify .env exists
ls -la .env

# Check critical settings
cat .env | grep -E "DB_NAME|DB_USER|DB_PASSWORD|BACKEND_PORT|FRONTEND_PORT|COMPOSE_FILE"

# Expected output should include:
# DB_NAME=edms_db
# DB_USER=edms_user
# DB_PASSWORD=edms_password
# BACKEND_PORT=8001
# FRONTEND_PORT=3001
# COMPOSE_FILE=docker-compose.prod.yml  # (This line might be new)
```

**If COMPOSE_FILE is missing, add it:**

```bash
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
```

**Checklist:**
- [ ] .env file exists
- [ ] Database credentials correct
- [ ] Port configuration correct (8001, 3001)
- [ ] COMPOSE_FILE set to docker-compose.prod.yml

---

## 🔨 Step 5: Build Fresh Images (5-8 minutes)

```bash
cd /path/to/edms

# Build all images from scratch (no cache)
docker compose -f docker-compose.prod.yml build --no-cache

# This takes 5-8 minutes
# You'll see:
# - Backend building Python dependencies
# - Frontend building npm packages and React app
# - Other services preparing
```

**Checklist:**
- [ ] Build started successfully
- [ ] No error messages during build
- [ ] All services built successfully
- [ ] Build completed without errors

---

## 🚀 Step 6: Start Services (2 minutes)

```bash
cd /path/to/edms

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to initialize
echo "Waiting for services to start..."
sleep 15

# Check status
docker compose -f docker-compose.prod.yml ps

# All services should show:
# - STATE: Up
# - STATUS: healthy (or starting)
```

**Checklist:**
- [ ] All services started
- [ ] No services in "Restarting" or "Exited" state
- [ ] Services showing "healthy" status

---

## ✅ Step 7: Health Verification

### Database Check

```bash
# Wait a bit more for full initialization
sleep 10

# Test database connection
docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_db -c "SELECT COUNT(*) FROM auth_user;"

# Should return number of users
```

### Backend Check

```bash
# Backend health
curl http://localhost:8001/api/v1/health/

# Expected: {"status":"healthy"}

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Look for:
# ✅ "Application startup complete"
# ✅ "Uvicorn running on..."
# ❌ No error messages
```

### Frontend Check

```bash
# Frontend health
curl -I http://localhost:3001/

# Expected: HTTP/1.1 200 OK

# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend --tail=50

# Look for:
# ✅ "nginx started successfully"
# ❌ No error messages
```

**Checklist:**
- [ ] Database accessible
- [ ] Backend health check passes
- [ ] Frontend returns 200 OK
- [ ] No errors in logs

---

## 🧪 Step 8: Functional Testing

### Test 1: Login

Open browser:
```
http://your-production-domain/
```

- [ ] Login page loads
- [ ] Can login with admin credentials
- [ ] Dashboard displays
- [ ] No console errors (F12)

### Test 2: Basic Functions

- [ ] Document list loads
- [ ] Can open a document
- [ ] Navigation works
- [ ] Filters work

### Test 3: Superuser Management

1. Go to User Management
2. Click "Manage Roles" on any user
3. Check for "Superuser Status" section at top

**Expected:**
- [ ] Superuser Status section visible
- [ ] Shows correct status (⭐ Superuser or Regular User)
- [ ] Grant/Revoke buttons present
- [ ] Purple gradient background

### Test 4: Superuser Protection

1. If logged in as superuser, go to User Management
2. Click "Manage Roles" on your account
3. Click "Revoke Superuser"

**Expected:**
- [ ] Error message appears
- [ ] Operation blocked
- [ ] Message says "cannot revoke last superuser"

---

## 🔍 Step 9: Verify All Services

```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps

# Check resource usage
docker stats --no-stream

# Check for any errors
docker compose -f docker-compose.prod.yml logs | grep -i error | tail -20

# Verify disk space
df -h
```

**Checklist:**
- [ ] All containers "Up" and "healthy"
- [ ] CPU usage normal (< 50%)
- [ ] Memory usage normal (< 80%)
- [ ] Disk space sufficient (> 20% free)
- [ ] No critical errors in logs

---

## 🎯 Step 10: Post-Deployment Actions

### Create Backup Superuser (Recommended)

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

```python
from apps.users.models import User

# Find a trusted user
alice = User.objects.get(username='author01')  # Replace with actual username
alice.is_superuser = True
alice.is_staff = True
alice.save()

print(f"✅ {alice.username} is now a superuser")
exit()
```

Or via UI:
1. User Management → Find user
2. Manage Roles → Grant Superuser

### Verify Superuser Count

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.users.models import User
count = User.objects.filter(is_superuser=True, is_active=True).count()
print(f'Active superusers: {count}')
for u in User.objects.filter(is_superuser=True, is_active=True):
    print(f'  - {u.username}')
"
```

**Checklist:**
- [ ] At least 2 superusers exist (for redundancy)
- [ ] Both superusers documented

---

## 📊 Clean Deployment Complete!

### Summary

**What was done:**
- ✅ Complete shutdown of old deployment
- ✅ Removed old containers and images
- ✅ Fresh build from latest code
- ✅ Started with clean configuration
- ✅ Verified all services healthy
- ✅ Tested core functionality
- ✅ Superuser features working

**Time taken:** ~_________ minutes  
**Issues encountered:** _________________  
**Resolution:** _________________________  

---

## 🔄 If Issues Persist

### Common Issues After Clean Deployment

#### Issue 1: Frontend Not Loading

**Symptoms:** Blank page, 404 errors, old version showing

**Cause:** Browser cache

**Solution:**
```bash
# Clear browser cache
# Chrome/Firefox: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
# Or use incognito/private mode

# Force frontend rebuild
docker compose -f docker-compose.prod.yml build frontend --no-cache
docker compose -f docker-compose.prod.yml up -d frontend --force-recreate
```

#### Issue 2: Backend Not Starting

**Symptoms:** Backend container keeps restarting

**Check logs:**
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

**Common causes:**
- Database connection issues
- Missing environment variables
- Port conflicts

**Solution:**
```bash
# Check database is running
docker compose -f docker-compose.prod.yml ps db

# Check environment variables
docker compose -f docker-compose.prod.yml exec backend env | grep DB_

# Check for port conflicts
netstat -tulpn | grep :8001
```

#### Issue 3: Database Connection Errors

**Symptoms:** Backend logs show "could not connect to database"

**Solution:**
```bash
# Restart database
docker compose -f docker-compose.prod.yml restart db

# Wait for database to be ready
sleep 10

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Check database logs
docker compose -f docker-compose.prod.yml logs db --tail=50
```

#### Issue 4: Superuser UI Not Showing

**Symptoms:** Manage Roles modal doesn't have Superuser Status section

**Cause:** Frontend cache or build issue

**Solution:**
```bash
# Verify frontend has latest code
docker compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html/static/js/

# Check build timestamp
docker compose -f docker-compose.prod.yml exec frontend find /usr/share/nginx/html -name "*.js" -ls | head -5

# If old, rebuild
docker compose -f docker-compose.prod.yml build frontend --no-cache
docker compose -f docker-compose.prod.yml up -d frontend --force-recreate

# Clear browser cache (Ctrl+F5)
```

---

## 🚨 Nuclear Option: Complete Reset

**Only if clean deployment doesn't work!**

This removes EVERYTHING including data (use backup to restore):

```bash
# DANGER: This removes ALL data!
cd /path/to/edms

# Stop everything
docker compose -f docker-compose.prod.yml down -v

# Remove all edms-related resources
docker ps -a | grep edms | awk '{print $1}' | xargs -r docker rm -f
docker images | grep edms | awk '{print $3}' | xargs -r docker rmi -f
docker volume ls | grep edms | awk '{print $2}' | xargs -r docker volume rm
docker network ls | grep edms | awk '{print $1}' | xargs -r docker network rm

# Rebuild from scratch
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Wait for initialization
sleep 30

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Restore data from backup
./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 📞 Getting Help

**Provide this information when asking for help:**

```bash
# Gather diagnostic info
cat > /tmp/diagnostic_info.txt << EOF
Date: $(date)
Git Commit: $(git rev-parse HEAD)
Docker Version: $(docker --version)
Docker Compose Version: $(docker compose version)

Container Status:
$(docker compose -f docker-compose.prod.yml ps)

Recent Backend Logs:
$(docker compose -f docker-compose.prod.yml logs backend --tail=50)

Recent Frontend Logs:
$(docker compose -f docker-compose.prod.yml logs frontend --tail=50)

Environment:
$(docker compose -f docker-compose.prod.yml exec backend env | grep -E "DB_|REDIS_|DJANGO_")
EOF

cat /tmp/diagnostic_info.txt
```

---

## ✅ Checklist Summary

### Pre-Deployment
- [ ] Backup created
- [ ] Current commit recorded

### Clean Deployment
- [ ] Services stopped and removed
- [ ] Old images cleaned
- [ ] Latest code pulled
- [ ] Configuration verified
- [ ] Fresh images built
- [ ] Services started successfully

### Verification
- [ ] Health checks pass
- [ ] Login works
- [ ] Basic functions work
- [ ] Superuser UI visible
- [ ] Protection works

### Post-Deployment
- [ ] Backup superuser created
- [ ] Services monitored
- [ ] Issues documented (if any)
- [ ] Team notified

---

**Clean deployment gives you a fresh start and resolves most configuration and caching issues!**

---

*Created: 2026-01-30*  
*Status: Ready to Use*
