#!/bin/bash
#
# EDMS Test Users Creation Script
#
# Creates test users with appropriate roles for development and testing

set -e

echo "👥 Creating EDMS Test Users"
echo "==========================="

# Check if backend service is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "❌ Backend service is not running. Please start it first with ./scripts/start-development.sh"
    exit 1
fi

# Create test users
echo "📝 Creating test users..."

docker compose exec backend python manage.py shell << 'EOF'
from apps.users.models import User, Role, UserRole
from django.contrib.auth.hashers import make_password

# Test user data with simple password for easy testing
simple_password = 'test123'  # Same password for all users for testing convenience

test_users = [
    {
        'username': 'docadmin',
        'password': simple_password,
        'email': 'docadmin@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Administrator',
        'is_staff': True,
        'department': 'IT',
        'position': 'System Administrator'
    },
    {
        'username': 'author',
        'password': simple_password,
        'email': 'author@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Author',
        'department': 'Quality Assurance',
        'position': 'Document Specialist'
    },
    {
        'username': 'reviewer',
        'password': simple_password,
        'email': 'reviewer@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Reviewer',
        'department': 'Quality Assurance',
        'position': 'QA Manager'
    },
    {
        'username': 'approver',
        'password': simple_password,
        'email': 'approver@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Approver',
        'department': 'Management',
        'position': 'Director'
    },
    {
        'username': 'placeholderadmin',
        'password': simple_password,
        'email': 'placeholderadmin@edms-project.com',
        'first_name': 'Placeholder',
        'last_name': 'Admin',
        'department': 'IT',
        'position': 'System Administrator'
    },
    {
        'username': 'admin',
        'password': simple_password,
        'email': 'admin@edms-project.com',
        'first_name': 'System',
        'last_name': 'Administrator',
        'is_staff': True,
        'is_superuser': True,
        'department': 'IT',
        'position': 'System Administrator'
    }
]

created_count = 0
for user_data in test_users:
    username = user_data['username']
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists, skipping...")
        continue
    
    # Create user
    password = user_data.pop('password')
    user = User.objects.create(**user_data)
    user.set_password(password)
    user.is_validated = True
    user.save()
    
    print(f"✅ Created user: {username}")
    created_count += 1

print(f"\n📊 Summary: {created_count} test users created")

# Create basic roles if they don't exist
roles_data = [
    {'name': 'Document Admin', 'module': 'O1', 'permission_level': 'admin'},
    {'name': 'Document Author', 'module': 'O1', 'permission_level': 'write'},
    {'name': 'Document Reviewer', 'module': 'O1', 'permission_level': 'review'},
    {'name': 'Document Approver', 'module': 'O1', 'permission_level': 'approve'},
    {'name': 'User Admin', 'module': 'S1', 'permission_level': 'admin'},
    {'name': 'Placeholder Admin', 'module': 'S6', 'permission_level': 'admin'},
]

for role_data in roles_data:
    role, created = Role.objects.get_or_create(
        module=role_data['module'],
        permission_level=role_data['permission_level'],
        defaults={'name': role_data['name'], 'is_system_role': True}
    )
    if created:
        print(f"✅ Created role: {role.name}")

print("\n🎭 Basic roles created")
EOF

echo ""
echo "✅ Test users creation completed!"
echo ""
echo "👤 Available test accounts (Simple Password for All):"
echo "   admin / test123 (Superuser)"
echo "   docadmin / test123 (Document Admin)"
echo "   author / test123 (Document Author)"
echo "   reviewer / test123 (Document Reviewer)"
echo "   approver / test123 (Document Approver)"
echo "   placeholderadmin / test123 (Placeholder Admin)"
echo ""
echo "🔑 All users have the same password: test123"
echo ""
echo "🌐 Login at: http://localhost:8000/admin"
echo ""