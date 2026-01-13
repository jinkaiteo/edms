# Staging Deployment Summary - Frontend Update

## 📦 What's Ready

I've prepared everything you need to deploy the frontend changes to your staging server.

### Recent Changes
- ✅ **Authentication redirect** in DocumentManagement component (commit 29e6433)
- ✅ Prevents unauthorized access to document management
- ✅ Redirects users to login page if not authenticated

---

## 🚀 How to Deploy (Choose One Method)

### Method 1: Quick Deploy Script (Fastest) ⚡
```bash
./QUICK_DEPLOY_STAGING.sh
```
**Time**: ~3-4 minutes  
**What it does**: Pulls code, rebuilds frontend, restarts container

### Method 2: Interactive Deploy Script (Safest) 🛡️
```bash
./deploy-staging-frontend-update.sh
```
**Time**: ~5-7 minutes  
**What it does**: Same as Method 1, but with:
- Pre-deployment checks
- Confirmation prompts
- Detailed verification
- Comprehensive logging

### Method 3: Manual Steps (Most Control) 🎮
See detailed steps in `STAGING_DEPLOYMENT_INSTRUCTIONS.md`

---

## 📋 Prerequisites

Before deploying, ensure:
- [ ] You have SSH access: `ssh lims@172.28.1.148`
- [ ] You're in the EDMS project root directory
- [ ] You're on the `develop` branch

---

## ⚡ Quick Start (Recommended)

```bash
# 1. Verify SSH access
ssh lims@172.28.1.148 "echo 'Connection OK'"

# 2. Run deployment
./QUICK_DEPLOY_STAGING.sh

# 3. Test in browser (use incognito mode!)
# http://172.28.1.148:3001
```

---

## 🧪 Testing After Deployment

### Test 1: Frontend Loads
```bash
curl http://172.28.1.148:3001/
```
✅ Should return HTML

### Test 2: Backend Health
```bash
curl http://172.28.1.148:8001/health/
```
✅ Should return `{"status": "healthy"}`

### Test 3: Authentication Redirect (In Browser)
1. Open `http://172.28.1.148:3001` in **incognito mode**
2. Try to access document management
3. Should redirect to login page ✅
4. Login with credentials
5. Should access document management ✅

---

## ⚠️ Critical: Browser Cache Issue

**Why incognito mode?**
- Frontend JavaScript is rebuilt during deployment
- Browsers aggressively cache JavaScript files
- Old cache = old code (no authentication redirect)
- Incognito mode = fresh download of new code

**For regular browsing:**
- Hard reload: `Ctrl+Shift+R` (Windows/Linux)
- Hard reload: `Cmd+Shift+R` (Mac)
- Or clear browser cache

---

## 📊 Expected Deployment Output

```bash
🚀 Deploying frontend changes to staging...

📥 1/5 Pulling latest code...
✅ Code updated

🛑 2/5 Stopping frontend...
✅ Frontend stopped

🔨 3/5 Rebuilding frontend (this takes 2-3 minutes)...
✅ Frontend rebuilt

🚀 4/5 Starting frontend...
✅ Frontend started

✅ 5/5 Verifying deployment...
NAME                   STATUS
edms_prod_frontend     Up

✅ Frontend is responding!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Deployment Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to staging server"
```bash
# Test SSH access
ssh lims@172.28.1.148 "echo 'test'"

# Check SSH config
cat ~/.ssh/config | grep 172.28.1.148
```

### Issue: "Frontend container won't start"
```bash
# Check logs
ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml logs frontend"

# Restart all services
ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml restart"
```

### Issue: "Changes not visible in browser"
- **Solution**: MUST use incognito mode or hard reload
- Browser is showing cached JavaScript
- Ctrl+Shift+R to force reload

---

## 📁 Files Created

1. **`QUICK_DEPLOY_STAGING.sh`** - Fast deployment script
2. **`deploy-staging-frontend-update.sh`** - Comprehensive deployment with checks
3. **`STAGING_DEPLOYMENT_INSTRUCTIONS.md`** - Detailed manual instructions
4. **`STAGING_DEPLOYMENT_SUMMARY.md`** - This file (quick reference)

---

## 🎯 Next Steps

1. **Run deployment** using one of the methods above
2. **Test in incognito mode** - Verify authentication redirect works
3. **Notify team** - Remind them to clear browser cache
4. **Monitor logs** - Watch for any errors in first few hours

---

## 📌 Quick Reference

| Item | Value |
|------|-------|
| **Server** | `172.28.1.148` |
| **User** | `lims` |
| **Path** | `/home/lims/edms-staging` |
| **Frontend** | `http://172.28.1.148:3001` |
| **Backend** | `http://172.28.1.148:8001/api/v1` |
| **Downtime** | ~3-5 minutes (frontend only) |
| **Branch** | `develop` |

---

## ✅ Deployment Checklist

After running the deployment script:

- [ ] Deployment completed without errors
- [ ] Frontend container shows "Up" status
- [ ] Frontend responds to HTTP requests
- [ ] Backend health check passes
- [ ] Authentication redirect tested (incognito mode!)
- [ ] Team notified about cache clearing

---

**Ready to deploy?** Run `./QUICK_DEPLOY_STAGING.sh` from your terminal! 🚀
