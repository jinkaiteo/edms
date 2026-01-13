# Complete Staging Deployment Guide

## 🎯 Overview

The frontend authentication changes (commit 29e6433) need to be deployed to staging. Since the staging server pulls code from GitHub, we need to ensure everything is pushed first.

---

## 📋 Current Situation

✅ **Already Done:**
- Frontend authentication redirect implemented (commit 29e6433)
- Changes committed to local `develop` branch
- Working on local: `http://localhost:3000/`

❓ **Need to Verify:**
- Are changes pushed to GitHub?
- Is staging server configured to pull from GitHub?

---

## 🚀 Complete Deployment Workflow

### Step 1: Push Changes to GitHub (If Not Already Done)

```bash
# Check if commit is already pushed
git log origin/develop..develop --oneline

# If it shows commit 29e6433, you need to push:
git push origin develop
```

**Expected output if push is needed:**
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
Writing objects: 100% (X/X), done.
To https://github.com/jinkaiteo/edms.git
   7c2392d..29e6433  develop -> develop
```

### Step 2: Verify Push to GitHub

```bash
# Check GitHub has the latest commit
git fetch origin
git log origin/develop -1 --oneline
```

**Should show:**
```
29e6433 fix: Add authentication redirect to DocumentManagement page
```

### Step 3: Deploy to Staging Server

**Option A: Using Quick Deploy Script**
```bash
./QUICK_DEPLOY_STAGING.sh
```

**Option B: Manual Deployment**
```bash
# SSH to staging
ssh lims@172.28.1.148

# Navigate to project
cd /home/lims/edms-staging

# Pull latest from GitHub
git fetch origin
git checkout develop
git pull origin develop

# Verify you got the changes
git log -1 --oneline
# Should show: 29e6433 fix: Add authentication redirect to DocumentManagement page

# Rebuild frontend
docker compose -f docker-compose.prod.yml stop frontend
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Verify
docker compose -f docker-compose.prod.yml ps frontend
curl http://localhost:3001/

# Exit
exit
```

### Step 4: Test Deployment

1. Open **incognito browser**: `http://172.28.1.148:3001`
2. Try to access document management
3. Should redirect to login ✅
4. Login and verify access works ✅

---

## 🔍 Verify GitHub Push Status

Run this command to check if your commit is already on GitHub:

```bash
git fetch origin
git log origin/develop -5 --oneline
```

**If you see `29e6433`** in the output → Already pushed ✅  
**If you DON'T see `29e6433`** → Need to push:
```bash
git push origin develop
```

---

## 🎯 Quick Command Sequence

```bash
# 1. Verify/push to GitHub
git fetch origin
git log origin/develop..develop --oneline

# If commit shows up, push it:
git push origin develop

# 2. Deploy to staging
ssh lims@172.28.1.148 << 'ENDSSH'
    cd /home/lims/edms-staging
    git pull origin develop
    docker compose -f docker-compose.prod.yml stop frontend
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    docker compose -f docker-compose.prod.yml up -d frontend
    docker compose -f docker-compose.prod.yml ps frontend
ENDSSH

# 3. Test
curl http://172.28.1.148:3001/
```

---

## ⚠️ Important Notes

### About GitHub
- Staging server **MUST** pull from GitHub (not local files)
- Changes must be committed AND pushed to `origin/develop`
- Staging server uses: `git pull origin develop`

### About Browser Cache
- After deployment, use **incognito mode** or **Ctrl+Shift+R**
- Frontend JavaScript is rebuilt and needs fresh download
- Old cache = old code (no authentication redirect)

### About Downtime
- Frontend rebuild takes ~3-5 minutes
- Backend continues running (no API disruption)
- Users may see brief "connection refused" during restart

---

## 📊 Expected Timeline

| Step | Time | Action |
|------|------|--------|
| 1. Push to GitHub | 10 sec | `git push origin develop` |
| 2. SSH to staging | 5 sec | `ssh lims@172.28.1.148` |
| 3. Pull from GitHub | 10 sec | `git pull origin develop` |
| 4. Stop frontend | 5 sec | `docker compose stop frontend` |
| 5. Rebuild frontend | **2-3 min** | `docker compose build --no-cache frontend` |
| 6. Start frontend | 10 sec | `docker compose up -d frontend` |
| 7. Verify | 10 sec | `docker compose ps; curl localhost:3001` |
| **TOTAL** | **~4 minutes** | |

---

## 🔧 Troubleshooting

### Issue: "Already up to date" when pulling on staging
```bash
# On staging server
cd /home/lims/edms-staging
git fetch origin
git log origin/develop -1
# Should show commit 29e6433

# If not, check GitHub repository
# If it's there, force update:
git reset --hard origin/develop
```

### Issue: "Permission denied (publickey)" on staging
```bash
# On staging server, verify GitHub access
ssh -T git@github.com
# Should say: "Hi jinkaiteo! You've successfully authenticated..."

# If not, check SSH keys
ls -la ~/.ssh/
# Should have id_rsa or id_ed25519
```

### Issue: Frontend shows old code after deployment
- **Solution**: Use incognito mode or hard reload (Ctrl+Shift+R)
- Browser is caching old JavaScript bundle
- Clearing cache or incognito forces new download

---

## ✅ Deployment Checklist

**Before Deployment:**
- [ ] Commit is on `develop` branch: `git log -1`
- [ ] Commit is pushed to GitHub: `git log origin/develop -1`
- [ ] SSH access to staging works: `ssh lims@172.28.1.148 "echo OK"`

**During Deployment:**
- [ ] Pulled latest code on staging
- [ ] Verified correct commit: `git log -1`
- [ ] Frontend container stopped
- [ ] Frontend image rebuilt (no cache)
- [ ] Frontend container started

**After Deployment:**
- [ ] Container shows "Up" status
- [ ] Frontend responds to HTTP: `curl localhost:3001`
- [ ] Tested in incognito browser
- [ ] Authentication redirect works
- [ ] Team notified about cache clearing

---

## 🎯 Ready? Here's Your Command

First, check if you need to push:
```bash
git fetch origin && git log origin/develop..develop --oneline
```

**If it shows commit 29e6433:**
```bash
# Push to GitHub first
git push origin develop

# Then deploy
./QUICK_DEPLOY_STAGING.sh
```

**If it shows nothing (already pushed):**
```bash
# Just deploy
./QUICK_DEPLOY_STAGING.sh
```

---

**Need help?** Let me know if you encounter any issues! 🚀
