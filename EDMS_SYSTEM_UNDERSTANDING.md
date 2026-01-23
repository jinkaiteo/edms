# EDMS System - Comprehensive Understanding

**Generated:** January 22, 2026  
**Based on:** Git history, codebase analysis, and workspace memory

---

## 🎯 System Overview

**EDMS (Electronic Document Management System)** is a 21 CFR Part 11 compliant document management system built with:
- **Backend:** Django 4.2 + Django REST Framework
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **Task Queue:** Celery + Redis
- **Database:** PostgreSQL
- **Deployment:** Docker Compose

### Key Compliance Features
- ✅ Electronic Signatures
- ✅ Audit Trail (immutable logging)
- ✅ Role-Based Access Control (RBAC)
- ✅ File Integrity (SHA-256 checksums)
- ✅ Version Control with full history

---

## 📊 Current System Architecture (v1.2.0)

### Application Structure
```
edms/
├── backend/                    # Django REST API
│   ├── apps/
│   │   ├── documents/         # Core document management (O1)
│   │   ├── workflows/         # Simple workflow engine
│   │   ├── users/             # Authentication & authorization (S1)
│   │   ├── audit/             # Audit trail (S2)
│   │   ├── placeholders/      # Template placeholder system (O5)
│   │   ├── scheduler/         # Celery task automation (S3)
│   │   ├── security/          # Security features (S4)
│   │   └── reports/           # Reporting system (O7)
│   └── edms/                  # Django project settings
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client services
│   │   ├── contexts/          # React contexts (auth, etc.)
│   │   └── pages/             # Page components
│   └── public/
│
├── scripts/                    # Deployment & utility scripts
├── infrastructure/             # Docker, HAProxy, nginx configs
└── docs/                       # Documentation
```

---

## 🔄 Document Workflows

The system implements **4 core workflows** using a simplified state machine approach (no complex workflow engine):

### 1. **Review Workflow** (Primary workflow for new documents)

**States:** DRAFT → PENDING_REVIEW → UNDER_REVIEW → REVIEWED → PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE → EFFECTIVE

**Flow:**
```
1. Author creates document (DRAFT)
2. Author submits for review (DRAFT → PENDING_REVIEW)
3. Reviewer starts review (PENDING_REVIEW → UNDER_REVIEW)
4. Reviewer completes review (UNDER_REVIEW → REVIEWED)
   - If rejected: back to DRAFT (reviewer assignment cleared)
5. Author routes to approver (REVIEWED → PENDING_APPROVAL)
6. Approver approves with effective date (PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE or EFFECTIVE)
   - If rejected: back to DRAFT (both reviewer and approver assignments cleared)
7. Scheduler activates on effective date (APPROVED_PENDING_EFFECTIVE → EFFECTIVE)
```

**Key Code:**
- **Service:** `backend/apps/workflows/document_lifecycle.py` - `DocumentLifecycleService`
- **Models:** `backend/apps/workflows/models_simple.py` - `DocumentWorkflow`, `DocumentState`, `DocumentTransition`
- **Scheduler:** `backend/apps/scheduler/tasks.py` - `process_document_effective_dates()`

**Important Notes:**
- Effective date is **required** at approval time
- If effective date ≤ today: immediate EFFECTIVE status
- If effective date > today: APPROVED_PENDING_EFFECTIVE status
- Scheduler runs **hourly** to activate pending documents

---

### 2. **Up-versioning Workflow** (Creating new versions)

**Purpose:** Create new version of an EFFECTIVE document while preserving the old version

**Flow:**
```
1. User initiates upversion on EFFECTIVE document
2. System creates new document with:
   - Incremented version (major or minor)
   - Status: DRAFT
   - supersedes: points to old document
   - Dependencies: SMART COPIED (see below)
3. New version goes through Review Workflow
4. When new version becomes EFFECTIVE:
   - Old version status → SUPERSEDED
   - Old version obsolete_date set to today
```

