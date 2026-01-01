#!/bin/bash
# Diagnose user role assignments on staging server

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

log "Diagnosing user role assignments..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role, UserRole

print("=" * 70)
print("ACTUAL ROLE ASSIGNMENTS ON STAGING SERVER")
print("=" * 70)

# Check reviewer01
print("\n### reviewer01 ###")
try:
    reviewer = User.objects.get(username='reviewer01')
    print(f"User exists: YES")
    print(f"User roles count: {reviewer.user_roles.count()}")
    if reviewer.user_roles.count() > 0:
        for user_role in reviewer.user_roles.all():
            print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level} (active: {user_role.is_active})")
    else:
        print("  ⚠️  NO ROLES ASSIGNED!")
except User.DoesNotExist:
    print("User exists: NO")

# Check approver01
print("\n### approver01 ###")
try:
    approver = User.objects.get(username='approver01')
    print(f"User exists: YES")
    print(f"User roles count: {approver.user_roles.count()}")
    if approver.user_roles.count() > 0:
        for user_role in approver.user_roles.all():
            print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level} (active: {user_role.is_active})")
    else:
        print("  ⚠️  NO ROLES ASSIGNED!")
except User.DoesNotExist:
    print("User exists: NO")

# Check author01 for comparison
print("\n### author01 ###")
try:
    author = User.objects.get(username='author01')
    print(f"User exists: YES")
    print(f"User roles count: {author.user_roles.count()}")
    if author.user_roles.count() > 0:
        for user_role in author.user_roles.all():
            print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level} (active: {user_role.is_active})")
    else:
        print("  ⚠️  NO ROLES ASSIGNED!")
except User.DoesNotExist:
    print("User exists: NO")

# Show all available roles
print("\n" + "=" * 70)
print("AVAILABLE ROLES IN DATABASE")
print("=" * 70)
for role in Role.objects.all().order_by('name'):
    print(f"  - {role.name}: {role.module}/{role.permission_level}")

# Check if roles can be found by the names used in script
print("\n" + "=" * 70)
print("ROLE LOOKUP TEST (what deployment script searches for)")
print("=" * 70)

test_names = ['Document Author', 'Document Reviewer', 'Document Approver']
for name in test_names:
    role = Role.objects.filter(name=name).first()
    if role:
        print(f"✓ Found: {name} → {role.module}/{role.permission_level}")
    else:
        print(f"✗ NOT FOUND: {name}")

PYTHON

log "✅ Diagnosis complete"
