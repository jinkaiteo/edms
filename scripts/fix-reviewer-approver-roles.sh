#!/bin/bash
# Fix reviewer01 and approver01 role assignments

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log "Fixing reviewer01 and approver01 role assignments..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role, UserRole
from django.contrib.auth.models import Group

print("=" * 70)
print("FIXING ROLE ASSIGNMENTS")
print("=" * 70)

# Get admin user for assigned_by
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    print("⚠️  No admin user found, using self-assignment")

# Fix reviewer01
print("\n### Fixing reviewer01 ###")
try:
    reviewer = User.objects.get(username='reviewer01')
    reviewer_role = Role.objects.filter(name='Document Reviewer').first()
    
    if not reviewer_role:
        print("✗ Document Reviewer role not found!")
    else:
        # Remove wrong roles
        removed_count = reviewer.user_roles.all().delete()[0]
        if removed_count > 0:
            print(f"  Removed {removed_count} incorrect role(s)")
        
        # Assign correct role
        UserRole.objects.create(
            user=reviewer,
            role=reviewer_role,
            is_active=True,
            assigned_by=admin if admin else reviewer
        )
        print(f"✓ Assigned: {reviewer_role.name} ({reviewer_role.module}/{reviewer_role.permission_level})")
        
        # Add to Reviewers group
        reviewers_group = Group.objects.filter(name='Reviewers').first()
        if reviewers_group:
            reviewer.groups.add(reviewers_group)
            print(f"✓ Added to Reviewers group")
        
        # Verify
        can_review = reviewer.user_roles.filter(
            role__module='O1',
            role__permission_level__in=['review', 'approve', 'admin'],
            is_active=True
        ).exists()
        print(f"  Can review documents: {can_review}")
        
except User.DoesNotExist:
    print("✗ reviewer01 user not found!")

# Fix approver01
print("\n### Fixing approver01 ###")
try:
    approver = User.objects.get(username='approver01')
    approver_role = Role.objects.filter(name='Document Approver').first()
    
    if not approver_role:
        print("✗ Document Approver role not found!")
    else:
        # Remove wrong roles
        removed_count = approver.user_roles.all().delete()[0]
        if removed_count > 0:
            print(f"  Removed {removed_count} incorrect role(s)")
        
        # Assign correct role
        UserRole.objects.create(
            user=approver,
            role=approver_role,
            is_active=True,
            assigned_by=admin if admin else approver
        )
        print(f"✓ Assigned: {approver_role.name} ({approver_role.module}/{approver_role.permission_level})")
        
        # Add to Approvers group
        approvers_group = Group.objects.filter(name='Approvers').first()
        if approvers_group:
            approver.groups.add(approvers_group)
            print(f"✓ Added to Approvers group")
        
        # Verify
        can_approve = approver.user_roles.filter(
            role__module='O1',
            role__permission_level__in=['approve', 'admin'],
            is_active=True
        ).exists()
        print(f"  Can approve documents: {can_approve}")
        
except User.DoesNotExist:
    print("✗ approver01 user not found!")

# Summary
print("\n" + "=" * 70)
print("FINAL ROLE ASSIGNMENTS")
print("=" * 70)

for username in ['author01', 'reviewer01', 'approver01']:
    try:
        user = User.objects.get(username=username)
        print(f"\n{username}:")
        if user.user_roles.count() > 0:
            for user_role in user.user_roles.all():
                print(f"  - {user_role.role.name}: {user_role.role.module}/{user_role.role.permission_level}")
        else:
            print("  ⚠️  NO ROLES")
    except User.DoesNotExist:
        print(f"\n{username}: NOT FOUND")

PYTHON

log "✅ Role assignments fixed!"
log ""
log "Test the users:"
echo "  reviewer01 - should be able to review documents"
echo "  approver01 - should be able to approve documents"
