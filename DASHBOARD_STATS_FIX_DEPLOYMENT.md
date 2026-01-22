# Dashboard Stats Fix - Deployment Guide

**Issue:** Dashboard showing all zeros (0) on stat cards
**Fix:** Corrected table names in SQL queries
**Commit:** Latest on `main` branch

---

## What Was Wrong

The `dashboard_stats.py` file was querying tables with incorrect names:

| Wrong Table Name | Correct Table Name | Issue |
|------------------|-------------------|--------|
| `workflow_instances` with `is_active` | `document_workflows` with `is_terminated` | Different table name and column |
| `placeholder_definitions` | `placeholders` | Wrong table name |
| Querying `workflow_instances` for pending reviews | Query `documents` table directly | More accurate |

---

## The Fix

Updated `backend/apps/api/dashboard_stats.py`:

1. **Active Workflows:**
   ```python
   # OLD (wrong)
   FROM workflow_instances WHERE is_active = true
   
   # NEW (correct)
   FROM document_workflows WHERE is_terminated = false
   ```

2. **Placeholders:**
   ```python
   # OLD (wrong)
   FROM placeholder_definitions
   
   # NEW (correct)
   FROM placeholders
   ```

3. **Pending Reviews:**
   ```python
   # OLD (indirect)
   FROM workflow_instances WHERE state ILIKE '%review%'
   
   # NEW (direct)
   FROM documents WHERE status IN ('PENDING_REVIEW', 'UNDER_REVIEW')
   ```

4. **Better Error Handling:**
   - Added `traceback` to error responses for debugging
   - Added `stat_cards` to fallback data

---

## Deploy to Staging Server

### Step 1: SSH to Staging

```bash
ssh lims@staging-server-ubuntu-20
cd ~/edms
```

### Step 2: Pull Latest Fix

```bash
git pull origin main
```

### Step 3: Restart Backend (No Rebuild Needed!)

```bash
# Quick restart - code change only
docker compose restart backend

# Wait for backend to restart
sleep 10
```

### Step 4: Test Dashboard Stats API

```bash
# Test the API directly
curl http://localhost:8000/api/v1/dashboard/stats/ | jq .

# Should now show actual counts, not all zeros!
```

### Step 5: Check in Browser

1. Open: `http://your-staging-server:3000/admin/dashboard`
2. Refresh the page (Ctrl+F5 to clear cache)
3. **Dashboard should now show real numbers!**

---

## Expected Results

**Before Fix:**
```json
{
  "total_documents": 0,
  "active_workflows": 0,
  "placeholders": 0,
  "stat_cards": {
    "total_documents": 0,
    "documents_needing_action": 0,
    "active_users_24h": 0
  }
}
```

**After Fix:**
```json
{
  "total_documents": 3,          // ✅ Real count
  "active_workflows": 0,         // ✅ May be 0 if no active workflows
  "placeholders": 32,            // ✅ Real placeholder count
  "stat_cards": {
    "total_documents": 3,        // ✅ Real count
    "documents_needing_action": 0, // ✅ May be 0 if nothing pending
    "active_users_24h": 1        // ✅ Users who logged in today
  }
}
```

---

## If Numbers Are Still Zero

This might be because:

1. **No data in database yet** (fresh deployment)
   
   **Solution:** Create some test data
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User
   from apps.documents.models import Document
   from apps.placeholders.models import Placeholder
   
   print('Users:', User.objects.count())
   print('Documents:', Document.objects.count())
   print('Placeholders:', Placeholder.objects.count())
   "
   ```

2. **Tables not initialized**
   
   **Solution:** Run initialization commands
   ```bash
   docker compose exec backend python manage.py setup_placeholders_simple
   ```

3. **API returning errors**
   
   **Solution:** Check backend logs
   ```bash
   docker logs edms_backend --tail=50 | grep -i error
   ```

---

## Quick Deployment Commands (Copy-Paste)

```bash
# SSH to staging
ssh lims@staging-server-ubuntu-20

# Navigate and pull
cd ~/edms
git pull origin main

# Verify you got the fix
git log --oneline -1
# Should show: "fix(dashboard): Correct table names..."

# Restart backend
docker compose restart backend
sleep 10

# Test API
curl http://localhost:8000/api/v1/dashboard/stats/ | jq .stat_cards

# Check placeholders count
docker compose exec backend python manage.py shell -c "
from apps.placeholders.models import Placeholder
print(f'Placeholders in database: {Placeholder.objects.count()}')
"
```

---

## Verify Fix Works

### Test 1: API Returns Data
```bash
curl http://localhost:8000/api/v1/dashboard/stats/ | jq .
```

Expected: JSON with actual numbers

### Test 2: Browser Shows Stats
1. Open browser: `http://staging-server:3000/admin/dashboard`
2. Hard refresh: `Ctrl+Shift+R` or `Cmd+Shift+R`
3. Dashboard should show real numbers

### Test 3: Check Database
```bash
docker compose exec backend python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM users')
    print(f'Users: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM placeholders')
    print(f'Placeholders: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM documents')
    print(f'Documents: {c.fetchone()[0]}')
"
```

---

## Troubleshooting

### Issue: Still showing zeros after restart

**Check if placeholders were created:**
```bash
docker compose exec backend python manage.py setup_placeholders_simple
```

**Check if initialization ran:**
```bash
docker logs edms_backend | grep -i "setup_placeholders\|initialization"
```

### Issue: API returns error

**Check backend logs:**
```bash
docker logs edms_backend --tail=100
```

**Test API with detailed error:**
```bash
curl -v http://localhost:8000/api/v1/dashboard/stats/
```

### Issue: Browser cache showing old data

**Clear browser cache:**
- Chrome/Edge: `Ctrl+Shift+Delete` → Clear cached images and files
- Firefox: `Ctrl+Shift+Delete` → Clear cache
- Or use Incognito/Private mode

---

## Timeline

- **Pull changes:** 10 seconds
- **Restart backend:** 20 seconds
- **Total:** ~30 seconds (no rebuild needed!)

---

## Success Indicators

✅ `git log` shows dashboard fix commit
✅ Backend restarts without errors
✅ API returns non-zero numbers
✅ Browser dashboard shows real stats
✅ No SQL errors in logs

---

**This is a quick fix - no container rebuild required!** Just pull and restart. 🚀
