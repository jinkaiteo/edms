# Document Dependencies Display Fix

## 🎉 Issue Resolved

**Problem:** Document dependencies were being saved to the database but not displaying in the frontend (document viewer or edit modal).

**Status:** ✅ **FIXED**

---

## 🔍 Root Cause Analysis

### The Issue

When editing a document and adding a dependency (e.g., referencing document ID 1), the frontend sent:
```javascript
dependencies[0]: "1"
```

The backend successfully saved it:
```
Reactivated existing dependency: 2 → 1
Updated dependencies to: [1]
```

But the frontend showed:
```javascript
dependenciesValue: []
dependenciesLength: 0
```

---

## 🐛 The Bug

The **serializer filters** in `backend/apps/documents/serializers.py` were filtering dependencies based on document status:

```python
# OLD CODE (Lines 291, 368-370)
depends_on__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
```

**Problem:** The system was using `'APPROVED_AND_EFFECTIVE'` status, which was **NOT** in this filter list. So:
- ✅ Dependencies were saved to database
- ❌ Dependencies were filtered out when retrieving (serializer excluded them)
- ❌ Frontend received empty arrays

---

## ✅ The Fix

### Phase 1: Quick Fix (Added APPROVED_AND_EFFECTIVE)
Initially added `APPROVED_AND_EFFECTIVE` to the filters:

```python
depends_on__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
```

**Files Updated:**
- `backend/apps/documents/serializers.py` (4 locations)

**Commit:** `cb31e9c`

---

### Phase 2: Complete Fix (Standardized on EFFECTIVE)

After analyzing the scheduler code, discovered it expected `EFFECTIVE` not `APPROVED_AND_EFFECTIVE`. Made decision to **standardize on EFFECTIVE everywhere**.

**Files Updated:**

**Backend (3 files):**
1. `backend/apps/workflows/document_lifecycle.py` - All status transitions
2. `backend/apps/documents/serializers.py` - Dependency filters  
3. `scripts/initialize-workflow-defaults.sh` - DocumentState creation

**Frontend (10 files):**
1. `frontend/src/types/api.ts` - DocumentStatus type
2. `frontend/src/components/documents/DownloadActionMenu.tsx`
3. `frontend/src/components/documents/DocumentSelector.tsx`
4. `frontend/src/components/documents/DocumentViewer.tsx`
5. `frontend/src/components/documents/DocumentList.tsx`
6. `frontend/src/components/documents/DocumentSearch.tsx`
7. `frontend/src/components/common/NewsFeed.tsx`
8. `frontend/src/components/workflows/WorkflowHistory.tsx`
9. `frontend/src/components/workflows/ViewReviewStatus.tsx`
10. `frontend/src/components/workflows/UnifiedWorkflowInterface.tsx`

**Migration:**
- `scripts/migrate-to-effective-status.sh` - Data migration script

**Commit:** `7b6a77a`

---

## 🎯 Current State

### Serializer Filters (Corrected)

**DocumentListSerializer:**
```python
def get_dependencies(self, obj):
    """Get only active dependencies where target documents are approved/effective."""
    active_dependencies = obj.dependencies.filter(
        is_active=True,
        depends_on__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
    )
    return DocumentDependencySerializer(active_dependencies, many=True, context=self.context).data

def get_dependents(self, obj):
    """Get active dependents where source documents are approved/effective."""
    active_dependents = obj.dependents.filter(
        is_active=True,
        document__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
    )
    return DocumentDependencySerializer(active_dependents, many=True, context=self.context).data
```

**DocumentDetailSerializer:** (Same filters)

---

## 📊 How It Works Now

### Document Approval Flow

1. **Draft Document** → status: `DRAFT`
2. **Submit for Review** → status: `PENDING_REVIEW`
3. **Under Review** → status: `UNDER_REVIEW`
4. **Reviewed** → status: `REVIEWED`
5. **Submit for Approval** → status: `PENDING_APPROVAL`
6. **Approve with Today's Date** → status: `EFFECTIVE` ✅

### Dependency Display Logic

When viewing a document:
1. Frontend requests document details from API
2. Backend serializer fetches dependencies
3. **Filter check:** `depends_on.status in ['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']`
4. ✅ If target document has `EFFECTIVE` status → Include in list
5. ❌ If target document has any other status → Exclude from list

**Result:** Only dependencies on approved/effective documents are shown (business requirement).

---

## 🧪 Testing

### Verify the Fix

1. **Create two documents:**
   - Document A (will be the dependency target)
   - Document B (will depend on A)

2. **Approve Document A:**
   - Submit for review
   - Approve
   - Status becomes: `EFFECTIVE`

3. **Edit Document B:**
   - Add dependency on Document A
   - Save

4. **Verify in Document B viewer:**
   - ✅ Dependency on Document A should appear
   - ✅ Shows in "Dependencies" section
   - ✅ Shows in edit modal

### Backend Verification

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

```python
from apps.documents.models import Document, DocumentDependency

# Check dependency in database
doc_b = Document.objects.get(document_number='SOP-2026-0001')
print(f"Dependencies count: {doc_b.dependencies.filter(is_active=True).count()}")
for dep in doc_b.dependencies.filter(is_active=True):
    print(f"  Depends on: {dep.depends_on.document_number}")
    print(f"  Target status: {dep.depends_on.status}")
```

---

## 🔧 Why Dependencies Might Not Show

Even after this fix, dependencies won't show if:

1. **Target document is not approved/effective**
   - Dependencies only show for `EFFECTIVE` or `APPROVED_PENDING_EFFECTIVE` documents
   - Draft documents as dependencies are hidden (by design)

2. **Dependency is marked inactive**
   - `is_active=False` in database

3. **Circular dependency blocked**
   - System blocks circular dependencies

4. **Target document deleted**
   - Cascade rules handle this

---

## 📝 Related Issues

This fix also resolved:
- PDF download button being disabled for effective documents
- Document search filters not finding effective documents  
- Workflow history not showing correct icons for effective state
- News feed not displaying recently effective documents

All were caused by the same `APPROVED_AND_EFFECTIVE` vs `EFFECTIVE` mismatch.

---

## 🚀 Deployment

### On Staging/Production

1. **Pull latest code:**
   ```bash
   git pull origin develop
   ```

2. **Run data migration (if needed):**
   ```bash
   bash scripts/migrate-to-effective-status.sh
   ```

3. **Rebuild and restart:**
   ```bash
   docker compose -f docker-compose.prod.yml stop backend frontend
   docker compose -f docker-compose.prod.yml build backend frontend
   docker compose -f docker-compose.prod.yml up -d
   ```

4. **Verify:**
   - Test document approval
   - Check dependencies display
   - Verify status is `EFFECTIVE`

---

## ✅ Success Criteria

- [x] Dependencies saved to database
- [x] Dependencies display in document viewer
- [x] Dependencies show in edit modal
- [x] Only effective/approved documents shown as dependencies
- [x] Status standardized on `EFFECTIVE`
- [x] Scheduler compatibility maintained
- [x] Frontend-backend alignment achieved

---

## 📚 References

- **Original Issue:** Commit `6236385` (debug logging)
- **Initial Fix:** Commit `cb31e9c` (added APPROVED_AND_EFFECTIVE to filters)
- **Complete Fix:** Commit `7b6a77a` (standardized on EFFECTIVE)
- **Analysis Document:** `DOCUMENT_WORKFLOW_STATES_ANALYSIS.md`
- **Migration Script:** `scripts/migrate-to-effective-status.sh`

---

**Date:** 2026-01-01  
**Status:** ✅ Resolved  
**Tested:** ✅ Working on staging
