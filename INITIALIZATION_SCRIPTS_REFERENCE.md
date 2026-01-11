# EDMS Initialization Scripts - Complete Reference

**Date:** 2026-01-10  
**Purpose:** Complete list of all deployment and initialization scripts  
**Status:** Ready to use

---

## 📋 **Quick Answer: YES - Scripts Exist for Everything!**

✅ **Document Types** - `create_default_document_types`  
✅ **Document Sources** - `create_default_document_sources`  
✅ **Placeholders** - `setup_placeholders_simple`  
✅ **All-in-One Script** - `initialize-all-defaults.sh`

---

## 🚀 **Main Initialization Scripts**

### **1. Initialize All Defaults (RECOMMENDED)**
**Script:** `scripts/initialize-all-defaults.sh`  
**Purpose:** One-click setup for all default data  
**Usage:**
```bash
./scripts/initialize-all-defaults.sh
```

**What it creates:**
- ✅ 7 Roles (Document Admin, Approver, Reviewer, Author, Viewer, User Admin, Placeholder Admin)
- ✅ 6 Django Groups (Document Admins, Reviewers, Approvers, etc.)
- ✅ 6 Document Types (POL, SOP, WI, MAN, FRM, REC)
- ✅ 3 Document Sources (Original Digital Draft, Scanned Original, Scanned Copy)

**Calls these management commands:**
1. `create_default_roles`
2. `create_default_groups`
3. `create_default_document_types`
4. `create_default_document_sources`

---

### **2. Initialize Database (COMPREHENSIVE)**
**Script:** `scripts/initialize-database.sh`  
**Purpose:** Complete database setup with all system data  
**Usage:**
```bash
./scripts/initialize-database.sh
```

**What it creates:**
- ✅ All default data from script #1
- ✅ Workflow states and transitions
- ✅ System settings
- ✅ Sample documents
- ✅ Test users (optional)

---

## 🎯 **Individual Django Management Commands**

### **Document Types**
**Command:** `create_default_document_types`  
**File:** `backend/apps/documents/management/commands/create_default_document_types.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_types
```

**Creates 6 Document Types:**

| Code | Name | Prefix | Description | Approval | Review |
|------|------|--------|-------------|----------|--------|
| POL | Policy | POL | Company policies and procedures | ✅ | ✅ |
| SOP | Standard Operating Procedure | SOP | Step-by-step procedures | ✅ | ✅ |
| WI | Work Instruction | WI | Detailed work instructions | ✅ | ✅ |
| MAN | Manual | MAN | User/training manuals | ✅ | ✅ |
| FRM | Form | FRM | Business forms and templates | ✅ | ✅ |
| REC | Record | REC | Business records | ❌ | ❌ |

**Features:**
- Smart creation/update logic (idempotent)
- Retention period defaults
- Template requirements
- Approval/review flags

---

### **Document Sources**
**Command:** `create_default_document_sources`  
**File:** `backend/apps/documents/management/commands/create_default_document_sources.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_sources
```

**Creates 3 Document Sources:**

| Name | Type | Verification | Signature | Description |
|------|------|--------------|-----------|-------------|
| Original Digital Draft | original_digital | ❌ | ❌ | Original digital draft uploaded to EDMS |
| Scanned Original | scanned_original | ✅ | ✅ | Scanned from paper original with wet signature |
| Scanned Copy | scanned_copy | ✅ | ❌ | Scanned copy of document |

**Features:**
- Verification requirements
- Signature requirements
- Traceability options
- Active/inactive status

---

### **Placeholders (32 Standard Placeholders)**
**Command:** `setup_placeholders_simple`  
**File:** `backend/apps/placeholders/management/commands/setup_placeholders_simple.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_placeholders_simple
```

**Creates 32 Placeholders:**

