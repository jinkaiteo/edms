# Next Steps: Fix CORS Issue

## 🎉 **Current Status: LOGIN WORKING!**

HAProxy is successfully deployed and authentication is working at `http://172.28.1.148`

---

## ⚠️ **Remaining Issue: CORS Errors**

**Problem:** Frontend making API calls to `http://localhost:8000` instead of using relative paths through HAProxy.

**Evidence:**
```
Cross-Origin Request Blocked: The Same Origin Policy disallows reading 
the remote resource at http://localhost:8000/api/v1/documents/documents/
```

---

## 🔧 **Root Cause**

The frontend container was built BEFORE `REACT_APP_API_URL=/api/v1` was set in `docker-compose.prod.yml`. 

React apps bake environment variables into the build at **build time**, not runtime. The current running container still has the old `localhost:8000` URLs compiled into the JavaScript bundle.

---

## ✅ **Solution: Rebuild Frontend**

### On Staging Server:

```bash
# Pull the rebuild script
git pull origin develop

# Run the rebuild script
bash scripts/rebuild-frontend-fix-api-url.sh
```

**What this does:**
1. Stops frontend container
2. Removes old container
3. Rebuilds with `--no-cache` (forces React to use new REACT_APP_API_URL)
4. Starts new container
5. Verifies it's healthy

**Time:** ~3-5 minutes

---

## 🎯 **Expected Result**

After rebuild:
- ✅ All API calls use `/api/v1/` (relative path)
- ✅ Requests go through HAProxy, not directly to localhost:8000
- ✅ No more CORS errors
- ✅ Document list loads correctly
- ✅ User profile loads correctly
- ✅ All features work

---

## 🧪 **How to Verify**

### 1. Clear Browser Cache
```
Press: Ctrl + Shift + R (or Cmd + Shift + R on Mac)
```

### 2. Open Browser Console
```
F12 → Console tab
```

### 3. Login and Watch Network Tab
```
F12 → Network tab
Filter: XHR
```

**Before Fix:**
```
❌ GET http://localhost:8000/api/v1/documents/...
   CORS Missing Allow Origin
```

**After Fix:**
```
✅ GET http://172.28.1.148/api/v1/documents/...
   Status: 200 OK
```

---

## 📋 **Quick Commands**

### On Staging Server:
```bash
# 1. Pull latest code
cd /home/lims/edms-staging
git pull origin develop

# 2. Rebuild frontend
bash scripts/rebuild-frontend-fix-api-url.sh

# 3. Wait for completion (~3-5 minutes)

# 4. Clear browser cache and test
# Open: http://172.28.1.148
# Login: admin / test123
# Check: No CORS errors in console
```

---

## 🔍 **Troubleshooting**

### If CORS errors persist after rebuild:

1. **Verify environment variable in container:**
```bash
docker compose -f docker-compose.prod.yml exec frontend env | grep REACT_APP_API_URL
# Should show: REACT_APP_API_URL=/api/v1
```

2. **Check if browser is caching old JS:**
```
- Open DevTools (F12)
- Go to Application tab
- Clear Storage → Clear site data
- Hard refresh (Ctrl+Shift+R)
```

3. **Verify HAProxy is routing correctly:**
```bash
curl -v http://localhost/api/v1/auth/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
# Should return 200 or 401, not 503
```

4. **Check HAProxy stats:**
```
http://172.28.1.148:8404/stats
# Both backends should be GREEN
```

---

## 📊 **Summary**

| Component | Status | Notes |
|-----------|--------|-------|
| HAProxy | ✅ Working | Routing correctly on port 80 |
| Backend | ✅ Working | Healthy and responding |
| Frontend Container | ⚠️ Needs Rebuild | Using old API URL |
| Login | ✅ Working | Authentication successful |
| Document Management | ❌ CORS Errors | Waiting for frontend rebuild |

---

## 🚀 **Action Required**

**Run on staging server:**
```bash
git pull origin develop
bash scripts/rebuild-frontend-fix-api-url.sh
```

**Then test in browser and all CORS issues should be resolved!** 🎉

---

**Last Updated:** 2026-01-01  
**Status:** Ready to fix CORS with frontend rebuild
