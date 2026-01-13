# Deploy Frontend to Staging - Ready to Execute

## ✅ Status Check

✅ **Commit 29e6433 is already on GitHub!**
```
29e6433 fix: Add authentication redirect to DocumentManagement page
```

✅ **No push needed** - Staging can pull directly from GitHub

---

## 🚀 Deploy Now (Choose One Method)

### Method 1: Automated Script (Recommended)

```bash
./QUICK_DEPLOY_STAGING.sh
```

### Method 2: Manual Commands

```bash
ssh lims@172.28.1.148 << 'ENDSSH'
    cd /home/lims/edms-staging
    
    # Pull latest code from GitHub
    git pull origin develop
    
    # Rebuild and restart frontend
    docker compose -f docker-compose.prod.yml stop frontend
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    docker compose -f docker-compose.prod.yml up -d frontend
    
    # Verify
    docker compose -f docker-compose.prod.yml ps frontend
    curl http://localhost:3001/
ENDSSH
```

---

## ⏱️ Expected Timeline

- **Duration**: ~4 minutes total
- **Downtime**: ~3 minutes (frontend only)
- **Backend**: Unaffected, continues running

---

## 🧪 Testing After Deployment

**Important: Use incognito mode!**

1. Open: `http://172.28.1.148:3001` (incognito)
2. Try to access document management
3. **Expected**: Redirects to login page ✅
4. Login with credentials
5. **Expected**: Access document management ✅

---

## ⚠️ Critical: Browser Cache

After deployment, users MUST:
- Use **incognito/private mode**, OR
- Hard reload: **Ctrl+Shift+R** (Windows/Linux) / **Cmd+Shift+R** (Mac)

Why? Frontend JavaScript is rebuilt - browser cache will show old code.

---

## 🎯 Execute Deployment

Run this command:
```bash
./QUICK_DEPLOY_STAGING.sh
```

**That's it!** The script will handle everything. 🚀
