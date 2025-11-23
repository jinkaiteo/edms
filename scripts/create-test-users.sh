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

# Test user data with simple passwords (updated from live system)
test_users = [
    {
        'username': 'docadmin',
        'password': 'testdocadmin123456',
        'email': 'docadmin@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Administrator',
        'is_staff': True,
        'department': 'IT',
        'position': 'System Administrator'
    },
    {
        'username': 'author',
        'password': 'testauthor123456',
        'email': 'author@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Author',
        'department': 'Quality Assurance',
        'position': 'Document Specialist'
    },
    {
        'username': 'reviewer',
        'password': 'testreviewer123456',
        'email': 'reviewer@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Reviewer',
        'department': 'Quality Assurance',
        'position': 'QA Manager'
    },
    {
        'username': 'approver',
        'password': 'testapprover123456',
        'email': 'approver@edms-project.com',
        'first_name': 'Document',
        'last_name': 'Approver',
        'department': 'Management',
        'position': 'Director'
    },
    {
        'username': 'placeholderadmin',
        'password': 'testplaceholder123456',
        'email': 'placeholderadmin@edms-project.com',
        'first_name': 'Placeholder',
        'last_name': 'Admin',
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
echo "👤 Available test accounts (Simple Password Pattern):"
echo "   docadmin / testdocadmin123456"
echo "   author / testauthor123456"
echo "   reviewer / testreviewer123456"
echo "   approver / testapprover123456"
echo "   placeholderadmin / testplaceholder123456"
echo ""
echo "📋 Password Pattern: test[username]123456"
echo ""
echo "🌐 Login at: http://localhost:8000/admin"
echo ""