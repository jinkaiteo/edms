# Sensitivity Label System - Implementation Checklist

## 📋 Pre-Implementation Checklist

### Environment Verification
- [ ] Database backup completed
- [ ] Git branch created: `feature/sensitivity-labels`
- [ ] Development environment running
- [ ] Docker containers healthy
- [ ] Requirements installed: `reportlab`, `PyPDF2`, `pytz`

```bash
# Verify requirements
cd backend
pip list | grep -E "reportlab|PyPDF2|pytz"

# If missing, install
pip install reportlab PyPDF2 pytz
```

---

## 🔧 Phase 1: Database Setup (15 minutes)

### Step 1.1: Add Model Fields
- [ ] Open `backend/apps/documents/models.py`
- [ ] Find line 237 (after `document_source` field)
- [ ] Add sensitivity fields from `models_sensitivity_patch.py`

**Add these imports at top:**
```python
from .sensitivity_labels import SENSITIVITY_CHOICES
```

**Add these fields after line 237:**
```python
# Sensitivity Label System (5-tier classification)
sensitivity_label = models.CharField(
    max_length=20,
    choices=SENSITIVITY_CHOICES,
    default='INTERNAL',
    db_index=True,
    help_text='Sensitivity classification (set by approver)'
)

sensitivity_set_by = models.ForeignKey(
    User,
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='sensitivity_labeled_documents',
    help_text='User who set the sensitivity label (typically approver)'
)

sensitivity_set_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text='When sensitivity label was set'
)

sensitivity_inherited_from = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='sensitivity_inherited_by',
    help_text='Parent document this sensitivity was inherited from'
)

sensitivity_change_reason = models.TextField(
    blank=True,
    help_text='Reason for sensitivity label change (required if changed from parent)'
)
```

### Step 1.2: Run Migration
- [ ] Create migration
- [ ] Apply migration
- [ ] Verify database schema

```bash
cd backend
python manage.py makemigrations documents
python manage.py migrate documents

# Verify
python manage.py dbshell
\d documents_document;  # Check for sensitivity_* columns
\q
```

### Step 1.3: Set Default Sensitivity for Existing Documents
- [ ] Run initialization script

```bash
python manage.py shell << EOF
from apps.documents.models import Document
from django.utils import timezone

# Set all existing documents to INTERNAL (safe default)
updated = Document.objects.filter(sensitivity_label__isnull=True).update(
    sensitivity_label='INTERNAL',
    sensitivity_set_at=timezone.now()
)

print(f"✅ Updated {updated} documents to INTERNAL")

# Verify
total = Document.objects.count()
with_sensitivity = Document.objects.exclude(sensitivity_label__isnull=True).count()
print(f"✅ {with_sensitivity}/{total} documents have sensitivity labels")
EOF
```

**Expected Output:**
```
✅ Updated X documents to INTERNAL
✅ X/X documents have sensitivity labels
```

---

## 🔄 Phase 2: Workflow Integration (30 minutes)

### Step 2.1: Update approve_document Method
- [ ] Open `backend/apps/workflows/document_lifecycle.py`
- [ ] Find `approve_document` method (around line 349)
- [ ] Add sensitivity parameters to method signature
- [ ] Add sensitivity validation logic
- [ ] Add audit trail logging

**Reference:** Use `backend/apps/workflows/lifecycle_sensitivity_patch.py`

**Key changes:**
1. Add parameters: `sensitivity_label: str = None`, `sensitivity_change_reason: str = ''`
2. Add validation before approval
3. Set sensitivity fields on document
4. Create audit trail entries

### Step 2.2: Update start_version_workflow Method
- [ ] Find `start_version_workflow` method (around line 653)
- [ ] Add sensitivity inheritance logic
- [ ] Add audit trail for inheritance

**Key changes:**
1. Copy `sensitivity_label` from parent
2. Set `sensitivity_inherited_from` to parent document
3. Clear `sensitivity_set_by` and `sensitivity_set_at` (will be set by approver)
4. Log inheritance in audit trail

### Step 2.3: Update API Views
- [ ] Open `backend/apps/workflows/views.py` or `api_views.py`
- [ ] Find approve endpoint (usually `@action(detail=True, methods=['post'])`)
- [ ] Add sensitivity parameters to request handling
- [ ] Pass to lifecycle service

