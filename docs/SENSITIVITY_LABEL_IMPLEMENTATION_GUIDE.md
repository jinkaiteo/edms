# Sensitivity Label Implementation Guide

## Complete Implementation - Placeholders, Watermarks, and Workflow Integration

This guide walks you through the complete implementation of the 5-tier sensitivity label system with placeholders and watermarks.

---

## ✅ What Has Been Implemented

### 1. **Sensitivity Label System** (5-Tier)
- ✅ `backend/apps/documents/sensitivity_labels.py` - Complete configuration
- ✅ 5 levels: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, PROPRIETARY
- ✅ Metadata, icons, descriptions, handling requirements

### 2. **Database Schema**
- ✅ `backend/apps/documents/migrations/0002_add_sensitivity_labels.py`
- ✅ Fields: `sensitivity_label`, `sensitivity_set_by`, `sensitivity_set_at`
- ✅ Fields: `sensitivity_inherited_from`, `sensitivity_change_reason`
- ✅ Indexes for performance

### 3. **Placeholder System**
- ✅ `backend/apps/documents/annotation_processor.py` - Updated with 12 new placeholders
- ✅ Basic: `{{SENSITIVITY_LABEL}}`, `{{SENSITIVITY_LABEL_FULL}}`, `{{SENSITIVITY_LABEL_ICON}}`
- ✅ Conditional: `{{IF_CONFIDENTIAL}}`, `{{IF_RESTRICTED}}`, `{{IF_PROPRIETARY}}`, etc.
- ✅ Metadata: `{{SENSITIVITY_SET_BY}}`, `{{SENSITIVITY_SET_DATE}}`, `{{SENSITIVITY_CHANGE_REASON}}`

### 4. **Watermark System (Dual-Layer)**
- ✅ `backend/apps/documents/watermark_processor.py` - Complete watermark engine
- ✅ Layer 1: Sensitivity header bar (top of page)
- ✅ Layer 2: Status diagonal watermark (center)
- ✅ `backend/apps/documents/services/pdf_generator.py` - Integration

### 5. **Documentation**
- ✅ `docs/SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md` - 500+ line user guide
- ✅ `docs/SENSITIVITY_WATERMARK_MOCKUPS.md` - Visual mockups
- ✅ `docs/SENSITIVITY_PLACEHOLDER_REFERENCE.md` - Placeholder reference

### 6. **Workflow Integration Patches**
- ✅ `backend/apps/workflows/lifecycle_sensitivity_patch.py` - Approval & versioning changes
- ✅ `backend/apps/documents/models_sensitivity_patch.py` - Model field additions

---

## 📋 Implementation Steps

### **Phase 1: Database Setup (15 minutes)**

#### Step 1.1: Apply Model Changes

Add sensitivity fields to `backend/apps/documents/models.py` at **line 237** (after `document_source`):

```python
# Add these imports at top of file
from .sensitivity_labels import SENSITIVITY_CHOICES

# Add these fields to Document model (after line 237)
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

#### Step 1.2: Run Migration

```bash
cd backend
python manage.py makemigrations documents
python manage.py migrate documents

# Verify migration
python manage.py dbshell
\d documents_document;  # Check for sensitivity_* columns
\q
```

#### Step 1.3: Set Default Sensitivity for Existing Documents

```bash
python manage.py shell

from apps.documents.models import Document
from django.utils import timezone

# Set all existing documents to INTERNAL (safe default)
Document.objects.filter(sensitivity_label__isnull=True).update(
    sensitivity_label='INTERNAL',
    sensitivity_set_at=timezone.now()
)

print(f"Updated {Document.objects.filter(sensitivity_label='INTERNAL').count()} documents to INTERNAL")
exit()
```

---

### **Phase 2: Workflow Integration (30 minutes)**

#### Step 2.1: Update `approve_document` Method

In `backend/apps/workflows/document_lifecycle.py`, update the `approve_document` method (around **line 349**):

**Find this signature:**
```python
def approve_document(self, document: Document, user: User, 
                    effective_date: date, comment: str = '', approved: bool = True,
                    review_period_months: int = None) -> bool:
