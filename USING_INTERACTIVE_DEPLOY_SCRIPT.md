# Using Interactive Deployment Script for Fresh Staging Deployment

**Date:** January 16, 2026
**Purpose:** Fresh deployment using existing `deploy-interactive.sh` script

---

## 🚀 Deployment Steps

### Step 1: SSH to Staging Server

```bash
ssh lims@staging-server-ubuntu-20
```

### Step 2: Clean Up Old Deployment (Recommended for Fresh Start)

```bash
cd ~/edms

# Stop and remove everything (including volumes)
docker compose down -v

# Optional but recommended: Remove all Docker resources
docker system prune -a --volumes -f
```

### Step 3: Ensure Latest Code

```bash
cd ~/edms

# Pull latest code (includes scheduler timeout fix)
git fetch origin
git pull origin main

# Verify you have the fix
git log --oneline -1
# Should show: 79d75df fix(scheduler): Replace synchronous task execution...
```

### Step 4: Run Interactive Deployment Script

```bash
cd ~/edms

# Make script executable (if not already)
chmod +x deploy-interactive.sh

# Run the interactive deployment
./deploy-interactive.sh
```

---

## 📋 Interactive Script Options

The script will guide you through these choices:

### 1️⃣ **Deployment Type Selection**

```
Select deployment type:
1) Development
2) Staging  ← SELECT THIS
3) Production
```

**Choose:** `2` (Staging)

---

### 2️⃣ **Deployment Action Selection**

```
Select deployment action:
1) Fresh deployment (clean slate)  ← SELECT THIS FOR FRESH START
2) Update existing deployment
3) Rebuild containers only
4) Restart services
```

**Choose:** `1` (Fresh deployment)

This will:
- Stop all containers
- Remove volumes
- Rebuild from scratch
- Initialize database
- Set up system defaults

---

### 3️⃣ **Database Initialization**

```
Initialize database? (y/n)
```

**Choose:** `y` (Yes)

This will:
- Run migrations
- Create admin user (interactive prompt)
- Set up default data

---

### 4️⃣ **Create Admin User**

```
Create superuser? (y/n)
```

**Choose:** `y` (Yes)

When prompted:
```
Username: admin
Email: admin@edms.local
Password: admin123
Password (again): admin123
```

---

### 5️⃣ **Initialize System Data**

```
Initialize system defaults? (y/n)
```

**Choose:** `y` (Yes)

This will:
- Create default groups
- Create default roles
- Set up document types
- Initialize workflows
- Create test users

---

### 6️⃣ **Health Check**

```
Run health check? (y/n)
```

**Choose:** `y` (Yes)

This verifies all services are running correctly.

---

## 🎯 Expected Process Flow

```
1. Select: Staging deployment
   ↓
2. Select: Fresh deployment
   ↓
3. Script stops containers
   ↓
4. Script removes volumes
   ↓
5. Script rebuilds containers (5-10 min)
   ↓
6. Script starts services
   ↓
7. You create admin user (interactive)
   ↓
8. Script initializes system data
   ↓
9. Script runs health check
   ↓
10. ✅ Deployment complete!
```

---

## 📝 Quick Reference Commands

```bash
# SSH to staging
ssh lims@staging-server-ubuntu-20

# Navigate to project
cd ~/edms

# Pull latest code
git pull origin main

# Verify scheduler fix is included
git log --oneline -1

# Run interactive deployment
./deploy-interactive.sh

# Follow prompts:
# 1. Choose: 2 (Staging)
# 2. Choose: 1 (Fresh deployment)
# 3. Choose: y (Initialize database)
# 4. Choose: y (Create superuser) → admin/admin123
# 5. Choose: y (Initialize system defaults)
# 6. Choose: y (Run health check)
```

---

## ✅ After Deployment

### Verify Services Are Running

```bash
docker compose ps

# Expected output:
# NAME                 STATUS
# edms_backend         Up
# edms_frontend        Up
# edms_celery_worker   Up (may show unhealthy but still works)
# edms_celery_beat     Up
# edms_db              Up
# edms_redis           Up
```

### Test Login

**Browser:**
- URL: `http://your-staging-server:3000`
- Username: `admin`
- Password: `admin123`

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/session/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Test Scheduler Fix

```bash
# Test manual trigger (should respond instantly)
time curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}'

# Expected: Response in <1 second with "success": true
```

---

## 🔧 Troubleshooting

### Issue: Script not found

```bash
# Check if script exists
ls -la deploy-interactive.sh

# If not in root, check scripts directory
ls -la scripts/deploy-interactive.sh

# If in scripts directory, run:
./scripts/deploy-interactive.sh
```

### Issue: Permission denied

```bash
chmod +x deploy-interactive.sh
./deploy-interactive.sh
```

### Issue: Celery shows unhealthy

This is normal! Check if it's actually working:

```bash
docker logs edms_celery_worker --tail=50
# Look for: "celery@... ready"
```

### Issue: Can't login after deployment

Reset admin password:

```bash
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
admin = User.objects.get(username='admin')
admin.set_password('admin123')
admin.save()
print('✅ Password reset to: admin123')
"
```

---

## 🎊 What's Included

Your fresh deployment will have:

✅ **Latest code with scheduler timeout fix** (commit 79d75df)
✅ **Clean database** with proper migrations
✅ **Admin user** (admin/admin123)
✅ **Test users** (author01, reviewer01, approver01 / test123)
✅ **Default workflows** (Draft → Review → Approval)
✅ **Document types** (SOP, Policy, Procedure, etc.)
✅ **System roles** (Author, Reviewer, Approver, Admin)
✅ **Scheduler** with instant manual trigger (no 30s timeout!)

---

## 📊 Expected Timeline

- **Container rebuild:** 5-10 minutes
- **Database initialization:** 2-3 minutes
- **System setup:** 1-2 minutes
- **Total:** ~15 minutes

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ All 6 containers running
- ✅ Can login with admin/admin123
- ✅ Frontend loads at port 3000
- ✅ Backend API responds at port 8000
- ✅ Scheduler manual trigger responds in <1 second
- ✅ No timeout errors when triggering tasks

---

## 📚 Additional Resources

- **Full deployment guide:** `FRESH_STAGING_DEPLOYMENT_STEPS.md`
- **Scheduler documentation:** `SCHEDULER_SYSTEM_ANALYSIS.md`
- **Timeout fix details:** `SCHEDULER_TIMEOUT_FIX_SUMMARY.md`

---

**You're ready to deploy! Good luck! 🚀**

Let me know if you encounter any issues during the interactive deployment.
