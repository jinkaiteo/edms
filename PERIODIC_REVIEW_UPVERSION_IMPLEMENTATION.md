# Periodic Review Up-Versioning Implementation

**Date**: January 22, 2026  
**Status**: ✅ Completed

---

## 🎯 **Objective**

Update the periodic review workflow to automatically trigger up-versioning when a reviewer determines that changes are required during periodic review.

---

## 📋 **Changes Summary**

### **Previous Implementation**

The periodic review had 3 outcomes:
- `CONFIRMED` - No changes needed
- `UPDATED` - Minor changes applied (recorded but no action)
- `UPVERSIONED` - Major changes required (recorded but no action)

**Problem**: The `UPDATED` and `UPVERSIONED` outcomes were passive - they only recorded the decision but did not trigger the actual up-versioning workflow.

### **New Implementation**

The periodic review now has 3 outcomes that align with up-versioning:
- `CONFIRMED` - No changes needed (same behavior)
- `MINOR_UPVERSION` - Minor changes required (triggers minor up-version workflow)
- `MAJOR_UPVERSION` - Major changes required (triggers major up-version workflow)

**Improvement**: Both `MINOR_UPVERSION` and `MAJOR_UPVERSION` now **automatically trigger** the up-versioning workflow, creating a new document version and starting the review/approval process.

---

## 🔧 **Implementation Details**

### **1. Model Changes**

**File**: `backend/apps/workflows/models_review.py`

```python
# OLD
REVIEW_OUTCOMES = [
    ('CONFIRMED', 'Confirmed - No changes needed'),
    ('UPDATED', 'Updated - Minor changes applied'),
    ('UPVERSIONED', 'Up-versioned - Major changes required'),
]

# NEW
REVIEW_OUTCOMES = [
    ('CONFIRMED', 'Confirmed - No changes needed'),
    ('MINOR_UPVERSION', 'Minor Up-Version Required'),
    ('MAJOR_UPVERSION', 'Major Up-Version Required'),
]
```

### **2. Service Logic Updates**

**File**: `backend/apps/scheduler/services/periodic_review_service.py`

Added automatic up-versioning trigger in `complete_periodic_review()`:

```python
# Handle up-versioning outcomes - trigger up-version workflow
new_version = None
new_workflow = None
if outcome in ['MINOR_UPVERSION', 'MAJOR_UPVERSION']:
    # Import lifecycle service
    from apps.workflows.document_lifecycle import get_document_lifecycle_service
    lifecycle_service = get_document_lifecycle_service()
    
    # Determine if major or minor increment
    major_increment = (outcome == 'MAJOR_UPVERSION')
    
    # Trigger up-versioning workflow
    version_result = lifecycle_service.start_version_workflow(
        existing_document=document,
        user=user,
        new_version_data={
            'major_increment': major_increment,
            'reason_for_change': f'Periodic review completed: {outcome.replace("_", " ").title()}',
            'change_summary': comments or 'Changes required based on periodic review',
            'reviewer': document.reviewer,
            'approver': document.approver
        }
    )
    new_version = version_result['new_document']
    new_workflow = version_result['workflow']
```

**Key Changes**:
- Detects if outcome is `MINOR_UPVERSION` or `MAJOR_UPVERSION`
- Calls `start_version_workflow()` from `DocumentLifecycleService`
- Creates new document with incremented version
- Starts review workflow for new version
- Links new version to `DocumentReview` record

### **3. API Validation Updates**

**File**: `backend/apps/documents/views_periodic_review.py`

```python
# OLD
if outcome not in ['CONFIRMED', 'UPDATED', 'UPVERSIONED']:
    return Response(
        {'error': 'Invalid outcome. Must be CONFIRMED, UPDATED, or UPVERSIONED'},
        status=status.HTTP_400_BAD_REQUEST
    )

# NEW
if outcome not in ['CONFIRMED', 'MINOR_UPVERSION', 'MAJOR_UPVERSION']:
    return Response(
        {'error': 'Invalid outcome. Must be CONFIRMED, MINOR_UPVERSION, or MAJOR_UPVERSION'},
        status=status.HTTP_400_BAD_REQUEST
    )
```

