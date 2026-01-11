# EDMS Application - Current Status & Overview

**Date:** 2026-01-07  
**Environment:** Production Docker Containers (Local Testing)  
**Branch:** `develop`  
**Last Major Update:** Method #2 Backup & Restore System Implementation

---

## 📋 **Application Overview**

### **System Name**
**EDMS** - Electronic Document Management System

### **Purpose**
21 CFR Part 11 Compliant Document Management System for regulated environments (pharmaceutical, medical device, food & beverage industries).

### **Compliance Standards**
- 21 CFR Part 11 (FDA Electronic Records and Signatures)
- Audit trails for all document operations
- Electronic signature support
- Version control and document lifecycle management

---

## 🏗️ **Architecture**

### **Technology Stack**

#### Backend
- **Framework:** Django 4.2+ (Python 3.11)
- **Database:** PostgreSQL 18
- **Cache/Broker:** Redis 7
- **Task Queue:** Celery (Worker + Beat scheduler)
- **API:** Django REST Framework
- **Authentication:** Session + Token-based

#### Frontend
- **Framework:** React 18+ (TypeScript)
- **UI Library:** Tailwind CSS, Heroicons
- **Build Tool:** Create React App
- **State Management:** React Hooks
- **API Communication:** Fetch API

#### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Web Server (Production):** Nginx (in frontend container)
- **Reverse Proxy Option:** HAProxy (for multi-server deployment)
- **Development Server:** Django runserver + React dev server

---

## 🐳 **Current Docker Setup**

### **Running Containers (Production Config)**
```
NAME                      STATUS                 PORTS
edms_prod_backend         Up 5 hours (healthy)   0.0.0.0:8001->8000/tcp
edms_prod_celery_worker   Up 5 hours (healthy)   8000/tcp
edms_prod_celery_beat     Up 5 hours             8000/tcp
edms_prod_db              Up 5 hours (healthy)   0.0.0.0:5432->5432/tcp
edms_prod_frontend        Up 5 hours (healthy)   0.0.0.0:3001->80/tcp
edms_prod_redis           Up 5 hours (healthy)   0.0.0.0:6380->6379/tcp
```

### **Access Points**
- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8001/api/v1/
- **Backend Health:** http://localhost:8001/health/
- **Database:** localhost:5432
- **Redis:** localhost:6380

### **Docker Compose Files**
1. **`docker-compose.yml`** - Development environment (ports 3000, 8000, 5432, 6379)
2. **`docker-compose.prod.yml`** - Production-like environment (ports 3001, 8001, 5432, 6380)

---

## 📁 **Repository Structure**

### **Key Directories**

```
QMS_04/
├── backend/                      # Django application
│   ├── apps/                     # Django apps
│   │   ├── admin_pages/         # Admin dashboard
│   │   ├── api/                 # REST API endpoints
│   │   ├── audit/               # Audit trail system
│   │   ├── documents/           # Document management
│   │   ├── placeholders/        # Document placeholder system
│   │   ├── scheduler/           # Celery tasks & scheduled jobs
│   │   ├── security/            # Electronic signatures, encryption
│   │   ├── users/               # User management & roles
│   │   └── workflows/           # Document workflow engine
│   ├── edms/                    # Django project settings
│   │   └── settings/            # Environment-specific settings
│   └── requirements/            # Python dependencies
│
├── frontend/                     # React application
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API service layer
│   │   └── utils/               # Utility functions
│   └── public/                  # Static assets
│
├── infrastructure/               # Deployment configuration
│   ├── containers/              # Dockerfiles
│   ├── nginx/                   # Nginx configurations
│   └── haproxy/                 # HAProxy configurations
│
├── scripts/                      # Deployment & utility scripts
├── e2e/                         # Playwright end-to-end tests
├── tests/                       # Additional test suites
├── docs/                        # Documentation
└── Dev_Docs/                    # Development documentation
```

---

## 🚀 **Core Features**

### **Document Management**
- ✅ Document upload (DOCX, PDF, TXT, ZIP)
- ✅ Version control (major.minor versioning)
- ✅ Document metadata management
- ✅ Placeholder replacement in documents
- ✅ PDF generation with annotations
- ✅ Document dependencies tracking
- ✅ Document lifecycle management

### **Workflow Engine**
- ✅ Simple workflow states: DRAFT → UNDER_REVIEW → APPROVED → EFFECTIVE
- ✅ Role-based workflow permissions (Author, Reviewer, Approver)
- ✅ Document routing and approval
- ✅ Rejection with comments
- ✅ Workflow history tracking
- ✅ Scheduled effective date activation

### **User Management**
- ✅ Custom user model with roles
- ✅ Role-based access control (RBAC)
- ✅ User groups: Authors, Reviewers, Approvers
- ✅ Session-based authentication
- ✅ Token-based API authentication (in progress)

