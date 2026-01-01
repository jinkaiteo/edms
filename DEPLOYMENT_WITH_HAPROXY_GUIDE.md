# EDMS Staging Deployment Guide with HAProxy

## 📊 Current Status

### ✅ Updated: `scripts/deploy-production.sh`
The deployment script now **automatically initializes** all system defaults:
- 7 User Roles
- 6 Django Groups  
- 6 Document Types
- 3 Document Sources
- Auto-creates admin user if needed

### HAProxy Deployment Status

**HAProxy is NOT included in the automated deployment script** because:

1. **HAProxy runs on the HOST, not in Docker**
   - It's installed via `apt` on Ubuntu
   - Runs as a systemd service
   - Configured separately from Docker containers

2. **HAProxy setup is a ONE-TIME infrastructure setup**, not part of app deployment
   - Install once on the server
   - Configure once
   - Runs independently

3. **Current Architecture:**
   ```
   Internet → HAProxy (port 80, systemd on host)
                ↓
                ├─ Frontend Container (port 3001)
                └─ Backend Container (port 8001)
   ```

## 🚀 Complete Staging Deployment Process

### Phase 1: Infrastructure Setup (ONE-TIME)

**On staging server (`172.28.1.148`):**

```bash
# 1. Install HAProxy
sudo bash scripts/setup-haproxy-staging.sh

# 2. Update Docker configuration for HAProxy
sudo bash scripts/update-docker-for-haproxy.sh

# 3. Verify HAProxy setup
sudo bash scripts/verify-haproxy-setup.sh
```

**This phase is DONE ONCE** - HAProxy keeps running even when you redeploy the app.

---

### Phase 2: Application Deployment (REPEATABLE)

**Every time you deploy new code:**

```bash
# Pull latest code
git pull origin develop

# Run deployment (now includes automatic initialization!)
bash scripts/deploy-production.sh
```

**The script now automatically:**
1. ✅ Checks requirements
2. ✅ Backs up existing deployment
3. ✅ Builds Docker images
4. ✅ Deploys containers
5. ✅ **Initializes system defaults (NEW!)**
   - Creates admin user if needed
   - Creates 7 roles
   - Creates 6 Django groups
   - Creates 6 document types
   - Creates 3 document sources
6. ✅ Runs workflow tests
7. ✅ Shows deployment summary

---

## 🎯 What Changed in `deploy-production.sh`

### New Function: `initialize_defaults()`

```bash
initialize_defaults() {
    log "Initializing system defaults..."
    
    # 1. Auto-create admin user if none exists
    # 2. Run create_default_roles
    # 3. Run create_default_groups
    # 4. Run create_default_document_types
    # 5. Run create_default_document_sources
}
```

### Updated Execution Flow:

**Before:**
```bash
main() {
    check_requirements
    backup_existing
    build_images
    deploy
    run_tests          # ❌ Tests would fail without data!
    show_info
}
```

**After:**
```bash
main() {
    check_requirements
    backup_existing
    build_images
    deploy
    initialize_defaults  # ✅ NEW! Creates all required data
    run_tests            # ✅ Now tests have data to work with
    show_info
}
```

---

## 📋 Current Staging Server Status

### What's Already Set Up:
- ✅ HAProxy installed and running (if Phase 1 completed)
- ✅ Docker and Docker Compose installed
- ✅ EDMS code repository cloned
- ✅ Environment files configured

### What Happens on Next Deployment:
- ✅ Automatic initialization of all system defaults
- ✅ No manual steps needed
- ✅ Ready to use immediately after deployment

---

## 🔄 Typical Deployment Workflow

### First Time Setup:
```bash
# On staging server
ssh lims@172.28.1.148

# ONE-TIME: Set up HAProxy
sudo bash scripts/setup-haproxy-staging.sh
sudo bash scripts/update-docker-for-haproxy.sh

# Deploy application
bash scripts/deploy-production.sh
```

### Subsequent Deployments:
```bash
# On staging server
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Pull and deploy
git pull origin develop
bash scripts/deploy-production.sh
```

**That's it!** No manual initialization needed anymore.

---

## 🎉 Benefits of the Update

### Before:
1. Run `deploy-production.sh`
2. **Manually** run `initialize-all-defaults.sh`
3. Remember to create superuser first
4. Risk of forgetting initialization steps

### After:
1. Run `deploy-production.sh`
2. ✅ **Everything automated!**
3. ✅ Admin user created automatically if needed
4. ✅ All defaults initialized
5. ✅ Tests run with proper data
6. ✅ Ready to use immediately

---

## 🔐 Security Notes

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `test123`

**⚠️ CHANGE IMMEDIATELY IN PRODUCTION!**

```bash
# Change password
docker compose -f docker-compose.prod.yml exec backend python manage.py changepassword admin
```

---

## 🧪 Testing the Deployment

After deployment completes, verify:

```bash
# 1. Check all containers are running
docker compose -f docker-compose.prod.yml ps

# 2. Check HAProxy status
sudo systemctl status haproxy

# 3. Test the application
curl http://172.28.1.148/health/
curl http://172.28.1.148/api/v1/health/

# 4. Open in browser
http://172.28.1.148
```

**Expected Results:**
- ✅ 7 containers running
- ✅ HAProxy active and running
- ✅ Health endpoints return 200 OK
- ✅ Login page loads
- ✅ Can login with admin/test123
- ✅ Document types, sources, and roles visible in admin panel

---

## 🛠️ Troubleshooting

### Initialization Fails
If initialization fails, check:
```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Manually run initialization
bash scripts/initialize-all-defaults.sh
```

### HAProxy Not Working
```bash
# Check HAProxy status
sudo systemctl status haproxy

# Check HAProxy logs
sudo tail -50 /var/log/haproxy.log

# Restart HAProxy
sudo systemctl restart haproxy
```

### Containers Not Starting
```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

---

## 📚 Related Documentation

- `HAPROXY_STAGING_SETUP.md` - HAProxy installation guide
- `STAGING_DEPLOYMENT_STEPS.md` - Step-by-step deployment
- `CELERY_FINAL_STATUS.md` - Celery health check notes
- `initialize-all-defaults.sh` - Manual initialization script (backup method)

---

## ✅ Summary

### What You Have Now:

1. ✅ **Updated `deploy-production.sh`** with automatic initialization
2. ✅ **HAProxy setup scripts** for infrastructure (one-time setup)
3. ✅ **Separate concerns:** Infrastructure vs Application deployment
4. ✅ **Automated workflow:** Pull code → Run script → Done
5. ✅ **No manual steps** needed for system defaults

### Deployment Flow:

```
┌─────────────────────────────────────────────────────┐
│  ONE-TIME: Infrastructure Setup                     │
│  - Install HAProxy on host                          │
│  - Configure firewall                               │
│  - Update Docker configuration                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  REPEATABLE: Application Deployment                 │
│  1. git pull origin develop                         │
│  2. bash scripts/deploy-production.sh               │
│     ├─ Build images                                 │
│     ├─ Deploy containers                            │
│     ├─ Initialize defaults (AUTO!)                  │
│     ├─ Run tests                                    │
│     └─ Show summary                                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  RESULT: Fully Deployed & Initialized System        │
│  - HAProxy routing on port 80                       │
│  - All containers running                           │
│  - System defaults created                          │
│  - Ready for users                                  │
└─────────────────────────────────────────────────────┘
```

---

**Ready to deploy?** Just run:
```bash
bash scripts/deploy-production.sh
```

🚀 **Happy Deploying!**