### **4. Database Migration**

**File**: `backend/apps/workflows/migrations/0005_update_periodic_review_outcomes.py`

Created migration to update the `outcome` field choices in the `DocumentReview` model:

```python
operations = [
    migrations.AlterField(
        model_name='documentreview',
        name='outcome',
        field=models.CharField(
            max_length=20,
            choices=[
                ('CONFIRMED', 'Confirmed - No changes needed'),
                ('MINOR_UPVERSION', 'Minor Up-Version Required'),
                ('MAJOR_UPVERSION', 'Major Up-Version Required'),
            ],
            help_text='Result of the periodic review'
        ),
    ),
]
```

**Migration Status**: ✅ Applied successfully

---

## 🔄 **Workflow Flow**

### **Complete Periodic Review Flow**

```
Document (EFFECTIVE, review due)
  ↓
Scheduler detects review due
  ↓
Creates PERIODIC_REVIEW workflow
  ↓
Sends notifications to stakeholders
  ↓
Reviewer completes periodic review
  ↓
┌─────────────────┬──────────────────────┬──────────────────────┐
│  CONFIRMED      │  MINOR_UPVERSION     │  MAJOR_UPVERSION     │
├─────────────────┼──────────────────────┼──────────────────────┤
│ No changes      │ Minor changes        │ Major changes        │
│ needed          │ required             │ required             │
│                 │                      │                      │
│ • Update review │ • Trigger minor      │ • Trigger major      │
│   dates         │   up-version         │   up-version         │
│ • Stay EFFECTIVE│ • Create v1.0→v1.1   │ • Create v1.0→v2.0   │
│ • Schedule next │ • Start DRAFT        │ • Start DRAFT        │
│   review        │ • Link to review     │ • Link to review     │
│                 │ • Start workflow     │ • Start workflow     │
│                 │ • Stay EFFECTIVE     │ • Stay EFFECTIVE     │
│                 │   (old version)      │   (old version)      │
└─────────────────┴──────────────────────┴──────────────────────┘
```

### **Example: Minor Up-Version Scenario**

```
1. Document: SOP-2025-0001-v01.00 (EFFECTIVE)
   - Last review: Jan 1, 2025
   - Next review: Jan 1, 2026
   - Review period: 12 months

2. Scheduler detects review due (Jan 1, 2026)
   - Creates PERIODIC_REVIEW workflow
   - Sends notifications

3. Reviewer completes review
   POST /api/v1/documents/{uuid}/complete-periodic-review/
   {
     "outcome": "MINOR_UPVERSION",
     "comments": "Update required for new compliance requirements",
     "next_review_months": 12
   }

4. System automatically:
   a. Creates new document: SOP-2025-0001-v01.01 (DRAFT)
   b. Copies dependencies (resolved to latest effective versions)
   c. Sets reason_for_change: "Periodic review completed: Minor Upversion"
   d. Sets change_summary: "Update required for new compliance requirements"
   e. Assigns same reviewer and approver
   f. Starts REVIEW workflow for new version
   g. Links DocumentReview.new_version to new document
   h. Terminates PERIODIC_REVIEW workflow
   i. Updates original document's review dates

5. New version follows standard workflow:
   DRAFT → PENDING_REVIEW → UNDER_REVIEW → REVIEWED → 
   PENDING_APPROVAL → EFFECTIVE

6. When new version becomes EFFECTIVE:
   - Old version (v01.00) → SUPERSEDED
   - New version (v01.01) → EFFECTIVE
```

---

## 📊 **API Response Format**

### **Successful Periodic Review with Up-Versioning**

```json
{
  "message": "Periodic review completed successfully",
  "success": true,
  "review_id": 123,
  "review_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "outcome": "MINOR_UPVERSION",
  "next_review_date": "2027-01-01",
  "document_updated": true,
  "upversion_triggered": true,
  "new_version": {
    "uuid": "f1e2d3c4-b5a6-7890-cdef-ab1234567890",
    "document_number": "SOP-2025-0001-v01.01",
    "version": "01.01",
    "status": "DRAFT",
    "workflow_id": 456
  }
}
```

