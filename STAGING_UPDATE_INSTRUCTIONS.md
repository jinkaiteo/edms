# Staging Server Update Instructions

**Date:** 2026-01-02  
**Server:** 172.28.1.148 (edms-staging)  
**Status:** ✅ Already deployed and verified

---

## 🎯 Current Status

### Already Deployed ✅

The timezone fixes and initialization improvements are **already live** on staging as of 2026-01-02 08:58 UTC.

**Verification:**
- All 6 tests passed
- Timezone displays correctly (e.g., "08:58:15 UTC")
- System defaults present (7 roles, 6 groups, 6 document types)

**If you need to verify or re-deploy, follow the instructions below.**

---

## 📋 Quick Verification (Check Current Status)

Before updating, verify the current deployment status:

```bash
# 1. SSH to staging server
ssh lims@172.28.1.148

# 2. Check current commit
cd /home/lims/edms-staging
git log --oneline -1

# Should show:
# 4f90489 test: Verify timezone consistency fix with comprehensive tests
# or later

# 3. Test timezone fix
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()
processor = DocumentAnnotationProcessor()
doc = Document.objects.first()
user = User.objects.first()

if doc and user:
    metadata = processor.get_document_metadata(doc, user)
    print(f"DOWNLOAD_TIME: {metadata.get('DOWNLOAD_TIME')}")
    print(f"TIMEZONE: {metadata.get('TIMEZONE')}")
    
    has_utc = 'UTC' in str(metadata.get('DOWNLOAD_TIME', ''))
    print(f"\n✅ Timezone working: {has_utc}")
else:
    print("⚠️  No test data available")
PYTHON
```

**Expected Output:**
```
DOWNLOAD_TIME: HH:MM:SS UTC
TIMEZONE: UTC

✅ Timezone working: True
```

**If you see the above:** ✅ Your staging is already up to date! No action needed.

**If you see issues:** Follow the update instructions below.

---

## 🚀 Update Instructions (If Needed)

### Prerequisites

- SSH access to staging server (172.28.1.148)
- User: `lims`
- Docker access on the server
- Estimated time: 5 minutes
- Downtime: ~2 minutes (backend only)

---

## Method 1: Automated Script (Recommended) ⚡

### Step 1: Pull Latest Code

```bash
# On staging server
ssh lims@172.28.1.148

cd /home/lims/edms-staging

# Pull latest changes
git pull origin develop
```

### Step 2: Run Automated Deployment

The repository includes an automated deployment script:

```bash
# If running from local machine
./deploy-to-staging.sh
```

**Or manually on the server:**

```bash
# On staging server
cd /home/lims/edms-staging

# Pull latest code
git pull origin develop

# Stop backend
docker compose -f docker-compose.prod.yml stop backend

# Rebuild backend with new code
docker compose -f docker-compose.prod.yml build backend

# Start backend
docker compose -f docker-compose.prod.yml up -d backend

# Wait for backend to be healthy
sleep 10

# Check status
docker compose -f docker-compose.prod.yml ps backend
```

### Step 3: Verify Deployment

```bash
# Test timezone fix
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()
processor = DocumentAnnotationProcessor()
doc = Document.objects.first()
user = User.objects.first()

if doc and user:
    metadata = processor.get_document_metadata(doc, user)
    
    print(f"DOWNLOAD_TIME: {metadata.get('DOWNLOAD_TIME')}")
    print(f"DOWNLOAD_DATETIME: {metadata.get('DOWNLOAD_DATETIME')}")
    print(f"TIMEZONE: {metadata.get('TIMEZONE')}")
    print("")
    
    has_utc = 'UTC' in str(metadata.get('DOWNLOAD_TIME', ''))
    has_timezone = metadata.get('TIMEZONE') == 'UTC'
    
    if has_utc and has_timezone:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  TESTS FAILED")
else:
    print("⚠️  No test data")
PYTHON
```

---

## Method 2: Manual Step-by-Step 🔧

### Step 1: Connect to Server

```bash
ssh lims@172.28.1.148
```

### Step 2: Navigate to Project Directory

```bash
cd /home/lims/edms-staging
```

### Step 3: Check Current Status

```bash
# Check current branch
git branch --show-current
# Should show: develop

# Check current commit
git log --oneline -1
```

### Step 4: Pull Latest Changes

```bash
git pull origin develop
```