```python
sensitivity_label = request.data.get('sensitivity_label')
sensitivity_change_reason = request.data.get('sensitivity_change_reason', '')

# Validate
if approved and not sensitivity_label:
    return Response(
        {'error': 'Sensitivity label is required for approval'},
        status=status.HTTP_400_BAD_REQUEST
    )

# Call service
success = lifecycle_service.approve_document(
    # ... existing parameters ...
    sensitivity_label=sensitivity_label,
    sensitivity_change_reason=sensitivity_change_reason
)
```

### Step 2.4: Update Serializers
- [ ] Open `backend/apps/documents/serializers.py`
- [ ] Add sensitivity fields to `DocumentListSerializer`
- [ ] Add sensitivity fields to `DocumentDetailSerializer`

**Add to both serializers:**
```python
sensitivity_label = serializers.CharField(read_only=True)
sensitivity_label_display = serializers.CharField(
    source='get_sensitivity_label_display',
    read_only=True
)
sensitivity_set_by_display = serializers.CharField(
    source='sensitivity_set_by.get_full_name',
    read_only=True,
    allow_null=True
)
```

**Add to DetailSerializer only:**
```python
sensitivity_set_at = serializers.DateTimeField(read_only=True)
sensitivity_change_reason = serializers.CharField(read_only=True)
sensitivity_inherited_from_number = serializers.CharField(
    source='sensitivity_inherited_from.document_number',
    read_only=True,
    allow_null=True
)
```

**Update Meta.fields:**
```python
class Meta:
    fields = [
        # ... existing fields ...
        'sensitivity_label',
        'sensitivity_label_display',
        'sensitivity_set_by_display',
        # ... for detail: sensitivity_set_at, etc.
    ]
```

### Step 2.5: Test Backend Changes
- [ ] Restart backend container
- [ ] Test API endpoints

```bash
# Restart
docker-compose restart backend

# Test document list endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/documents/ | jq '.results[0].sensitivity_label'

# Should return: "INTERNAL"
```

---

## 🎨 Phase 3: Frontend Integration (30 minutes)

### Step 3.1: Verify Components Exist
- [ ] Check `frontend/src/components/common/SensitivityBadge.tsx` exists
- [ ] Check `frontend/src/components/workflows/SensitivityLabelSelector.tsx` exists

### Step 3.2: Update ApproverInterface
- [ ] Open `frontend/src/components/workflows/ApproverInterface.tsx`
- [ ] Import `SensitivityLabelSelector`
- [ ] Add to form state
- [ ] Add to JSX
- [ ] Pass to API call

```tsx
import SensitivityLabelSelector from './SensitivityLabelSelector';

// Add to state
const [formData, setFormData] = useState({
  // ... existing fields ...
  sensitivityLabel: document.sensitivity_label || 'INTERNAL',
  sensitivityChangeReason: ''
});

// Add handler
const handleSensitivityChange = (label: string, reason: string) => {
  setFormData({
    ...formData,
    sensitivityLabel: label,
    sensitivityChangeReason: reason
  });
};

// Add to JSX (after effective date field)
<SensitivityLabelSelector
  value={formData.sensitivityLabel}
  onChange={handleSensitivityChange}
  inheritedFrom={document.sensitivity_inherited_from_number}
  originalValue={document.sensitivity_label}
  required={true}
/>

// Update API call
const response = await workflowService.approveDocument(
  document.uuid,
  {
    // ... existing fields ...
    sensitivity_label: formData.sensitivityLabel,
    sensitivity_change_reason: formData.sensitivityChangeReason
  }
);
```

### Step 3.3: Update UnifiedWorkflowInterface (if used)
- [ ] Apply same changes as ApproverInterface
- [ ] Test approval flow

### Step 3.4: Add Sensitivity Badge to Document List
- [ ] Open `frontend/src/components/documents/DocumentList.tsx`
- [ ] Import `SensitivityBadge`
- [ ] Add column to table

```tsx
import SensitivityBadge from '../common/SensitivityBadge';

// Add table column
<td className="px-4 py-3">
  <SensitivityBadge label={document.sensitivity_label} size="sm" />
</td>
```

### Step 3.5: Add Sensitivity Display to Document Viewer
- [ ] Open `frontend/src/components/documents/DocumentViewer.tsx`
- [ ] Import `SensitivityBadge`
- [ ] Add to header

