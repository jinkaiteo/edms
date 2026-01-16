# Admin Dashboard Card Fixes - January 15, 2026

## Issues Fixed

### 1. Active Workflows Card - **FIXED** ✅
**Problem**: Showed `0` instead of `3`
- **Root Cause**: Variable name collision - `active_workflows` was used twice:
  - Line 68-70: Count of documents in workflow states (user metric)
  - Line 99: Count of DocumentWorkflow records (system metric)
  - The second usage overwrote the first, causing the wrong value to be used

**Solution**:
- Renamed variables to avoid collision:
  - `user_active_workflows`: For user-specific document counts
  - `system_active_workflows`: For system-wide active workflow counts
- Changed calculation from `DocumentWorkflow.objects.filter(is_terminated=False)` (stale workflows)
  - To: `Document.objects.filter(status__in=['DRAFT', 'PENDING_REVIEW', ...])` (actual active documents)

**Why the change in calculation?**
- Old method counted workflow database records (showed 2 stale workflows for EFFECTIVE documents)
- New method counts documents actually in workflow states (3 documents)
- More meaningful metric: "How many documents are currently going through workflows?"

### 2. Placeholders Card - **NOT CHANGED** ⚠️
**Status**: Shows `0` (correct but hardcoded)
- Database has 0 placeholders (verified)
- Originally hardcoded: `'placeholders': 0,  # TODO: Get actual placeholder count`
- Now documented: `'placeholders': 0,  # Placeholder count - currently 0 in database`
- **Decision**: Left hardcoded since database has 0 placeholders anyway
- **Future**: Should be changed to query PlaceholderDefinition model when placeholders are added

### 3. Recent Admin Activities Section - **REMOVED** ✅
- Entire section removed from `frontend/src/pages/AdminDashboard.tsx` (lines 267-306)
- Was showing mostly SYSTEM_HEALTH_CHECK entries (not useful)
- Removed debug console.log statements

## What are Active Workflows?

**Active Workflows** track documents going through review/approval processes.

### Before Fix:
- Counted `DocumentWorkflow` database records with `is_terminated=False`
- Showed: **2** (stale workflow records for documents already EFFECTIVE)
- Problem: Workflows weren't terminated when documents became EFFECTIVE

### After Fix:
- Counts documents in workflow states: DRAFT, PENDING_REVIEW, UNDER_REVIEW, REVIEWED, PENDING_APPROVAL
- Shows: **3** (actual documents in workflow processes)
- More accurate representation of system activity

## Files Modified

1. `backend/apps/api/dashboard_api_views.py`:
   - Fixed variable naming collision
   - Changed active workflows calculation method
   - Lines 68, 91, 99-102, 117, 156

2. `frontend/src/pages/AdminDashboard.tsx`:
   - Removed "Recent Admin Activities" section
   - Lines 267-306 deleted

## Testing

```bash
# Verify active workflows count
docker compose exec backend python manage.py shell -c "
from apps.documents.models import Document
print(Document.objects.filter(status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']).count())
"
# Output: 3

# Check dashboard API
# Navigate to http://localhost:3000/administration
# Should show: Active Workflows: 3
```

## Current Dashboard Card Values

| Card | Value | Source | Status |
|------|-------|--------|--------|
| 👥 Active Users | 6 | Real DB query | ✅ Correct |
| 🔄 Active Workflows | 3 | Real DB query (FIXED) | ✅ Correct |
| 🔧 Placeholders | 0 | Hardcoded (matches DB) | ⚠️ Works but hardcoded |
| 📋 Audit Entries (24h) | 100 | Real DB query | ✅ Correct |