```

**Replace with** (use `lifecycle_sensitivity_patch.py` as complete reference):
```python
def approve_document(self, document: Document, user: User, 
                    effective_date: date, comment: str = '', approved: bool = True,
                    review_period_months: int = None,
                    sensitivity_label: str = None,  # NEW
                    sensitivity_change_reason: str = '') -> bool:  # NEW
    """
    Approve document with required effective date and sensitivity label.
    """
    # ... existing validation code ...
    
    # === NEW: SENSITIVITY LABEL VALIDATION ===
    if not sensitivity_label:
        raise ValidationError("Sensitivity label is required for document approval")
    
    from apps.documents.sensitivity_labels import SENSITIVITY_CHOICES
    valid_labels = [choice[0] for choice in SENSITIVITY_CHOICES]
    if sensitivity_label not in valid_labels:
        raise ValidationError(f"Invalid sensitivity label: {sensitivity_label}")
    
    # Detect if sensitivity changed
    sensitivity_changed = (document.sensitivity_label != sensitivity_label)
    
    if sensitivity_changed and not sensitivity_change_reason:
        raise ValidationError(
            "A detailed reason is required when changing sensitivity classification"
        )
    
    # Set sensitivity label
    old_sensitivity = document.sensitivity_label
    document.sensitivity_label = sensitivity_label
    document.sensitivity_set_by = user
    document.sensitivity_set_at = timezone.now()
    
    if sensitivity_changed:
        document.sensitivity_change_reason = sensitivity_change_reason
    
    document.save()
    
    # Log in audit trail
    from apps.audit.models import AuditTrail
    if sensitivity_changed:
        AuditTrail.objects.create(
            document=document,
            action='SENSITIVITY_CHANGED',
            user=user,
            details={
                'old_sensitivity': old_sensitivity,
                'new_sensitivity': sensitivity_label,
                'reason': sensitivity_change_reason,
                'changed_during': 'approval'
            }
        )
    else:
        AuditTrail.objects.create(
            document=document,
            action='SENSITIVITY_CONFIRMED',
            user=user,
            details={
                'sensitivity': sensitivity_label,
                'inherited_from': document.sensitivity_inherited_from.document_number if document.sensitivity_inherited_from else None
            }
        )
    
    # ... rest of existing approval code ...
```

#### Step 2.2: Update `start_version_workflow` Method

In same file, update `start_version_workflow` method (around **line 653**):

```python
def start_version_workflow(self, existing_document: Document, user: User,
                          new_version_data: Dict[str, Any]) -> Dict[str, Any]:
    """Start up-versioning workflow with sensitivity inheritance."""
    
    # ... existing version creation code ...
    
    new_document = Document.objects.create(
        # ... other fields ...
        
        # === INHERIT SENSITIVITY FROM PARENT ===
        sensitivity_label=existing_document.sensitivity_label,
        sensitivity_inherited_from=existing_document,
        sensitivity_set_by=None,  # Will be set by approver
        sensitivity_set_at=None,
        sensitivity_change_reason='',
        # === END SENSITIVITY INHERITANCE ===
        
        status='DRAFT'
    )
    
    # Log inheritance
    from apps.audit.models import AuditTrail
    AuditTrail.objects.create(
        document=new_document,
        action='VERSION_CREATED',
        user=user,
        details={
            'parent_version': f"{existing_document.document_number}",
            'inherited_sensitivity': existing_document.sensitivity_label,
            'message': f"New version inherits {existing_document.get_sensitivity_label_display()} classification"
        }
    )
    
    # ... rest of existing code ...
