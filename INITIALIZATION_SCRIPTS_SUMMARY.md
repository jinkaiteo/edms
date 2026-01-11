# Initialization Scripts Summary

## Scripts Executed

The following management commands were run to populate the database with default data:

### 1. Document Types
**Command**: `python manage.py create_default_document_types`

**Creates**:
- SOP (Standard Operating Procedure)
- Policy
- Form
- Work Instruction
- Quality Manual
- Record
- Protocol
- Report
- Specification
- Drawing

**Location**: `backend/apps/documents/management/commands/create_default_document_types.py`

---

### 2. Document Sources
**Command**: `python manage.py create_default_document_sources`

**Creates**:
- Internal
- External
- Vendor
- Regulatory
- Customer
- Consultant
- Third Party Lab

**Location**: `backend/apps/documents/management/commands/create_default_document_sources.py`

---

### 3. Roles
**Command**: `python manage.py create_default_roles`

**Creates**:
- Administrator
- Document Controller
- Author
- Reviewer
- Approver
- Reader

**Location**: `backend/apps/users/management/commands/create_default_roles.py`

---

### 4. Groups
**Command**: `python manage.py create_default_groups`

**Creates default Django groups for permissions**

**Location**: `backend/apps/users/management/commands/create_default_groups.py`

---

### 5. Placeholders (Optional)
**Command**: `python manage.py setup_placeholders_simple`

**Creates**: Template placeholders for document generation

**Location**: `backend/apps/placeholders/management/commands/setup_placeholders_simple.py`

---

### 6. Workflows (Optional)
**Command**: `python manage.py setup_simple_workflows`

**Creates**: Default workflow templates

**Location**: `backend/apps/workflows/management/commands/setup_simple_workflows.py`

---

## Automated Initialization Script

**Script**: `scripts/initialize-all-defaults.sh`

This script runs all initialization commands in sequence:

```bash
#!/bin/bash
# Location: scripts/initialize-all-defaults.sh

cd ~/edms-staging

echo "Initializing all default data..."

# Document Types
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_types

# Document Sources
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_sources

# Roles
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_roles

# Groups
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_groups

# Placeholders (optional)
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_placeholders_simple

# Workflows (optional)
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_simple_workflows

echo "✓ All defaults initialized"
```

---

## What Was Missing

Before running these scripts, the database had:
- ❌ No document types
- ❌ No document sources
- ❌ No roles

These dropdowns appeared empty in the UI.

After running the scripts:
- ✅ 10 document types
- ✅ 7 document sources
- ✅ 6 roles
- ✅ Groups created
- ✅ Placeholders configured
- ✅ Workflows set up

---

## When to Run

These initialization scripts should be run:

1. **After fresh deployment** - When deploying to a new environment
2. **After database migration** - When database schema is created
3. **Before first use** - Before users start creating documents

---

## Verification

To verify initialization:

```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from apps.documents.models import DocumentType, DocumentSource
from apps.users.models import Role

print(f'Document Types: {DocumentType.objects.count()}')
print(f'Document Sources: {DocumentSource.objects.count()}')
print(f'Roles: {Role.objects.count()}')
PYEOF
```

Expected output:
- Document Types: 10
- Document Sources: 7
- Roles: 6

---

## Integration with Deployment

**Recommendation**: Add these commands to deployment scripts

In `deploy-interactive.sh` or deployment documentation, add step:

```bash
# After database migrations
echo "Initializing default data..."
python manage.py create_default_document_types
python manage.py create_default_document_sources
python manage.py create_default_roles
python manage.py create_default_groups
```

Or simply:

```bash
./scripts/initialize-all-defaults.sh
```
