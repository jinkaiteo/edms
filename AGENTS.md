# EDMS Development Agent Guidelines

## Project Overview

### Purpose
21 CFR Part 11 compliant Electronic Document Management System (EDMS) for regulated industries like pharmaceuticals. Focuses on secure, on-premise deployment with complete document lifecycle management.

### Core Technologies
- **Backend**: Django 4.2 + Django REST Framework + Enhanced Simple Workflow Engine
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL 18 with encryption + full-text search
- **Cache**: Redis 7+ for sessions and task queues
- **Containers**: Docker with multi-container deployment
- **Authentication**: Entra ID integration support
- **Document Processing**: python-docx-template, PyPDF2, Tesseract

### Architecture Decision
- **HTTP-only internal deployment** (simplified from HTTPS for easier setup)
- **PostgreSQL full-text search** (simplified from Elasticsearch)
- **On-premise deployment** with Ubuntu 20.04.6 LTS Server
- **Modular approach** with operational (O1) and service modules (S1-S7)

## Current Project Status

### Implementation Phase
- ✅ **Architecture & documentation complete** - comprehensive technical specs ready
- ✅ **Repository setup** - clean structure with proper documentation
- ⏳ **Code implementation** - not yet started (planning phase complete)
- ⏳ **Development environment** - containers and scripts to be created

### Expected Project Structure
```
edms/
├── backend/                # Django application (to be created)
│   ├── edms/              # Django project
│   ├── apps/              # Django apps (documents, users, workflows)
│   └── requirements/      # Python dependencies
├── frontend/              # React application (to be created)
│   ├── src/              # React components and pages
│   └── public/           # Static assets
├── infrastructure/        # Container configs (to be created)
├── scripts/              # Automation scripts (to be created)
├── Dev_Docs/            # ✅ Complete technical documentation
└── storage/             # Document storage (encrypted, to be created)
```

## Key Documentation Files

### Essential Reading
- `README.md` - Project overview and quick start
- `Dev_Docs/EDMS_details.txt` - Core system requirements
- `Dev_Docs/1_EDMS_Database_Schema_Complete.md` - Complete database design
- `Dev_Docs/7_Django_Models_Implementation.md` - Django model specifications
- `Dev_Docs/EDMS_Placeholder_Metadata_Pairs.md` - Document placeholder system

### Implementation Guides
- `Dev_Docs/6_Environment_Setup_Scripts.md` - Setup automation scripts
- `Dev_Docs/2_EDMS_API_Specifications.md` - REST API design
- `Dev_Docs/3_Enhanced_Simple_Workflow_Setup.md` - Custom Workflow Engine configuration
- `Dev_Docs/Missing_Configuration_Templates.md` - Config templates

### Security & Compliance
- `SECURITY.md` - Security policies and vulnerability reporting
- `Dev_Docs/4_Authentication_Integration.md` - Auth implementation
- All features must comply with **21 CFR Part 11** and **ALCOA principles**

## Development Conventions

### Code Organization
- **Modular architecture**: Operational module O1 + Service modules S1-S7
- **App structure**: Separate Django apps for documents, users, workflows, audit, etc.
- **API design**: RESTful endpoints following specification in `2_EDMS_API_Specifications.md`

### Database Conventions
- **Primary keys**: Use Django's default auto-incrementing IDs
- **UUIDs**: Add UUID fields for external references and security
- **Audit trail**: All model changes must be tracked (S2 module)
- **Encryption**: Sensitive document data encrypted at rest

### Document Management
- **Placeholder system**: Use `{{PLACEHOLDER_NAME}}` format for document templates
- **File processing**: Support .docx (python-docx-template), PDF (PyPDF2), OCR (Tesseract)
- **Version control**: Major.minor versioning (e.g., 1.2)
- **Workflow states**: Draft → Review → Approval → Effective → (Superseded/Obsolete)

### Security Requirements
- **Role-based permissions**: read, write, review, approve, admin levels
- **Audit logging**: All database modifications must be recorded
- **Input validation**: Comprehensive validation for all user inputs
- **Session security**: Secure session management with Redis
- **File integrity**: SHA-256 checksums for all documents

## Test Users and Data

### Default Test Accounts (from EDMS_Test_Users_Credentials.md)
- **Document Admin**: `docadmin` / `EDMSAdmin2024!`
- **Document Author**: `author` / `AuthorPass2024!`
- **Document Reviewer**: `reviewer` / `ReviewPass2024!`
- **Document Approver**: `approver` / `ApprovePass2024!`
- **Placeholder Admin**: `placeholderadmin` / `PlaceholderAdmin2024!`

### Test Data Categories
- Test documents for each document type (Policy, Manual, Procedures, SOP, Forms, Records)
- Workflow scenarios (review, approval, up-versioning, obsoleting)
- Permission testing across different user roles

