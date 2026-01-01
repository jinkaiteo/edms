#!/bin/bash
#
# Check user roles and permissions
#

echo "Checking admin user roles and permissions..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from apps.users.models import User, Role, UserRole

# Get admin user
try:
    admin = User.objects.get(username='admin')
    print(f"✓ Found user: {admin.username}")
    print(f"  - Email: {admin.email}")
    print(f"  - Is superuser: {admin.is_superuser}")
    print(f"  - Is staff: {admin.is_staff}")
    print("")
    
    # Check roles
    print("Active roles:")
    roles = UserRole.objects.filter(user=admin, is_active=True).select_related('role')
    if roles.exists():
        for ur in roles:
            print(f"  - {ur.role.name} (Module: {ur.role.module}, Level: {ur.role.permission_level})")
    else:
        print("  No active roles assigned")
    
    print("")
    print("All available roles in system:")
    all_roles = Role.objects.all()
    for role in all_roles:
        print(f"  - {role.name} (Module: {role.module}, Level: {role.permission_level})")
        
    print("")
    print("S1 Admin roles (required for role assignment):")
    s1_admin = Role.objects.filter(module='S1', permission_level='admin')
    if s1_admin.exists():
        for role in s1_admin:
            print(f"  ✓ {role.name} (id: {role.id})")
    else:
        print("  ✗ No S1 Admin roles found!")
        
except User.DoesNotExist:
    print("✗ Admin user not found!")
except Exception as e:
    print(f"✗ Error: {e}")

EOF
