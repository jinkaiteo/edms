# Fresh Staging Deployment - Interactive Script Guide

## ✅ Frontend Changes Status

**All frontend changes are committed and pushed to GitHub!**

### Commits on GitHub (develop branch):
- ✅ **`6d1f3dd`** - Deployment scripts and documentation
- ✅ **`29e6433`** - Frontend authentication redirect to DocumentManagement page
- ✅ **`7c2392d`** - Staging HAProxy test deployment guide
- ✅ **Plus all other frontend improvements**

### What's in the Frontend Authentication Fix (29e6433):
```typescript
// frontend/src/pages/DocumentManagement.tsx
useEffect(() => {
  if (!user) {
    navigate('/login');  // Redirects to login if not authenticated
  }
}, [user, navigate]);
```

**This prevents unauthorized access to document management pages.**

---

## 🚀 Deploy to Fresh Staging Server

You have **3 deployment options** for your fresh staging server:

### Option 1: Interactive Deployment Script (Recommended for Fresh Setup)

The `deploy-interactive.sh` script will:
- ✅ Collect configuration (server IP, paths, ports)
- ✅ Transfer files to staging server
- ✅ Set up Docker environment
- ✅ Pull code from GitHub
- ✅ Build and start all services
- ✅ Initialize database
- ✅ Create default users
- ✅ Run health checks

### Option 2: Manual Fresh Deployment

Step-by-step manual setup for complete control.

### Option 3: Quick Deployment (For Existing Setup)

If staging already has Docker and project files.

---

## 📋 Option 1: Interactive Deployment Script (Recommended)

### Prerequisites

1. **Fresh staging server** at `172.28.1.148`
2. **SSH access** configured: `ssh lims@172.28.1.148`
3. **Docker** installed on staging (or script can help install)
4. **GitHub access** configured on staging server

### Step 1: Prepare Local Environment

```bash
# Ensure you're in the project root
cd /path/to/edms

# Verify you have the interactive script
ls -lh deploy-interactive.sh

# Make it executable (if not already)
chmod +x deploy-interactive.sh
```

### Step 2: Run Interactive Deployment Script

```bash
./deploy-interactive.sh
```

### Step 3: Follow Interactive Prompts

The script will ask you:

#### **1. Deployment Type**
```
Select deployment type:
1) Development
2) Staging
3) Production
```
**Choose**: `2` (Staging)

#### **2. Server Configuration**
```
Enter server IP/hostname: [default: 172.28.1.148]
Enter SSH user: [default: lims]
Enter deployment path: [default: /home/lims/edms-staging]
```
**Use defaults** or customize

#### **3. Port Configuration**
```
Frontend port: [default: 3001]
Backend port: [default: 8001]
Database port: [default: 5433]
Redis port: [default: 6380]
```
**Use defaults** or customize

#### **4. Database Configuration**
```
Database name: [default: edms_staging]
Database user: [default: edms_user]
Database password: [will be generated or enter custom]
```

#### **5. GitHub Configuration**
```
GitHub repository: [default: https://github.com/jinkaiteo/edms.git]
Branch: [default: develop]
```
**Use defaults** to pull the latest frontend changes

#### **6. Installation Options**
```
Install Docker? (y/n)
Set up backup automation? (y/n)
Initialize default data? (y/n)
```

### Step 4: Script Actions

The script will automatically:

1. **Transfer files** to staging server
2. **Install Docker** (if needed)
3. **Clone repository** from GitHub
4. **Checkout develop branch** (includes frontend changes!)
5. **Create environment files**
6. **Build Docker images**
7. **Start services**:
   - PostgreSQL database
   - Redis cache
   - Django backend
   - Celery worker
   - Celery beat
   - React frontend (with authentication fix!)
8. **Run migrations**
9. **Create superuser**
10. **Initialize default data**
11. **Health checks**

### Step 5: Verify Deployment

After script completes:

```bash
# SSH to staging
ssh lims@172.28.1.148

# Check services
cd /home/lims/edms-staging
docker compose -f docker-compose.prod.yml ps

# Should show all services "Up"
```

---

## 📋 Option 2: Manual Fresh Deployment

If you prefer manual control:

### Step 1: SSH to Staging Server

```bash
ssh lims@172.28.1.148
```

### Step 2: Clone Repository from GitHub

```bash
# Create project directory
mkdir -p /home/lims/edms-staging
cd /home/lims/edms-staging

# Clone from GitHub
git clone https://github.com/jinkaiteo/edms.git .

# Checkout develop branch (has all frontend changes)
git checkout develop

# Verify you have the latest commits
git log -3 --oneline
# Should show:
# 6d1f3dd docs: Add comprehensive staging deployment scripts and guides
# 29e6433 fix: Add authentication redirect to DocumentManagement page
# 7c2392d docs: Add staging HAProxy test deployment guide
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit configuration
nano backend/.env
```

Update these values:
```bash
DEBUG=False
DJANGO_SETTINGS_MODULE=edms.settings.production
DB_HOST=db
DB_NAME=edms_staging
DB_USER=edms_user
DB_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=172.28.1.148,localhost
```

### Step 4: Build and Start Services

```bash
# Build all services
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to start
sleep 30

# Check status
docker compose -f docker-compose.prod.yml ps
```

### Step 5: Initialize Database

```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Initialize default data (optional)
docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_groups
docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_roles
```

### Step 6: Verify Deployment

```bash
# Check frontend
curl http://localhost:3001/

# Check backend API
curl http://localhost:8001/health/

# Check logs
docker compose -f docker-compose.prod.yml logs --tail=20 frontend
docker compose -f docker-compose.prod.yml logs --tail=20 backend

# Exit SSH
exit
```

---

## 📋 Option 3: Quick Deployment (Existing Setup)

If staging already has the project:

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Pull latest from GitHub (includes frontend changes)
git fetch origin
git checkout develop
git pull origin develop

# Verify commits
git log -3 --oneline

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose -f docker-compose.prod.yml ps
curl http://localhost:3001/
```

---

## 🧪 Test Frontend Authentication Fix

After deployment, test in **incognito browser**:

### Test 1: Unauthenticated Access (Should Redirect)
1. Open: `http://172.28.1.148:3001`
2. Try to navigate to document management
3. **Expected**: Redirects to login page ✅

### Test 2: Authenticated Access (Should Work)
1. Login with credentials
2. Navigate to document management
3. **Expected**: Access granted ✅

### Test 3: Logout and Retry
1. Logout
2. Try to access document management again
3. **Expected**: Redirects to login page ✅

---

## ⚠️ Critical: Browser Cache

**After deployment, always test in incognito mode!**

Why?
- Frontend JavaScript is rebuilt from GitHub code
- Browser cache shows old code
- Incognito mode forces fresh download

**For regular browsing:**
- Hard reload: `Ctrl+Shift+R` (Windows/Linux)
- Hard reload: `Cmd+Shift+R` (Mac)

---

## 🔍 Verify GitHub Code is Deployed

After deployment, verify the frontend changes are actually deployed:

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Check current commit
git log -1 --oneline
# Should show: 6d1f3dd or 29e6433

# Check the authentication code exists
grep -A 5 "Redirect to login if not authenticated" frontend/src/pages/DocumentManagement.tsx