### **Audit & Compliance**
- ✅ Complete audit trail for all operations
- ✅ Login/logout tracking
- ✅ Document access logging
- ✅ Database change logging
- ✅ PDF audit reports generation
- ✅ Timezone-aware timestamps (UTC + SGT display)

### **Backup & Restore**
- ✅ Method #2: PostgreSQL pg_dump/restore
- ✅ Backup with metadata (timestamp, version, description)
- ✅ Backup validation before restore
- ✅ System reinitialization capability
- ✅ Storage file backup integration

### **Scheduler & Automation**
- ✅ Celery Beat for scheduled tasks
- ✅ Automatic document activation on effective date
- ✅ Notification system
- ✅ Background task processing

### **Placeholder System**
- ✅ 32 standard placeholders (COMPANY_NAME, EFFECTIVE_DATE, etc.)
- ✅ Automatic placeholder replacement in documents
- ✅ Placeholder validation in templates
- ✅ Custom placeholder management

---

## 📊 **Database Schema**

### **Core Models**

#### Users & Permissions
- `User` - Custom user model
- `UserRole` - Role assignments
- `Role` - System roles (Author, Reviewer, Approver)

#### Documents
- `Document` - Main document model
- `DocumentVersion` - Version history
- `DocumentType` - Document categories
- `DocumentSource` - Document origins
- `DocumentDependency` - Inter-document relationships

#### Workflows
- `DocumentWorkflow` - Workflow instances
- `DocumentState` - Workflow states
- `DocumentTransition` - State transitions
- `WorkflowType` - Workflow templates

#### Audit & Security
- `AuditTrail` - Document operation logs
- `LoginAudit` - Authentication logs
- `DocumentAccessLog` - Access tracking
- `DatabaseChangeLog` - Database change tracking
- `ElectronicSignature` - 21 CFR Part 11 signatures

#### System
- `Placeholder` - Template placeholders
- `ScheduledTask` - Celery scheduled tasks
- `SystemSettings` - Application configuration

---

## 🔧 **Recent Development Work**

### **Latest Commit (HEAD)**
```
411324e - WIP: Method #2 Backup & Restore System Implementation
```

### **Recent Major Changes (Last 30 commits)**
1. ✅ Method #2 Backup/Restore implementation (pg_dump)
2. ✅ Backup system documentation
3. ✅ Help system with GitHub Wiki integration
4. ✅ Removal of old backup app (Phase 1-7)
5. ✅ System reinitialization functionality
6. ✅ Restore validation fixes
7. ✅ JWT authentication routing improvements
8. ✅ Staging deployment configuration

### **Key Features Recently Added**
- Method #2 backup system using PostgreSQL native tools
- Comprehensive backup/restore documentation
- GitHub Wiki help system
- System reset capability (CLI)
- Enhanced restore validation
- Timezone consistency (UTC storage, SGT display)

---

## ⚙️ **Configuration**

### **Environment Variables (Key)**
```bash
# Django
DEBUG=True/False
SECRET_KEY=<secret>
DJANGO_SETTINGS_MODULE=edms.settings.development|production

# Database
DB_HOST=db
DB_NAME=edms_db
DB_USER=edms_user
DB_PASSWORD=edms_password
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0

# Frontend
REACT_APP_API_URL=/api/v1
PROXY_TARGET=http://backend:8000
```

### **Settings Modules**
- `base.py` - Common settings
- `development.py` - Development environment
- `production.py` - Production environment
- `test.py` - Testing environment

---

## 🧪 **Testing**

### **Test Frameworks**
- **Backend:** pytest, Django TestCase
- **Frontend:** React Testing Library
- **E2E:** Playwright
- **API:** Direct API testing scripts

### **Test Locations**
- `backend/apps/*/tests/` - Unit tests
- `e2e/` - End-to-end tests
- `tests/` - Integration tests
- `scripts/test-*.sh` - Testing scripts

---

## 📦 **Deployment**

### **Deployment Scripts**
```bash
scripts/
├── deploy-production.sh          # Production deployment
├── deploy-to-remote.sh           # Remote server deployment
├── setup-staging-env.sh          # Staging environment setup
├── setup-haproxy-staging.sh      # HAProxy configuration
├── pre-deploy-check.sh           # Pre-deployment validation
└── post-deploy-check.sh          # Post-deployment verification
```

### **Deployment Packages**
Recent deployment packages available in:
- `edms-deployment-20260106-091146/`
- `edms-deployment-20260105-222100/`
- `edms-production-20260106-170206/`
- `edms-production-20251224-103733/`

### **Staging Server**
- **IP:** 172.28.1.148
- **Status:** Ready for testing
- **Last Deployment:** 2026-01-03
- **Current State:** Backend healthy, backup/restore system ready

---

## 🔍 **Current Status**

### **✅ Working & Stable**
- Docker containers running healthy
- Backend API operational
- Frontend serving correctly
- Database connectivity
- Celery workers processing tasks
- Health checks passing
- Backup creation functional
- Core CRUD operations