#### Document Metadata (10)
- `DOCUMENT_NUMBER` - Unique document identifier
- `DOCUMENT_TITLE` - Full document title
- `DOCUMENT_VERSION` - Version number (e.g., 1.0)
- `DOCUMENT_TYPE` - Type code (POL, SOP, etc.)
- `DOCUMENT_DESCRIPTION` - Brief description
- `AUTHOR` - Document author name
- `EFFECTIVE_DATE` - Date when effective
- `REVISION_NUMBER` - Current revision
- `OBSOLETE_DATE` - Date when obsoleted
- `NEXT_REVIEW_DATE` - Scheduled review date

#### Organization (5)
- `ORGANIZATION` - Organization name
- `DEPARTMENT` - Department name
- `LOCATION` - Physical location
- `SITE` - Site identifier
- `FACILITY` - Facility name

#### Workflow & Status (8)
- `APPROVAL_DATE` - Date approved
- `APPROVER_NAME` - Approver's name
- `APPROVER_TITLE` - Approver's title
- `REVIEWER_NAME` - Reviewer's name
- `REVIEWER_TITLE` - Reviewer's title
- `CURRENT_STATUS` - Document status
- `WORKFLOW_STAGE` - Current workflow stage
- `WORKFLOW_HISTORY` - Complete workflow history

#### Dates & Timestamps (5)
- `CURRENT_DATE` - Today's date
- `CURRENT_DATETIME` - Current date and time
- `CREATED_DATE` - Document creation date
- `MODIFIED_DATE` - Last modified date
- `GENERATED_DATE` - PDF generation date

#### System & Technical (4)
- `SYSTEM_VERSION` - EDMS version
- `PAGE_NUMBER` - Current page number
- `TOTAL_PAGES` - Total page count
- `QR_CODE` - QR code for document

**Features:**
- Type-aware (TEXT, DATE, USER, etc.)
- Data source mapping (from Document model, User model, etc.)
- Default values
- Date formatting options

---

### **User Roles**
**Command:** `create_default_roles`  
**File:** `backend/apps/users/management/commands/create_default_roles.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_roles
```

**Creates 7 Roles:**
1. Document Admin (S2/admin)
2. Document Approver (S2/approver)
3. Document Reviewer (S2/reviewer)
4. Document Author (S2/author)
5. Document Viewer (S2/viewer)
6. User Admin (S1/admin)
7. Placeholder Admin (S6/admin)

---

### **User Groups**
**Command:** `create_default_groups`  
**File:** `backend/apps/users/management/commands/create_default_groups.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_groups
```

**Creates 6 Groups:**
1. Document Admins
2. Document Reviewers
3. Document Approvers
4. Senior Document Approvers
5. Document_Reviewers
6. Document_Approvers

---

### **Workflows**
**Command:** `setup_simple_workflows`  
**File:** `backend/apps/workflows/management/commands/setup_simple_workflows.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_simple_workflows
```

**Creates:**
- Workflow states (DRAFT, UNDER_REVIEW, APPROVED, EFFECTIVE, etc.)
- Workflow transitions
- State permissions
- Workflow types

---

### **Scheduler Tasks**
**Command:** `setup_scheduled_tasks`  
**File:** `backend/apps/scheduler/management/commands/setup_scheduled_tasks.py`  
**Usage:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_scheduled_tasks
```

**Creates:**
- Periodic tasks for document activation
- Scheduled cleanup tasks
- Notification tasks

---

## 📦 **All Management Commands Available**

### Documents App
- `create_default_document_types` - Create 6 document types
- `create_default_document_sources` - Create 3 document sources
- `check_circular_dependencies` - Validate document dependencies

### Placeholders App
- `setup_placeholders` - Full placeholder setup (32 placeholders)
- `setup_placeholders_simple` - Simplified placeholder setup

### Users App
- `create_default_roles` - Create 7 system roles
- `create_default_groups` - Create 6 Django groups
- `seed_test_users` - Create test users

### Workflows App
- `setup_workflows` - Full workflow setup
- `setup_simple_workflows` - Simplified workflow setup
- `update_workflow_states` - Update existing workflow states

### Scheduler App
- `setup_scheduled_tasks` - Set up Celery Beat tasks
- `setup_scheduler` - Full scheduler setup
- `activate_pending_documents` - Manual document activation
- `cleanup_workflow_tasks` - Clean up old tasks

### Security App
- `setup_electronic_signatures` - Set up e-signature system

### Admin Pages App
- `validate_data_lifecycle` - Validate document lifecycle data

---

## 🎯 **Recommended Deployment Sequence**

### **For Fresh Installation:**

```bash
# 1. Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 2. Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 3. Initialize all defaults (ONE COMMAND!)
./scripts/initialize-all-defaults.sh

