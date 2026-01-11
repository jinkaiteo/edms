# User Creation - Complete Summary ✅

## Existing Scripts Found

### 1. Management Command: seed_test_users.py
**Location**: `backend/apps/users/management/commands/seed_test_users.py`

**Purpose**: Creates a comprehensive set of test users with different roles

**Usage**:
```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_test_users
```

### 2. Shell Script: create-test-users.sh
**Location**: `scripts/create-test-users.sh`

**Purpose**: Quick script to create basic test users

**Usage**:
```bash
cd ~/edms-staging
./scripts/create-test-users.sh
```

### 3. Fixtures: initial_users.json
**Location**: `backend/fixtures/initial_users.json`

**Contains**: Pre-configured test users (admin, author, reviewer, approver, docadmin)

**Usage**:
```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata initial_users
```

---

## Test Users Created

After running `seed_test_users`, the following users are available:

### Admin Users
- **admin** - System administrator (superuser)
  - Email: admin@edms.local
  - Groups: Document Admins

- **docadmin** - Document administrator
  - Email: docadmin@edms.local
  - Groups: Document Admins

### Authors
- **author** / **author01** - Document authors
  - Email: author@edms.local / author01@edms.local
  - Groups: Document Authors
  - Can create and edit documents

### Reviewers
- **reviewer** / **reviewer01** - Document reviewers
  - Email: reviewer@edms.local / reviewer01@edms.local
  - Groups: Document Reviewers
  - Can review documents

### Approvers
- **approver** / **approver01** - Document approvers
  - Email: approver@edms.local / approver01@edms.local
  - Groups: Document Approvers
  - Can approve documents

### Default Password
All test users have the same password: **TestPassword123**

---

## User Groups Available

From `create_default_groups.py`:

1. **Document Admins** - Full system access
2. **Document Authors** - Can create documents
3. **Document Reviewers** - Can review documents  
4. **Document Approvers** - Can approve documents
5. **Senior Document Approvers** - Can approve high-level documents
6. **Document Viewers** - Read-only access

---

## How to Add More Users

### Method 1: Django Admin (GUI)
```
URL: http://172.28.1.148:8001/admin/
Login: admin / AdminPassword123
Navigate: Authentication and Authorization → Users → Add User
```

### Method 2: Management Command (Modify and Run)
Edit `seed_test_users.py` to add more users, then:
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_test_users
```

### Method 3: Django Shell (Quick)
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

Then:
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

user = User.objects.create_user(
    username='newuser',
    email='newuser@edms.local',
    password='TestPassword123',
    first_name='New',
    last_name='User'
)

# Add to group
group = Group.objects.get(name='Document Authors')
user.groups.add(group)

print(f'✓ Created {user.username}')
```

### Method 4: Frontend (Production Use)
```
Login as admin → Administration → User Management → Create User
```

---

## Verification

To check users:
```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()

for user in User.objects.all().order_by('username'):
    groups = ', '.join([g.name for g in user.groups.all()])
    print(f'{user.username}: {groups}')
PYEOF
```

---

## Summary

✅ **Script exists**: `seed_test_users.py`
✅ **Already executed**: Test users created on staging
✅ **Total users**: Multiple users with different roles
✅ **Password**: TestPassword123 (for all test users)
✅ **Groups**: Users assigned to appropriate groups

**Test users are ready for use!**
