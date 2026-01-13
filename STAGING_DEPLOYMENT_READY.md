# ✅ Staging Deployment Ready - Complete Instructions

## 🎉 GitHub Commit Complete!

All deployment scripts and documentation have been committed and pushed to GitHub:

**Commit**: `6d1f3dd` - docs: Add comprehensive staging deployment scripts and guides  
**Previous commit**: `29e6433` - fix: Add authentication redirect to DocumentManagement page

Both commits are now on GitHub `develop` branch and ready to deploy to staging!

---

## 🚀 Deploy to Staging - Complete Workflow

### Step 1: SSH to Staging Server

```bash
ssh lims@172.28.1.148
```

### Step 2: Navigate to Project Directory

```bash
cd /home/lims/edms-staging
```

### Step 3: Pull Latest Code from GitHub

```bash
git fetch origin
git checkout develop
git pull origin develop
```

You should see:
```
Updating 29e6433..6d1f3dd
Fast-forward
 DEPLOY_NOW.md                          | ...
 DEPLOY_TO_STAGING_COMPLETE_GUIDE.md    | ...
 EXECUTE_STAGING_DEPLOYMENT.sh          | ...
 QUICK_DEPLOY_STAGING.sh                | ...
 STAGING_DEPLOYMENT_INSTRUCTIONS.md     | ...
 STAGING_DEPLOYMENT_SUMMARY.md          | ...
 deploy-staging-frontend-update.sh      | ...
 7 files changed, 1230 insertions(+)
```

### Step 4: Verify You Have the Latest Code

```bash
git log -2 --oneline
```

Should show:
```
6d1f3dd docs: Add comprehensive staging deployment scripts and guides
29e6433 fix: Add authentication redirect to DocumentManagement page
```

### Step 5: Deploy Frontend (Choose One Method)

#### Option A: Use the Deployment Script (Recommended)

```bash
./EXECUTE_STAGING_DEPLOYMENT.sh
```

**This will:**
- Stop frontend container
- Rebuild frontend with authentication changes
- Start frontend container
- Verify deployment
- Takes ~4 minutes

#### Option B: Manual Deployment

```bash
# Stop frontend
docker compose -f docker-compose.prod.yml stop frontend

# Rebuild frontend (no cache to ensure fresh build)
docker compose -f docker-compose.prod.yml build --no-cache frontend

# Start frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Wait for startup
sleep 15

# Verify
docker compose -f docker-compose.prod.yml ps frontend
curl http://localhost:3001/
```

### Step 6: Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check frontend logs
docker compose -f docker-compose.prod.yml logs --tail=20 frontend

# Test HTTP response
curl http://localhost:3001/

# Test backend health
curl http://localhost:8001/health/
```

Expected results:
- ✅ Frontend container shows "Up" status
- ✅ HTTP response returns HTML
- ✅ Backend returns `{"status": "healthy"}`

### Step 7: Exit SSH

```bash
exit
```

---

## 🧪 Test in Browser

**CRITICAL: You MUST use incognito mode or hard reload!**

### From Your Local Machine:

1. **Open incognito browser window**
   - Chrome: `Ctrl+Shift+N` (Windows) / `Cmd+Shift+N` (Mac)
   - Firefox: `Ctrl+Shift+P` (Windows) / `Cmd+Shift+P` (Mac)

2. **Navigate to**: `http://172.28.1.148:3001`

3. **Test authentication redirect**:
   - Try to access document management without logging in
   - **Expected**: Redirects to login page ✅
   
4. **Login and verify**:
   - Login with test credentials
   - Navigate to document management
   - **Expected**: Access granted ✅

### Why Incognito Mode?

Frontend JavaScript is rebuilt during deployment. Browser cache will show OLD code unless you:
- Use incognito/private mode, OR
- Hard reload: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

---

## 📋 Complete Command Sequence (Copy & Paste)

```bash
# 1. SSH to staging
ssh lims@172.28.1.148

# 2. Navigate and pull
cd /home/lims/edms-staging
git pull origin develop

# 3. Run deployment script
./EXECUTE_STAGING_DEPLOYMENT.sh

# 4. Exit
exit

# 5. Test from your machine
curl http://172.28.1.148:3001/
```

---

## 📊 What Gets Deployed

