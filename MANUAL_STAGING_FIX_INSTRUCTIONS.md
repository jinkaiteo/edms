# Manual Instructions to Fix VERSION_HISTORY Timezone on Staging

**Issue:** VERSION_HISTORY dates not showing "UTC" suffix in downloaded documents

**Root Cause:** Backend container needs to be rebuilt to load the new Python code

---

## ✅ Quick Fix Instructions

Run these commands **directly on the staging server**:

### Step 1: SSH to Staging Server

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging
```

### Step 2: Pull Latest Code

```bash
git pull origin develop
```

**Expected:** Already up to date (you have commit 29d5a93)

### Step 3: Stop Backend

```bash
docker compose -f docker-compose.prod.yml stop backend
```

**Wait:** ~10 seconds

### Step 4: Rebuild Backend (CRITICAL)

```bash
docker compose -f docker-compose.prod.yml build --no-cache backend
```

**Time:** ~3-5 minutes  
**Why:** This loads the new Python code into the Docker image

### Step 5: Start Backend

```bash
docker compose -f docker-compose.prod.yml up -d backend
```

**Wait:** ~15 seconds for backend to start

### Step 6: Check Backend Status

```bash
docker compose -f docker-compose.prod.yml ps backend
```

**Expected:** Should show `Up` and `(healthy)` status

### Step 7: Verify the Fix

```bash
bash test-version-history-timezone.sh
```

**Expected Output:**
```
Testing with: REC-2026-0001-v01.00
Generated: 01/02/2026 09:XX AM UTC    ✅
First row date: 01/02/2026 UTC        ✅

Verification:
  ✅ Date includes UTC: True
  ✅ Generated includes UTC: True

🎉 VERSION_HISTORY TIMEZONE FIX WORKING!
```

---

## 🧪 Test the Fix in Browser

1. Go to http://172.28.1.148:3001
2. Login as any user
3. Find a document with version history
4. Click **Download Official PDF**
5. Open the downloaded PDF
6. Scroll to **VERSION HISTORY** section
7. Verify dates show: `01/02/2026 UTC` (with UTC)
8. Verify generated shows: `01/02/2026 09:XX AM UTC` (with UTC)

---

## ❓ Troubleshooting

### Issue: Backend Won't Start

**Check logs:**
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

**Solution:** Wait 30 seconds, backend may still be starting

### Issue: Still No UTC in Downloaded Documents

**Verify code is loaded:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'EOF'
import inspect
from apps.placeholders.services import PlaceholderService
source = inspect.getsource(PlaceholderService._get_version_history_data)
print("✅ UTC fix found" if "strftime('%m/%d/%Y UTC')" in source else "❌ UTC fix NOT found")
EOF
```

**If "NOT found":** Rebuild didn't work - try again with `--no-cache`

### Issue: Build Fails

**Clean up and retry:**
```bash
docker system prune -f
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend
```

---

## 📊 What Changed

### Files Modified:
- `backend/apps/placeholders/services.py` (2 lines)

### Changes:
**Line 407:**
```python
# Before
date = version_doc.created_at.strftime('%m/%d/%Y')

# After
date = version_doc.created_at.strftime('%m/%d/%Y UTC')
```

**Line 434:**
```python
# Before
'generated': timezone.now().strftime('%m/%d/%Y %I:%M %p')

# After
'generated': timezone.now().strftime('%m/%d/%Y %I:%M %p UTC')
```

---

## ⚠️ Important Notes

1. **OLD documents won't update** - You must download a NEW document to see the fix
2. **Browser cache** - Clear cache or use incognito mode
3. **Container must be rebuilt** - Simple restart won't work for Python code changes
4. **Wait for healthy status** - Backend needs ~15 seconds to start properly

---

## ✅ Success Criteria

The fix is working when:
- ✅ Test script shows "VERSION_HISTORY TIMEZONE FIX WORKING!"
- ✅ Downloaded PDF shows dates with "UTC" suffix
- ✅ Generated timestamp shows "UTC" suffix
- ✅ All timestamps consistent across document

---

**Current Status:** Code is on staging server, just needs backend rebuild to take effect.

**Estimated Time:** 5-7 minutes total