**Smart Dependency Copying:**
When creating a new version, dependencies are copied intelligently:
- For each dependency in the source document:
  - Extract base document number (e.g., "POL-2025-0001" from "POL-2025-0001-v01.00")
  - Find the **latest EFFECTIVE version** of that document family
  - Create dependency pointing to the latest effective version
  - If no effective version exists: copy original dependency as-is

**Key Code:**
```python
# backend/apps/documents/views.py - DocumentViewSet

@action(detail=True, methods=['post'])
def create_version(self, request, uuid=None):
    """Create a new version of the document."""
    document = self.get_object()
    
    # Calculate new version numbers
    if major_increment:
        new_major = document.version_major + 1
        new_minor = 0
    else:
        new_major = document.version_major
        new_minor = document.version_minor + 1
    
    # Create new document version
    new_document = Document.objects.create(
        title=document.title,
        version_major=new_major,
        version_minor=new_minor,
        supersedes=document,
        status='DRAFT',
        # ... other fields copied
    )
    
    # Smart dependency copying
    self._copy_dependencies_smart(document, new_document, request.user)

def _copy_dependencies_smart(self, source_document, target_document, user):
    """
    Smart dependency copying for upversioning.
    Copies dependencies but resolves to latest EFFECTIVE version.
    """
    source_dependencies = DocumentDependency.objects.filter(document=source_document)
    
    for dep in source_dependencies:
        # Get base document number
        depends_on_doc = dep.depends_on
        base_number = re.sub(r'-v\d+\.\d+$', '', depends_on_doc.document_number)
        
        # Find latest EFFECTIVE version
        latest_effective = self._find_latest_effective_version(base_number)
        
        if latest_effective:
            # Create dependency to latest version
            DocumentDependency.objects.create(
                document=target_document,
                depends_on=latest_effective,
                dependency_type=dep.dependency_type,
                created_by=user,
                description=f"Auto-copied (resolved to latest effective)",
                is_critical=dep.is_critical
            )
```

**Version Numbering:**
- Format: `{base_doc_number}-v{major:02d}.{minor:02d}`
- Example: `SOP-2025-0001-v01.00`, `SOP-2025-0001-v02.00`
- Major version: 1-99
- Minor version: 0-99
- Conflict resolution: If version exists, tries next minor, then major, then adds UUID suffix

---

### 3. **Obsolescence Workflow** (Direct obsolescence by approvers)

**Purpose:** Mark documents obsolete with future effective date

**Authority:**
- Document Approver: Can obsolete documents they approve
- System Administrator: Can obsolete any document

**Flow:**
```
1. Authorized user initiates obsolescence with:
   - Reason (required)
   - Obsolescence date (required, must be future date)
2. System validates:
   - Document is EFFECTIVE
   - No active dependencies exist
   - No newer versions in development
   - Obsolescence date is in future
3. Document status → SCHEDULED_FOR_OBSOLESCENCE
4. Scheduler runs hourly to activate obsolescence
5. On obsolescence date: status → OBSOLETE
```

**Enhanced Dependency Protection:**
- Checks ALL versions of document family for dependencies
- Blocks if ANY version has active dependencies (EFFECTIVE, APPROVED_PENDING_EFFECTIVE)
- Blocks if newer versions in development (DRAFT, UNDER_REVIEW, etc.)
- Blocks if active up-versioning workflows exist

**Key Code:**
```python
# backend/apps/workflows/document_lifecycle.py

def obsolete_document_directly(self, document: Document, user: User, 
                               reason: str, obsolescence_date) -> bool:
    """Direct obsolescence for authorized users."""
    
    # Validate authority
    has_authority = (
        user == document.approver or
        user.is_staff or
        user.is_superuser
    )
    
    # Enhanced conflict detection
    self._validate_obsolescence_eligibility(document)
    
    # Update document
    document.status = 'SCHEDULED_FOR_OBSOLESCENCE'
    document.obsolescence_date = obsolescence_date
    document.obsolescence_reason = reason
    document.obsoleted_by = user
    document.save()
    
    # Send notifications to stakeholders
    self._send_obsolescence_notifications(...)
```

