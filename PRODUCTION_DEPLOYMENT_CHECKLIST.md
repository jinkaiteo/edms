# Production Deployment Checklist - v1.3.1

**Date:** 2026-01-30  
**Features:** Superuser Protection + Port Configuration Fix  
**Commits:** 0e39704, 9d241ec, 7a0a703, d0a4d30, 0db0987, b9f4834  

---

## 🎯 Pre-Deployment Checklist

### Preparation
- [ ] **Notify team** of scheduled deployment
- [ ] **Schedule deployment window** (recommended: off-peak hours)
- [ ] **Backup access ready** (SSH credentials, database access)
- [ ] **Rollback plan reviewed** (see section below)

### Documentation Review
- [ ] Read `DEPLOY_COMPLETE_SUPERUSER_FEATURE.md`
- [ ] Read `FIX_PRODUCTION_PORTS.md`
- [ ] Have rollback commands ready

---

## 🚀 Deployment Steps

### Phase 1: Pre-Deployment Backup (5 minutes) ⚠️ CRITICAL

```bash
# SSH to production
ssh user@production-server
cd /path/to/edms

# Create backup
./scripts/backup-hybrid.sh

# Record current commit for rollback
git rev-parse HEAD > /tmp/rollback_commit.txt
echo "Rollback commit: $(cat /tmp/rollback_commit.txt)"
```

**Checklist:**
- [ ] Backup completed successfully
- [ ] Backup file exists in `backups/` directory
- [ ] Backup file size reasonable (not 0 bytes)
- [ ] Rollback commit recorded

---

### Phase 2: Port Configuration Diagnosis (3 minutes)

```bash
cd /path/to/edms

# Run diagnostic
wget -O /tmp/check_ports.sh https://raw.githubusercontent.com/jinkaiteo/edms/main/CHECK_PRODUCTION_PORTS.sh
chmod +x /tmp/check_ports.sh
bash /tmp/check_ports.sh
```

**Checklist:**
- [ ] Diagnostic script executed
- [ ] Current ports identified (8000/3000 or 8001/3001?)
- [ ] Docker compose file identified (docker-compose.yml or docker-compose.prod.yml?)

**If using wrong ports (8000/3000), proceed to Phase 2A. Otherwise skip to Phase 3.**

---

### Phase 2A: Fix Port Configuration (5 minutes) - OPTIONAL

**Only if diagnostic showed wrong ports!**

```bash
cd /path/to/edms

# Stop services
docker compose down

# Set default compose file
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env

# Verify .env has correct ports
grep -E "BACKEND_PORT|FRONTEND_PORT" .env
# Should show: BACKEND_PORT=8001, FRONTEND_PORT=3001

# Start with production config
docker compose -f docker-compose.prod.yml up -d

# Verify correct ports
docker ps --format "table {{.Names}}\t{{.Ports}}"
# Should show: 0.0.0.0:8001->8000 and 0.0.0.0:3001->80
```

**Checklist:**
- [ ] Services stopped cleanly
- [ ] COMPOSE_FILE added to .env
- [ ] Services started on correct ports (8001/3001)
- [ ] All containers running and healthy

**If you fixed ports, you may need to update HAProxy/nginx configs!**

---

### Phase 3: Pull Latest Code (1 minute)

```bash
cd /path/to/edms

# Fetch latest
git fetch origin main
git checkout main
git pull origin main

# Verify commits
git log --oneline -6
```

**Expected output:**
```
0e39704 fix: Correct docker-compose file references and add port diagnostics
9d241ec docs: Add complete deployment guide for superuser feature
7a0a703 feat: Add frontend UI for superuser management
d0a4d30 docs: Add hotfix deployment guide for superuser protection
0db0987 fix: Add critical superuser protection to prevent admin lockout
b9f4834 docs: Add production deployment guide for v1.3.0
```

