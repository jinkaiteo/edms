# EDMS Workflows - Part 2: Technical Implementation

## 🔧 Technical Architecture

### Database Models

#### **1. Document Model** (`backend/apps/documents/models.py`)

**Key Fields**:
```python
class Document(models.Model):
    # Identification
    uuid = UUIDField()
    document_number = CharField(unique=True)  # e.g., "SOP-2025-0001-v01.00"
    
    # Content
    title = CharField()
    description = TextField()
    
    # Versioning
    version_major = PositiveIntegerField()  # 1-99
    version_minor = PositiveIntegerField()  # 0-99
    
    # Classification
    document_type = ForeignKey(DocumentType)  # SOP, Policy, Form, etc.
    document_source = ForeignKey(DocumentSource)
    
    # Lifecycle Status
    status = CharField(choices=DOCUMENT_STATUS_CHOICES)
    # Choices: DRAFT, PENDING_REVIEW, UNDER_REVIEW, REVIEW_COMPLETED,
    #          PENDING_APPROVAL, APPROVED_PENDING_EFFECTIVE, EFFECTIVE,
    #          SCHEDULED_FOR_OBSOLESCENCE, SUPERSEDED, OBSOLETE, TERMINATED
    
    # People
    author = ForeignKey(User, related_name='authored_documents')
    reviewer = ForeignKey(User, related_name='reviewed_documents', null=True)
    approver = ForeignKey(User, related_name='approved_documents', null=True)
    
    # Important Dates
    created_at = DateTimeField()
    review_date = DateTimeField(null=True)
    approval_date = DateTimeField(null=True)
    effective_date = DateField(null=True)  # When document becomes active
    obsolescence_date = DateField(null=True)  # Scheduled retirement date
    
    # Change Management
    supersedes = ForeignKey('self', null=True)  # Links to previous version
    reason_for_change = TextField()
    change_summary = TextField()
    
    # File Information
    file_path = CharField()
    file_name = CharField()
    file_checksum = CharField()  # SHA-256 for integrity
```

**Status Choices**:
```python
DOCUMENT_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('PENDING_REVIEW', 'Pending Review'),
    ('UNDER_REVIEW', 'Under Review'),
    ('REVIEW_COMPLETED', 'Review Completed'),
    ('PENDING_APPROVAL', 'Pending Approval'),
    ('UNDER_APPROVAL', 'Under Approval'),
    ('APPROVED', 'Approved'),
    ('APPROVED_PENDING_EFFECTIVE', 'Approved Pending Effective'),
    ('EFFECTIVE', 'Effective'),
    ('SCHEDULED_FOR_OBSOLESCENCE', 'Scheduled for Obsolescence'),
    ('SUPERSEDED', 'Superseded'),
    ('OBSOLETE', 'Obsolete'),
    ('TERMINATED', 'Terminated'),
]
```

---

#### **2. DocumentWorkflow Model** (`backend/apps/workflows/models_simple.py`)

**Purpose**: Tracks the active workflow for each document.

```python
class DocumentWorkflow(models.Model):
    uuid = UUIDField()
    document = OneToOneField(Document, related_name='workflow')
    
    # Workflow Configuration
    workflow_type = CharField(choices=WORKFLOW_TYPES)
    # Types: REVIEW, UP_VERSION, OBSOLETE, TERMINATION
    
    # Current State
    current_state = ForeignKey(DocumentState)
    
    # People
    initiated_by = ForeignKey(User)
    current_assignee = ForeignKey(User, null=True)
    
    # Timing
    started_at = DateTimeField()
    completed_at = DateTimeField(null=True)
    due_date = DateTimeField(null=True)
    
    # Status
    is_active = BooleanField(default=True)
    is_completed = BooleanField(default=False)
    completion_reason = CharField()
```

**Relationship**: One-to-One with Document (each document has one active workflow)

---

#### **3. DocumentState Model** (`backend/apps/workflows/models_simple.py`)

**Purpose**: Defines valid workflow states.

```python
class DocumentState(models.Model):
    code = CharField(unique=True)  # DRAFT, PENDING_REVIEW, etc.
    name = CharField()
    description = TextField()
    
    # State Type
    is_initial = BooleanField()  # DRAFT is initial
    is_terminal = BooleanField()  # EFFECTIVE, OBSOLETE, TERMINATED
    
    # Ordering
    sequence_order = IntegerField()
    
    # Allowed Transitions
    allowed_transitions = ManyToManyField('self')
```

