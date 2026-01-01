#!/bin/bash
# Assign Document Author role to author01 for document creation

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

log "Assigning Document Author role to author01..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role

print("=== Checking author01 ===\n")

try:
    author = User.objects.get(username='author01')
except User.DoesNotExist:
    print("✗ author01 user not found!")
    print("Create the user first.")
    exit(1)

print("Current roles:")
for user_role in author.user_roles.all():
    print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level} (active: {user_role.is_active})")

# Check permission
has_perm = author.user_roles.filter(
    role__module='O1',
    role__permission_level__in=['write', 'admin'],
    is_active=True
).exists()

print(f"\nCan create documents: {has_perm}")

if not has_perm:
    print("\n=== Assigning Document Author Role ===\n")
    
    # Find Document Author role
    doc_author_role = Role.objects.filter(name='Document Author').first()
    
    if not doc_author_role:
        print("✗ Document Author role not found!")
        print("Available roles:")
        for role in Role.objects.all():
            print(f"  - {role.name}: {role.module}/{role.permission_level}")
        exit(1)
    
    # Check if already assigned but inactive
    from apps.users.models import UserRole
    existing = UserRole.objects.filter(user=author, role=doc_author_role).first()
    
    if existing:
        existing.is_active = True
        existing.save()
        print(f"✓ Activated existing '{doc_author_role.name}' role for author01")
    else:
        # Create new UserRole assignment
        UserRole.objects.create(
            user=author,
            role=doc_author_role,
            is_active=True,
            assigned_by=author  # Self-assigned for now
        )
        print(f"✓ Assigned '{doc_author_role.name}' ({doc_author_role.module}/{doc_author_role.permission_level}) to author01")
    
    # Verify
    has_perm_now = author.user_roles.filter(
        role__module='O1',
        role__permission_level__in=['write', 'admin'],
        is_active=True
    ).exists()
    
    print(f"\n=== Verification ===")
    print(f"Can create documents NOW: {has_perm_now}")
    
    if has_perm_now:
        print("\n✅ SUCCESS! author01 can now create documents!")
    else:
        print("\n✗ FAILED! Still cannot create documents.")
        print("Check user_roles relationship and is_active status.")
else:
    print("\n✅ author01 already has document creation permissions!")

print("\n=== Final Role Assignment ===\n")
print("author01 roles:")
for user_role in author.user_roles.all():
    print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level} (active: {user_role.is_active})")
PYTHON

log "✅ Done! Try creating a document with author01"
