# Deployment Final Status and Instructions

## Current Situation

The deployment is **technically correct**:
- ✅ Using docker-compose.prod.yml (correct file)
- ✅ Production containers running (edms_prod_*)
- ✅ Correct ports (3001/8001)
- ✅ Frontend source code has username display (line 554: `{user?.full_name || user?.username}`)
- ✅ Backend API working
- ✅ Profile endpoint returns user data

## Issue: Username Not Showing

The username display code EXISTS in the frontend source (Layout.tsx line 554), but you're not seeing it. This suggests:

### Possible Causes

1. **Browser Cache**
   - Your browser is serving old JavaScript files
   - Even though container has new build, browser cached old version

2. **Authentication State**
   - Frontend not properly storing/using JWT tokens
   - User object not being populated after login

3. **API Endpoint Mismatch**
   - Frontend still calling wrong endpoints (despite rebuild)
   - Profile data not loading

---

## Immediate Troubleshooting Steps

### Step 1: Clear Browser Cache Completely

**Hard Refresh (Force cache clear):**
- **Chrome/Edge**: Ctrl+Shift+Del → Clear cache → Hard refresh (Ctrl+F5)
- **Firefox**: Ctrl+Shift+Del → Clear cache → Hard refresh (Ctrl+F5)
- **Or use Incognito/Private mode** to test without cache

### Step 2: Check Browser Console

Open browser console (F12) and check for:
1. **API errors**: Look for 404 or 500 errors when calling `/api/v1/auth/profile/`
2. **JavaScript errors**: Any errors preventing username display
3. **Network tab**: Check if profile API is being called and what it returns

### Step 3: Verify Authentication

After login, check:
1. Open Console (F12) → Application → Local Storage
2. Look for `access_token` and `refresh_token`
3. If missing, authentication is not working

### Step 4: Test Profile API Manually

From browser console, test if profile data loads:
```javascript
fetch('http://172.28.1.148:8001/api/v1/auth/profile/', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(r => r.json())
.then(console.log)
```

Should return your user object with `username: "admin"`

---

## Manual Cleanup and Fresh Deployment Instructions

If the above doesn't work, here's how to do a completely fresh deployment:

### Complete Cleanup (Run on Staging Server)

```bash
ssh lims@172.28.1.148

cd ~/edms-staging

# Stop all containers
docker compose -f docker-compose.prod.yml down -v

# Remove all containers
docker stop $(docker ps -a -q) 2>/dev/null
docker rm $(docker ps -a -q) 2>/dev/null

# Remove images
docker rmi $(docker images -q edms-staging*) 2>/dev/null

# Prune everything
docker system prune -a --volumes -f

# Clean directory
cd ~
rm -rf edms-staging-old
mv edms-staging edms-staging-old

# Keep backups!
# ls -lh ~/edms-backups/
```

### Fresh Deployment (After Cleanup)

```bash
# You'll need to copy the correct deployment package again
# Then:
cd ~/edms-staging

# Ensure correct .env file
# Ensure using docker-compose.prod.yml

# Build and start
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Initialize database
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
# Username: admin
# Email: admin@edms-staging.local  
# Password: AdminPassword123!@#
```

---

## What to Check After Fresh Deployment

1. **Container Status**
```bash
docker compose -f docker-compose.prod.yml ps
```
All 6 containers should show "Up" or "healthy"

2. **Frontend Build Timestamp**
```bash
docker compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html/static/js/
```
Should show recent timestamp

3. **Login and Check**
- Go to http://172.28.1.148:3001
- Login with admin / AdminPassword123!@#
- Check top-right corner for username
- Check browser console for errors

---

## Expected Behavior (Working System)

When working correctly, you should see:

1. **After Login**:
   - Username "admin" or "Admin" in top-right corner
   - Dropdown with profile options when clicked
   - No console errors

2. **Dashboard**:
   - Document counts loading
   - No 404 errors in console
   - All navigation working

3. **API Calls** (Check Network tab):
   - `/api/v1/auth/token/` → Returns access/refresh tokens
   - `/api/v1/auth/profile/` → Returns user data
   - `/api/v1/documents/` → Returns documents (not `/documents/documents/`)

---

## Current Deployment Configuration

**Containers**: edms_prod_* (correct)
**Ports**: 3001/8001 (correct)
**Frontend Build**: Jan 6 00:54 UTC (should be latest)
**Source Code**: Has username display at line 554 (correct)

**The code is correct. The issue is likely browser cache or authentication state.**

---

## Recommended Action

1. **Try Incognito/Private browsing mode** first
2. **Clear all browser cache** and try again
3. **Check browser console** for actual errors
4. If still not working, provide the console errors and we can diagnose further

The deployment itself appears to be correct - this is likely a client-side caching or authentication issue.
