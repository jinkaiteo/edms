# Local Instance Test Users - Deployment Script

## Summary

✅ **4 users created** matching exactly what `deploy-interactive.sh` creates.

Created by: `scripts/create-test-users.sh`

## Login Credentials

### Superuser
| Username | Password | Full Name | Email |
|----------|----------|-----------|-------|
| `admin` | `admin123` | Admin User | admin@edms.com |

### Test Users  
| Username | Password | Role | Full Name | Email |
|----------|----------|------|-----------|-------|
| `author01` | `test123` | Document Author | Author One | author01@edms.com |
| `reviewer01` | `test123` | Document Reviewer | Reviewer User | reviewer01@edms.com |
| `approver01` | `test123` | Document Approver | Approver User | approver01@edms.com |

## Quick Test Workflow

1. **Login as author01** (`test123`)
   - Create a new document
   - Submit for review

2. **Login as reviewer01** (`test123`)
   - Review the document
   - Approve or request changes

3. **Login as approver01** (`test123`)
   - Give final approval
   - Set effective date

## Access URLs

- **Frontend:** http://localhost:3001/
- **Backend Admin:** http://localhost:8001/admin/
- **Backend API:** http://localhost:8001/api/v1/

## How These Users Were Created

The deployment script (`deploy-interactive.sh` line 816) calls:

```bash
bash scripts/create-test-users.sh
```

Which creates these exact 4 users with a Python script:

```python
# Admin user
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@edms.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True
    }
)
admin.set_password('admin123')

# Test users
test_users = [
    ('author01', 'Author', 'One', 'author01@edms.com'),
    ('reviewer01', 'Reviewer', 'User', 'reviewer01@edms.com'),
    ('approver01', 'Approver', 'User', 'approver01@edms.com'),
]
# Password: test123 for all test users
```

## Role Assignment

After creating users, the deployment script assigns roles via:

```bash
bash scripts/fix-reviewer-approver-roles.sh
```

This assigns:
- **author01** → Document Author role (write permission)
- **reviewer01** → Document Reviewer role (review permission)
- **approver01** → Document Approver role (approve permission)

## Recreate These Users

To recreate exactly what the deployment script creates:

```bash
bash scripts/create-test-users.sh
bash scripts/fix-reviewer-approver-roles.sh
```

## Notes

- These are the **exact** users created by the deployment script
- Minimal set for basic workflow testing (author → reviewer → approver)
- For more comprehensive testing with 13 users, use: `python manage.py seed_test_users`
- The deployment script keeps it simple with just 3 test users + 1 admin

---

**Created:** January 26, 2026  
**Source:** `scripts/create-test-users.sh` (called by deploy-interactive.sh)  
**Status:** ✅ Matches deployment script exactly