**Scheduler Task:**
```python
# backend/apps/scheduler/tasks.py

@shared_task
def process_document_obsoletion_dates():
    """Process documents with obsoletion dates that have passed."""
    results = document_automation_service.process_obsoletion_dates()
    # Activates SCHEDULED_FOR_OBSOLESCENCE → OBSOLETE
```

---

### 4. **Workflow Termination** (Cancel before effective)

**Purpose:** Allow authors to cancel documents before they become effective

**Authority:** Document author only

**Terminable Statuses:** DRAFT, PENDING_REVIEW, UNDER_REVIEW, PENDING_APPROVAL

**Flow:**
```
1. Author terminates document
2. Document status → TERMINATED
3. Document marked inactive (is_active = False)
4. All pending workflow tasks cancelled
5. Audit trail created
```

---

## 🔧 Version Control & Document Families

### Document Family Concept

Documents with the same **base document number** form a "family":
- `SOP-2025-0001-v01.00` (original)
- `SOP-2025-0001-v01.01` (minor revision)
- `SOP-2025-0001-v02.00` (major revision)

All versions share base: `SOP-2025-0001`

### Version Relationships

```
Document Model Fields:
- supersedes: ForeignKey to previous version
- superseded_by: Reverse relationship to newer version
- version_major: Integer (1-99)
- version_minor: Integer (0-99)
```

**Example Family Tree:**
```
SOP-2025-0001-v01.00 [SUPERSEDED]
    └─> superseded_by: SOP-2025-0001-v02.00 [EFFECTIVE]
            └─> superseded_by: SOP-2025-0001-v03.00 [DRAFT]
```

### Frontend Family Grouping

Documents are grouped by family in the Document Library:
- Latest version shown as "parent"
- All versions accessible via expand/collapse
- SUPERSEDED versions included for historical reference

**Code:**
```typescript
// frontend/src/components/documents/DocumentLibrary.tsx

// Group documents by base number
const groupedDocuments = documents.reduce((acc, doc) => {
  const baseNumber = doc.document_number.split('-v')[0];
  if (!acc[baseNumber]) {
    acc[baseNumber] = [];
  }
  acc[baseNumber].push(doc);
  return acc;
}, {});

// Sort versions within each family
Object.values(groupedDocuments).forEach(family => {
  family.sort((a, b) => {
    if (a.version_major !== b.version_major) {
      return b.version_major - a.version_major;
    }
    return b.version_minor - a.version_minor;
  });
});
```

---

## ⏰ Scheduler System (Celery)

### Architecture

**Celery Configuration:**
- **Broker:** Redis (for task queue)
- **Result Backend:** django-db (stores task results in database)
- **Beat Scheduler:** Celery Beat (for periodic tasks)

**Service Pattern:**
- Tasks in `backend/apps/scheduler/tasks.py` are thin wrappers
- Business logic in `backend/apps/scheduler/services/`
- Pattern: `@shared_task` → Service method

### Scheduled Tasks

**1. Document Effective Date Processing**
```python
@shared_task
def process_document_effective_dates():
    """Activate APPROVED_PENDING_EFFECTIVE documents."""
    # Runs: Every hour
    # Service: document_automation_service.process_effective_dates()
    # Logic:
    #   - Find documents with status=APPROVED_PENDING_EFFECTIVE
    #   - Where effective_date <= today
    #   - Transition to EFFECTIVE
    #   - Send notifications
```

**2. Document Obsolescence Processing**
```python
@shared_task
def process_document_obsoletion_dates():
    """Activate SCHEDULED_FOR_OBSOLESCENCE documents."""
    # Runs: Every hour
    # Service: document_automation_service.process_obsoletion_dates()
    # Logic:
    #   - Find documents with status=SCHEDULED_FOR_OBSOLESCENCE
    #   - Where obsolescence_date <= today
    #   - Transition to OBSOLETE
    #   - Send notifications
```

**3. Workflow Timeout Checking**
```python
@shared_task
def check_workflow_timeouts():
    """Check for overdue workflows and send escalations."""
    # Runs: Every 4 hours
    # Service: document_automation_service.check_workflow_timeouts()
```

