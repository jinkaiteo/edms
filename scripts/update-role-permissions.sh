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

print("=== Current Roles ===\n")
for role in Role.objects.all():
    print(f"  {role.name}: {role.module}/{role.permission_level}")

print("\n=== Updating Roles (with unique constraint handling) ===\n")

# Strategy: Update roles in order to avoid unique constraint violations
# The constraint is on (module, permission_level)

# First, update roles to temporary values to free up the slots
roles_to_update = []

# Collect all roles that need updating
for name in ['Document Admin', 'Approver', 'Document Approver']:
    role = Role.objects.filter(name=name).first()
    if role:
        roles_to_update.append(('admin', role, name))

for name in ['Reviewer', 'Document Reviewer', 'Author', 'Document Author']:
    role = Role.objects.filter(name=name).first()
    if role:
        roles_to_update.append(('write', role, name))
        
for name in ['Viewer', 'Document Viewer']:
    role = Role.objects.filter(name=name).first()
    if role:
        roles_to_update.append(('read', role, name))

# Step 1: Move all to temporary module to free constraints
print("Step 1: Moving to temporary module...")
for perm_level, role, name in roles_to_update:
    role.module = 'TEMP'
    role.save()
    print(f"  Moved: {name} -> TEMP/{role.permission_level}")

# Step 2: Now update to final values (no conflicts)
print("\nStep 2: Setting final values...")

# Admin level - only Document Admin or first Approver
admin_role = Role.objects.filter(name='Document Admin').first()
if not admin_role:
    admin_role = Role.objects.filter(name__in=['Approver', 'Document Approver']).first()
if admin_role:
    admin_role.module = 'O1'
    admin_role.permission_level = 'admin'
    admin_role.save()
    print(f"✓ {admin_role.name} -> O1/admin")

# Write level - Author (primary)
author_role = None
for name in ['Author', 'Document Author']:
    author_role = Role.objects.filter(name=name).first()
    if author_role:
        break
if author_role:
    author_role.module = 'O1'
    author_role.permission_level = 'write'
    author_role.save()
    print(f"✓ {author_role.name} -> O1/write")

# Read level - Viewer
viewer_role = None
for name in ['Viewer', 'Document Viewer']:
    viewer_role = Role.objects.filter(name=name).first()
    if viewer_role:
        break
if viewer_role:
    viewer_role.module = 'O1'
    viewer_role.permission_level = 'read'
    viewer_role.save()
    print(f"✓ {viewer_role.name} -> O1/read")

# Reviewer gets approve level
reviewer_role = None
for name in ['Reviewer', 'Document Reviewer']:
    reviewer_role = Role.objects.filter(name=name).first()
    if reviewer_role:
        break
if reviewer_role:
    reviewer_role.module = 'O1'
    reviewer_role.permission_level = 'approve'
    reviewer_role.save()
    print(f"✓ {reviewer_role.name} -> O1/approve")

# Approver (if different from admin) gets review level
approver_role = Role.objects.filter(name__in=['Approver', 'Document Approver']).exclude(id=admin_role.id if admin_role else None).first()
if approver_role:
    approver_role.module = 'O1'
    approver_role.permission_level = 'review'
    approver_role.save()
    print(f"✓ {approver_role.name} -> O1/review")

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
