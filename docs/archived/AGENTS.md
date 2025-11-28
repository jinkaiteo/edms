# EDMS Development Guidelines

## Project Overview

### Purpose
**21 CFR Part 11 compliant Electronic Document Management System (EDMS)** for regulated industries like pharmaceuticals. Designed for secure, on-premise deployment with complete document lifecycle management including up-versioning, obsolescence workflows, and comprehensive audit trails.

### Core Technologies
- **Backend**: Django 4.2 + Django REST Framework + Enhanced Simple Workflow Engine
- **Frontend**: React 18 + TypeScript + Tailwind CSS 
- **Database**: PostgreSQL 18 with full-text search and encryption
- **Cache & Tasks**: Redis 7+ for sessions, task queues, and caching
- **Containers**: Docker with multi-container deployment via docker-compose
- **Authentication**: JWT + Entra ID integration support
- **Document Processing**: python-docx-template, PyPDF2, Tesseract OCR
- **Testing**: Playwright for E2E, pytest for backend, Jest for frontend

### Architecture Decisions
- **HTTP-only internal deployment** (simplified from HTTPS for development)
- **PostgreSQL full-text search** (simplified from Elasticsearch)
- **On-premise Ubuntu 20.04.6 LTS Server** deployment target
- **Enhanced Simple Workflow Engine** instead of complex workflow libraries
- **Modular approach** with operational (O1) and service modules (S1-S7)

## Current Implementation Status

### ✅ Completed Features
- **Core workflow system** - Review, approval, up-versioning, supersession
- **Document management** - Upload, versioning, grouped view with version history
- **User authentication** - JWT-based with role permissions
- **Audit trail** - Complete 21 CFR Part 11 compliant logging
- **Document downloads** - Original, annotated, official PDF with digital signatures
- **Frontend UI** - Professional React interface with accordion version history
- **Test users** - Complete set of role-based test accounts

### 🔄 In Progress
- **Obsolete workflow** - Mark documents obsolete with dependency checking
- **Termination workflow** - Cancel workflows before approval
- **Enhanced notifications** - Email alerts for workflow events

### Project Structure
```
edms/
├── backend/                # ✅ Django application (COMPLETE)
│   ├── edms/              # Django project settings
│   ├── apps/              # Django apps (documents, users, workflows, audit, etc.)
│   ├── requirements/      # Python dependencies by environment
│   └── fixtures/          # Initial data and test users
├── frontend/              # ✅ React application (COMPLETE)
│   ├── src/              # React components, pages, hooks, contexts
│   └── public/           # Static assets
├── infrastructure/        # ✅ Container configurations
├── scripts/              # ✅ Automation and deployment scripts
├── Dev_Docs/            # ✅ Complete technical documentation
├── tests/               # ✅ E2E Playwright tests
└── test_doc/           # Sample documents for testing
```

## Essential Documentation

### Core System Requirements
- `README.md` - Project overview and quick start guide
- `Dev_Docs/EDMS_details.txt` - Complete system requirements and workflows
- `Dev_Docs/1_EDMS_Database_Schema_Complete.md` - Database design
- `SECURITY.md` - Security policies and 21 CFR Part 11 compliance

### Implementation Guides
- `Dev_Docs/2_EDMS_API_Specifications.md` - REST API design patterns
- `Dev_Docs/3_Enhanced_Simple_Workflow_Setup.md` - Workflow engine configuration
- `Dev_Docs/7_Django_Models_Implementation.md` - Django model specifications
- `CONTRIBUTING.md` - Development workflow and coding standards

### Authentication & Testing
- `QUICK_LOGIN_CREDENTIALS.md` - Current test user credentials (password: `test123`)
- `Dev_Docs/EDMS_Test_Users_Credentials.md` - Complete test user matrix
- `UAT_QUICK_START_GUIDE.md` - User acceptance testing procedures

## Development Standards

