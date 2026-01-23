# EDMS Repository Understanding Summary

## 📚 **Repository Overview**

The EDMS (Electronic Document Management System) is a **21 CFR Part 11 compliant** document management platform designed for regulated industries, particularly pharmaceuticals. It's a full-stack application with:

- **Backend**: Django 4.2+ (Python 3.11+)
- **Frontend**: React 18+
- **Database**: PostgreSQL (with support for document versioning and audit trails)
- **Task Queue**: Celery with Redis/RabbitMQ
- **Container**: Docker & Docker Compose
- **Deployment**: Supports on-premise, staging, and production environments

---

## 🏗️ **System Architecture**

### **Core Modules**

The system is organized into several Django apps:

1. **`apps/documents/`** - Document management (O1 module)
   - Document creation, versioning, storage
   - File upload, download, processing
   - Document types, sources, dependencies
   - Placeholder/template system

2. **`apps/workflows/`** - Workflow engine (O2 module)
   - Document lifecycle workflows
   - State transitions
   - Review and approval processes
   - Periodic review system

3. **`apps/users/`** - User management (O3 module)
   - User authentication
   - Role-based access control (RBAC)
   - User roles and permissions

4. **`apps/audit/`** - Audit trail (O4 module)
   - Complete audit logging
   - Access tracking
   - Compliance reporting

5. **`apps/scheduler/`** - Task scheduler (O5 module)
   - Automated tasks
   - Periodic review reminders
   - Document activation
   - Backup automation

6. **`apps/backup/`** - Backup & restore (O6 module)
   - Database backups
   - Configuration exports
   - System restore capabilities

---

## 📋 **Document Lifecycle Workflows**

The EDMS implements **4 primary workflows** using a simplified workflow engine:

### **1. Review & Approval Workflow (Primary)**

The main document workflow from creation to effectiveness:

```
DRAFT 
  ↓ (Author submits)
PENDING_REVIEW 
  ↓ (Reviewer starts review)
UNDER_REVIEW 
  ↓ (Reviewer completes review)
REVIEWED 
  ↓ (Author routes to approver)
PENDING_APPROVAL 
  ↓ (Approver approves with effective date)
APPROVED_PENDING_EFFECTIVE or EFFECTIVE
  ↓ (Scheduler activates on effective date)
EFFECTIVE
```

**Key Points:**
- **Author**: Creates document, submits for review, routes to approver
- **Reviewer**: Reviews document, can approve or reject back to DRAFT
- **Approver**: Final approval with required effective date
- **Effective Date**: If future date → `APPROVED_PENDING_EFFECTIVE`, scheduler activates on date
- **Rejection**: Can occur at review or approval stage, returns to DRAFT with cleared assignments

**Implementation:**
- **File**: `backend/apps/workflows/document_lifecycle.py`
- **Service**: `DocumentLifecycleService` class
- **Methods**: 
  - `submit_for_review()` - DRAFT → PENDING_REVIEW
  - `start_review()` - PENDING_REVIEW → UNDER_REVIEW
  - `complete_review()` - UNDER_REVIEW → REVIEWED (or back to DRAFT)
  - `route_for_approval()` - REVIEWED → PENDING_APPROVAL
  - `approve_document()` - PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE/EFFECTIVE
  - `activate_pending_effective_documents()` - Scheduler task for activation

---

### **2. Up-versioning Workflow**

Creates new versions of existing documents with smart dependency management:

```
Existing Document (EFFECTIVE v1.0)
  ↓ (User initiates versioning)
New Document Created (DRAFT v2.0)
  ↓ (Follows standard Review & Approval workflow)
New Document → EFFECTIVE v2.0
  ↓ (Automatic supersession)
Old Document → SUPERSEDED v1.0
```

**Key Features:**

1. **Version Number Management**:
   - Major version increment: v1.0 → v2.0 (breaking changes)
   - Minor version increment: v1.0 → v1.1 (minor updates)
   - Versions limited to 1-99 for major, 0-99 for minor

2. **Document Number Format**:
   - Base: `SOP-2025-0001` (generated from document type prefix + year + sequence)
   - Versioned: `SOP-2025-0001-v01.00` (base + version suffix)
   - Conflict resolution: Auto-increments if version exists