**Checklist:**
- [ ] Code pulled successfully
- [ ] All 6 commits present
- [ ] No merge conflicts
- [ ] Working directory clean

---

### Phase 4: Deploy Backend (2 minutes)

```bash
cd /path/to/edms

# Restart backend (code-only changes, no rebuild needed)
docker compose -f docker-compose.prod.yml restart backend

# Wait for startup
sleep 10

# Check status
docker compose -f docker-compose.prod.yml ps backend

# Check logs
docker compose -f docker-compose.prod.yml logs backend --tail=50 | grep -i error
```

**Checklist:**
- [ ] Backend restarted successfully
- [ ] Container status shows "Up" and "healthy"
- [ ] No error messages in logs
- [ ] Backend responds: `curl http://localhost:8001/api/v1/health/`

---

### Phase 5: Deploy Frontend (8 minutes)

```bash
cd /path/to/edms

# Rebuild frontend with new UI
docker compose -f docker-compose.prod.yml build frontend --no-cache

# This takes 5-8 minutes - wait for completion

# Start frontend with new image
docker compose -f docker-compose.prod.yml up -d frontend

# Check status
docker compose -f docker-compose.prod.yml ps frontend

# Check logs
docker compose -f docker-compose.prod.yml logs frontend --tail=50
```

**Checklist:**
- [ ] Frontend build completed without errors
- [ ] Container status shows "Up" and "healthy"
- [ ] No error messages in logs
- [ ] Frontend responds: `curl -I http://localhost:3001/`

---

### Phase 6: Health Verification (2 minutes)

```bash
# Backend health
curl http://localhost:8001/api/v1/health/
# Expected: {"status":"healthy"}

# Frontend accessible
curl -I http://localhost:3001/
# Expected: HTTP/1.1 200 OK

# Database accessible
docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_db -c "SELECT 1;"
# Expected: Returns 1

# Redis accessible
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Expected: PONG
```

**Checklist:**
- [ ] Backend health check passes
- [ ] Frontend returns 200 OK
- [ ] Database connection works
- [ ] Redis connection works
- [ ] All containers running

---

## ✅ Post-Deployment Testing

### Test 1: Login and Basic Functionality (3 minutes)

**In Browser:**
1. Navigate to `http://your-production-domain/`
2. Login with superuser credentials
3. Check dashboard loads
4. Check document list loads
5. Open a document

**Checklist:**
- [ ] Login successful
- [ ] Dashboard displays
- [ ] Navigation works
- [ ] Document list loads
- [ ] Document viewer opens
- [ ] No console errors (F12)

---

### Test 2: Superuser Protection (3 minutes)

**Test Backend Protection:**

```bash
# Get your superuser UUID
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.users.models import User
admin = User.objects.get(username='admin')
print(f'Admin UUID: {admin.uuid}')
print(f'Active superusers: {User.objects.filter(is_superuser=True, is_active=True).count()}')
"
```

**In Browser:**
1. Go to User Management
2. Click "Manage Roles" on your superuser account
3. **Look for new "Superuser Status" section at TOP of modal**
   - Should see: ⭐ Superuser
   - Purple gradient background
   - Red "Revoke Superuser" button

**Checklist:**
- [ ] Superuser status section appears at top of modal
- [ ] Shows ⭐ Superuser indicator
- [ ] Purple gradient background visible
- [ ] "Revoke Superuser" button present (red)
- [ ] Description text displays correctly

---

### Test 3: Protection Logic (2 minutes)

**Test: Cannot Revoke Last Superuser**

1. In the role management modal for your superuser
2. Click "Revoke Superuser" button
3. Confirm in dialog
4. Enter reason in prompt

**Expected Result:**
- ❌ Error popup appears
- Message: "Cannot revoke superuser status from the last superuser"
- Detail: "Please grant superuser status to another user first."
- Operation blocked ✅

**Checklist:**
- [ ] Error message displayed
- [ ] Operation blocked successfully
- [ ] User remains as superuser
- [ ] No errors in browser console