# 4. Set up placeholders
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_placeholders_simple

# 5. Set up workflows
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_simple_workflows

# 6. Set up scheduled tasks
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_scheduled_tasks

# 7. Optionally create test users
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_test_users
```

### **For Existing Installation (Update Only):**

```bash
# Just run the all-in-one script
./scripts/initialize-all-defaults.sh

# It's idempotent - won't duplicate existing data
```

---

## 🔧 **Deployment Scripts**

### Production Deployment
- `deploy-production.sh` - Full production deployment
- `deploy-to-remote.sh` - Deploy to remote server
- `quick-prod-deploy.sh` - Quick production update

### Staging Deployment
- `setup-staging-env.sh` - Set up staging environment
- `setup-haproxy-staging.sh` - Configure HAProxy for staging

### Verification
- `pre-deploy-check.sh` - Pre-deployment validation
- `post-deploy-check.sh` - Post-deployment verification
- `verify-haproxy-setup.sh` - Verify HAProxy configuration

### Utilities
- `create-test-users.sh` - Create test user accounts
- `create-production-package.sh` - Package for deployment
- `setup-backup-cron.sh` - Configure automated backups

---

## 💡 **Usage Tips**

### **1. Check What Already Exists**
```bash
# Check document types
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from apps.documents.models import DocumentType
>>> DocumentType.objects.all().count()
>>> list(DocumentType.objects.values_list('code', 'name'))

# Check document sources
>>> from apps.documents.models import DocumentSource
>>> DocumentSource.objects.all().count()

# Check placeholders
>>> from apps.placeholders.models import PlaceholderDefinition
>>> PlaceholderDefinition.objects.all().count()
```

### **2. All Commands Are Idempotent**
You can run them multiple times safely. They will:
- Create missing items
- Update existing items if different
- Skip unchanged items

### **3. Verify After Running**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend --tail 50

# Test in browser
# Go to: http://localhost:3001/admin
# Create a document and check dropdowns
```

---

## 📊 **Summary Table**

| What | Management Command | Shell Script |
|------|-------------------|--------------|
| **Document Types** | `create_default_document_types` | Part of `initialize-all-defaults.sh` |
| **Document Sources** | `create_default_document_sources` | Part of `initialize-all-defaults.sh` |
| **Placeholders** | `setup_placeholders_simple` | Separate (run after) |
| **Roles** | `create_default_roles` | Part of `initialize-all-defaults.sh` |
| **Groups** | `create_default_groups` | Part of `initialize-all-defaults.sh` |
| **Everything** | Multiple commands | `initialize-database.sh` |

---

## ✅ **What Gets Created Summary**

After running `initialize-all-defaults.sh` + `setup_placeholders_simple`:

- ✅ **7 Roles** - Permission management
- ✅ **6 Groups** - User organization
- ✅ **6 Document Types** - POL, SOP, WI, MAN, FRM, REC
- ✅ **3 Document Sources** - Digital, Scanned Original, Scanned Copy
- ✅ **32 Placeholders** - Complete metadata replacement system

**Total time:** ~2 minutes  
**User interaction:** Minimal (just confirm prompts)  
**Risk:** Very low (idempotent, can be run multiple times)

---

## 🎯 **For Your Current Situation**

Since you're experiencing document creation errors, run this NOW:

```bash
# On your local machine OR staging server:
cd /path/to/edms
./scripts/initialize-all-defaults.sh
```

This will ensure all document types and sources exist, fixing the dropdown population issues.

---

**Status:** ✅ COMPLETE REFERENCE  
**All Scripts Documented:** YES  
**Ready to Use:** YES

**Last Updated:** 2026-01-10 17:35 SGT