**Pre-configured States**:
- DRAFT (initial)
- PENDING_REVIEW
- UNDER_REVIEW
- REVIEW_COMPLETED
- PENDING_APPROVAL
- APPROVED
- APPROVED_PENDING_EFFECTIVE
- EFFECTIVE (terminal)
- SCHEDULED_FOR_OBSOLESCENCE
- OBSOLETE (terminal)
- SUPERSEDED (terminal)
- TERMINATED (terminal)

---

#### **4. WorkflowTransition Model** (`backend/apps/workflows/models.py`)

**Purpose**: Audit trail of all state changes.

```python
class WorkflowTransition(models.Model):
    uuid = UUIDField()
    workflow_instance = ForeignKey(WorkflowInstance)
    
    # Transition Details
    from_state = CharField()
    to_state = CharField()
    transition_name = CharField()
    
    # Actor
    transitioned_by = ForeignKey(User)
    transitioned_at = DateTimeField()
    
    # Context
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    comment = TextField()
    
    # Compliance Data
    transition_data = JSONField()  # Additional metadata
```

**Why It Matters**: 21 CFR Part 11 requires complete audit trail of all changes.

---

## 📡 API Endpoints

### Document Workflow Endpoints

#### **Submit for Review**
```http
POST /api/v1/documents/{uuid}/submit-for-review/
Content-Type: application/json

{
  "reviewer_id": 123,
  "comment": "Please review this SOP",
  "due_date": "2026-01-20"
}

Response 200:
{
  "message": "Document submitted for review",
  "document": {...},
  "workflow": {...}
}
```

#### **Complete Review**
```http
POST /api/v1/documents/{uuid}/complete-review/
Content-Type: application/json

{
  "approved": true,
  "comment": "Review passed, ready for approval",
  "reviewer_id": 123
}

Response 200:
{
  "message": "Review completed",
  "new_status": "REVIEW_COMPLETED",
  "workflow": {...}
}
```

#### **Route for Approval**
```http
POST /api/v1/documents/{uuid}/route-for-approval/
Content-Type: application/json

{
  "approver_id": 456,
  "comment": "Routing to senior approver",
  "due_date": "2026-01-25"
}

Response 200:
{
  "message": "Document routed for approval",
  "approver": {...},
  "workflow": {...}
}
```

#### **Approve Document**
```http
POST /api/v1/documents/{uuid}/approve/
Content-Type: application/json

{
  "approved": true,
  "effective_date": "2026-01-15",
  "comment": "Approved for implementation"
}

Response 200:
{
  "message": "Document approved",
  "new_status": "APPROVED_PENDING_EFFECTIVE",
  "effective_date": "2026-01-15"
}
```

#### **Reject Document**
```http
POST /api/v1/documents/{uuid}/reject/
Content-Type: application/json

{
  "comment": "Needs revision in section 3.2",
  "reason": "Incomplete procedure steps"
}

Response 200:
{
  "message": "Document rejected",
  "new_status": "DRAFT",
  "workflow": {...}
}
```

#### **Terminate Document**
```http
POST /api/v1/documents/{uuid}/terminate/
Content-Type: application/json

{
  "reason": "Business requirements changed"
}

Response 200:
{
  "message": "Document terminated",
  "new_status": "TERMINATED"
}
```

---

## 🎨 Frontend Integration

### React Components

#### **1. DocumentViewer Component**

**Location**: `frontend/src/components/documents/DocumentViewer.tsx`

**Purpose**: Main document interface with workflow action buttons.

**Dynamic Buttons Based on Status**:

```typescript
// Button visibility logic
const showButtons = {
  submitForReview: document.status === 'DRAFT' && isAuthor,
  startReview: document.status === 'PENDING_REVIEW' && isReviewer,
  completeReview: document.status === 'UNDER_REVIEW' && isReviewer,
  routeForApproval: document.status === 'REVIEW_COMPLETED' && isAdmin,
  approve: document.status === 'PENDING_APPROVAL' && isApprover,
  reject: document.status === 'PENDING_APPROVAL' && isApprover,
  terminate: ['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW'].includes(document.status) && isAuthor,
  scheduleObsolescence: document.status === 'EFFECTIVE' && isApprover,
};
```

**Workflow Actions**:
```typescript
const handleSubmitForReview = async () => {
  const response = await api.post(
    `/documents/${document.uuid}/submit-for-review/`,
    { reviewer_id: selectedReviewer, comment }
  );
  // Refresh document
};

const handleApprove = async () => {
  const response = await api.post(
    `/documents/${document.uuid}/approve/`,
    { approved: true, effective_date: selectedDate, comment }
  );
  // Update status
};
```