3. **Smart Dependency Copying**:
   - Copies dependencies from old version to new version
   - **Automatically resolves to latest EFFECTIVE version** of each dependency
   - Example: Old version depends on `POL-2025-0001-v01.00`
     - If `POL-2025-0001-v02.00` is now EFFECTIVE
     - New version automatically depends on v02.00 (latest)
   - Prevents outdated dependency chains

4. **Automatic Supersession**:
   - When new version becomes EFFECTIVE, old version → SUPERSEDED
   - Maintains document family relationships
   - Frontend groups documents by base number for family view

**Implementation:**
- **File**: `backend/apps/workflows/document_lifecycle.py`
- **Methods**:
  - `start_version_workflow()` - Creates new version document
  - `complete_versioning()` - Marks old version as SUPERSEDED
- **Smart Dependency Copy**: `backend/apps/documents/views.py`
  - `_copy_dependencies_smart()` - Resolves to latest effective versions
  - `_find_latest_effective_version()` - Finds latest EFFECTIVE in family

**Example Flow:**
```python
# User creates new version of SOP-2025-0001 v1.0 (EFFECTIVE)
result = lifecycle_service.start_version_workflow(
    existing_document=sop_v1,
    user=request.user,
    new_version_data={
        'major_increment': True,  # v1.0 → v2.0
        'reason_for_change': 'Updated to reflect new regulations',
        'change_summary': 'Added compliance section'
    }
)

# Result:
# - New document created: SOP-2025-0001-v02.00 (DRAFT)
# - Dependencies copied and resolved to latest versions
# - New document enters review workflow
# - When approved and EFFECTIVE, old v1.0 → SUPERSEDED
```

---

### **3. Periodic Review Workflow**

Ensures documents are reviewed at regular intervals for regulatory compliance:

```
Document (EFFECTIVE)
  ↓ (Review period expires)
Scheduler detects review due
  ↓ (Email notification sent)
Reviewer receives task
  ↓ (Reviewer completes periodic review)
Review Outcome:
  - CONFIRMED: No changes needed (document stays EFFECTIVE)
  - UPDATED: Minor changes applied (stays EFFECTIVE)
  - UPVERSIONED: Major changes needed (creates new version)
```

**Key Components:**

1. **Document Review Fields** (in `Document` model):
   ```python
   review_period_months = 12  # Default annual review
   last_review_date = None    # When last reviewed
   next_review_date = None    # When next review due
   last_reviewed_by = None    # Who reviewed
   ```

2. **DocumentReview Model** (audit trail):
   - Tracks each periodic review completion
   - Records outcome (CONFIRMED/UPDATED/UPVERSIONED)
   - Links to new version if up-versioned
   - Stores reviewer comments

3. **Scheduler Integration**:
   - Daily task checks for documents due for review
   - Sends email notifications to stakeholders
   - Creates pending tasks for reviewers

4. **Review Outcomes**:
   - **CONFIRMED**: Document reviewed, no changes needed
     - Updates `last_review_date` and `next_review_date`
     - Creates `DocumentReview` record
     - Document remains EFFECTIVE
   - **MINOR_UPVERSION**: Minor changes required
     - **Automatically triggers minor up-versioning workflow**
     - Creates new version: v1.0 → v1.1
     - New version starts in DRAFT status
     - Links `DocumentReview` to new version
     - Original document remains EFFECTIVE until new version approved
   - **MAJOR_UPVERSION**: Major changes required
     - **Automatically triggers major up-versioning workflow**
     - Creates new version: v1.0 → v2.0
     - New version starts in DRAFT status
     - Links `DocumentReview` to new version
     - Original document remains EFFECTIVE until new version approved

**Implementation:**
- **Models**: 
  - `backend/apps/workflows/models_review.py` - `DocumentReview` model
  - `backend/apps/documents/models.py` - Review fields on `Document`
- **Views**: `backend/apps/documents/views_periodic_review.py` - `PeriodicReviewMixin`
- **Service**: `backend/apps/scheduler/services/periodic_review_service.py`
- **Scheduler**: Automated detection and notification

