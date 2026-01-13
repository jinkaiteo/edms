# ✅ Production Branch Switch - Ready to Execute

## 🎉 Main Branch Updated Successfully!

The `main` branch has been updated with all the latest code from `develop` and pushed to GitHub.

**Latest commit on main**: `8135cb5` - docs: Add deployment guides and analysis documents  
**Includes**: All frontend changes, authentication fixes, deployment scripts, and documentation

---

## 🚀 Next Step: Switch Production Server to Main Branch

Now we need to update the production server to use the `main` branch instead of `develop`.

---

## 📋 Execute on Production Server

### Option 1: Quick Command (One-liner)

```bash
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git fetch origin && git checkout main && git pull origin main && docker compose -f docker-compose.prod.yml restart"
```

---

### Option 2: Step-by-Step (Recommended for Verification)

```bash
# Step 1: SSH to production
ssh lims@172.28.1.149

# Step 2: Navigate to production directory
cd /home/lims/edms-production

# Step 3: Check current branch
git branch
# Currently shows: * develop (we're changing this)

# Step 4: Fetch latest from GitHub
git fetch origin

# Step 5: Switch to main branch
git checkout main

# Step 6: Pull latest code
git pull origin main

# Step 7: Verify you're on main with latest code
git branch
# Should show: * main

git log -3 --oneline
# Should show:
# 8135cb5 docs: Add deployment guides and analysis documents
# fbec2fd docs: Add Git workflow guide and production branch switch instructions
# 95e47bf docs: Add production port conflict resolution guide

# Step 8: Restart services (or rebuild if needed)
docker compose -f docker-compose.prod.yml restart

# If you want a full rebuild:
# docker compose -f docker-compose.prod.yml down
# docker compose -f docker-compose.prod.yml build --no-cache
# docker compose -f docker-compose.prod.yml up -d

# Step 9: Verify services are running
docker compose -f docker-compose.prod.yml ps

# Step 10: Test endpoints
curl http://localhost:3002/
curl http://localhost:8002/health/

# Step 11: Exit SSH
exit
```

---

## ✅ Verify Configuration After Switch

### Check Both Servers:

```bash
# Verify staging is on develop (should not change)
ssh lims@172.28.1.148 "cd /home/lims/edms-staging && git branch"
# Expected: * develop ✅

# Verify production is on main (should be changed)
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git branch"
# Expected: * main ✅
```

---

## 📊 Final Configuration

After executing the switch:

| Server | Environment | Branch | Ports | Purpose |
|--------|-------------|--------|-------|---------|
| **172.28.1.148** | Staging | `develop` | 3001, 8001, 5433, 6380 | Test new features |
| **172.28.1.149** | Production | `main` | 3002, 8002, 5434, 6381 | Stable releases |

---

## 🧪 Test Production After Switch

### Test 1: Frontend Access
```bash
# From your local machine
curl http://172.28.1.149:3002/
```

### Test 2: Backend Health
```bash
curl http://172.28.1.149:8002/health/
```

### Test 3: Authentication (Browser - Incognito Mode)
1. Open: `http://172.28.1.149:3002`
2. Try to access document management without login
3. **Expected**: Redirects to login page ✅
4. Login with credentials
5. **Expected**: Access document management ✅

---

## 🔄 Future Workflow

### For Staging Deployments (Testing):
```bash
# Push to develop
git checkout develop
git add .
git commit -m "feat: New feature"
git push origin develop

# Deploy to staging
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

## 📝 Why This Matters

### Benefits:
✅ **Stability** - Production only gets tested code  
✅ **Safety** - Experimental features don't affect production  
✅ **Rollback** - Easy to revert production if needed  
✅ **Compliance** - Clear audit trail for regulatory requirements  
✅ **Best Practice** - Industry standard Git workflow  

### Before (Incorrect):
❌ Both staging and production using `develop`  
❌ Untested code could reach production  
❌ No clear separation of concerns  

### After (Correct):
✅ Staging uses `develop` for testing  
✅ Production uses `main` for stability  
✅ Clear workflow: develop → staging test → main → production  

---

## 🎯 Execute Now

Run this command to switch production to main branch:

```bash
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git fetch origin && git checkout main && git pull origin main && docker compose -f docker-compose.prod.yml restart"
```

**Or follow the step-by-step instructions above for more control.**

---

## ✅ After Execution Checklist

- [ ] Production server switched to `main` branch
- [ ] `git branch` shows `* main` on production
- [ ] Services restarted successfully
- [ ] All containers showing "Up" status
- [ ] Frontend accessible: `http://172.28.1.149:3002`
- [ ] Backend healthy: `http://172.28.1.149:8002/health/`
- [ ] Authentication redirect tested in browser
- [ ] Staging still on `develop` (verified)

---

## 📞 Need Help?

If you encounter issues:

1. **Check current branch**:
   ```bash
   ssh lims@172.28.1.149 "cd /home/lims/edms-production && git branch"
   ```

2. **Check container status**:
   ```bash
   ssh lims@172.28.1.149 "cd /home/lims/edms-production && docker compose -f docker-compose.prod.yml ps"
   ```

3. **Check logs**:
   ```bash
   ssh lims@172.28.1.149 "cd /home/lims/edms-production && docker compose -f docker-compose.prod.yml logs --tail=50"
   ```

---

## 🎉 Summary

**Completed:**
✅ Main branch updated with all latest code from develop  
✅ Main branch pushed to GitHub  
✅ Documentation created  

**Next Step:**
🚀 Switch production server to use `main` branch

**Command:**
```bash
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git fetch origin && git checkout main && git pull origin main && docker compose -f docker-compose.prod.yml restart"
```

**Ready to execute?** 🚀