```

#### Step 2.3: Update API Views

In `backend/apps/workflows/views.py` or `api_views.py`, update the approve endpoint:

```python
@action(detail=True, methods=['post'])
def approve(self, request, uuid=None):
    """Approve document with sensitivity label."""
    document = self.get_object()
    
    # Extract parameters
    effective_date_str = request.data.get('effective_date')
    comment = request.data.get('comment', '')
    approved = request.data.get('approved', True)
    review_period_months = request.data.get('review_period_months')
    sensitivity_label = request.data.get('sensitivity_label')  # NEW
    sensitivity_change_reason = request.data.get('sensitivity_change_reason', '')  # NEW
    
    # Validate sensitivity label
    if approved and not sensitivity_label:
        return Response(
            {'error': 'Sensitivity label is required for approval'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Call lifecycle service
    success = lifecycle_service.approve_document(
        document=document,
        user=request.user,
        effective_date=effective_date,
        comment=comment,
        approved=approved,
        review_period_months=review_period_months,
        sensitivity_label=sensitivity_label,  # NEW
        sensitivity_change_reason=sensitivity_change_reason  # NEW
    )
    
    # ... rest of existing code ...
```

#### Step 2.4: Update Serializers

In `backend/apps/documents/serializers.py`, add sensitivity fields:

```python
class DocumentListSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    # Add after line 246
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
    
    class Meta:
        model = Document
        fields = [
            # ... existing fields ...
            'sensitivity_label',
            'sensitivity_label_display',
            'sensitivity_set_by_display',
        ]

class DocumentDetailSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    # Add sensitivity fields
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
    sensitivity_set_at = serializers.DateTimeField(read_only=True)
    sensitivity_change_reason = serializers.CharField(read_only=True)
    sensitivity_inherited_from_number = serializers.CharField(
        source='sensitivity_inherited_from.document_number',
        read_only=True,
        allow_null=True
    )
```

---

### **Phase 3: Frontend Integration (30 minutes)**

#### Step 3.1: Update ApproverInterface.tsx

In `frontend/src/components/workflows/ApproverInterface.tsx`:

```tsx
import SensitivityLabelSelector from './SensitivityLabelSelector';

interface ApproveFormData {
  effectiveDate: string;
  comment: string;
  reviewPeriod: string;
  sensitivityLabel: string;  // NEW
  sensitivityChangeReason: string;  // NEW
}

const ApproverInterface: React.FC<Props> = ({ document, onComplete }) => {
  const [formData, setFormData] = useState<ApproveFormData>({
    effectiveDate: tomorrow,
    comment: '',
    reviewPeriod: 'none',
    sensitivityLabel: document.sensitivity_label || 'INTERNAL',  // NEW
    sensitivityChangeReason: ''  // NEW
  });
  
  const handleSensitivityChange = (label: string, reason: string) => {
    setFormData({
      ...formData,
      sensitivityLabel: label,
      sensitivityChangeReason: reason
    });
  };
  
  return (
    <div className="space-y-4">
      {/* Existing effective date field */}
      
      {/* NEW: Sensitivity Label Selector */}
      <SensitivityLabelSelector
        value={formData.sensitivityLabel}
        onChange={handleSensitivityChange}
        inheritedFrom={document.sensitivity_inherited_from_number}
        originalValue={document.sensitivity_label}
        required={true}
      />
      
      {/* Existing comment and review period fields */}
      
      <button onClick={handleApprove}>
        Approve Document
      </button>
    </div>
  );
};
```

#### Step 3.2: Add Sensitivity Badge to Document List

In `frontend/src/components/documents/DocumentList.tsx`:

```tsx
import SensitivityBadge from '../common/SensitivityBadge';

// Add column to table
<td className="px-4 py-3">
  <SensitivityBadge label={document.sensitivity_label} size="sm" />
</td>
```

#### Step 3.3: Add Sensitivity Display to Document Viewer

In `frontend/src/components/documents/DocumentViewer.tsx`:

```tsx
import SensitivityBadge from '../common/SensitivityBadge';

// Add to header
<div className="flex items-center justify-between border-b pb-4 mb-4">
  <div>
    <h1 className="text-2xl font-bold">{document.title}</h1>
    <p className="text-gray-600">{document.document_number}</p>
  </div>
  
  <div className="flex items-center gap-3">
    <SensitivityBadge label={document.sensitivity_label} size="lg" />
    <span className="text-sm text-gray-500">
      Status: {document.status_display}
    </span>
  </div>
</div>

{/* Show classification metadata */}
{document.sensitivity_set_by_display && (
  <div className="bg-gray-50 rounded-md p-3 text-sm mb-4">
    <p className="text-gray-600">
      Classified as <strong>{document.sensitivity_label_display}</strong> by{' '}
      <strong>{document.sensitivity_set_by_display}</strong> on{' '}
      {new Date(document.sensitivity_set_at).toLocaleDateString()}
    </p>
  </div>
)}
```

---

### **Phase 4: Testing (30 minutes)**

#### Test Plan

**Test 1: Create and Approve New Document**
```bash
1. Create new document (DRAFT, inherits INTERNAL by default)
2. Submit for review
3. Review → Route for approval
4. During approval:
   - See pre-selected INTERNAL label
   - Change to CONFIDENTIAL
   - Provide reason: "Contains customer pricing information"
5. Approve document
6. Verify: Document shows CONFIDENTIAL badge
7. Download PDF → Verify orange "CONFIDENTIAL" header bar
```

**Test 2: Up-Version with Sensitivity Inheritance**
```bash
1. Take CONFIDENTIAL document v1.0
2. Create new version v2.0
3. During approval:
   - See "Inherited: CONFIDENTIAL from v1.0" message
   - Keep as CONFIDENTIAL (no reason needed)
4. Approve
5. Verify: v2.0 is CONFIDENTIAL
6. Download PDF → Verify both versions have orange header
```

**Test 3: Change Sensitivity During Up-Version**
```bash
1. Take INTERNAL document v1.0
2. Create new version v2.0
3. During approval:
   - See "Inherited: INTERNAL from v1.0"
   - Change to PROPRIETARY
   - Provide reason: "Added trade secret formula"
4. Approve
5. Verify: v2.0 is PROPRIETARY, v1.0 still INTERNAL
6. Download v2.0 PDF → Verify red "PROPRIETARY" header
```

**Test 4: Watermarks on DRAFT Documents**
```bash
1. Create CONFIDENTIAL document
2. While still DRAFT:
   - Download PDF
   - Verify: Orange "CONFIDENTIAL" header + Red "DRAFT" diagonal
3. Approve document
4. Download again:
   - Verify: Orange header remains, DRAFT diagonal removed
```

**Test 5: Placeholders in Templates**
```bash
1. Create document template with:
   {{SENSITIVITY_LABEL_FULL}}
   {{IF_CONFIDENTIAL}}
   {{SENSITIVITY_SET_BY}}
2. Upload template
3. Approve as CONFIDENTIAL
4. Download processed DOCX
5. Verify placeholders replaced correctly
```

---

### **Phase 5: User Training (1 day)**

#### Step 5.1: Share Classification Guide

Distribute `docs/SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md` to all approvers.

Key training points:
- Default is INTERNAL (70% of documents)
- CONFIDENTIAL for business-sensitive (25% of documents)
- RESTRICTED for regulatory/compliance (3% of documents)
- PROPRIETARY for trade secrets (1% of documents)
- When to upgrade/downgrade sensitivity

#### Step 5.2: Conduct Training Session

**30-minute session covering:**
1. Why sensitivity labels matter (5 min)
2. The 5 tiers explained with examples (10 min)
3. How to classify during approval (5 min)
4. What happens with up-versioning (5 min)
5. Q&A (5 min)

#### Step 5.3: Create Quick Reference Card

```
┌─────────────────────────────────────────┐
│ SENSITIVITY LABEL QUICK REFERENCE       │
├─────────────────────────────────────────┤
│ 🏢 INTERNAL (Default)                   │
│    SOPs, policies, procedures           │
│                                         │
│ 🔒 CONFIDENTIAL                         │
│    Contracts, audits, validation        │
│                                         │
│ ⚠️ RESTRICTED                           │
│    FDA submissions, regulatory docs     │
│                                         │
│ 🛡️ PROPRIETARY                          │
│    Trade secrets, formulations          │
│                                         │
│ When unsure → Choose INTERNAL           │
└─────────────────────────────────────────┘
```

---

## 🔍 Verification Checklist

After implementation, verify:

### Database
- [ ] Migration applied successfully
- [ ] All documents have sensitivity_label set
- [ ] Indexes created on sensitivity fields

### Backend
- [ ] Placeholders work in annotation_processor
- [ ] Watermarks render in PDF generator
- [ ] Approval requires sensitivity_label parameter
- [ ] Up-versioning inherits sensitivity
- [ ] API returns sensitivity fields

### Frontend
- [ ] SensitivityBadge shows in document list
- [ ] SensitivityLabelSelector works in approval UI
- [ ] Change reason field appears when label changes
- [ ] Inheritance message shows in selector

### PDF Generation
- [ ] DRAFT documents show red diagonal watermark
- [ ] CONFIDENTIAL documents show orange header bar
- [ ] RESTRICTED documents show purple header bar
- [ ] PROPRIETARY documents show red header bar
- [ ] EFFECTIVE documents have no diagonal (clean)
- [ ] Watermarks appear on ALL pages

### Placeholders
- [ ] `{{SENSITIVITY_LABEL}}` replaced correctly
- [ ] `{{IF_CONFIDENTIAL}}` works conditionally
- [ ] `{{SENSITIVITY_SET_BY}}` shows approver name
- [ ] All 12 placeholders functional

---

## 🚨 Troubleshooting

### Issue: Migration Fails

**Error:** `django.db.utils.ProgrammingError: column "sensitivity_label" already exists`

**Solution:**
```bash
python manage.py migrate documents --fake 0002
python manage.py migrate documents
```

### Issue: Watermarks Not Showing

**Error:** PDF downloads but no watermarks visible

**Solution:**
1. Check `settings.py`: `OFFICIAL_PDF_CONFIG['PDF_WATERMARK'] = True`
2. Verify ReportLab installed: `pip install reportlab PyPDF2`
3. Check logs: `docker-compose logs backend | grep -i watermark`
4. Test watermark processor directly:
```python
from apps.documents.watermark_processor import watermark_processor
info = watermark_processor.get_watermark_status('CONFIDENTIAL', 'DRAFT')
print(info)  # Should show requires_watermark=True
```

### Issue: Placeholders Not Replaced

**Error:** Document shows `{{SENSITIVITY_LABEL}}` instead of value

**Solution:**
1. Verify annotation_processor updated
2. Check document has sensitivity_label set
3. Test metadata generation:
```python
from apps.documents.annotation_processor import annotation_processor
from apps.documents.models import Document

doc = Document.objects.first()
metadata = annotation_processor.get_document_metadata(doc)
print(metadata['SENSITIVITY_LABEL'])  # Should print label
```

### Issue: Frontend Not Showing Sensitivity

**Error:** Document list shows no sensitivity badges

**Solution:**
1. Check API response includes `sensitivity_label`
2. Verify serializer has sensitivity fields
3. Check frontend component imports `SensitivityBadge`
4. Clear browser cache and rebuild frontend

---

## 📊 Expected Results

After full implementation:

### Document Distribution
- 70% INTERNAL (SOPs, procedures)
- 25% CONFIDENTIAL (contracts, audits)
- 3% RESTRICTED (FDA submissions)
- 1% PROPRIETARY (trade secrets)
- <1% PUBLIC (certificates)

### User Experience
- Approvers spend 30 seconds selecting classification
- 95% of up-versions keep same sensitivity (quick)
- 5% change sensitivity (with documented reason)
- Clear visual indicators in UI and PDFs

### Compliance Benefits
- Complete audit trail of classifications
- Clear handling requirements per document
- Automated watermarking prevents misuse
- Consistent classification across organization

---

## 📚 Related Documentation

- **Classification Guide**: `docs/SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md`
- **Placeholder Reference**: `docs/SENSITIVITY_PLACEHOLDER_REFERENCE.md`
- **Watermark Mockups**: `docs/SENSITIVITY_WATERMARK_MOCKUPS.md`
- **Patch Files**: 
  - `backend/apps/workflows/lifecycle_sensitivity_patch.py`
  - `backend/apps/documents/models_sensitivity_patch.py`

---

## ✅ Implementation Complete!

Once all phases are complete:
1. All documents have sensitivity labels
2. Approvers select sensitivity during approval
3. Up-versioning inherits sensitivity automatically
4. PDFs show appropriate watermarks
5. Placeholders work in templates
6. Full audit trail maintained

**Estimated Total Time:** 2-3 hours implementation + 1 day training

---

**Questions?** Contact the EDMS development team or refer to the comprehensive documentation provided.