### Frontend Changes:
1. **Authentication redirect** (commit 29e6433)
   - Prevents unauthorized access to document management
   - Redirects to login page if user not authenticated

2. **Deployment scripts** (commit 6d1f3dd)
   - New deployment automation tools
   - Documentation for future deployments

### Backend:
- No changes (remains running during deployment)
- No downtime for API

---

## ⏱️ Expected Timeline

| Step | Time | Action |
|------|------|--------|
| SSH to server | 5 sec | `ssh lims@172.28.1.148` |
| Pull from GitHub | 10 sec | `git pull origin develop` |
| Stop frontend | 5 sec | `docker compose stop frontend` |
| Rebuild frontend | **2-3 min** | `docker compose build --no-cache frontend` |
| Start frontend | 15 sec | `docker compose up -d frontend` |
| Verify | 10 sec | Check status and logs |
| **TOTAL** | **~4 minutes** | |

---

## ⚠️ Important Notes

### 1. Browser Cache (Most Important!)
- Users MUST clear cache or use incognito mode
- Without this, they'll see old code (no authentication redirect)
- Notify all team members about this requirement

### 2. Downtime
- Frontend: ~3 minutes downtime during rebuild
- Backend: No downtime (continues running)
- Database: No impact

### 3. Testing
- Always test in incognito mode first
- Verify authentication redirect works
- Test login functionality
- Verify document access after login

### 4. Rollback (if needed)
```bash
# If deployment fails, rollback to previous commit
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git checkout 29e6433
docker compose -f docker-compose.prod.yml restart frontend
```

---

## 🔧 Troubleshooting

### Issue 1: "git pull" shows "Already up to date"

```bash
# Force update
git fetch origin
git reset --hard origin/develop
git log -2 --oneline  # Verify commits
```

### Issue 2: Frontend container won't start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs frontend

# Try full restart
docker compose -f docker-compose.prod.yml restart frontend
```

### Issue 3: "Already up to date" but don't see new commits

```bash
# Verify GitHub connection
git remote -v
git fetch origin --verbose

# Check branch
git branch -a
git status
```

### Issue 4: Changes not visible in browser

**Solution**: This is the #1 issue - browser cache!
- MUST use incognito mode or Ctrl+Shift+R
- Frontend JavaScript is rebuilt and needs fresh download
- Clear browser cache completely if needed

---

## ✅ Deployment Checklist

**Before Deployment:**
- [x] Commits pushed to GitHub (done!)
- [ ] SSH access to staging verified
- [ ] No critical operations running on staging

**During Deployment:**
- [ ] SSH to staging server
- [ ] Pull latest code: `git pull origin develop`
- [ ] Verify commits: `git log -2`
- [ ] Run deployment script: `./EXECUTE_STAGING_DEPLOYMENT.sh`
- [ ] Verify container status: `docker compose ps`

**After Deployment:**
- [ ] Frontend container shows "Up" status
- [ ] HTTP test passes: `curl localhost:3001`
- [ ] Backend health check passes: `curl localhost:8001/health/`
- [ ] Test in incognito browser
- [ ] Authentication redirect works
- [ ] Login and document access works
- [ ] Team notified about cache clearing

---

## 🎯 Ready to Deploy?

**Execute these commands:**

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git pull origin develop
./EXECUTE_STAGING_DEPLOYMENT.sh
```

**Then test in incognito browser**: `http://172.28.1.148:3001`

---

## 📞 Need Help?

If you encounter issues:

1. **Check logs**: 
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml logs --tail=50 frontend"
   ```

2. **Check container status**:
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml ps"
   ```

3. **Restart services**:
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml restart"
   ```

---

## 🎉 Success Indicators

After successful deployment, you should see:

✅ Git shows both commits (6d1f3dd and 29e6433)  
✅ Frontend container status: "Up"  
✅ HTTP response: Returns HTML  
✅ Backend health: `{"status": "healthy"}`  
✅ Browser (incognito): Authentication redirect works  
✅ Login: Successful access to document management  

---

**Deployment prepared by**: Rovo Dev  
**Date**: January 13, 2026  
**Changes**: Frontend authentication redirect + deployment scripts  
**Impact**: Frontend rebuild required, ~3 min downtime  

---

**Good luck with the deployment! 🚀**