### Code Organization
- **Modular Django architecture**: Separate apps for documents, users, workflows, audit
- **Enhanced Simple Workflow Engine**: Custom workflow implementation in `apps/workflows/`
- **API-first design**: RESTful endpoints with consistent response formats
- **Component-based frontend**: Reusable React components with TypeScript

### Database Conventions
- **Auto-incrementing primary keys**: Use Django defaults
- **UUID fields**: For external references and security (`uuid` field on all main models)
- **Audit trail**: All model changes tracked via signals in `apps/audit/`
- **Versioned document numbering**: `{BASE}-v{MAJOR}.{MINOR}` format

### Document Management Conventions
- **Document types**: Policy, Manual, Procedures, SOP, Forms, Records
- **Document sources**: Original Digital Draft, Scanned Original, Scanned Copy  
- **Workflow states**: `DRAFT` → `PENDING_REVIEW` → `UNDER_REVIEW` → `REVIEWED` → `PENDING_APPROVAL` → `APPROVED_AND_EFFECTIVE` → `SUPERSEDED`/`OBSOLETE`
- **Version control**: Automatic supersession when new versions become effective

### Security & Compliance
- **Role-based permissions**: read, write, review, approve, admin levels
- **Complete audit logging**: All database modifications recorded with user attribution
- **Input validation**: Comprehensive validation at API and model levels
- **File integrity**: SHA-256 checksums for all uploaded documents
- **21 CFR Part 11**: Electronic signatures, tamper-proof audit trails, access controls

## Test Users & Development

### Standard Test Credentials
**All test users use password: `test123`**

| Username | Role | Department | Capabilities |
|----------|------|------------|-------------|
| `admin` | System Admin | IT Systems | Full superuser access |
| `author01`/`author02` | Document Author | QA/Regulatory | Create & edit documents |
| `reviewer01`/`reviewer02` | Document Reviewer | QA/Regulatory | Review documents |
| `approver01`/`approver02` | Document Approver | QA/Regulatory | Approve documents |

### Quick Testing Workflow
1. **Login as `author01`** → Create document → Submit for review
2. **Login as `reviewer01`** → Review and approve document
3. **Login as `author01`** → Route document for approval  
4. **Login as `approver01`** → Approve and set effective date
5. **Test up-versioning** → Create new version → Complete workflow

### Development Environment
```bash
# Start development environment
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000  
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

## API Design Patterns

### REST Endpoints Structure
- **Base URL**: `/api/v1/`
- **Authentication**: JWT Bearer tokens
- **Documents**: `/api/v1/documents/documents/` (CRUD + workflow actions)
- **Workflows**: `/api/v1/workflows/documents/{uuid}/` (workflow state management)
- **Users**: `/api/v1/users/` (user management)
- **Audit**: `/api/v1/audit/` (audit trail access)

### Standard Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "errors": []
}
```

### Workflow Actions
- `start_review` - Begin review workflow
- `submit_for_review` - Submit to reviewer
- `complete_review` - Complete review process
- `route_for_approval` - Send to approver
- `approve_document` - Approve with effective date
- `start_version_workflow` - Create new document version
- `terminate_workflow` - Cancel workflow before approval

## Document Features

### Document States & Visibility
- **DRAFT** - Visible only to author
- **PENDING_REVIEW** - Visible to author + assigned reviewer
- **APPROVED_AND_EFFECTIVE** - Visible to all authenticated users
- **SUPERSEDED** - Visible via version history accordion UI

### Download Types
1. **Original Document** - Unmodified uploaded file
2. **Annotated Document** - With metadata placeholders replaced
3. **Official PDF** - Digitally signed PDF with full metadata annotation

### Grouped Document View
- Documents grouped by base number (e.g., `FORM-2025-0001`)
- Current version displayed prominently with "Current Version" badge
- Previous versions accessible via expandable accordion interface
- Professional status indicators and icons

## Workflow Implementation

### Review Workflow (✅ Complete)
- Author creates document → Reviewer reviews → Approver approves → Becomes effective
- Full audit trail and email notifications
- Status transitions with proper validation