# Should show:
#   // Redirect to login if not authenticated
#   useEffect(() => {
#     if (!user) {
#       navigate('/login');
#     }
#   }, [user, navigate]);
```

---

## 📊 Expected Results After Deployment

### Container Status
```bash
docker compose -f docker-compose.prod.yml ps
```

Should show:
```
NAME                     STATUS          PORTS
edms_prod_frontend       Up (healthy)    0.0.0.0:3001->80/tcp
edms_prod_backend        Up (healthy)    0.0.0.0:8001->8000/tcp
edms_prod_db            Up (healthy)    0.0.0.0:5433->5432/tcp
edms_prod_redis         Up (healthy)    0.0.0.0:6380->6379/tcp
edms_prod_celery_worker Up
edms_prod_celery_beat   Up
```

### Frontend Test
```bash
curl http://172.28.1.148:3001/
```
Should return HTML content

### Backend Health
```bash
curl http://172.28.1.148:8001/health/
```
Should return: `{"status": "healthy"}`

---

## 🔧 Troubleshooting

### Issue: "git clone" fails with permission denied

```bash
# On staging server, set up GitHub SSH key
ssh-keygen -t ed25519 -C "lims@staging"
cat ~/.ssh/id_ed25519.pub

# Add this key to GitHub:
# GitHub → Settings → SSH Keys → Add SSH Key

# Test connection
ssh -T git@github.com

# Try clone again with SSH URL
git clone git@github.com:jinkaiteo/edms.git .
```

### Issue: Frontend shows old code after deployment

**Solution**: Use incognito mode or hard reload
- Browser is caching old JavaScript
- Ctrl+Shift+R forces reload

### Issue: Services won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check Docker
docker system df
docker system prune -f  # Clean up if needed
```

### Issue: Can't connect to staging server

```bash
# Test SSH
ssh -v lims@172.28.1.148

# Check SSH config
cat ~/.ssh/config

# Try with password
ssh -o PreferredAuthentications=password lims@172.28.1.148
```

---

## ✅ Deployment Checklist

**Before Deployment:**
- [ ] SSH access to staging server verified
- [ ] GitHub repository accessible
- [ ] Docker installed on staging (or ready to install)
- [ ] Ports 3001, 8001, 5433, 6380 available

**During Deployment:**
- [ ] Choose deployment method (interactive/manual/quick)
- [ ] Clone/pull from GitHub develop branch
- [ ] Verify commits include 29e6433 (auth fix)
- [ ] Build Docker images
- [ ] Start all services
- [ ] Run migrations
- [ ] Create superuser

**After Deployment:**
- [ ] All containers show "Up" status
- [ ] Frontend responds: `curl http://localhost:3001/`
- [ ] Backend healthy: `curl http://localhost:8001/health/`
- [ ] Test in incognito browser
- [ ] Authentication redirect works
- [ ] Login and access works
- [ ] Team notified about cache clearing

---

## 🎯 Recommended Approach

**For fresh staging server, use Interactive Script:**

```bash
./deploy-interactive.sh
```

**Then follow the prompts, using these values:**
- Deployment type: **Staging (2)**
- Server: **172.28.1.148**
- User: **lims**
- Path: **/home/lims/edms-staging**
- Branch: **develop** (important - has frontend changes!)
- Ports: **Use defaults (3001, 8001, 5433, 6380)**

**This will:**
1. ✅ Pull code from GitHub (includes all frontend changes)
2. ✅ Build fresh Docker images
3. ✅ Start all services
4. ✅ Initialize database
5. ✅ Create users
6. ✅ Run health checks

**Total time: ~10-15 minutes for fresh setup**

---

## 📞 Need Help?

If you encounter issues:

1. **Check the script logs** (saved automatically)
2. **Check Docker logs**: `docker compose logs`
3. **Verify GitHub code**: `git log -3 --oneline`
4. **Check service status**: `docker compose ps`

---

## 🎉 Summary

**Frontend changes are on GitHub**: ✅  
**Commit 29e6433** includes authentication redirect: ✅  
**Commit 6d1f3dd** includes deployment scripts: ✅  
**Interactive script ready**: ✅  
**Fresh staging deployment ready**: ✅  

**Run this to deploy:**
```bash
./deploy-interactive.sh
```

Choose **Staging**, use **develop branch**, and the script will pull all your frontend changes from GitHub!

---

**Good luck with your fresh staging deployment! 🚀**