---

#### **2. My Tasks Dashboard**

**Location**: `frontend/src/pages/MyTasks.tsx`

**Purpose**: Shows documents requiring user action.

**Query Logic**:
```typescript
// Fetch documents where user has pending actions
const fetchMyTasks = async () => {
  const response = await api.get('/documents/', {
    params: {
      filter: 'my_tasks',  // Special filter
      // Returns documents where:
      // - User is author and status is DRAFT
      // - User is reviewer and status is PENDING_REVIEW/UNDER_REVIEW
      // - User is approver and status is PENDING_APPROVAL
    }
  });
};
```

**Task Categorization**:
```typescript
const tasks = {
  drafts: documents.filter(d => d.status === 'DRAFT' && d.author_id === user.id),
  pendingReview: documents.filter(d => d.status === 'PENDING_REVIEW' && d.reviewer_id === user.id),
  underReview: documents.filter(d => d.status === 'UNDER_REVIEW' && d.reviewer_id === user.id),
  pendingApproval: documents.filter(d => d.status === 'PENDING_APPROVAL' && d.approver_id === user.id),
};
```

---

#### **3. Document Library**

**Location**: `frontend/src/pages/DocumentLibrary.tsx`

**Purpose**: Shows approved and effective documents.

**Query Logic**:
```typescript
const fetchLibrary = async () => {
  const response = await api.get('/documents/', {
    params: {
      filter: 'library',
      // Returns documents with status:
      // - APPROVED_PENDING_EFFECTIVE
      // - EFFECTIVE
      // - SCHEDULED_FOR_OBSOLESCENCE
    }
  });
};
```

---

## 🔒 Security & Compliance

### 21 CFR Part 11 Requirements

#### **1. Audit Trail**

Every action is logged:
```python
from apps.audit.models import AuditTrail

AuditTrail.objects.create(
    user=request.user,
    action='DOCUMENT_APPROVED',
    content_object=document,
    description=f'Document {document.document_number} approved',
    field_changes={
        'old_status': 'PENDING_APPROVAL',
        'new_status': 'APPROVED_PENDING_EFFECTIVE',
        'approved_by': approver.username,
        'approval_date': timezone.now().isoformat(),
        'effective_date': effective_date.isoformat(),
    },
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
)
```

**Audit Trail Records**:
- Who performed the action
- What changed (old value → new value)
- When it happened
- Where (IP address)
- Why (comment/reason)

#### **2. Electronic Signatures**

Workflow actions serve as electronic signatures:
- User authentication required
- Action timestamp recorded
- User intent captured (approve/reject + comment)
- Non-repudiation (cannot deny the action)

#### **3. Access Control**

Role-based permissions enforced at every level:
```python
def can_approve(user, document):
    # Must be assigned approver
    if document.approver != user:
        return False
    
    # Must have approval role
    has_role = user.user_roles.filter(
        role__module='O1',
        role__permission_level__in=['approve', 'admin'],
        is_active=True
    ).exists()
    
    # Document must be in correct status
    status_ok = document.status == 'PENDING_APPROVAL'
    
    return has_role and status_ok
```

#### **4. Data Integrity**

File checksums ensure documents haven't been tampered with:
```python
def verify_file_integrity(document):
    current_checksum = calculate_sha256(document.file_path)
    stored_checksum = document.file_checksum
    
    if current_checksum != stored_checksum:
        raise IntegrityError("Document file has been modified!")
    
    return True
```

---

## 📊 Workflow States Detailed

### State Characteristics

| State | Initial | Terminal | Can Edit | Can View | Typical Duration |
|-------|---------|----------|----------|----------|------------------|
| DRAFT | ✅ | ❌ | Author | Author | Days-Weeks |
| PENDING_REVIEW | ❌ | ❌ | None | Author, Reviewer | Hours-Days |
| UNDER_REVIEW | ❌ | ❌ | None | Author, Reviewer | Days |
| REVIEW_COMPLETED | ❌ | ❌ | None | Author, Reviewer | Minutes-Hours |
| PENDING_APPROVAL | ❌ | ❌ | None | Author, Reviewer, Approver | Days |
| APPROVED_PENDING_EFFECTIVE | ❌ | ❌ | None | All | Days-Weeks |
| EFFECTIVE | ❌ | ✅ | None | All | Months-Years |
| SCHEDULED_FOR_OBSOLESCENCE | ❌ | ❌ | None | All | Days-Months |
| OBSOLETE | ❌ | ✅ | None | All (archived) | Permanent |
| SUPERSEDED | ❌ | ✅ | None | All (history) | Permanent |
| TERMINATED | ❌ | ✅ | None | Author (audit) | Permanent |

