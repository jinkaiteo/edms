# EDMS System Defaults Summary

## 🎯 **Complete List of System Defaults**

---

## 1️⃣ **Roles (7 total)** 
*Used by: RBAC system for fine-grained permissions*

### Document Management (O1) - 5 roles
| Role | Module | Level | Description |
|------|--------|-------|-------------|
| Document Admin | O1 | admin | Full admin access to document management |
| Document Approver | O1 | approve | Final approval and set effective dates |
| Document Reviewer | O1 | review | Review and approve/reject documents |
| Document Author | O1 | write | Create and edit documents |
| Document Viewer | O1 | read | View approved documents only |

### User Management (S1) - 1 role
| Role | Module | Level | Description |
|------|--------|-------|-------------|
| User Admin | S1 | admin | User management and security |

### Placeholder Management (S6) - 1 role
| Role | Module | Level | Description |
|------|--------|-------|-------------|
| Placeholder Admin | S6 | admin | Manage placeholders |

---

## 2️⃣ **Django Groups (6 total)**
*Used by: Workflow system for document operations*

| Group Name | Purpose |
|------------|---------|
| Document Admins | Administrative access to documents |
| Document Reviewers | Can review documents in workflow |
| Document Approvers | Can approve documents in workflow |
| Senior Document Approvers | Can approve all documents including sensitive |
| Document_Reviewers | Alternative name (underscore version) |
| Document_Approvers | Alternative name (underscore version) |

**Note:** The system checks BOTH space and underscore versions for backward compatibility.

---

## 3️⃣ **Document Types (6 total)**
*Used by: Document categorization and numbering*

| Code | Name | Numbering Prefix | Description | Retention |
|------|------|------------------|-------------|-----------|
| **POL** | Policy | POL | Company policies and governance | 7 years |
| **SOP** | Standard Operating Procedure | SOP | Standard operating procedures | 5 years |
| **WI** | Work Instruction | WI | Detailed work instructions | 5 years |
| **MAN** | Manual | MAN | User manuals and handbooks | 5 years |
| **FRM** | Form | FRM | Forms and templates | 3 years |
| **REC** | Record | REC | Business records and completed forms | 7 years |

**Approval Requirements:**
- POL, SOP, WI, MAN, FRM: Require review AND approval
- REC: No review/approval required (records are already final)

---

## 4️⃣ **Document Sources (3 total)**
*Used by: Tracking document origin for compliance*

| Name | Source Type | Verification | Signature | Description |
|------|-------------|--------------|-----------|-------------|
| **Original Digital Draft** | original_digital | No | No | Born-digital documents uploaded to EDMS |
| **Scanned Original** | scanned_original | Yes | No | Scanned from original physical document |
| **Scanned Copy** | scanned_copy | Yes | No | Scanned from photocopy of original |

**Verification Requirements:**
- Original Digital: No verification needed (born digital)
- Scanned sources: Verification required to ensure scan quality

---

## 🚀 **Initialization Commands**

### Individual Commands
```bash
# Roles
python manage.py create_default_roles

# Django Groups  
python manage.py create_default_groups

# Document Types
python manage.py create_default_document_types

# Document Sources
python manage.py create_default_document_sources
```

### All-in-One Script (Recommended)
```bash
bash scripts/initialize-all-defaults.sh
```

---

## 📊 **Why These Specific Defaults?**

### Roles: 7 Essential Roles
Based on `seed_test_users.py` and actual system usage. These are the core roles protected by the backup/restore system.

### Groups: 6 for Workflow
Based on actual workflow code that checks for these specific group names when determining permissions for review/approval.

### Document Types: 6 Core Types
Based on `system_reinit.py` canonical types and ISO 9001/quality management system standards:
- **POL**: High-level governance
- **SOP**: Process documentation
- **WI**: Task-level instructions
- **MAN**: Reference materials
- **FRM**: Data collection
- **REC**: Completed/archived

### Document Sources: 3 Canonical Sources
Based on `system_reinit.py` and audit requirements. These 3 cover all common scenarios:
- **Digital**: Modern document creation
- **Scanned Original**: Digitizing official documents
- **Scanned Copy**: Digitizing reference copies

---

## 🎓 **Usage in System**

### For Administrators
1. **After fresh installation:** Run `initialize-all-defaults.sh`
2. **Assign roles to users:** Via Django Admin → Users → UserRoles
3. **Assign users to groups:** Via Django Admin → Groups
4. **Users can then:** Create documents with proper types and sources

### For Document Authors
- Choose **Document Type** when creating documents (POL, SOP, WI, etc.)
- Choose **Document Source** to indicate document origin
- System automatically applies correct workflow based on type

### For Backup/Restore
- **Roles** are protected - restored during system restore
- **Document Types and Sources** are included in backups
- **Django Groups** are standard Django objects, backed up normally

---

## 🔍 **Common Questions**

### Q: Why 7 roles but 6 groups?
**A:** They serve different purposes:
- **Roles** = RBAC system (new, fine-grained)
- **Groups** = Workflow permissions (existing, coarse-grained)

### Q: Can I add more types/sources?
**A:** Yes! Via Django Admin:
- Document Types: `/admin/documents/documenttype/`
- Document Sources: `/admin/documents/documentsource/`

### Q: What about PROC (Procedures)?
**A:** In this system, "Procedures" = SOP (Standard Operating Procedure). Same concept, different terminology.

### Q: Why both "Document Reviewers" and "Document_Reviewers"?
**A:** Backward compatibility. Old code used underscores, new code uses spaces. System checks both.

---

## 📋 **Verification**

Check what's currently in the database:

```bash
# Check roles
bash scripts/check-user-roles-simple.sh

# Check groups
docker compose exec -T backend python -c "
from django.contrib.auth.models import Group
for g in Group.objects.all():
    print(f'- {g.name} ({g.user_set.count()} users)')
"

# Check document types
docker compose exec -T backend python -c "
from apps.documents.models import DocumentType
for dt in DocumentType.objects.filter(is_active=True):
    print(f'- {dt.code}: {dt.name}')
"

# Check document sources
docker compose exec -T backend python -c "
from apps.documents.models import DocumentSource
for ds in DocumentSource.objects.filter(is_active=True):
    print(f'- {ds.name} ({ds.source_type})')
"
```

---

## ✅ **Complete Initialization Checklist**

- [ ] Run `initialize-all-defaults.sh`
- [ ] Verify 7 roles created
- [ ] Verify 6 groups created
- [ ] Verify 6 document types created
- [ ] Verify 3 document sources created
- [ ] Assign admin user to "User Admin" role
- [ ] Assign document authors to appropriate groups
- [ ] Test document creation with all types
- [ ] Test workflow with different user roles

---

**Last Updated:** 2026-01-01  
**Status:** Complete and ready for deployment  
**Based on:** system_reinit.py canonical definitions
