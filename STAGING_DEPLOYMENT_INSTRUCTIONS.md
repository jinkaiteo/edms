# Staging Deployment Instructions - Frontend Update

## 🎯 Purpose
Deploy recent frontend authentication changes to staging server at `172.28.1.148`.

## 📝 Changes Being Deployed
- **Authentication redirect** in DocumentManagement component (commit 29e6433)
- Users accessing document management without login will be redirected to login page
- Frontend-only change requiring React rebuild

---

## 🚀 Deployment Steps (Run from Your Local Machine)

### Prerequisites
1. SSH access to staging server configured
2. You're in the EDMS project root directory
3. On the `develop` branch with latest changes

### Step 1: Verify SSH Access
```bash
ssh lims@172.28.1.148 "echo 'Connection OK'"
```
✅ Should print "Connection OK"

---

### Step 2: Run Deployment Script

**Option A: Automated Deployment (Recommended)**
```bash
./deploy-staging-frontend-update.sh
```

The script will:
- Show you what changes will be deployed
- Ask for confirmation before proceeding
- Pull latest code on staging
- Rebuild frontend container (3-5 min)
- Verify deployment
- Provide testing instructions

**Option B: Manual Deployment**
If you prefer manual control:

```bash
# 1. SSH to staging
ssh lims@172.28.1.148

# 2. Navigate to project
cd /home/lims/edms-staging

# 3. Check current status
docker compose -f docker-compose.prod.yml ps

# 4. Pull latest code
git fetch origin
git checkout develop
git pull origin develop

# 5. View recent commits
git log --oneline -5

# 6. Rebuild frontend (this is the key step!)
docker compose -f docker-compose.prod.yml stop frontend
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend

# 7. Verify deployment
docker compose -f docker-compose.prod.yml ps frontend
docker compose -f docker-compose.prod.yml logs --tail=20 frontend

# 8. Test HTTP response
curl http://localhost:3001/
curl http://localhost:8001/health/

# 9. Exit SSH
exit
```

---

## ✅ Post-Deployment Verification

### From Your Local Machine:

1. **Test Frontend Access**
   ```bash
   curl http://172.28.1.148:3001/
   ```
   Should return HTML content

2. **Test Backend API**
   ```bash
   curl http://172.28.1.148:8001/health/
   ```
   Should return: `{"status": "healthy"}`

3. **Test in Browser**
   - Open: `http://172.28.1.148:3001`
   - **IMPORTANT**: Use incognito mode or hard reload (Ctrl+Shift+R)
   - Try to access document management without logging in
   - Should redirect to login page ✅

---

## ⚠️ Critical: Browser Cache

**The frontend JavaScript has been rebuilt!**

Users must clear browser cache to see the new changes:

### For Testing:
- Use **Incognito/Private browsing mode**, OR
- Hard reload: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)

### For All Users:
Notify team members to clear cache or use hard reload when accessing staging.

---

## 🔍 Troubleshooting

### Issue 1: Frontend container won't start
```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging
docker compose -f docker-compose.prod.yml logs frontend
```

### Issue 2: Port already in use
```bash
# Check what's using port 3001
sudo lsof -i :3001

# If nginx is running standalone, stop it
sudo systemctl stop nginx
```

### Issue 3: Build fails due to disk space
```bash
# Clean up old Docker images
docker system prune -a --volumes
```

### Issue 4: Changes not visible in browser
- **Solution**: Must use incognito mode or hard reload
- Browser caches the old JavaScript bundle
- Ctrl+Shift+R forces download of new bundle

---

## 📊 Expected Results

### Container Status
```
NAME                   STATUS          PORTS
edms_prod_frontend     Up (healthy)    0.0.0.0:3001->80/tcp
edms_prod_backend      Up (healthy)    0.0.0.0:8001->8000/tcp
edms_prod_db          Up (healthy)    0.0.0.0:5433->5432/tcp
edms_prod_redis       Up (healthy)    0.0.0.0:6380->6379/tcp
```

### Frontend Logs (Last Lines)
```
Nginx started successfully
Frontend application ready
```

### Test Results
- ✅ Frontend loads at `http://172.28.1.148:3001`
- ✅ Accessing document management redirects to login
- ✅ After login, document management is accessible
- ✅ Backend API responds at `http://172.28.1.148:8001/health/`

---

## 📝 Deployment Checklist

- [ ] SSH access verified
- [ ] Deployment script run or manual steps completed
- [ ] Frontend container rebuilt successfully
- [ ] Container status shows "Up (healthy)"
- [ ] Frontend accessible via HTTP
- [ ] Backend health check passes
- [ ] Authentication redirect tested (use incognito mode!)
- [ ] Team notified about browser cache clearing

---

## 🆘 Need Help?

If deployment fails:

1. **Check logs**:
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml logs --tail=50 frontend"
   ```

2. **Restart all services**:
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml restart"
   ```

3. **Full rebuild** (if needed):
   ```bash
   ssh lims@172.28.1.148 "cd /home/lims/edms-staging && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d"
   ```

---

## 📌 Quick Reference

| Item | Value |
|------|-------|
| **Server** | `172.28.1.148` |
| **User** | `lims` |
| **Path** | `/home/lims/edms-staging` |
| **Frontend URL** | `http://172.28.1.148:3001` |
| **Backend API** | `http://172.28.1.148:8001/api/v1` |
| **Compose File** | `docker-compose.prod.yml` |
| **Expected Downtime** | 3-5 minutes (frontend only) |
| **Branch** | `develop` |

---

## ✨ After Successful Deployment

1. Update team on Slack/communication channel
2. Test the authentication flow thoroughly
3. Monitor logs for any errors: `docker compose -f docker-compose.prod.yml logs -f frontend`
4. Remind users to clear browser cache

---

**Deployment Date**: January 13, 2026  
**Changes**: Authentication redirect in DocumentManagement  
**Impact**: Frontend only, backend unaffected