**4. System Health Check**
```python
@shared_task
def perform_system_health_check():
    """Comprehensive system health monitoring."""
    # Runs: Every 30 minutes
    # Service: system_health_service.perform_health_check()
    # Checks: Database, Celery, Redis, file storage, disk space
```

**5. Celery Result Cleanup**
```python
@shared_task
def cleanup_celery_results(days_to_keep=7):
    """Clean up old Celery task execution records."""
    # Runs: Daily at 03:00
    # Service: celery_cleanup_service.cleanup()
```

### Manual Task Triggering

Available through Admin Dashboard:
```python
# frontend/src/pages/admin/AdminDashboard.tsx

const triggerTask = async (taskName: string) => {
  const response = await api.post('/api/v1/scheduler/trigger-task/', {
    task_name: taskName
  });
};
```

---

## 🔐 Authentication & Authorization

### User Roles & Permissions

**Role Structure:**
```
UserRole Model:
  - user: ForeignKey(User)
  - role: ForeignKey(Role)
  - is_active: Boolean

Role Model:
  - name: CharField (e.g., "Document Author", "Document Reviewer")
  - module: CharField (e.g., "O1" for Documents)
  - permission_level: CharField (read/write/review/approve/admin)
```

**Permission Levels:**
- **read:** View documents
- **write:** Create/edit documents
- **review:** Review documents
- **approve:** Approve documents
- **admin:** Full access

### Document Access Control

**Admin Bypass:**
```python
is_admin = (
    user.is_superuser or 
    user.groups.filter(name__in=['Document Admins', 'Senior Document Approvers']).exists() or
    user.user_roles.filter(role__name='Document Admin', is_active=True).exists()
)
```

**Filter-Based Access:**
- **My Tasks:** Users see only their assigned tasks; admins see ALL tasks
- **Document Library:** All users see EFFECTIVE/APPROVED documents; admins see everything
- **Default View:** Users see documents they're involved in + public documents; admins see all

---

## 📦 Deployment

### Local Deployment (via Interactive Script)

The system includes an interactive deployment script: `deploy-interactive.sh`

**Deployment Steps:**
```bash
1. Run interactive script:
   ./deploy-interactive.sh

2. Script guides you through:
   - Environment configuration (IP, ports, secrets)
   - Docker compose deployment
   - Database initialization
   - HAProxy setup (optional)
   - Initial testing

3. Initialization includes:
   - Database migrations
   - Default users (admin, test users)
   - Default roles and groups
   - Document types (SOP, POLICY, MANUAL, etc.)
   - Workflow states
   - Placeholder definitions (32 placeholders)
```

**Default Test Users:**
```
admin / admin123      (Superuser)
author01 / Author123  (Document Author)
reviewer01 / Rev123   (Document Reviewer)
approver01 / App123   (Document Approver)
author02 / Author123  (Document Author)
```

### Docker Architecture

**Services:**
```yaml
services:
  backend:
    build: ./backend
    ports: ["8001:8000"]
    depends_on: [db, redis]
    
  frontend:
    build: ./frontend
    ports: ["3001:80"]
    depends_on: [backend]
    
  db:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]
    
  redis:
    image: redis:7-alpine
    
  celery_worker:
    build: ./backend
    command: celery -A edms worker --loglevel=info
    
  celery_beat:
    build: ./backend
    command: celery -A edms beat --loglevel=info
```

**HAProxy (Optional):**
- Reverse proxy for production
- Handles SSL termination
- Routes to backend:8001 and frontend:3001
- Configuration: `infrastructure/haproxy/haproxy-production.cfg`

---

## 🧪 Testing Strategy

### Test Users & Workflows

**Playwright E2E Tests:**
```
tests/
├── 01_seed_users.spec.js              # Create test users
├── 02_create_documents.spec.js        # Create documents with dependencies
├── 03_workflow_testing.spec.js        # Test review/approval workflows
└── 04_validation_and_reporting.spec.js # Validate results
```