## API Design Patterns

### Endpoint Structure
- **Base URL**: `/api/v1/`
- **Authentication**: JWT-based API authentication
- **Modules**: `/documents/`, `/users/`, `/workflows/`, `/audit/`, etc.
- **Standard responses**: Consistent error handling and response formats

### Key API Modules
1. **Documents API** (`/api/v1/documents/`) - CRUD operations, workflow actions
2. **Users API** (`/api/v1/users/`) - User management, roles, permissions
3. **Workflows API** (`/api/v1/workflows/`) - Workflow state management
4. **Audit API** (`/api/v1/audit/`) - Compliance and audit trail access

## Compliance Requirements

### 21 CFR Part 11 Implementation
- **Electronic records**: Complete metadata tracking
- **Electronic signatures**: Secure signature validation
- **Audit trails**: Tamper-proof activity logging
- **Access controls**: Role-based permission system
- **System validation**: Documented validation process

### ALCOA Principles
- **Attributable**: All actions linked to authenticated users
- **Legible**: Clear, readable audit trails and records
- **Contemporaneous**: Real-time activity logging
- **Original**: Tamper-proof record keeping with checksums
- **Accurate**: Data validation and integrity checks

## Development Workflow

### Git Conventions
- **Main branch**: `main` (protected, requires PR)
- **Feature branches**: `feature/module-name` or `feature/issue-number`
- **Commit format**: Use conventional commits (feat:, fix:, docs:, etc.)

### Testing Requirements
- **Backend**: pytest with coverage for Django apps
- **Frontend**: Jest + React Testing Library
- **E2E**: Playwright for end-to-end testing
- **Compliance**: Specific tests for regulatory requirements

### CI/CD Pipeline (`.github/workflows/ci.yml`)
- **Python 3.11** for backend development
- **Node.js 18+** for frontend development
- **Automated testing** on push/PR
- **Security scanning** and dependency checks

## Environment Setup

### Development Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 18
- Redis 7+

### Key Scripts (to be created in `/scripts/`)
- `infrastructure-setup.sh` - Initial environment setup
- `start-development.sh` - Start dev environment
- `initialize-database.sh` - Database setup and migrations
- `create-test-users.sh` - Create test user accounts

## Important Security Notes

### Development vs Production
- **Development**: HTTP-only for internal deployment simplicity
- **Production**: Should implement HTTPS with proper certificates
- **Never commit**: Certificates, private keys, production secrets

### Sensitive Files (in `.gitignore`)
- `storage/` - Document storage directory
- `certificates/`, `*.key`, `*.crt`, `*.pem` - Certificate files
- `.env*` files - Environment configurations (except `.env.example`)

## Module Implementation Priority

### Phase 1: Core Infrastructure
1. **Django project setup** with apps structure
2. **Database models** implementation (S1, S2, O1 core)
3. **Basic authentication** and user management
4. **Document upload/storage** functionality

### Phase 2: Workflow Engine
1. **Enhanced Simple Workflow Engine integration** for workflow management
2. **Document lifecycle** implementation (Draft → Effective)
3. **Role-based permissions** system
4. **Audit trail** logging (S2 module)

### Phase 3: Document Processing
1. **Placeholder replacement** system (S6 module)
2. **PDF generation** and digital signatures
3. **Search functionality** with PostgreSQL full-text
4. **Document versioning** and dependencies

### Phase 4: Frontend & UI
1. **React application** with TypeScript setup
2. **User dashboard** and document management UI
3. **Workflow interfaces** for review/approval
4. **Responsive design** with Tailwind CSS

## Common Pitfalls to Avoid

### Security
- Never expose debug information in production
- Always validate user inputs and permissions
- Implement proper error handling without information leakage
- Maintain audit trails for all database modifications

### Compliance
- Document workflow state changes must be atomic
- Audit records must be tamper-proof and timestamped
- Electronic signatures require proper validation chains
- All user actions must be attributable and logged

### Performance
- Use database indexes for frequently queried fields
- Implement proper caching strategies with Redis
- Optimize document file handling for large files
- Consider pagination for large document lists

## Getting Help

### Documentation Hierarchy
1. **This AGENTS.md file** - Development guidelines
2. **Dev_Docs/** - Detailed technical specifications
3. **README.md** - Project overview and quick start
4. **SECURITY.md** - Security policies and practices

### Key Contacts (from SECURITY.md)
- **Security Team**: security@edms-project.com
- **Compliance Officer**: compliance@edms-project.com
- **Development Lead**: dev@edms-project.com

---

**Remember**: This is a regulated industry application. Security, compliance, and audit requirements are not optional - they are core functional requirements that must be implemented correctly from the start.