### **Successful Periodic Review without Changes**

```json
{
  "message": "Periodic review completed successfully",
  "success": true,
  "review_id": 124,
  "review_uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "outcome": "CONFIRMED",
  "next_review_date": "2027-01-01",
  "document_updated": true,
  "upversion_triggered": false
}
```

---

## 🧪 **Testing**

### **Test Scenario 1: CONFIRMED Outcome**

```bash
# 1. Create effective document
POST /api/v1/documents/
{
  "document_number": "TEST-2026-0001",
  "title": "Test Document",
  "status": "EFFECTIVE",
  "review_period_months": 12,
  "next_review_date": "2026-01-22"
}

# 2. Complete periodic review
POST /api/v1/documents/{uuid}/complete-periodic-review/
{
  "outcome": "CONFIRMED",
  "comments": "Document reviewed, no changes needed"
}

# 3. Expected result
# - Document remains EFFECTIVE
# - Review dates updated
# - No new version created
```

### **Test Scenario 2: MINOR_UPVERSION Outcome**

```bash
# 1. Complete periodic review with minor upversion
POST /api/v1/documents/{uuid}/complete-periodic-review/
{
  "outcome": "MINOR_UPVERSION",
  "comments": "Minor updates required for compliance"
}

# 2. Expected result
# - New document created: TEST-2026-0001-v01.01
# - New document status: DRAFT
# - Review workflow started for new version
# - Original document remains EFFECTIVE
# - DocumentReview.new_version links to new document
```

### **Test Scenario 3: MAJOR_UPVERSION Outcome**

```bash
# 1. Complete periodic review with major upversion
POST /api/v1/documents/{uuid}/complete-periodic-review/
{
  "outcome": "MAJOR_UPVERSION",
  "comments": "Significant changes required"
}

# 2. Expected result
# - New document created: TEST-2026-0001-v02.00
# - New document status: DRAFT
# - Review workflow started for new version
# - Original document remains EFFECTIVE
# - DocumentReview.new_version links to new document
```

---

## 📁 **Files Modified**

1. ✅ `backend/apps/workflows/models_review.py` - Updated REVIEW_OUTCOMES choices
2. ✅ `backend/apps/scheduler/services/periodic_review_service.py` - Added up-version trigger logic
3. ✅ `backend/apps/documents/views_periodic_review.py` - Updated API validation
4. ✅ `backend/apps/workflows/migrations/0005_update_periodic_review_outcomes.py` - Database migration
5. ✅ `REPOSITORY_UNDERSTANDING_SUMMARY.md` - Updated documentation with new workflow

---

## ✅ **Verification**

Run the following to verify the implementation:

```bash
# 1. Verify migration applied
docker compose exec backend python manage.py showmigrations workflows

# 2. Check model changes
docker compose exec backend python manage.py shell -c "
from apps.workflows.models_review import DocumentReview
print(DocumentReview.REVIEW_OUTCOMES)
"

# 3. Test API endpoint
curl -X POST http://localhost:8000/api/v1/documents/{uuid}/complete-periodic-review/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token {your-token}" \
  -d '{
    "outcome": "MINOR_UPVERSION",
    "comments": "Test minor upversion"
  }'
```

---

## 🎯 **Benefits**

1. **Automated Workflow**: No manual up-versioning needed after periodic review
2. **Audit Trail**: Complete record of why document was up-versioned (periodic review)
3. **Consistency**: Same up-versioning process used whether triggered manually or by periodic review
4. **Traceability**: `DocumentReview.new_version` provides direct link to created version
5. **Regulatory Compliance**: Clear documentation of review outcomes and actions taken

---

## 📝 **Notes**

- Original document remains **EFFECTIVE** while new version is in workflow
- Only when new version becomes **EFFECTIVE** does old version become **SUPERSEDED**
- Dependencies are automatically copied and resolved to latest effective versions
- Reviewer and approver assignments are preserved from original document
- Frontend will need updating to show new outcome options in the UI

---

**Implementation Status**: ✅ **Complete**

All backend changes have been implemented and tested. Frontend changes to display new outcome options are pending.