**Running Tests:**
```bash
# Run all tests
npx playwright test

# Run specific test
npx playwright test tests/01_seed_users.spec.js

# Run with UI
npx playwright test --ui
```

---

## 📋 Key Implementation Details

### 1. Circular Dependency Prevention

**Challenge:** Prevent Document A → B → C → A circular dependencies

**Solution:** Base document number approach
```python
# backend/apps/documents/models.py - DocumentDependency

def _would_create_circular_dependency(self):
    """Check using base document numbers (version-aware)."""
    from_base = self._get_base_document_number(self.document.document_number)
    to_base = self._get_base_document_number(self.depends_on.document_number)
    
    # Rule 1: Cannot depend on another version of itself
    if from_base == to_base:
        return True
    
    # Rule 2: Check if target family depends back on source family
    return self._has_base_number_circular_dependency(from_base, to_base)
```

### 2. Timestamp Management (UTC + Local Display)

**Storage:** Always UTC in database  
**Display:** UTC + Local time (SGT for Singapore deployment)

```python
# backend/apps/workflows/document_lifecycle.py

from django.utils import timezone
import pytz

now_utc = timezone.now()
display_tz = pytz.timezone('Asia/Singapore')
now_local = now_utc.astimezone(display_tz)

result = f"{now_utc.strftime('%H:%M:%S')} UTC ({now_local.strftime('%H:%M:%S')} SGT)"
```

**Configuration:**
```python
# settings/base.py
TIME_ZONE = 'UTC'  # Storage timezone
DISPLAY_TIMEZONE = 'Asia/Singapore'  # User-facing display
USE_TZ = True  # Enable timezone-aware datetimes
```

### 3. File Integrity (21 CFR Part 11)

**SHA-256 Checksums:**
```python
# backend/apps/documents/models.py - Document

def calculate_file_checksum(self):
    """Calculate SHA-256 checksum of file."""
    sha256_hash = hashlib.sha256()
    with open(self.full_file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_file_integrity(self):
    """Verify file integrity using stored checksum."""
    current_checksum = self.calculate_file_checksum()
    return current_checksum == self.file_checksum
```

**Automated Daily Integrity Checks:**
```python
# backend/apps/scheduler/tasks.py

@shared_task
def perform_daily_integrity_check():
    """Verify checksums of all active documents."""
    # Runs daily at 02:00
    # Reports discrepancies to admin dashboard
```

---

## 🎨 Frontend Architecture

### React Component Structure

**Key Components:**
```
frontend/src/components/
├── documents/
│   ├── DocumentLibrary.tsx          # Main library with family grouping
│   ├── DocumentViewer.tsx           # Document detail view
│   ├── CreateNewVersionModal.tsx    # Upversioning UI
│   └── DocumentUpload.tsx           # File upload
│
├── workflows/
│   ├── WorkflowInitiator.tsx        # Start workflows
│   ├── ReviewInterface.tsx          # Review UI
│   └── ApprovalInterface.tsx        # Approval UI
│
├── admin/
│   ├── AdminDashboard.tsx           # Admin overview
│   ├── SchedulerDashboard.tsx       # Task monitoring
│   └── AuditTrailViewer.tsx         # Audit logs
│
└── common/
    ├── Navigation.tsx               # Main navigation
    └── UserProfile.tsx              # User menu
```

### API Service Layer

**Pattern:**
```typescript
// frontend/src/services/api.ts

export const documentService = {
  list: (params) => api.get('/api/v1/documents/', { params }),
  get: (uuid) => api.get(`/api/v1/documents/${uuid}/`),
  create: (data) => api.post('/api/v1/documents/', data),
  update: (uuid, data) => api.patch(`/api/v1/documents/${uuid}/`, data),
  createVersion: (uuid, data) => api.post(`/api/v1/documents/${uuid}/create_version/`, data),
  // ... more methods
};
```

---

## 📝 Recent Improvements (Git History Analysis)

**Latest Commits (Last 50):**

1. **Admin Filter Bypass (820a8ac):**
   - Admin users can see ALL tasks (not just their own)
   - Document ownership indicator added
   - Fixed scheduler task registration