### Up-versioning Workflow (✅ Complete)  
- Create new version from effective document
- Automatic supersession when new version becomes effective
- Proper version numbering with major/minor increments
- Notification to dependent document owners

### Document Lifecycle Service
Located in `backend/apps/workflows/document_lifecycle.py`:
- `start_version_workflow()` - Creates new document versions
- `complete_versioning()` - Handles supersession logic
- `start_obsolete_workflow()` - Initiates obsolescence with dependency checks
- `terminate_workflow()` - Returns document to last approved state

## Frontend Architecture

### Component Structure
```
frontend/src/
├── components/
│   ├── documents/          # Document management UI
│   ├── workflows/          # Workflow interfaces  
│   ├── common/            # Shared components
│   └── audit/             # Audit trail viewer
├── contexts/              # React contexts (Auth, Toast)
├── hooks/                 # Custom React hooks
├── pages/                 # Main page components
└── services/             # API service layer
```

### Key Components
- **DocumentList.tsx** - Grouped document view with version history
- **DocumentViewer.tsx** - Document details with workflow actions
- **CreateNewVersionModal.tsx** - Up-versioning interface
- **SubmitForReviewModal.tsx** - Review workflow initiation
- **ApproverInterface.tsx** - Document approval interface

## Development Workflow

### Git Conventions
- **Main branch**: `main` (protected, requires PR)
- **Feature branches**: `feature/description` or `fix/description`
- **Commit format**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)

### Testing Strategy
- **Backend**: `pytest` with Django test client
- **Frontend**: Jest + React Testing Library
- **E2E**: Playwright for complete workflow testing
- **Manual**: User acceptance testing scenarios

### Docker Development
- **Backend**: Django development server with hot reload
- **Frontend**: React development server with hot reload  
- **Database**: PostgreSQL with persistent volumes
- **Shared volumes**: For document storage and development

## Security Guidelines

### Development Security
- HTTP-only for internal development (HTTPS for production)
- All sensitive data encrypted at rest
- JWT tokens with proper expiration
- CORS configured for localhost development

### Production Security  
- HTTPS with valid certificates
- Environment variable configuration
- Database encryption
- Regular security scans and dependency updates

### Compliance Requirements (21 CFR Part 11)
- Electronic signatures with validation chains
- Tamper-proof audit trails with timestamps
- Role-based access controls with proper authorization
- Complete document lifecycle tracking

## Common Development Tasks

### Adding New Document Types
1. Update `DocumentType` choices in `backend/apps/documents/models.py`
2. Add corresponding UI options in frontend document creation forms
3. Update API serializers and validation

### Extending Workflows
1. Add new states to `DocumentState` model
2. Implement transition logic in `DocumentLifecycleService`
3. Create frontend interfaces for new workflow steps
4. Add appropriate audit logging

### Testing Workflows
1. Use provided test users with `test123` password
2. Follow complete workflow cycles from creation to effectiveness
3. Test edge cases like workflow termination and document dependencies
4. Verify audit trail entries for compliance

## Troubleshooting

### Common Issues
- **Authentication failures**: Check JWT token storage and API endpoints
- **Permission errors**: Verify user roles and document ownership
- **Version conflicts**: Ensure proper document status before up-versioning
- **Database constraints**: Check for proper foreign key relationships

### Debug Tools
- Django admin interface for database inspection
- Browser developer tools for frontend debugging
- Docker logs for container troubleshooting
- Playwright test reports for E2E test analysis

## Key Contacts & Resources

### Project Information
- **Security Team**: security@edms-project.com
- **Compliance Officer**: compliance@edms-project.com  
- **Development Lead**: dev@edms-project.com

### Documentation References
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [21 CFR Part 11 Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

---

**Important**: This is a regulated industry application. Security, compliance, and audit requirements are core functional requirements that must be implemented correctly from the start. All database modifications must be logged, all user actions must be attributable, and all workflows must maintain complete audit trails.