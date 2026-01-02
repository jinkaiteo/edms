# Fresh Deployment Guide - Staging Server

## 🎯 Complete Teardown and Fresh Setup

This guide will completely remove the existing deployment and set up a fresh instance from scratch.

---

## ⚠️ **WARNING: Data Loss**

This will **DELETE ALL DATA** including:
- All documents
- All users (except those recreated)
- All workflows
- All database records
- All uploaded files

**Only proceed if you have backups or this is acceptable!**

---

## 📋 **Step-by-Step Teardown**

### Step 1: Stop All Services

```bash
cd /home/lims/edms-staging

# Stop all Docker containers
docker compose -f docker-compose.prod.yml down

# Verify containers are stopped
docker ps | grep edms
# Should return nothing
```

### Step 2: Stop HAProxy (if running)

```bash
# Check if HAProxy is running
sudo systemctl status haproxy

# Stop HAProxy
sudo systemctl stop haproxy

# Disable from auto-start (optional)
sudo systemctl disable haproxy
```

### Step 3: Remove Docker Volumes (Database & Files)

```bash
# List all edms-related volumes
docker volume ls | grep edms

# Remove all edms volumes (THIS DELETES ALL DATA)
docker volume rm edms-staging_postgres_data
docker volume rm edms-staging_redis_data
docker volume rm edms-staging_media_files
docker volume rm edms-staging_static_files

# Or remove all unused volumes
docker volume prune -f
```

### Step 4: Remove Docker Images (Force Fresh Build)

```bash
# List edms images
docker images | grep edms

# Remove edms images
docker rmi edms-staging-backend
docker rmi edms-staging-frontend
docker rmi edms-staging-celery_worker
docker rmi edms-staging-celery_beat

# Or remove all unused images
docker image prune -a -f
```

### Step 5: Clean Up Application Files (Optional)

```bash
cd /home/lims/edms-staging

# Remove any local database files
rm -f backend/*.sqlite3
rm -f backend/edms_*.sqlite3

# Remove uploaded files
rm -rf backend/media/*

# Remove static files
rm -rf backend/staticfiles/*

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove node_modules (will be rebuilt)
rm -rf frontend/node_modules

# Remove logs
rm -rf logs/*
```

### Step 6: Clean Up Environment Files

```bash
# Check for old environment files
ls -la backend/.env*

# Backup if needed
cp backend/.env backend/.env.backup.old

# Remove old env file (will be recreated by deployment script)
rm -f backend/.env
```

---

## 🚀 **Fresh Deployment**

### Step 1: Ensure Code is Up to Date

```bash
cd /home/lims/edms-staging

# Stash any local changes
git stash

# Pull latest code
git checkout develop
git pull origin develop

# Verify you have the latest
git log --oneline -1
# Should show: "fix: Add workflow initialization to deployment scripts"
```

### Step 2: Run Interactive Deployment Script

```bash
bash deploy-interactive.sh
```

**What the script will do:**

1. ✅ Check prerequisites (Docker, ports)
2. ✅ Generate secure passwords
3. ✅ Create `.env` file
4. ✅ Build Docker images from scratch
5. ✅ Start all services
6. ✅ Run database migrations
7. ✅ Create default roles and groups
8. ✅ Create default document types
9. ✅ **Initialize workflow states and types** ← NEW!
10. ✅ Create test users
11. ✅ Collect static files
12. ✅ Health checks

### Step 3: Configure HAProxy (if needed)

If you want to use HAProxy again:

```bash
# Edit HAProxy config if needed
sudo nano /etc/haproxy/haproxy.cfg

# Start HAProxy
sudo systemctl start haproxy
sudo systemctl enable haproxy

# Verify
sudo systemctl status haproxy
```

---

## 🧪 **Verification Steps**

### 1. Check All Services are Running

```bash
docker compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                      STATUS
edms_prod_backend         Up (healthy)
edms_prod_celery_beat     Up
edms_prod_celery_worker   Up
edms_prod_db              Up (healthy)
edms_prod_frontend        Up
edms_prod_redis           Up (healthy)
```

### 2. Check Database Initialization

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'EOF'
from apps.workflows.models import DocumentState, WorkflowType
from apps.users.models import User
from apps.documents.models import DocumentType

print(f"DocumentStates: {DocumentState.objects.count()}")
print(f"WorkflowTypes: {WorkflowType.objects.count()}")
print(f"Users: {User.objects.count()}")
print(f"DocumentTypes: {DocumentType.objects.count()}")

# Check for EFFECTIVE state
effective = DocumentState.objects.filter(code='EFFECTIVE')
print(f"\nEFFECTIVE state exists: {effective.exists()}")
if effective.exists():
    print(f"EFFECTIVE state name: {effective.first().name}")
