# Quick Staging Update Reference

⚡ **Fast reference for updating staging server with timezone fixes**

---

## 🎯 Current Status

✅ **Already Deployed:** Timezone fixes are live on staging (2026-01-02 08:58 UTC)

**To verify or re-deploy, use the commands below.**

---

## ⚡ Quick Update (3 Commands)

```bash
# 1. SSH to staging server
ssh lims@172.28.1.148

# 2. Navigate and pull latest code
cd /home/lims/edms-staging
git pull origin develop

# 3. Rebuild backend (REQUIRED for code changes)
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

**Time:** ~5 minutes  
**Downtime:** ~2 minutes (backend only)

---

## ✅ Quick Verification

```bash
# Check if timezone fix is working
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
    print(f"\n{'✅' if has_utc else '❌'} Timezone working: {has_utc}")
PYTHON
```

**Expected Output:**
```
DOWNLOAD_TIME: HH:MM:SS UTC
TIMEZONE: UTC

✅ Timezone working: True
```

---

## ⚠️ Critical Notes

1. **MUST rebuild container**, not just restart
   - ❌ `docker compose restart backend` - Won't work!
   - ✅ `docker compose build backend` - Required!

2. **Why?** Docker containers run from images (snapshots), not live code

3. **No database changes** - No migrations, no data loss, fully compatible

---

## 🔗 Full Documentation

- **STAGING_UPDATE_INSTRUCTIONS.md** - Complete step-by-step guide
- **STAGING_DEPLOYMENT_SUCCESS_20260102.md** - Deployment report
- **TIMEZONE_CONSISTENCY_FIX.md** - Technical details

---

## 📊 What's Updated

### Code Changes:
- ✅ Timezone consistency (UTC display everywhere)
- ✅ ISO 8601 timestamp support
- ✅ Complete initialization sequence

### New Metadata Fields:
- `DOWNLOAD_TIME`: `08:58:15 UTC` (was: `08:58:15`)
- `TIMEZONE`: `UTC` (new field)
- `DOWNLOAD_DATETIME_ISO`: ISO 8601 format (new field)

---

## 🚨 Troubleshooting

**Problem:** Timezone not showing after update  
**Solution:** You restarted instead of rebuilding - run:
```bash
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

**Problem:** Backend won't start  
**Solution:** Check logs:
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

---

**Server:** 172.28.1.148 (edms-staging)  
**GitHub:** https://github.com/jinkaiteo/edms.git  
**Branch:** develop  
**Latest Commit:** 498d0a5