---

### Test 4: Grant Superuser (5 minutes)

**Create Backup Superuser:**

1. Go to User Management
2. Find a regular user (e.g., author01, reviewer01)
3. Click "Manage Roles" on that user
4. Should see "Regular User" status at top
5. Click "Grant Superuser" (purple button)
6. Enter reason: "Creating backup superuser for redundancy"

**Expected Result:**
- ✅ Success message appears
- User status updates to "⭐ Superuser"
- Button changes to "Revoke Superuser" (red)
- Indicator dot changes to purple

**Checklist:**
- [ ] Success message displayed
- [ ] User status updated in modal
- [ ] Button changed from Grant to Revoke
- [ ] User list shows updated status
- [ ] No errors in console

---

### Test 5: Verify Multiple Superusers (2 minutes)

```bash
# Check superuser count
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.users.models import User
superusers = User.objects.filter(is_superuser=True, is_active=True)
print(f'\nActive superusers: {superusers.count()}')
for u in superusers:
    print(f'  - {u.username} ({u.email})')
"
```

**Expected:** Should show 2 superusers now

**Checklist:**
- [ ] 2 superusers exist
- [ ] Original admin still superuser
- [ ] New user is superuser
- [ ] Both show is_superuser=True

---

### Test 6: Revoke Now Works (3 minutes)

**Test: Can Revoke When Multiple Superusers Exist**

1. Go back to your original superuser account
2. Click "Manage Roles"
3. Click "Revoke Superuser"
4. Confirm and provide reason

**Expected Result:**
- ✅ Success message appears
- Status changes to "Regular User"
- Button changes to "Grant Superuser"
- Operation succeeds (because 2+ superusers exist)

**Then restore it:**
1. Grant superuser back to your account
2. Revoke from the test user
3. Back to 1 superuser (your original account)

