# Switch Production to Main Branch - Action Plan

## ✅ Good News: Main Branch Already Exists!

Your repository already has a `main` branch. Now we need to:
1. Update `main` with latest code from `develop`
2. Switch production server to use `main` branch
3. Keep staging on `develop` branch

---

## 📊 Current Situation

### Branch Status:
- ✅ **`main` branch exists** on GitHub
- ✅ **`develop` branch exists** with latest code
- ❌ **Production is using `develop`** (should use `main`)
- ✅ **Staging is using `develop`** (correct!)

### What Needs to Change:
- Merge `develop` → `main` (update main with latest code)
- Switch production server to `main` branch
- Keep staging on `develop` (no change needed)

---

## 🚀 Step-by-Step Fix

### Step 1: Update Main Branch with Latest Code

```bash
# On your local machine
cd /path/to/edms

# Switch to main branch
git checkout main
git pull origin main

# Merge develop into main
git merge origin/develop

# Push updated main to GitHub
git push origin main
```

**This brings main branch up to date with all your frontend changes!**

---

### Step 2: Switch Production Server to Main Branch

```bash
# SSH to production server
ssh lims@172.28.1.149  # Replace with your production IP

# Navigate to production directory
cd /home/lims/edms-production

# Check current branch
git branch
# Shows: * develop (we need to change this)

# Fetch latest from GitHub
git fetch origin

# Switch to main branch
git checkout main

# Pull latest code
git pull origin main

# Verify you're on main with latest code
git branch
# Should show: * main

git log -3 --oneline
# Should show latest commits including frontend fix

# Rebuild containers with main branch code
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Verify deployment
docker compose -f docker-compose.prod.yml ps
```

---

### Step 3: Verify Staging Stays on Develop (No Changes Needed)

```bash
# SSH to staging server
ssh lims@172.28.1.148  # Your staging IP

# Verify staging is on develop
cd /home/lims/edms-staging
git branch
# Should show: * develop

# This is correct - no changes needed for staging
exit
```

---

## ✅ After These Steps

### Branch Configuration:
| Server | Environment | Branch | Purpose |
|--------|-------------|--------|---------|
| **172.28.1.148** | Staging | `develop` | Testing new features |
| **172.28.1.149** | Production | `main` | Stable production code |
| **Local** | Development | `develop` or `feature/*` | Active development |

---

## 🔄 Future Deployment Workflow

### For Staging Deployments (Frequent):
```bash
# 1. Push changes to develop
git checkout develop
git add .
git commit -m "feat: New feature"
git push origin develop

# 2. Deploy to staging
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git pull origin develop
docker compose -f docker-compose.prod.yml restart
```

### For Production Deployments (Stable Releases):
```bash
# 1. Test thoroughly on staging first!

# 2. Merge develop to main
git checkout main
git pull origin main
git merge develop
git push origin main

# 3. Deploy to production
ssh lims@172.28.1.149
cd /home/lims/edms-production
git pull origin main
docker compose -f docker-compose.prod.yml restart
```

---

## 📋 Complete Command Sequence (Copy & Paste)

Execute these commands in order:

### Part A: Update Main Branch (Local Machine)

```bash
cd /path/to/edms
git checkout main
git pull origin main
git merge develop
git push origin main
```

### Part B: Switch Production to Main (Production Server)

```bash
ssh lims@172.28.1.149
cd /home/lims/edms-production
git fetch origin
git checkout main
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
exit
```

### Part C: Verify Configuration

```bash
# Check staging (should be develop)
ssh lims@172.28.1.148 "cd /home/lims/edms-staging && git branch"

# Check production (should be main)
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git branch"
```

Expected output:
```
Staging:    * develop
Production: * main
```

---

## 🔧 Update Deployment Scripts

### Update deploy-interactive.sh

```bash
nano deploy-interactive.sh
```

Find the branch configuration section (around line 250-280) and update:

```bash
collect_configuration() {
    # ...
    
    # Set default branch based on deployment type
    if [ "$DEPLOY_TYPE" = "production" ]; then
        BRANCH=${BRANCH:-main}              # Production uses main
        FRONTEND_PORT=${FRONTEND_PORT:-3002}
        BACKEND_PORT=${BACKEND_PORT:-8002}
        DB_PORT=${DB_PORT:-5434}
        REDIS_PORT=${REDIS_PORT:-6381}
    elif [ "$DEPLOY_TYPE" = "staging" ]; then
        BRANCH=${BRANCH:-develop}           # Staging uses develop
        FRONTEND_PORT=${FRONTEND_PORT:-3001}
        BACKEND_PORT=${BACKEND_PORT:-8001}
        DB_PORT=${DB_PORT:-5433}
        REDIS_PORT=${REDIS_PORT:-6380}
    else
        BRANCH=${BRANCH:-develop}           # Development uses develop
        FRONTEND_PORT=${FRONTEND_PORT:-3000}
        BACKEND_PORT=${BACKEND_PORT:-8000}
        DB_PORT=${DB_PORT:-5432}
        REDIS_PORT=${REDIS_PORT:-6379}
    fi
}
```

---

## ⚠️ Important Notes

### Why This Matters:

1. **Stability**: Production only gets tested code that passed staging
2. **Safety**: Experimental features in develop don't affect production
3. **Rollback**: Easy to revert production by checking out previous main commit
4. **Compliance**: Clear audit trail of what's in production

### Branch Protection (Recommended):

Set up branch protection on GitHub:
1. Go to: `https://github.com/jinkaiteo/edms/settings/branches`
2. Add rule for `main` branch
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass (if you have CI/CD)

This prevents accidental direct pushes to production.

---

## 🧪 Verify After Switch

### Test Production:
```bash
# Frontend (use new port if you changed it)
curl http://YOUR_PROD_IP:3002/

# Backend
curl http://YOUR_PROD_IP:8002/health/

# In browser (incognito mode)
http://YOUR_PROD_IP:3002
```

### Check Branch Status:
```bash
# On production server
ssh lims@172.28.1.149
cd /home/lims/edms-production
git branch
git log -3 --oneline
```

Should show:
- Current branch: `* main`
- Latest commits including frontend authentication fix

---

## 📚 Summary

**Current Problem:**
- Both staging and production using `develop` branch
- Not following Git best practices
- Risky for production stability

**Solution:**
1. ✅ Update `main` branch with latest code
2. ✅ Switch production to `main` branch
3. ✅ Keep staging on `develop` branch
4. ✅ Update deployment scripts

**Result:**
- Production runs stable code from `main`
- Staging tests new features from `develop`
- Clear separation and safety

---

## 🎯 Ready to Execute?

Run these commands now:

```bash
# 1. Update main branch
git checkout main && git pull origin main && git merge develop && git push origin main

# 2. Switch production
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git fetch origin && git checkout main && git pull origin main"

# 3. Rebuild production
ssh lims@172.28.1.149 "cd /home/lims/edms-production && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml build --no-cache && docker compose -f docker-compose.prod.yml up -d"

# 4. Verify
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git branch && docker compose -f docker-compose.prod.yml ps"
```

**Total time: ~5-10 minutes**

---

Would you like me to help you execute these steps? 🚀
