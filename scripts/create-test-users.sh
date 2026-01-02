#!/bin/bash
# Create test users for EDMS

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

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "Creating test users..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model

User = get_user_model()

# Create admin user
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@edms.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
    print("✓ Created admin user")
else:
    print("✓ Admin user already exists")

# Create test users
test_users = [
    ('author01', 'Author', 'One', 'author01@edms.com'),
    ('reviewer01', 'Reviewer', 'User', 'reviewer01@edms.com'),
    ('approver01', 'Approver', 'User', 'approver01@edms.com'),
]

for username, first, last, email in test_users:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': first,
            'last_name': last,
            'is_staff': False,
            'is_superuser': False
        }
    )
    if created:
        user.set_password('test123')
        user.save()
        print(f"✓ Created {username}")
    else:
        print(f"✓ {username} already exists")

print(f"\nTotal users: {User.objects.count()}")
PYTHON

log "✅ Test users created successfully"