**Checklist:**
- [ ] Can revoke when 2+ superusers exist
- [ ] Success message displayed
- [ ] Status updated correctly
- [ ] Restored original state
- [ ] Protection still works (can't revoke last one)

---

## 🔍 Additional Verification

### System Health Checks

```bash
# Container status
docker compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream

# Recent errors in logs
docker compose -f docker-compose.prod.yml logs --tail=100 | grep -i error

# Disk space
df -h
```

**Checklist:**
- [ ] All containers "Up" and "healthy"
- [ ] CPU usage normal (< 80%)
- [ ] Memory usage normal (< 90%)
- [ ] No critical errors in logs
- [ ] Sufficient disk space (> 20% free)

---

### Feature Regression Tests

Test that existing features still work:

- [ ] User login
- [ ] Document creation
- [ ] Document upload
- [ ] Document approval workflow
- [ ] Email notifications (if configured)
- [ ] Search functionality
- [ ] Filters work
- [ ] Download documents
- [ ] Version history displays

---

## 📊 Deployment Summary

### Record Deployment Details

```bash
# Record deployment info
cat > /tmp/deployment_$(date +%Y%m%d_%H%M%S).txt << EOF
Deployment Date: $(date)
Deployed By: $(whoami)
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)

Container Status:
$(docker compose -f docker-compose.prod.yml ps)

Active Superusers:
$(docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.users.models import User
for u in User.objects.filter(is_superuser=True, is_active=True):
    print(f'{u.username}')
")

Health Check:
$(curl -s http://localhost:8001/api/v1/health/)
EOF

cat /tmp/deployment_$(date +%Y%m%d_%H%M%S).txt
```

---

## 📝 Post-Deployment Actions

### Immediate (Within 1 Hour)

- [ ] **Monitor logs** for errors
  ```bash
  docker compose -f docker-compose.prod.yml logs -f | grep -i error
  ```

- [ ] **Test user flows** (login, document access, workflows)

- [ ] **Notify team** deployment complete

- [ ] **Document any issues** encountered

---

### Short Term (Within 24 Hours)

- [ ] **Monitor application performance**
- [ ] **Check for user-reported issues**
- [ ] **Verify backup superuser documented**
- [ ] **Update internal documentation**
- [ ] **Review audit logs** for superuser changes

---

### Long Term (Within 1 Week)

- [ ] **Audit all superusers** - verify who has access
- [ ] **Document superuser procedures** for team
- [ ] **Schedule training** on new superuser management features
- [ ] **Review security practices**

---

## 🚨 Rollback Procedure

### If Critical Issues Arise

**Quick Rollback (Backend Only):**

```bash
cd /path/to/edms

# Get rollback commit
ROLLBACK_COMMIT=$(cat /tmp/rollback_commit.txt)

# Rollback code
git checkout $ROLLBACK_COMMIT

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

**Full Rollback (Backend + Frontend):**

```bash
cd /path/to/edms

# Get rollback commit
ROLLBACK_COMMIT=$(cat /tmp/rollback_commit.txt)

# Rollback code
git checkout $ROLLBACK_COMMIT

# Rebuild and restart
docker compose -f docker-compose.prod.yml build backend frontend
docker compose -f docker-compose.prod.yml up -d
```

**Database Restore (If Needed):**

```bash
cd /path/to/edms

# Find your backup
ls -lht backups/ | head -5

# Restore
./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

**Checklist for Rollback:**
- [ ] Services stopped
- [ ] Code reverted to previous commit
- [ ] Services restarted
- [ ] Health checks pass
- [ ] Application accessible
- [ ] Document why rollback was needed

---

## 📞 Support & Escalation

### If Issues Arise

**Check First:**
1. Browser console (F12) for frontend errors
2. Backend logs: `docker compose -f docker-compose.prod.yml logs backend --tail=100`
3. Frontend logs: `docker compose -f docker-compose.prod.yml logs frontend --tail=100`
4. Database connectivity: `docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_db -c "SELECT 1;"`

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Frontend not showing changes | Clear browser cache (Ctrl+F5) |
| "Cannot revoke last superuser" | This is CORRECT - create another superuser first |
| Superuser section not visible | Hard refresh browser, check if frontend rebuilt |
| API returns 403 | Check user is actually logged in as superuser |
| Services won't start | Check logs, verify ports not in use |

**Escalation:**
1. Try rollback procedure
2. Check documentation
3. Review GitHub issues
4. Contact system administrator

---

## ✅ Final Sign-Off

### Deployment Complete

**Deployed By:** ________________  
**Date/Time:** ________________  
**All Tests Pass:** ☐ Yes ☐ No  
**Issues Encountered:** ________________  
**Rollback Required:** ☐ Yes ☐ No  

**Deployment Status:**
- ☐ ✅ **Successful - All Features Working**
- ☐ ⚠️ **Successful - Minor Issues (documented)**
- ☐ ❌ **Failed - Rolled Back**

**Notes:**
```
[Space for deployment notes, issues, or observations]
```

---

## 📚 Reference Documentation

- `DEPLOY_COMPLETE_SUPERUSER_FEATURE.md` - Complete deployment guide
- `SUPERUSER_MANAGEMENT_GUIDE.md` - Usage guide
- `FIX_PRODUCTION_PORTS.md` - Port configuration guide
- `HOTFIX_DEPLOYMENT_SUPERUSER_PROTECTION.md` - Backend deployment
- `CHECK_PRODUCTION_PORTS.sh` - Diagnostic script
- `DEPLOY_HOTFIX_NOW.sh` - Automated deployment script

---

**Total Deployment Time:** ~20-30 minutes  
**Downtime:** ~30 seconds (backend restart only)  
**Complexity:** Medium  
**Risk Level:** Low (backward compatible, protection-only)  

---

*Checklist Version: 1.0*  
*Created: 2026-01-30*  
*Status: Production Ready*