### **⚠️ In Progress / Known Issues**
- JWT authentication routing (some endpoints)
- Token-based authentication refinement
- Web-based system reset (auth issue)
- Some frontend authentication features

### **🔄 Recently Fixed**
- Restore validation errors
- UUID conflict resolution
- Backup format standardization
- Database constraint handling
- Timezone consistency
- Storage permissions

---

## 📝 **Key Documentation Files**

### **Deployment**
- `STAGING_DEPLOYMENT_COMPLETE_20260103.md` - Latest staging status
- `DEPLOYMENT_COMPLETE_GUIDE.md` - Deployment procedures
- `HAPROXY_PRODUCTION_SETUP_GUIDE.md` - HAProxy setup

### **Backup & Restore**
- `docs/BACKUP_RESTORE_METHOD2.md` - Method #2 documentation
- `docs/BACKUP_RESTORE_USER_GUIDE.md` - User guide
- `METHOD2_BACKUP_RESTORE_REFERENCE.md` - Quick reference

### **Development**
- `Dev_Docs/EDMS_Development_Roadmap_Updated.md` - Development roadmap
- `Dev_Docs/EDMS_Requirements_Architecture_Setup.md` - Architecture
- `AGENTS.md` - Development patterns and best practices

### **Testing**
- `WEB_INTERFACE_TESTING_GUIDE.md` - Testing procedures
- `COMPREHENSIVE_FEATURE_TEST_GUIDE.md` - Feature testing

---

## 🎯 **Next Steps for Staging Deployment**

### **Immediate Actions**
1. ✅ Verify all containers healthy (DONE)
2. ✅ Confirm backend API responding (DONE)
3. ✅ Check frontend accessibility (DONE)
4. 🔄 Test user authentication flow
5. 🔄 Verify backup/restore functionality
6. 🔄 Run end-to-end test suite
7. 🔄 Validate workflow operations

### **Pre-Deployment Checklist**
- [ ] Run `scripts/pre-deploy-check.sh`
- [ ] Review uncommitted changes
- [ ] Test backup creation
- [ ] Test restore validation
- [ ] Verify user permissions
- [ ] Check audit trail logging
- [ ] Test document upload/download
- [ ] Verify scheduled tasks

### **Deployment Process**
1. Create deployment package
2. Transfer to staging server
3. Run pre-deployment checks
4. Execute deployment script
5. Run post-deployment verification
6. Perform smoke testing
7. Document any issues

---

## 🔗 **Important Links**

### **GitHub**
- Repository: (configure GitHub remote)
- Wiki: Help documentation location
- Issues: Track bugs and features

### **Local Access**
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001/api/v1/
- API Documentation: http://localhost:8001/api/v1/docs/ (if enabled)

### **Staging Server**
- Server IP: 172.28.1.148
- Access: SSH required
- Status: Ready for deployment testing

---

## 📞 **Support & Maintenance**

### **Logs Location**
- **Docker Logs:** `docker compose -f docker-compose.prod.yml logs [service]`
- **Backend Logs:** Container stdout/stderr
- **Frontend Logs:** Browser console + container logs
- **Celery Logs:** Worker/beat container logs

### **Health Checks**
```bash
# Backend health
curl http://localhost:8001/health/

# Frontend health  
curl http://localhost:3001/health

# Database connectivity
docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_db -c "SELECT 1;"

# Redis connectivity
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### **Common Operations**
```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart service
docker compose -f docker-compose.prod.yml restart backend

# Rebuild service
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# Access container shell
docker compose -f docker-compose.prod.yml exec backend bash

# Django management commands
docker compose -f docker-compose.prod.yml exec backend python manage.py [command]
```

---

## 📈 **Version History**

### **Current Version**
- **Backend:** Django 4.2+
- **Frontend:** 1.0.1
- **Database Schema:** Latest migration
- **Deployment Package:** 20260106-091146

### **Major Milestones**
- Initial development: Phase I complete
- Backup/Restore: Method #2 implemented
- Workflow Engine: Simple workflow operational
- Staging Deployment: Ready for testing
- Production Package: Available for deployment

---

## ✅ **Summary**

**Application Status:** 🟢 **OPERATIONAL - READY FOR STAGING TESTING**

The EDMS application is currently running in production-configured Docker containers on the local development machine. All core services are healthy and operational. The application is ready for comprehensive testing before deployment to the staging server (172.28.1.148).

**Key Strengths:**
- Robust document management capabilities
- Compliance-focused audit system
- Simple yet effective workflow engine
- Containerized architecture for easy deployment
- Comprehensive backup/restore system

**Focus Areas:**
- Complete staging server deployment
- Resolve JWT authentication routing
- Full end-to-end testing
- Performance validation under load
- User acceptance testing preparation

**Last Updated:** 2026-01-07 16:59 SGT  
**Prepared For:** Staging deployment testing and validation
