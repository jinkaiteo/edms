#!/bin/bash
#
# Simple user roles check without TTY issues
#

echo "Checking admin user roles and permissions..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.production')
django.setup()

from apps.users.models import User, Role, UserRole

# Get admin user
admin = User.objects.get(username='admin')
print(f'User: {admin.username}')
print(f'Email: {admin.email}')
print(f'Is superuser: {admin.is_superuser}')
print(f'Is staff: {admin.is_staff}')
print('')

# Check roles
print('Active roles assigned to admin:')
roles = UserRole.objects.filter(user=admin, is_active=True).select_related('role')
if roles.exists():
    for ur in roles:
        print(f'  - {ur.role.name} (Module: {ur.role.module}, Level: {ur.role.permission_level})')
else:
    print('  No active roles assigned')

print('')
print('All available roles in system:')
all_roles = Role.objects.all()
if all_roles.exists():
    for role in all_roles:
        print(f'  - {role.name} (Module: {role.module}, Level: {role.permission_level})')
else:
    print('  No roles defined in system!')

print('')
print('S1 Admin roles (required for role assignment):')
s1_admin = Role.objects.filter(module='S1', permission_level='admin')
if s1_admin.exists():
    for role in s1_admin:
        print(f'  Found: {role.name} (id: {role.id})')
else:
    print('  WARNING: No S1 Admin roles found!')
"