**API Endpoints** (via `PeriodicReviewMixin`):
```
POST /api/v1/documents/{uuid}/start-periodic-review/
POST /api/v1/documents/{uuid}/complete-periodic-review/
GET  /api/v1/documents/{uuid}/review-history/
```

**Example Flow:**
```python
# Document becomes effective with review period
document.effective_date = date(2025, 1, 1)
document.review_period_months = 12
document.next_review_date = date(2026, 1, 1)

# Scheduler checks daily (Jan 1, 2026)
# → Detects document.next_review_date <= today
# → Sends email to reviewer, approver, author

# Reviewer completes periodic review
# Option 1: CONFIRMED - No changes needed
review = DocumentReview.objects.create(
    document=document,
    reviewed_by=reviewer,
    outcome='CONFIRMED',
    comments='Document reviewed, no changes needed',
    next_review_date=date(2027, 1, 1)  # Schedule next review
)

# Option 2: MINOR_UPVERSION - Minor changes required
# This automatically triggers minor up-versioning workflow
review = DocumentReview.objects.create(
    document=document,
    reviewed_by=reviewer,
    outcome='MINOR_UPVERSION',
    comments='Minor updates required for compliance',
    next_review_date=date(2027, 1, 1)
)
# → Creates new document: SOP-2025-0001-v01.01 (DRAFT)
# → Starts review workflow for new version
# → Links review.new_version to new document

# Option 3: MAJOR_UPVERSION - Major changes required
# This automatically triggers major up-versioning workflow
review = DocumentReview.objects.create(
    document=document,
    reviewed_by=reviewer,
    outcome='MAJOR_UPVERSION',
    comments='Significant changes required',
    next_review_date=date(2027, 1, 1)
)
# → Creates new document: SOP-2025-0001-v02.00 (DRAFT)
# → Starts review workflow for new version
# → Links review.new_version to new document

# Document updated automatically
document.last_review_date = date(2026, 1, 1)
document.next_review_date = date(2027, 1, 1)
document.last_reviewed_by = reviewer
```

---

### **4. Obsolescence Workflow**

Marks documents as obsolete with dependency validation:

```
Document (EFFECTIVE)
  ↓ (Approver schedules obsolescence)
Document (SCHEDULED_FOR_OBSOLESCENCE)
  ↓ (Scheduler activates on obsolescence date)
Document (OBSOLETE)
```

**Key Features:**

1. **Dependency Protection**:
   - Cannot obsolete if other EFFECTIVE documents depend on it
   - Validates across entire document family (all versions)
   - Provides detailed blocking dependency report

2. **Direct Obsolescence** (for authorized users):
   - Approvers/admins can directly schedule obsolescence
   - Requires future obsolescence date
   - Requires reason for obsolescence
   - Sends notifications to stakeholders

3. **Family Validation**:
   - Checks all versions in document family
   - Prevents obsolescence if newer versions in development
   - Ensures no active up-versioning workflows

4. **Conflict Detection**:
   - Validates no active workflows (REVIEW, UP_VERSION)
   - Checks for documents already scheduled
   - Prevents concurrent obsolescence operations

**Implementation:**
- **File**: `backend/apps/workflows/document_lifecycle.py`
- **Methods**:
  - `obsolete_document_directly()` - Direct obsolescence scheduling
  - `_validate_obsolescence_eligibility()` - Dependency checks
  - `_validate_no_newer_versions_in_development()` - Family validation
  - `_send_obsolescence_notifications()` - Stakeholder notifications

**Validation Example:**
```python
# Check if document can be obsoleted
validation = document.can_obsolete_family()

# Result structure:
{
    'can_obsolete': False,
    'reason': 'Cannot obsolete: 2 active document(s) depend on this family',
    'blocking_dependencies': [
        {
            'version': '01.00',
            'document_number': 'SOP-2025-0001-v01.00',
            'status': 'EFFECTIVE',
            'dependent_count': 2,
            'dependents': [
                {
                    'document_number': 'WI-2025-0001',
                    'title': 'Work Instruction for XYZ',
                    'status': 'EFFECTIVE'
                }
            ]
        }
    ]
}
```

---

## 🔧 **Technical Implementation Details**

### **Workflow State Management**

The system uses a **hybrid approach** combining:

1. **Document Status Field** (`document.status`):
   - Primary source of truth
   - 13 possible states (DRAFT → EFFECTIVE → OBSOLETE)
   - Database indexed for fast queries

2. **DocumentWorkflow Model**:
   - Tracks active workflow instance
   - Links to current state via `DocumentState`
   - Records workflow type (REVIEW, UP_VERSION, OBSOLETE, PERIODIC_REVIEW)
   - Maintains current assignee and workflow data

3. **DocumentState Model** (static states):
   - Pre-defined workflow states
   - Maps to document status codes
   - Defines allowed transitions

4. **DocumentTransition Model** (audit trail):
   - Records every state change
   - Captures user, timestamp, comment
   - Provides complete workflow history

**Key Files:**
- `backend/apps/workflows/models.py` - Workflow models
- `backend/apps/workflows/models_simple.py` - DocumentState definitions
- `backend/apps/workflows/document_lifecycle.py` - Workflow service

---

### **Scheduler Tasks**

The scheduler runs automated tasks for document lifecycle management:

1. **Activate Pending Documents** (Daily at midnight):
   - Finds documents with `status='APPROVED_PENDING_EFFECTIVE'`
   - Checks if `effective_date <= today`
   - Transitions to `EFFECTIVE` status
   - **Method**: `activate_pending_effective_documents()`

2. **Periodic Review Detection** (Daily):
   - Finds documents with `next_review_date <= today`
   - Sends email notifications to reviewers
   - Creates pending review tasks
   - **Service**: `periodic_review_service.py`

3. **Obsolescence Activation** (Daily):
   - Finds documents with `status='SCHEDULED_FOR_OBSOLESCENCE'`
   - Checks if `obsolescence_date <= today`
   - Transitions to `OBSOLETE` status
   - Sends completion notifications

4. **Data Integrity Checks** (Daily):
   - Validates file checksums
   - Verifies workflow consistency
   - Reports anomalies

**Scheduler Configuration:**
- **Task Registration**: `backend/apps/scheduler/tasks.py`
- **Celery Beat**: Schedules periodic tasks
- **Implementation**: Uses Celery with Redis/RabbitMQ backend

---

## 🗂️ **Document Version Management**

### **Version Numbering Scheme**

```
Document Number Format: {PREFIX}-{YEAR}-{SEQUENCE}-v{MAJOR}.{MINOR}

Examples:
  SOP-2025-0001-v01.00  (First version)
  SOP-2025-0001-v01.01  (Minor update)
  SOP-2025-0001-v02.00  (Major revision)
  POL-2025-0005-v03.15  (3rd major, 15th minor)
```

**Rules:**
- Major version: 1-99 (breaking changes, requires full review)
- Minor version: 0-99 (minor updates, may require lighter review)
- Base number remains constant across versions
- Version suffix added for all documents

### **Document Family Concept**

All versions of a document form a "family" identified by base number:

```
SOP-2025-0001 Family:
├── SOP-2025-0001-v01.00 (SUPERSEDED)
├── SOP-2025-0001-v02.00 (SUPERSEDED)
└── SOP-2025-0001-v03.00 (EFFECTIVE) ← Latest version
```

**Family Operations:**
- **Get Family Versions**: Retrieve all versions for grouping/display
- **Latest Version Query**: Find current EFFECTIVE version
- **Family Obsolescence**: Validate dependencies across all versions
- **Version History**: Show evolution of document over time

**Implementation:**
```python
# Get all versions in family
family_versions = document.get_family_versions()

# Check family obsolescence eligibility
validation = document.can_obsolete_family()

# Get latest effective version of a document family
latest = _find_latest_effective_version('SOP-2025-0001')
```

---

## 📄 **Document Templates & Placeholders**

The system supports **DOCX template processing** with dynamic placeholder replacement:

### **Placeholder System**

32 built-in placeholders for metadata injection:

```
Document Metadata:
{{DOCUMENT_NUMBER}}    - SOP-2025-0001-v01.00
{{DOCUMENT_TITLE}}     - Standard Operating Procedure
{{VERSION_MAJOR}}      - 01
{{VERSION_MINOR}}      - 00
{{VERSION_FULL}}       - v01.00

Dates and Times:
{{CREATED_DATE}}       - January 15, 2025
{{EFFECTIVE_DATE}}     - February 1, 2025
{{CURRENT_DATETIME}}   - 15:52:33 UTC (23:52:33 SGT)

People:
{{AUTHOR}}             - John Doe
{{REVIEWER}}           - Jane Smith
{{APPROVER}}           - Bob Johnson

Status:
{{STATUS}}             - EFFECTIVE
{{APPROVAL_DATE}}      - January 30, 2025

Computed Placeholders:
{{VERSION_HISTORY}}    - Native DOCX table with all versions
```

### **Template Processing Flow**

```
1. User uploads DOCX template with placeholders
2. Document created/updated in system
3. User downloads "annotated" version
4. System processes template:
   a. Replace all {{PLACEHOLDER}} with actual values
   b. Generate native DOCX tables for {{VERSION_HISTORY}}
   c. Add metadata footer
   d. Return processed DOCX
```

**Implementation:**
- **Processor**: `backend/apps/documents/docx_processor.py`
- **Placeholder Service**: `backend/apps/placeholders/services.py`
- **Version History Tables**: Uses `python-docx` for native table creation

**Special Feature - Version History Table:**
- Automatically creates professional Word table
- Includes all document versions with date, author, status, comments
- Editable in Microsoft Word
- Professional formatting with borders

---

## 🔐 **Security & Compliance**

### **21 CFR Part 11 Compliance**

The system implements key requirements:

1. **Electronic Signatures**:
   - User authentication required for all actions
   - Password validation
   - Session management

2. **Audit Trail**:
   - Complete record of all document actions
   - User, timestamp, action, changes recorded
   - Cannot be modified or deleted
   - Exportable for compliance reports

3. **Access Control**:
   - Role-based permissions (RBAC)
   - User roles: Author, Reviewer, Approver, Admin
   - Module-level permissions (O1-O6)
   - Permission levels: read, write, review, approve, admin

4. **Version Control**:
   - Complete version history
   - Immutable approved documents
   - Change tracking and justification

5. **Validation**:
   - Workflow validation rules
   - Data integrity checks (checksums)
   - Circular dependency prevention

### **Data Integrity**

- **File Checksums**: SHA-256 hashes for file integrity verification
- **Version Immutability**: Approved documents cannot be edited
- **Dependency Validation**: Prevents broken references
- **Circular Dependency Detection**: Graph-based validation

---

## 🚀 **Deployment**

### **Interactive Deployment Script**

The system includes a comprehensive interactive deployment script:

```bash
./deploy-interactive.sh
```

**Features:**
- Environment detection (development, staging, production)
- Pre-deployment checks (dependencies, ports, disk space)
- Database migration management
- Static file collection
- Container health monitoring
- Post-deployment validation
- Rollback capability

**Deployment Steps:**
1. Check system requirements
2. Build Docker containers
3. Initialize database (migrations)
4. Create/update default data (document types, states, placeholders)
5. Create test users (development only)
6. Start services
7. Verify health
8. Display access URLs

### **Environment Configuration**

Three environments supported:

1. **Development** (`docker-compose.yml`):
   - All services exposed
   - Debug mode enabled
   - Test users created
   - Hot reload enabled

2. **Staging** (subset of production):
   - Production-like configuration
   - Testing before deployment
   - Monitoring enabled

3. **Production** (`docker-compose.prod.yml`):
   - HAProxy load balancer
   - Only frontend exposed
   - All security features enabled
   - Backup automation
   - Monitoring and alerts

---

## 📊 **Key Database Models**

### **Document Model** (`apps/documents/models.py`)

```python
class Document(models.Model):
    # Identification
    uuid = UUIDField()
    document_number = CharField()  # SOP-2025-0001-v01.00
    
    # Content
    title = CharField()
    description = TextField()
    
    # Version
    version_major = PositiveIntegerField()  # 1-99
    version_minor = PositiveIntegerField()  # 0-99
    
    # Lifecycle
    status = CharField(choices=DOCUMENT_STATUS_CHOICES)
    effective_date = DateField()
    
    # People
    author = ForeignKey(User)
    reviewer = ForeignKey(User)
    approver = ForeignKey(User)
    
    # Periodic Review
    review_period_months = PositiveIntegerField(default=12)
    last_review_date = DateField()
    next_review_date = DateField()
    last_reviewed_by = ForeignKey(User)
    
    # Obsolescence
    obsolescence_date = DateField()
    obsolescence_reason = TextField()
    obsoleted_by = ForeignKey(User)
    
    # File
    file_name = CharField()
    file_path = CharField()
    file_checksum = CharField()  # SHA-256
```