**Expected output:**
```
Updating 1d256bc..4f90489
Fast-forward
 STAGING_DEPLOYMENT_FIX_COMPLETE.md             | 335 +++++++++++++++++++
 TIMEZONE_CONSISTENCY_FIX.md                    | 437 +++++++++++++++++++++++++
 TIMEZONE_TEST_RESULTS.md                       | 298 +++++++++++++++++
 backend/apps/documents/annotation_processor.py |  34 +-
 deploy-interactive.sh                          |  42 ++-
 5 files changed, 1133 insertions(+), 13 deletions(-)
```

### Step 5: Check Container Status

```bash
docker compose -f docker-compose.prod.yml ps
```

### Step 6: Stop Backend Container

```bash
docker compose -f docker-compose.prod.yml stop backend
```

**Expected output:**
```
 Container edms_prod_backend  Stopping
 Container edms_prod_backend  Stopped
```

### Step 7: Rebuild Backend Image

⚠️ **CRITICAL:** You must rebuild the image, not just restart!

```bash
docker compose -f docker-compose.prod.yml build backend
```

**Expected output:**
```
Building backend...
[+] Building 18s
...
 backend  Built
```

**Build time:** ~18-30 seconds

### Step 8: Start Backend with New Image

```bash
docker compose -f docker-compose.prod.yml up -d backend
```

**Expected output:**
```
 Container edms_prod_backend  Recreated
 Container edms_prod_backend  Starting
 Container edms_prod_backend  Started
```

### Step 9: Wait for Backend to be Healthy

```bash
# Wait 10 seconds
sleep 10

# Check status
docker compose -f docker-compose.prod.yml ps backend
```

**Expected output:**
```
NAME                IMAGE                  COMMAND                  SERVICE   CREATED          STATUS                    PORTS
edms_prod_backend   edms-staging-backend   "sh -c 'echo 'Starti…"   backend   XX seconds ago   Up XX seconds (healthy)   0.0.0.0:8001->8000/tcp
```

Wait until you see **(healthy)** status.

### Step 10: Verify Timezone Fix

```bash
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from django.conf import settings
from django.utils import timezone

print(f"TIME_ZONE: {settings.TIME_ZONE}")
print(f"Current UTC: {timezone.now()}")
PYTHON
```

**Expected output:**
```
TIME_ZONE: UTC
Current UTC: 2026-01-02 09:XX:XX.XXXXXX+00:00
```

### Step 11: Test Annotation Processor

```bash
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()
processor = DocumentAnnotationProcessor()
doc = Document.objects.first()
user = User.objects.first()

if doc and user:
    metadata = processor.get_document_metadata(doc, user)
    
    print(f"Test Document: {doc.document_number}")
    print(f"DOWNLOAD_TIME: {metadata.get('DOWNLOAD_TIME')}")
    print(f"DOWNLOAD_DATETIME: {metadata.get('DOWNLOAD_DATETIME')}")
    print(f"TIMEZONE: {metadata.get('TIMEZONE')}")
    print("")
    
    # Verify
    has_utc_time = 'UTC' in str(metadata.get('DOWNLOAD_TIME', ''))
    has_timezone = metadata.get('TIMEZONE') == 'UTC'
    
    print(f"✅ DOWNLOAD_TIME includes UTC: {has_utc_time}")
    print(f"✅ TIMEZONE field is UTC: {has_timezone}")
    
    if has_utc_time and has_timezone:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
else:
    print("⚠️  No documents or users found for testing")
PYTHON
```

**Expected output:**
```
Test Document: REC-2026-0001-v01.00
DOWNLOAD_TIME: 09:XX:XX UTC
DOWNLOAD_DATETIME: 2026-01-02 09:XX:XX UTC
TIMEZONE: UTC

✅ DOWNLOAD_TIME includes UTC: True
✅ TIMEZONE field is UTC: True

🎉 ALL TESTS PASSED!
```

---

## ✅ Success Criteria

Deployment is successful when you see:

1. ✅ `git pull` completes without errors
2. ✅ Docker build completes successfully
3. ✅ Backend container shows `(healthy)` status
4. ✅ `TIME_ZONE: UTC` in Django settings
5. ✅ `DOWNLOAD_TIME` shows "HH:MM:SS UTC" format
6. ✅ `TIMEZONE` field shows "UTC"
7. ✅ All verification tests pass

---

## 🔍 Troubleshooting

### Issue 1: Git Pull Shows Conflicts

**Problem:** Merge conflicts when pulling

**Solution:**
```bash
# Stash local changes
git stash

# Pull again
git pull origin develop

# Apply stashed changes (if needed)
git stash pop
```

### Issue 2: Docker Build Fails

**Problem:** Build errors during `docker compose build`