---

## 🎯 Workflow Patterns & Best Practices

### Pattern 1: Fast-Track Approval (Same-Day Effective)

```python
# When document needs to be effective immediately
approve_document(
    document=doc,
    approver=user,
    effective_date=timezone.now().date(),  # Today
    comment="Urgent - immediate implementation"
)
# Result: Status goes directly to EFFECTIVE
```

### Pattern 2: Scheduled Effectiveness

```python
# When document should be effective in the future
approve_document(
    document=doc,
    approver=user,
    effective_date=date(2026, 2, 1),  # Future date
    comment="Effective from next month"
)
# Result: Status = APPROVED_PENDING_EFFECTIVE
# Scheduler will activate on 2026-02-01
```

### Pattern 3: Review Rejection Loop

```python
# Reviewer finds issues
complete_review(
    document=doc,
    reviewer=user,
    approved=False,
    comment="Section 3.2 needs clarification"
)
# Result: Document returns to DRAFT
# Author revises and resubmits
# Process starts over
```

### Pattern 4: Approval Rejection

```python
# Approver rejects during final approval
reject_document(
    document=doc,
    approver=user,
    comment="Regulatory requirements not addressed"
)
# Result: Document returns to DRAFT
# Must go through entire workflow again
```

---

## 🔍 Workflow Queries

### Common Backend Queries

```python
# Get all documents pending my review
pending_review = Document.objects.filter(
    reviewer=request.user,
    status__in=['PENDING_REVIEW', 'UNDER_REVIEW']
)

# Get all documents pending my approval
pending_approval = Document.objects.filter(
    approver=request.user,
    status='PENDING_APPROVAL'
)

# Get all effective documents
effective_docs = Document.objects.filter(
    status='EFFECTIVE',
    is_active=True
)

# Get documents becoming effective today
activation_due = Document.objects.filter(
    status='APPROVED_PENDING_EFFECTIVE',
    effective_date__lte=timezone.now().date()
)

# Get overdue workflows
overdue = DocumentWorkflow.objects.filter(
    is_active=True,
    due_date__lt=timezone.now(),
    is_completed=False
)
```

---

## 📈 Workflow Metrics & Monitoring

### Key Performance Indicators

1. **Average Review Time**: Time from PENDING_REVIEW to REVIEW_COMPLETED
2. **Average Approval Time**: Time from PENDING_APPROVAL to APPROVED
3. **Time to Effectiveness**: Time from DRAFT to EFFECTIVE
4. **Rejection Rate**: Percentage of documents rejected
5. **Overdue Tasks**: Number of tasks past due date

### Dashboard Widgets

```python
# Workflow health dashboard
metrics = {
    'pending_review_count': Document.objects.filter(status='PENDING_REVIEW').count(),
    'pending_approval_count': Document.objects.filter(status='PENDING_APPROVAL').count(),
    'overdue_reviews': calculate_overdue_reviews(),
    'avg_approval_time_days': calculate_avg_approval_time(),
    'effectiveness_pending': Document.objects.filter(status='APPROVED_PENDING_EFFECTIVE').count(),
}
```

---

## 🚀 Summary

### Workflow Types
1. ✅ **Review Workflow** - Main document approval process
2. ✅ **Up-versioning Workflow** - Create new document versions
3. ✅ **Obsolescence Workflow** - Retire outdated documents
4. ✅ **Termination Workflow** - Cancel documents before effectiveness

### Key Features
- ✅ State-based workflow engine
- ✅ Role-based access control
- ✅ Complete audit trail (21 CFR Part 11)
- ✅ Automated scheduling (effective dates, obsolescence)
- ✅ Notification system
- ✅ Version control with supersession
- ✅ Document dependencies tracking
- ✅ Electronic signatures via workflow actions

### Integration Points
- ✅ Backend: Django REST Framework APIs
- ✅ Frontend: React with TypeScript
- ✅ Scheduler: Celery Beat for automation
- ✅ Database: PostgreSQL with audit tables
- ✅ Notifications: In-app + Email

---

**The EDMS workflow system is production-ready, fully compliant, and scalable for pharmaceutical and regulated environments!** 🎉