```tsx
import SensitivityBadge from '../common/SensitivityBadge';

// Add to header section
<div className="flex items-center justify-between">
  <div>
    <h1>{document.title}</h1>
  </div>
  <div className="flex items-center gap-3">
    <SensitivityBadge label={document.sensitivity_label} size="lg" />
    <span>{document.status_display}</span>
  </div>
</div>

{/* Add metadata section */}
{document.sensitivity_set_by_display && (
  <div className="bg-gray-50 rounded-md p-3 text-sm mb-4">
    <p>
      Classified as <strong>{document.sensitivity_label_display}</strong> by{' '}
      <strong>{document.sensitivity_set_by_display}</strong>
    </p>
  </div>
)}
```

### Step 3.6: Rebuild Frontend
- [ ] Rebuild and test

```bash
cd frontend
npm run build

# Or restart container
docker-compose restart frontend
```

---

## 🧪 Phase 4: Testing (30 minutes)

### Test 1: Create and Approve New Document
- [ ] Create new DRAFT document
- [ ] Submit for review
- [ ] Review and route for approval
- [ ] During approval: Select CONFIDENTIAL sensitivity
- [ ] Approve document
- [ ] **Verify:** Document shows CONFIDENTIAL badge in list
- [ ] **Verify:** Document detail shows sensitivity metadata
- [ ] Download PDF
- [ ] **Verify:** PDF has orange CONFIDENTIAL header bar
- [ ] **Verify:** PDF has no diagonal (EFFECTIVE status)

### Test 2: Up-Version with Inheritance
- [ ] Take existing CONFIDENTIAL document v1.0
- [ ] Create new version v2.0
- [ ] During approval: See "Inherited: CONFIDENTIAL from v1.0"
- [ ] Keep as CONFIDENTIAL (no reason needed)
- [ ] Approve
- [ ] **Verify:** v2.0 is CONFIDENTIAL
- [ ] **Verify:** Audit trail shows "SENSITIVITY_CONFIRMED"
- [ ] Download PDF
- [ ] **Verify:** Both v1.0 and v2.0 have orange header

### Test 3: Change Sensitivity During Up-Version
- [ ] Take INTERNAL document v1.0
- [ ] Create new version v2.0
- [ ] During approval: Change to PROPRIETARY
- [ ] Provide reason: "Added trade secret formula"
- [ ] Approve
- [ ] **Verify:** v2.0 is PROPRIETARY, v1.0 still INTERNAL
- [ ] **Verify:** Audit trail shows "SENSITIVITY_CHANGED" with reason
- [ ] Download v2.0 PDF
- [ ] **Verify:** v2.0 has red PROPRIETARY header
- [ ] Download v1.0 PDF
- [ ] **Verify:** v1.0 has no header (INTERNAL)

### Test 4: Watermarks on DRAFT Documents
- [ ] Create CONFIDENTIAL document
- [ ] While DRAFT: Download PDF
- [ ] **Verify:** Orange CONFIDENTIAL header + Red DRAFT diagonal
- [ ] Approve document (becomes EFFECTIVE)
- [ ] Download again
- [ ] **Verify:** Orange header remains, DRAFT diagonal removed

### Test 5: All Status Watermarks
- [ ] Test PENDING_REVIEW status → Orange "PENDING REVIEW"
- [ ] Test UNDER_REVIEW status → Orange "UNDER REVIEW"
- [ ] Test REVIEW_COMPLETED status → Green "REVIEW COMPLETED"
- [ ] Test PENDING_APPROVAL status → Blue "PENDING APPROVAL"
- [ ] Test OBSOLETE status → Gray "OBSOLETE\nDO NOT USE"

### Test 6: Placeholders in Templates
- [ ] Create document template with:
  - `{{SENSITIVITY_LABEL}}`
  - `{{SENSITIVITY_LABEL_FULL}}`
  - `{{IF_CONFIDENTIAL}}`
  - `{{SENSITIVITY_SET_BY}}`
- [ ] Upload as document template
- [ ] Create document from template
- [ ] Approve as CONFIDENTIAL
- [ ] Download processed DOCX
- [ ] **Verify:** All placeholders replaced correctly

### Test 7: API Endpoints
- [ ] Test document list API returns sensitivity fields
- [ ] Test document detail API returns full sensitivity metadata
- [ ] Test approval API requires sensitivity_label
- [ ] Test approval API rejects without sensitivity for approval
- [ ] Test version creation inherits sensitivity

```bash
# Test document list
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/documents/ \
  | jq '.results[0] | {sensitivity_label, sensitivity_label_display}'

# Test approval validation
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "effective_date": "2026-02-06"}' \
  http://localhost:8000/api/v1/documents/<uuid>/approve/

# Should return 400 error: "Sensitivity label is required"
```

