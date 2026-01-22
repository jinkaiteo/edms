# Dashboard Stats Showing Zero - Table Name Mismatch Issue

**Date:** January 16, 2026
**Issue:** Dashboard stat cards showing all zeros
**Root Cause:** SQL queries using wrong table names

---

## Problem Identified

The `dashboard_stats.py` file uses hardcoded table names that don't match your actual database tables:

### What the code queries (WRONG):
```python
FROM users               # ✅ Correct
FROM workflow_instances  # ❌ Wrong - doesn't exist
FROM placeholder_definitions  # ❌ Wrong - doesn't exist  
FROM audit_trail         # ❌ Wrong - should be audit_trails
FROM documents          # ✅ Correct
FROM login_audit        # ❌ Wrong - should be login_audits
```

### Actual table names:
```python
users                    # ✅ User model
roles                    # Role model
user_roles              # UserRole model
documents               # ✅ Document model
document_types          # DocumentType model
document_workflows      # DocumentWorkflow model (not workflow_instances!)
audit_trails            # AuditTrail model (plural!)
login_audits            # LoginAudit model (plural!)
placeholders            # Placeholder model (not placeholder_definitions!)
```

---

## The Fix

We need to update the SQL queries in `dashboard_stats.py` to use correct table names.