**Check:**
```bash
# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -f

# Retry build
docker compose -f docker-compose.prod.yml build --no-cache backend
```

### Issue 3: Backend Won't Start

**Problem:** Container starts but immediately stops

**Check logs:**
```bash
docker compose -f docker-compose.prod.yml logs backend
```

**Common causes:**
- Database connection issues
- Port already in use
- Configuration errors

### Issue 4: Timezone Fix Not Working

**Problem:** Still seeing timestamps without "UTC"

**Reason:** Container not rebuilt, just restarted

**Solution:**
```bash
# MUST rebuild, not just restart
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

**Why:** Docker containers run from images. Code changes require rebuilding the image.

### Issue 5: Backend Shows Unhealthy

**Problem:** Container running but health check fails

**Check:**
```bash
# Check health endpoint
curl http://localhost:8001/health/

# Check logs
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

**Wait:** Health check may take 30-60 seconds to pass after startup.

---

## 🔄 Rollback Procedure

If something goes wrong, you can rollback:

### Option 1: Rollback Code

```bash
cd /home/lims/edms-staging

# Find previous commit
git log --oneline -5

# Rollback to previous commit
git reset --hard <previous-commit-hash>

# Rebuild with old code
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

### Option 2: Restart with Existing Image

```bash
# Just restart (if issue is not code-related)
docker compose -f docker-compose.prod.yml restart backend
```

### Option 3: Full Redeploy

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Pull specific working commit
git reset --hard 1d256bc  # Previous working commit

# Rebuild and start
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## 📊 What Gets Updated

### Code Changes (2 files):

1. **backend/apps/documents/annotation_processor.py**
   - Replaced `datetime.now()` with `timezone.now()` (4 locations)
   - Added timezone display to timestamps
   - Added ISO 8601 format fields
   - Added TIMEZONE metadata field

2. **deploy-interactive.sh**
   - Added `create_default_roles` step
   - Added `create_default_groups` step
   - Added `create_default_document_types` step

### Documentation Added (3 files):

1. **STAGING_DEPLOYMENT_FIX_COMPLETE.md** (335 lines)
2. **TIMEZONE_CONSISTENCY_FIX.md** (437 lines)
3. **TIMEZONE_TEST_RESULTS.md** (298 lines)

### No Database Changes:
- ❌ No migrations required
- ❌ No data loss
- ❌ No database downtime
- ✅ Fully backward compatible

---

## ⏱️ Deployment Timeline

| Step | Duration | Downtime |
|------|----------|----------|
| Git pull | ~5 seconds | None |
| Stop backend | ~10 seconds | Starts here |
| Build image | ~18 seconds | Backend down |
| Start backend | ~5 seconds | Backend down |
| Health check | ~10 seconds | Backend down |
| Verification | ~30 seconds | None |
| **TOTAL** | **~80 seconds** | **~2 minutes** |

**Note:** Only backend has downtime. Frontend, database, and other services continue running.

---

## 📝 Post-Update Checklist

After updating, verify:

- [ ] Backend container shows `(healthy)` status
- [ ] Timestamps include "UTC" suffix
- [ ] TIMEZONE field shows "UTC"
- [ ] No errors in backend logs
- [ ] Frontend still accessible
- [ ] Users can login
- [ ] Documents can be viewed
- [ ] Document download works
- [ ] Annotations show timezone

---

## 🔗 Related Documentation

- **STAGING_DEPLOYMENT_SUCCESS_20260102.md** - Complete deployment report
- **TIMEZONE_CONSISTENCY_FIX.md** - Technical implementation details
- **TIMEZONE_TEST_RESULTS.md** - Comprehensive test results
- **deploy-to-staging.sh** - Automated deployment script

---

## 📞 Support

### If You Need Help:

**Server Access:**
- URL: http://172.28.1.148
- SSH: `ssh lims@172.28.1.148`
- Path: `/home/lims/edms-staging`

**Quick Commands:**
```bash
# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Restart if needed
docker compose -f docker-compose.prod.yml restart backend

# Full rebuild
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

---

## ✅ Summary

**Current Status:** ✅ Already deployed and verified (2026-01-02 08:58 UTC)

**To Update/Re-deploy:**
1. SSH to staging server
2. Pull latest code: `git pull origin develop`
3. **REBUILD** (not restart): `docker compose build backend`
4. Start: `docker compose up -d backend`
5. Verify: Run test script above

**Key Point:** ⚠️ Must **rebuild** container, not just restart, for Python code changes!

---

**Last Updated:** 2026-01-02  
**Current Commit:** d6d2062  
**Status:** ✅ Instructions tested and verified
