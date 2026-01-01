# 🚨 IMMEDIATE FIX: Document Creation Error on Staging

## Problem
Document creation fails with:
```
PermissionError: [Errno 13] Permission denied: '/app/storage/documents'
```

## Root Cause
The storage directory doesn't have proper write permissions for the Docker container.

---

## ✅ IMMEDIATE FIX (Run on Staging Server Now)

### Option 1: Use the Fix Script (Recommended)

```bash
# SSH to staging server
ssh lims@172.28.1.148

# Navigate to project
cd /home/lims/edms-staging

# Pull latest code (includes the fix script)
git pull origin develop

# Run the fix script
bash scripts/fix-storage-permissions.sh
```

**This will:**
- ✅ Create all required storage directories
- ✅ Set proper permissions (755)
- ✅ Restart backend container
- ✅ Verify health

---

### Option 2: Manual Fix (Quick)

```bash
# SSH to staging server
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Create directories
mkdir -p storage/documents storage/backups storage/temp
mkdir -p logs/backend logs/db logs/redis logs/nginx

# Fix permissions
chmod -R 755 storage/
chmod -R 755 logs/

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Wait 10 seconds
sleep 10

# Test
curl http://localhost:8001/health/
```

---

## ✅ Verification

After running the fix:

1. **Check permissions:**
   ```bash
   ls -lah storage/
   # Should show: drwxr-xr-x (755)
   ```

2. **Try creating a document in the app**
   - Navigate to http://172.28.1.148
   - Login with admin/test123
   - Try creating a document
   - Should work now! ✅

3. **Verify file was created:**
   ```bash
   ls -lah storage/documents/
   # Should show your uploaded document
   ```

---

## 🔄 PERMANENT FIX (Already Done)

The `deploy-production.sh` script has been updated to automatically:
- ✅ Create storage directories
- ✅ Set proper permissions
- ✅ Happens automatically on every deployment

**Next time you deploy, this issue won't happen!**

---

## 📊 Technical Details

### Why This Happened

1. **Local works:** Your local development likely created `storage/` directory with your user permissions
2. **Staging failed:** When you deployed to staging, the `storage/` directory either:
   - Didn't exist
   - Was created with wrong permissions
   - Wasn't accessible by the Docker container user

### The Fix

The Docker container mounts `./storage:/app/storage:rw` but needs:
- Directory must exist on host
- Directory must have write permissions
- Permissions: 755 (owner write, group/others read+execute)

### Updated Deployment Flow

```
deploy-production.sh
    ↓
1. setup_storage()           # NEW! Creates dirs & sets permissions
    ↓
2. Build images
    ↓
3. Start containers
    ↓
4. Initialize defaults
    ↓
5. Run tests
```

---

## 🎯 Summary

### Immediate Action Required:
```bash
# On staging server:
cd /home/lims/edms-staging
bash scripts/fix-storage-permissions.sh
```

### Future Deployments:
✅ **Automatic!** The deployment script now handles this.

---

## 🧪 Test After Fix

```bash
# Test document creation via API
curl -X POST http://172.28.1.148/api/v1/documents/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Test Document" \
  -F "description=Testing storage" \
  -F "document_type=1" \
  -F "document_source=1" \
  -F "file=@test.pdf"

# Should return 201 Created (not 500 Internal Server Error)
```

---

## 📞 Need Help?

If the fix doesn't work:

1. **Check backend logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs backend --tail=50
   ```

2. **Check if directory is writable:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend touch /app/storage/documents/test.txt
   docker compose -f docker-compose.prod.yml exec backend ls -l /app/storage/documents/test.txt
   ```

3. **Check container user:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend whoami
   docker compose -f docker-compose.prod.yml exec backend id
   ```

---

**Ready to fix?** Run:
```bash
bash scripts/fix-storage-permissions.sh
```

🎉 **Problem solved!**
