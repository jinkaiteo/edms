# User Creation Guide

## Current User Management

### Existing Users
The system has one admin user:
- **Username**: admin
- **Password**: AdminPassword123
- **Type**: Superuser (staff + superuser)

### Test User Fixture
A fixture file exists at `backend/fixtures/initial_users.json` but it's empty (only contains `[]`).

---

## Methods to Add Users

### Method 1: Django Admin Interface (Recommended for GUI)

1. **Access Django Admin**:
   ```
   http://172.28.1.148:8001/admin/
   ```

2. **Login**: admin / AdminPassword123

3. **Navigate**: Users → Add User

4. **Fill in**:
   - Username
   - Password
   - Email
   - Groups (for permissions)
   - Staff status / Superuser status

---

### Method 2: Management Command (Programmatic)

**Create a script**: `backend/apps/users/management/commands/create_test_users.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for EDMS'

    def handle(self, *args, **options):
        test_users = [
            {
                'username': 'author01',
                'email': 'author01@edms.local',
                'password': 'TestPassword123',
                'first_name': 'Test',
                'last_name': 'Author',
                'is_staff': False,
                'is_superuser': False,
                'groups': ['Document Authors']
            },
            {
                'username': 'reviewer01',
                'email': 'reviewer01@edms.local',
                'password': 'TestPassword123',
                'first_name': 'Test',
                'last_name': 'Reviewer',
                'groups': ['Document Reviewers']
            },
            {
                'username': 'approver01',
                'email': 'approver01@edms.local',
                'password': 'TestPassword123',
                'first_name': 'Test',
                'last_name': 'Approver',
                'groups': ['Document Approvers']
            },
        ]

        for user_data in test_users:
            username = user_data['username']
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'✓ User {username} already exists')
                continue
            
            groups = user_data.pop('groups', [])
            password = user_data.pop('password')
            
            user = User.objects.create_user(**user_data)
            user.set_password(password)
            user.save()
            
            # Add to groups
            for group_name in groups:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    self.stdout.write(f'Warning: Group {group_name} not found')
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created user: {username}'))
        
        self.stdout.write(self.style.SUCCESS('All test users created'))
```

**Usage**:
```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py create_test_users
```

---

### Method 3: Django Shell (Quick One-Off)

```bash
cd ~/edms-staging
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

Then:
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Create author
author = User.objects.create_user(
    username='author01',
    email='author01@edms.local',
    password='TestPassword123',
    first_name='Test',
    last_name='Author'
)
author.groups.add(Group.objects.get(name='Document Authors'))

# Create reviewer
reviewer = User.objects.create_user(
    username='reviewer01',
    email='reviewer01@edms.local',
    password='TestPassword123',
    first_name='Test',
    last_name='Reviewer'
)
reviewer.groups.add(Group.objects.get(name='Document Reviewers'))

# Create approver
approver = User.objects.create_user(
    username='approver01',
    email='approver01@edms.local',
    password='TestPassword123',
    first_name='Test',
    last_name='Approver'
)
approver.groups.add(Group.objects.get(name='Document Approvers'))

print('✓ Users created')
```

---

### Method 4: Frontend User Management

**For end users (preferred for production)**:

1. Login as admin
2. Navigate to: Administration → User Management
3. Click "Add User" or "Create User"
4. Fill in user details
5. Assign groups/roles
6. Save

---

## Available Groups

From `create_default_groups.py`, the following groups exist:

1. **Document Admins** - Full system access
2. **Document Authors** - Can create documents
3. **Document Reviewers** - Can review documents
4. **Document Approvers** - Can approve documents
5. **Senior Document Approvers** - Can approve high-level documents
6. **Document Viewers** - Read-only access

---

## User Roles (from Role system)

From initialization, these roles exist:
1. Document Admin
2. Document Author
3. Document Reviewer
4. Document Approver
5. Document Viewer
6. (+ 2 more)

---

## Recommendation

**For testing**: Use Method 2 (Management Command)
- Create the script above
- Deploy to server
- Run command
- Instantly get test users

**For production**: Use Method 4 (Frontend)
- User-friendly interface
- Audit trail
- No direct database access needed

**For quick testing**: Use Method 3 (Django Shell)
- Fastest for one or two users
- No file creation needed

---

## Quick Script for Deployment

**File**: `scripts/create-test-users.sh`

```bash
#!/bin/bash
cd ~/edms-staging

echo "Creating test users..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

users = [
    ('author01', 'author01@edms.local', 'Document Authors'),
    ('reviewer01', 'reviewer01@edms.local', 'Document Reviewers'),
    ('approver01', 'approver01@edms.local', 'Document Approvers'),
]

for username, email, group_name in users:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username, email, 'TestPassword123')
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        print(f'✓ Created {username}')
    else:
        print(f'✓ {username} already exists')
PYEOF

echo "✓ Test users ready"
```

**Make executable and run**:
```bash
chmod +x scripts/create-test-users.sh
./scripts/create-test-users.sh
```