EOF
```

**Expected Output:**
```
DocumentStates: 12
WorkflowTypes: 4
Users: 4 (or more)
DocumentTypes: 6

EFFECTIVE state exists: True
EFFECTIVE state name: Effective
```

### 3. Test Frontend Access

```bash
# If using HAProxy
curl -I http://172.28.1.148/

# If direct access
curl -I http://172.28.1.148:3001/
```

**Expected:** HTTP 200 OK

### 4. Test Login

Open browser and navigate to:
- With HAProxy: `http://172.28.1.148/login`
- Direct: `http://172.28.1.148:3001/login`

**Test Users:**
- `admin` / (password from .env or script output)
- `author01` / `test123`
- `reviewer01` / `test123`
- `approver01` / `test123`

---

## 📊 **Complete Workflow Test**

### 1. Login as author01

```
Username: author01
Password: test123
```

### 2. Create a Document

- Go to "Create Document"
- Title: "Test Policy"
- Type: Policy (POL)
- Click "Create"

### 3. Submit for Review

- Select the document
- Click "Submit for Review"
- Select reviewer: `reviewer01`
- Click "Submit"
- **Verify:** Status changes to "Pending Review"

### 4. Logout and Login as reviewer01

```
Username: reviewer01
Password: test123
```

- Go to "My Tasks"
- Find the document
- Click "Review" → "Approve"
- **Verify:** Status changes to "Pending Approval"

### 5. Logout and Login as approver01

```
Username: approver01
Password: test123
```

- Go to "My Tasks"
- Find the document
- Click "Approve"
- Set effective date: Today's date
- Click "Approve"
- **Verify:** Status changes to **"EFFECTIVE"** ✅ (not APPROVED_AND_EFFECTIVE)

### 6. Test Dependencies

- Login as `author01`
- Create another document "Test SOP"
- Click Edit
- In "Referenced Documents" section, search and select "Test Policy"
- Save
- **Verify:** Dependency shows in document viewer

---

## 🔧 **Troubleshooting**

### Issue: Port 80 Already in Use

```bash
# Check what's using port 80
sudo lsof -i :80

# If it's HAProxy
sudo systemctl stop haproxy

# If it's nginx
sudo systemctl stop nginx

# Try deployment again
```

### Issue: Docker Volume Won't Delete

```bash
# Force stop all containers
docker stop $(docker ps -aq)

# Remove containers
docker rm $(docker ps -aq)

# Try volume removal again
docker volume rm edms-staging_postgres_data
```

### Issue: Permission Denied on Files

```bash
cd /home/lims/edms-staging

# Fix ownership
sudo chown -R $USER:$USER .

# Fix permissions
chmod -R 755 scripts/
```

### Issue: "No REVIEW workflow type found"

This means workflow initialization didn't run. Manually run:

```bash
cd /home/lims/edms-staging
bash scripts/initialize-workflow-defaults.sh
```

---

## 📝 **Verification Checklist**

After fresh deployment, verify:

- [ ] All Docker containers are running and healthy
- [ ] Database has 12 DocumentStates
- [ ] Database has 4 WorkflowTypes
- [ ] EFFECTIVE state exists (not APPROVED_AND_EFFECTIVE)
- [ ] Test users can login
- [ ] Documents can be created
- [ ] Review workflow works
- [ ] Approval workflow works
- [ ] Final status is EFFECTIVE
- [ ] Dependencies display correctly
- [ ] PDF download works
- [ ] No console errors in browser

---

## 🎉 **Success Criteria**

Fresh deployment is successful when:

1. ✅ All services start without errors
2. ✅ Database has all required defaults
3. ✅ Users can login
4. ✅ Complete workflow (draft → review → approve → effective) works
5. ✅ Documents show status as "EFFECTIVE" (not "APPROVED_AND_EFFECTIVE")
6. ✅ Dependencies display correctly
7. ✅ No "No REVIEW workflow type found" errors
8. ✅ Frontend shows no console errors

---

## 🔄 **Rollback Plan**

If fresh deployment fails:

1. Stop services: `docker compose -f docker-compose.prod.yml down`
2. Restore from backup (if available)
3. Report errors for investigation
4. Keep old .env file for reference

---

## 📞 **Support**

If you encounter issues:

1. Check logs: `docker compose -f docker-compose.prod.yml logs backend`
2. Check the troubleshooting section above
3. Refer to documentation:
   - `DEPENDENCY_DISPLAY_FIX.md`
   - `DOCUMENT_WORKFLOW_STATES_ANALYSIS.md`
   - `DEPLOYMENT_QUICK_START.md`

---

**Last Updated:** 2026-01-01  
**Tested On:** Staging Server 172.28.1.148  
**Status:** ✅ Verified working