---

## 📚 Phase 5: Documentation & Training (1 day)

### Step 5.1: Distribute Documentation
- [ ] Share `docs/SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md` with approvers
- [ ] Share quick reference card
- [ ] Create internal wiki page

### Step 5.2: Conduct Training Session
- [ ] Schedule 30-minute session for approvers
- [ ] Cover the 5 sensitivity levels
- [ ] Demonstrate approval workflow
- [ ] Show up-versioning inheritance
- [ ] Q&A session

**Training agenda:**
1. Why sensitivity labels (5 min)
2. The 5 tiers with examples (10 min)
3. How to classify during approval (5 min)
4. Up-versioning behavior (5 min)
5. Q&A (5 min)

### Step 5.3: Create User Quick Reference
- [ ] Print quick reference cards for approvers
- [ ] Post on internal wiki
- [ ] Add to onboarding materials

---

## ✅ Post-Implementation Verification

### Database Verification
- [ ] All documents have `sensitivity_label` set
- [ ] No NULL values in `sensitivity_label`
- [ ] Indexes created on sensitivity fields
- [ ] Foreign keys working correctly

```bash
python manage.py shell << EOF
from apps.documents.models import Document

total = Document.objects.count()
with_label = Document.objects.exclude(sensitivity_label__isnull=True).count()
by_label = Document.objects.values('sensitivity_label').annotate(count=models.Count('id'))

print(f"Total documents: {total}")
print(f"With sensitivity: {with_label}")
print("\nDistribution:")
for item in by_label:
    print(f"  {item['sensitivity_label']}: {item['count']}")
EOF
```

### Backend Verification
- [ ] Placeholders work in annotation processor
- [ ] Watermarks render in PDF generator
- [ ] Approval requires sensitivity_label
- [ ] Up-versioning inherits sensitivity
- [ ] API returns sensitivity fields
- [ ] Audit trail captures changes

### Frontend Verification
- [ ] Badges display in document list
- [ ] Selector works in approval UI
- [ ] Change reason field appears when needed
- [ ] Inheritance message shows correctly
- [ ] Document viewer shows sensitivity

### PDF Verification
- [ ] DRAFT shows red diagonal
- [ ] CONFIDENTIAL shows orange header
- [ ] RESTRICTED shows purple header
- [ ] PROPRIETARY shows red header
- [ ] EFFECTIVE has no diagonal (clean)
- [ ] All statuses have correct watermarks
- [ ] Watermarks on ALL pages

---

## 🚨 Rollback Plan (If Needed)

### If Issues Found During Testing

**Option 1: Rollback Migration**
```bash
cd backend
python manage.py migrate documents <previous_migration_number>
```

**Option 2: Revert Code Changes**
```bash
git checkout develop
git branch -D feature/sensitivity-labels
```

**Option 3: Disable Watermarks Temporarily**
In `settings.py`:
```python
OFFICIAL_PDF_CONFIG = {
    'PDF_WATERMARK': False,  # Disable temporarily
}
```

---

## 📊 Success Metrics

After full implementation, verify:

### Adoption Metrics
- [ ] 100% of new documents have sensitivity labels
- [ ] <5% classification errors reported
- [ ] All sensitivity changes have documented reasons
- [ ] No watermark rendering failures

### User Experience Metrics
- [ ] Average classification time <30 seconds
- [ ] 95%+ of up-versions keep same sensitivity
- [ ] Approver satisfaction >90%
- [ ] Zero access control violations

### Technical Metrics
- [ ] PDF generation time <2 seconds
- [ ] No database performance degradation
- [ ] API response times unchanged
- [ ] Zero data integrity issues

---

## 📞 Support Contacts

**Technical Issues:**
- Backend: [Development team]
- Frontend: [Development team]
- Database: [DBA team]

**User Training:**
- Document Control: [Contact]
- Quality Assurance: [Contact]

**Escalation:**
- Project Manager: [Contact]
- QA Director: [Contact]

---

## ✅ Final Sign-Off

- [ ] All phases completed
- [ ] All tests passed
- [ ] Documentation distributed
- [ ] Training completed
- [ ] Rollback plan documented
- [ ] Success metrics defined
- [ ] Support contacts listed

**Implemented by:** _________________  
**Date:** _________________  
**Approved by:** _________________  
**Date:** _________________  

---

**Total Estimated Time:** 2-3 hours implementation + 1 day training
**Status:** Ready for Implementation