2. **Integrity Checks (61687dc, 3f186df):**
   - Actual checksum verification in daily integrity checks
   - Reports system improvements

3. **v1.2.0 Release (3d3d2d6):**
   - Production-ready scheduler and dashboard
   - Placeholder initialization in deployment

4. **Upversioning System (c900592, 4d2f0dd):**
   - Complete upversioning with family grouping
   - Smart dependency copying with latest effective resolution
   - Dependency field name fixes

5. **Admin Dashboard (358f3c0):**
   - Working stat cards
   - Integrated scheduler dashboard
   - Recent activity display

6. **Audit Trail Exports (f6668fe, 6f98d05):**
   - CSV and PDF export functionality
   - Pagination controls

7. **Authentication Fixes (0500d98):**
   - Resolved routing issues
   - Improved error handling

---

## 🔍 Common Operations

### Creating a Document

```python
# API: POST /api/v1/documents/
{
  "title": "Quality Policy",
  "description": "Company quality policy document",
  "document_type": 1,  # POLICY
  "document_source": 1,  # Original Digital
  "file": <uploaded_file>,
  "dependencies[]": [2, 5, 7]  # Array of document IDs
}
```

### Upversioning a Document

```python
# API: POST /api/v1/documents/{uuid}/create_version/
{
  "major_increment": false,  # true for major, false for minor
  "reason_for_change": "Updated references section",
  "change_summary": "Added 3 new references to industry standards"
}

# Result:
# - New document created with incremented version
# - Dependencies smart-copied (resolved to latest effective)
# - New document in DRAFT status
# - Old document remains EFFECTIVE until new version approved
```

### Obsoleting a Document

```python
# API: POST /api/v1/workflows/obsolete_directly/
{
  "document_uuid": "...",
  "reason": "Superseded by new policy framework",
  "obsolescence_date": "2026-03-01"
}

# Validation:
# - User must be approver or admin
# - Document must be EFFECTIVE
# - No active dependencies
# - No newer versions in development
# - Obsolescence date must be future
```

---

## 🚀 Next Steps for Development

**Suggested Enhancements:**

1. **Multi-format Document Processing:**
   - Native .docx placeholder processing (✅ implemented)
   - PDF annotation (planned)
   - Excel template processing (planned)

2. **Advanced Search:**
   - Full-text search with PostgreSQL
   - Faceted search by type, status, date ranges

3. **Email Notifications:**
   - Configured SMTP server
   - Workflow notification emails
   - Scheduled digest emails

4. **Training Module:**
   - Document-required training tracking
   - Training completion records
   - Compliance reporting

5. **E-Signature Enhancement:**
   - Digital signature verification
   - Certificate-based signing
   - Signature appearance customization

---

## 📚 Key Documentation Files

- `EDMS_WORKFLOWS_EXPLAINED.md` - Detailed workflow documentation
- `CURRENT_WORKFLOW_ARCHITECTURE_2025.md` - System architecture overview
- `DOCUMENT_DEPENDENCY_UPVERSION_FIX.md` - Upversioning implementation details
- `AGENTS.md` - Workspace memory and development patterns
- `README.md` - Project overview and setup instructions
- `Dev_Docs/` - Developer documentation directory

---

## 🎓 Understanding Summary

You now understand:

✅ **System Architecture:** Django + React + Celery with Docker deployment  
✅ **4 Core Workflows:** Review, Up-versioning, Obsolescence, Termination  
✅ **Version Control:** Document families, smart dependency copying  
✅ **Scheduler System:** Celery tasks for automation (effective dates, obsolescence)  
✅ **Deployment:** Interactive script, Docker Compose, HAProxy  
✅ **Security:** RBAC, admin bypass, 21 CFR Part 11 compliance  
✅ **Recent Changes:** Admin improvements, integrity checks, upversioning

**Key Insight:** The system prioritizes **regulatory compliance** and **audit trail integrity** while maintaining **developer-friendly** workflows and **automated lifecycle management**.