### **DocumentWorkflow Model** (`apps/workflows/models.py`)

```python
class DocumentWorkflow(models.Model):
    document = ForeignKey(Document)
    workflow_type = CharField()  # REVIEW, UP_VERSION, OBSOLETE, PERIODIC_REVIEW
    current_state = ForeignKey(DocumentState)
    current_assignee = ForeignKey(User)
    initiated_by = ForeignKey(User)
    is_terminated = BooleanField()
    workflow_data = JSONField()  # Additional metadata
```

### **DocumentReview Model** (`apps/workflows/models_review.py`)

```python
class DocumentReview(models.Model):
    document = ForeignKey(Document)
    review_date = DateField()
    reviewed_by = ForeignKey(User)
    outcome = CharField(choices=['CONFIRMED', 'UPDATED', 'UPVERSIONED'])
    comments = TextField()
    next_review_date = DateField()
    new_version = ForeignKey(Document, null=True)  # If upversioned
    workflow = ForeignKey(DocumentWorkflow, null=True)
```

### **DocumentDependency Model** (`apps/documents/models.py`)

```python
class DocumentDependency(models.Model):
    document = ForeignKey(Document)  # Source
    depends_on = ForeignKey(Document)  # Target
    dependency_type = CharField(choices=[
        'REFERENCE', 'TEMPLATE', 'SUPERSEDES', 
        'INCORPORATES', 'SUPPORTS', 'IMPLEMENTS'
    ])
    is_critical = BooleanField()
    is_active = BooleanField()
    
    # Circular dependency validation
    def clean(self):
        if self._would_create_circular_dependency():
            raise ValidationError("Circular dependency detected")
```

---

## 🔄 **Recent Development Highlights**

Based on recent commits, the system has been actively developed with these key additions:

### **January 2025 Updates**

1. **Admin Filter Bypass** (commit `820a8ac`):
   - Admins can see all documents regardless of filters
   - Document ownership indicators
   - Scheduler task fixes

2. **Upversioning System** (commit `4d2f0dd`):
   - Complete family grouping implementation
   - Smart dependency resolution
   - Automatic version management

3. **Scheduler Dashboard** (commit `358f3c0`):
   - Integrated task monitoring
   - Working stat cards
   - Activity tracking

4. **Reports System** (commit `3f186df`):
   - Enhanced reporting capabilities
   - Export functionality
   - Preview and download

5. **Periodic Review** (multiple commits):
   - System design complete
   - Scheduler integration
   - Email notifications

6. **Version History Tables** (documentation):
   - Native DOCX table generation
   - Professional formatting
   - Editable in Word

---

## 📝 **Development Patterns**

### **Code Organization**

```
backend/apps/
├── documents/          # O1: Document management
│   ├── models.py      # Document, DocumentDependency, DocumentVersion
│   ├── views.py       # REST API endpoints
│   ├── serializers.py # DRF serializers
│   ├── services.py    # Business logic
│   ├── docx_processor.py     # Template processing
│   ├── annotation_processor.py  # Metadata injection
│   └── views_periodic_review.py  # Periodic review mixin
│
├── workflows/         # O2: Workflow engine
│   ├── models.py      # DocumentWorkflow, WorkflowInstance
│   ├── models_review.py  # DocumentReview
│   ├── document_lifecycle.py  # Core workflow service
│   ├── services.py    # High-level workflow operations
│   └── tasks.py       # Celery tasks
│
├── scheduler/         # O5: Automated tasks
│   ├── tasks.py       # Celery task definitions
│   ├── services/
│   │   └── periodic_review_service.py  # Review automation
│   └── automated_tasks.py  # Task implementations
│
└── [other apps...]
```

### **API Patterns**

All APIs follow RESTful conventions with DRF:

```python
# Document endpoints
GET    /api/v1/documents/              # List documents
POST   /api/v1/documents/              # Create document
GET    /api/v1/documents/{uuid}/       # Get document detail
PATCH  /api/v1/documents/{uuid}/       # Update document
DELETE /api/v1/documents/{uuid}/       # Delete document

# Custom actions
POST   /api/v1/documents/{uuid}/create-version/
POST   /api/v1/documents/{uuid}/submit-for-review/
POST   /api/v1/documents/{uuid}/start-periodic-review/
GET    /api/v1/documents/{uuid}/family-versions/
```

### **Frontend Integration**

React frontend communicates via REST APIs:
- Token-based authentication
- React Router for navigation
- Context API for state management
- Axios for HTTP requests

---

## 🎓 **Testing & Quality**

### **Test Coverage**

- Unit tests for models and services
- Integration tests for workflows
- End-to-end tests with Playwright
- API tests with Django REST framework

### **Test Users**

Default test users created in development:

```
Author (author01):
  - Username: author01
  - Password: TestPass123!
  - Role: Document Author

Reviewer (reviewer01):
  - Username: reviewer01
  - Password: TestPass123!
  - Role: Document Reviewer

Approver (approver01):
  - Username: approver01
  - Password: TestPass123!
  - Role: Document Approver

Admin (admin):
  - Username: admin
  - Password: admin123
  - Role: Superuser
```

---

## 📚 **Documentation**

Comprehensive documentation available in `Dev_Docs/`:

- `1_EDMS_Database_Schema_Complete.md` - Complete database schema
- `2_EDMS_API_Specifications.md` - API documentation
- `3_Enhanced_Simple_Workflow_Setup.md` - Workflow configuration
- `4_Authentication_Integration.md` - Auth setup
- `5_File_Storage_Architecture.md` - File storage design
- `Simplified_Workflow_Architecture.md` - Workflow overview

Additional guides:
- `EDMS_WORKFLOWS_EXPLAINED.md` - Workflow details
- `PERIODIC_REVIEW_SYSTEM_DESIGN.md` - Periodic review specs
- `DOCUMENT_DEPENDENCY_UPVERSION_FIX.md` - Upversioning guide
- `VERSION_HISTORY_NATIVE_DOCX_IMPLEMENTATION_COMPLETE.md` - Template system

---

## 🚦 **Getting Started**

### **Quick Start (Local Development)**

```bash
# 1. Clone repository
git clone <repository-url>
cd QMS_04

# 2. Run interactive deployment
./deploy-interactive.sh

# 3. Access application
Frontend: http://localhost:3000
Backend:  http://localhost:8000
Admin:    http://localhost:8000/admin

# 4. Login with test users
Username: author01
Password: TestPass123!
```

### **Workflow Testing**

```bash
# 1. Login as author01
# 2. Create new document
# 3. Assign reviewer (reviewer01) and approver (approver01)
# 4. Submit for review
# 5. Login as reviewer01
# 6. Review and approve document
# 7. Login as author01
# 8. Route to approver
# 9. Login as approver01
# 10. Approve with effective date
# 11. Document becomes EFFECTIVE (immediately or via scheduler)
```

---

## 🎯 **Key Takeaways**

1. **Simplified Workflow Engine**: Uses `DocumentLifecycleService` for all 4 workflows
2. **Smart Dependency Management**: Auto-resolves to latest effective versions
3. **Periodic Review System**: Automated compliance with configurable review periods
4. **Version Family Concept**: Groups all versions by base document number
5. **Native DOCX Processing**: Professional template system with real Word tables
6. **21 CFR Part 11 Ready**: Complete audit trail and electronic signatures
7. **Docker-First**: Containerized for consistent deployment
8. **Interactive Deployment**: Guided setup with validation

---

## 📞 **Support & Resources**

- **Memory Files**: `AGENTS.md` contains development patterns and lessons learned
- **Recent Changes**: Check recent commits for latest features
- **Documentation**: Extensive docs in `Dev_Docs/` folder
- **Testing**: Playwright tests in `e2e/` and `tests/` directories

---

**Generated**: January 22, 2026
**Version**: Based on commit `820a8ac` (main branch)
