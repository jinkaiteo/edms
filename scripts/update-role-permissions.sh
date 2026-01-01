#!/bin/bash
# Update existing roles with correct module and permission_level

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

log "Updating role permissions for document creation..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import Role

print("=== Updating Roles ===\n")

# Update Document Admin
role = Role.objects.filter(name='Document Admin').first()
if role:
    role.module = 'O1'
    role.permission_level = 'admin'
    role.save()
    print(f"✓ Updated: Document Admin -> O1/admin")

# Update Approver (need different name check)
for name in ['Approver', 'Document Approver']:
    role = Role.objects.filter(name=name).first()
    if role:
        role.module = 'O1'
        role.permission_level = 'admin'
        role.save()
        print(f"✓ Updated: {name} -> O1/admin")
        break

# Update Reviewer
for name in ['Reviewer', 'Document Reviewer']:
    role = Role.objects.filter(name=name).first()
    if role:
        role.module = 'O1'
        role.permission_level = 'write'
        role.save()
        print(f"✓ Updated: {name} -> O1/write")
        break

# Update Author
for name in ['Author', 'Document Author']:
    role = Role.objects.filter(name=name).first()
    if role:
        role.module = 'O1'
        role.permission_level = 'write'
        role.save()
        print(f"✓ Updated: {name} -> O1/write")
        break

# Update Viewer
for name in ['Viewer', 'Document Viewer']:
    role = Role.objects.filter(name=name).first()
    if role:
        role.module = 'O1'
        role.permission_level = 'read'
        role.save()
        print(f"✓ Updated: {name} -> O1/read")
        break

# Update User Admin
role = Role.objects.filter(name='User Admin').first()
if role:
    role.module = 'S1'
    role.permission_level = 'admin'
    role.save()
    print(f"✓ Updated: User Admin -> S1/admin")

# Update Placeholder Admin
role = Role.objects.filter(name='Placeholder Admin').first()
if role:
    role.module = 'S6'
    role.permission_level = 'admin'
    role.save()
    print(f"✓ Updated: Placeholder Admin -> S6/admin")

print("\n=== Current Roles ===\n")
for role in Role.objects.all().order_by('name'):
    print(f"  {role.name}: {role.module}/{role.permission_level}")

print("\n=== Checking author01 permissions ===\n")
from apps.users.models import User
try:
    author = User.objects.get(username='author01')
    has_perm = author.user_roles.filter(
        role__module='O1',
        role__permission_level__in=['write', 'admin'],
        is_active=True
    ).exists()
    print(f"author01 can create documents: {has_perm}")
    if has_perm:
        print("✓ author01 has correct permissions!")
    else:
        print("✗ author01 still missing permissions - check role assignment")
except User.DoesNotExist:
    print("author01 user not found")

PYTHON

log "✅ Role permissions updated!"
log ""
log "Next: Try creating a document with author01"
