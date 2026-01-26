# Local Instance Test Users - Created Successfully

## Summary

✅ **13 test users created** with appropriate roles and permissions for testing the EDMS system.

All users created from the `seed_test_users` management command based on the EDMS_Test_Users.md specification.

## Login Credentials

**Password for all test users:** `test123`

## User Accounts by Role

### 📖 Document Viewers (read permission)
Can view approved/effective documents only.

| Username | Full Name | Department | Email |
|----------|-----------|------------|-------|
| `viewer01` | Alice Johnson | Quality Assurance | alice.johnson@edmstest.com |
| `viewer02` | Bob Wilson | Manufacturing | bob.wilson@edmstest.com |
| `viewer03` | Carol Davis | Research | carol.davis@edmstest.com |

### ✍️ Document Authors (write permission)
Can create, edit, and submit documents for review.

| Username | Full Name | Department | Email |
|----------|-----------|------------|-------|
| `author01` | David Brown | Quality Assurance | david.brown@edmstest.com |
| `author02` | Emma Garcia | Regulatory Affairs | emma.garcia@edmstest.com |
| `author03` | Frank Miller | Manufacturing | frank.miller@edmstest.com |
| `author04` | Grace Lee | Research Development | grace.lee@edmstest.com |

### 🔍 Document Reviewers (review permission)
Can review and approve/reject documents during review process.

| Username | Full Name | Department | Email |
|----------|-----------|------------|-------|
| `reviewer01` | Henry Taylor | Quality Assurance | henry.taylor@edmstest.com |
| `reviewer02` | Isabel Martinez | Regulatory Affairs | isabel.martinez@edmstest.com |
| `reviewer03` | Jack Anderson | Manufacturing | jack.anderson@edmstest.com |

### ✅ Document Approvers (approve permission)
Can give final approval to documents and set effective dates.

| Username | Full Name | Department | Email |
|----------|-----------|------------|-------|
| `approver01` | Karen White | Quality Assurance | karen.white@edmstest.com |
| `approver02` | Lucas Thompson | Regulatory Affairs | lucas.thompson@edmstest.com |
| `approver03` | Maria Rodriguez | Manufacturing | maria.rodriguez@edmstest.com |

## Quick Test Scenarios

### Test Complete Document Workflow

1. **Author Creates Document**
   - Login as: `author01` / `test123`
   - Create a new document (SOP, Policy, etc.)
   - Submit for review

2. **Reviewer Reviews Document**
   - Login as: `reviewer01` / `test123`
   - Review the document
   - Approve or request changes

3. **Approver Final Approval**
   - Login as: `approver01` / `test123`
   - Give final approval
   - Set effective date

4. **Viewer Access**
   - Login as: `viewer01` / `test123`
   - Verify can view effective documents
   - Verify cannot edit or create documents

## Access URLs

- **Frontend:** http://localhost:3001/
- **Backend API:** http://localhost:8001/api/v1/
- **Backend Admin:** http://localhost:8001/admin/

## Role Permissions

| Role | Permission Level | Capabilities |
|------|------------------|--------------|
| Document Viewer | `read` | View approved/effective documents |
| Document Author | `write` | Create, edit, submit documents + view |
| Document Reviewer | `review` | Review, approve/reject + write access |
| Document Approver | `approve` | Final approval, set dates + review access |
| Document Admin | `admin` | Full system access + approve access |

## Testing Workflow Segregation

The test users are designed to test **segregation of duties**:

✅ **Authors cannot review their own documents**
✅ **Reviewers cannot approve documents they reviewed**
✅ **Each role has distinct permissions**
✅ **Cross-department workflows** (QA → Regulatory → Manufacturing)

## Resetting Test Users

To clear and recreate all test users:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py seed_test_users --clear-existing
```

To update passwords for existing users:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py seed_test_users --update-passwords
```

## Management Command

The users were created using:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py seed_test_users
```

**Command Options:**
- `--clear-existing` - Delete existing test users before creating
- `--update-passwords` - Reset all test user passwords to `test123`

## System Roles Created

The following system roles were created for the document management module (O1):

1. **Document Viewer** (O1/read)
2. **Document Author** (O1/write)
3. **Document Reviewer** (O1/review)
4. **Document Approver** (O1/approve)
5. **Document Admin** (O1/admin)

## Next Steps

1. ✅ Test users created successfully
2. ✅ Roles assigned to users
3. ⏭️ Create a superuser for admin access (if needed):
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     python manage.py createsuperuser
   ```
4. ⏭️ Start testing document workflows!

---

**Created:** January 26, 2026  
**Status:** ✅ All test users active and ready for testing  
**Total Users:** 13 test users + any superusers you create
