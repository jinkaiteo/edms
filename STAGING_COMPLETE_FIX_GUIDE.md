# 🚨 COMPLETE FIX: Document Upload on Staging

## Problem Summary

**Issue 1:** Permission denied on `/app/storage/media`  
**Issue 2:** Multiple draft documents created without files

## Root Cause

Django's `MEDIA_ROOT` is set to `/app/storage/media` but only `/app/storage/documents` was created.

---

## ✅ COMPLETE FIX (Run on Staging Server)

### Step 1: Pull Latest Fix

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Pull the latest fix (includes storage/media directory)
git pull origin develop
```

### Step 2: Run Storage Fix Script

```bash
# Run the updated fix script with sudo
sudo bash scripts/fix-storage-permissions.sh
```

**This will now create:**
- ✅ `storage/documents` - For document storage
- ✅ `storage/media` - **CRITICAL: For file uploads**
- ✅ `storage/media/certificates` - For PDF signatures
- ✅ `storage/backups` - For system backups
- ✅ All log directories

### Step 3: Clean Up Duplicate Drafts

```bash
# Clean up the draft documents without files
bash scripts/cleanup-duplicate-drafts.sh
```

**This will:**
- Show you how many drafts without files exist
- Ask for confirmation
- Delete them safely

### Step 4: Test Document Creation

1. Open http://172.28.1.148
2. Login with admin/test123
3. Create a new document with a file
4. Should work perfectly now! ✅

---

## 📊 What Was Fixed

### Commit History:

1. **`4d3e617`** - Added automatic storage setup and initialization
2. **`d86b159`** - Added sudo support to fix script
3. **`b2ade8b`** - **CRITICAL: Added storage/media directory** ✅

### Directory Structure (Correct):

```
storage/
├── documents/          # Document files
├── media/              # ✅ File uploads (MEDIA_ROOT)
│   └── certificates/   # PDF signatures
├── backups/            # System backups
└── temp/               # Temporary files

logs/
├── backend/
├── db/
├── redis/
└── nginx/
```

---

## 🔍 Technical Details

### Why This Happened

**Django File Upload Flow:**
```python
# backend/edms/settings/base.py
MEDIA_ROOT = BASE_DIR / 'storage' / 'media'  # ← Files saved here

# backend/apps/documents/models.py
file = models.FileField(upload_to='documents/')  # ← Uploaded to MEDIA_ROOT/documents/
```

**What Went Wrong:**
1. Script only created `storage/documents`
2. Django tried to write to `storage/media/documents/`
3. Directory didn't exist → **Permission denied**
4. Document created but file upload failed → Draft without file

**The Fix:**
- Create `storage/media` directory
- Django can now write files
- File uploads work correctly

---

## 🧪 Verification

After running the fix:

### 1. Check Directories Exist
```bash
ls -lah storage/
# Should show:
# drwxr-xr-x  documents
# drwxr-xr-x  media      ← MUST BE PRESENT
# drwxr-xr-x  backups
```

### 2. Check Permissions
```bash
ls -ld storage/media
# Should show: drwxr-xr-x (755)
```

### 3. Test Write Access from Container
```bash
docker compose -f docker-compose.prod.yml exec backend touch /app/storage/media/test.txt
docker compose -f docker-compose.prod.yml exec backend ls -l /app/storage/media/test.txt
docker compose -f docker-compose.prod.yml exec backend rm /app/storage/media/test.txt
# All should succeed without errors
```

### 4. Check Backend Logs
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
# Should NOT show permission errors
```

### 5. Test Document Creation
- Create document with file
- Check file was saved:
```bash
ls -lah storage/media/documents/
# Should show your uploaded file
```

---

## 🎯 Summary

### Commands to Run:

```bash
# On staging server (172.28.1.148):
cd /home/lims/edms-staging

# 1. Pull latest fix
git pull origin develop

# 2. Fix storage permissions (includes media directory now!)
sudo bash scripts/fix-storage-permissions.sh

# 3. Clean up duplicate drafts
bash scripts/cleanup-duplicate-drafts.sh

# 4. Test document creation
# Open http://172.28.1.148 and create a document
```

### Expected Results:

- ✅ No permission errors
- ✅ Files upload successfully
- ✅ Documents created with files attached
- ✅ Document type and source saved correctly
- ✅ No duplicate drafts

---

## 🚀 Future Deployments

**Good news:** This is now automated!

The `deploy-production.sh` script now includes `storage/media` in the setup, so future deployments will automatically have the correct directory structure.

---

## 🆘 Troubleshooting

### If document creation still fails:

1. **Check backend logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs backend --tail=100 | grep -i error
   ```

2. **Verify directory exists in container:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend ls -la /app/storage/
   docker compose -f docker-compose.prod.yml exec backend ls -la /app/storage/media/
   ```

3. **Check directory ownership:**
   ```bash
   ls -lah storage/
   # Should be owned by 'lims' user or have 755 permissions
   ```

4. **Restart backend container:**
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

### If drafts keep appearing:

This means file upload is still failing. Check:
1. Directory permissions (755)
2. Directory ownership (lims user)
3. Container can write to directory (test with touch command above)

---

## 📞 Need Help?

If you're still having issues after running all steps:

1. Share the output of:
   ```bash
   ls -lah storage/
   docker compose -f docker-compose.prod.yml logs backend --tail=100
   ```

2. Try creating a document and share the exact error message

---

**Ready to fix?** Just run:

```bash
git pull origin develop
sudo bash scripts/fix-storage-permissions.sh
bash scripts/cleanup-duplicate-drafts.sh
```

🎉 **Document creation will work!**
