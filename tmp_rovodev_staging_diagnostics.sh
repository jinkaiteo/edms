#!/bin/bash
# Staging Server Login Diagnostics Script

echo "=========================================="
echo "EDMS Staging Server Login Diagnostics"
echo "=========================================="
echo ""

cd /home/lims/edms-staging

echo "1. Checking if users exist in database..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth.models import User
users = User.objects.all()
print(f"\nTotal users in database: {users.count()}")
print("\nUser list:")
for u in users:
    print(f"  - {u.username} | Email: {u.email} | Staff: {u.is_staff} | Superuser: {u.is_superuser} | Active: {u.is_active}")
EOF

echo ""
echo "2. Testing backend authentication endpoint..."
curl -s -X POST http://localhost:8001/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' | python3 -m json.tool 2>/dev/null || echo "Authentication failed or endpoint issue"

echo ""
echo "3. Checking CORS configuration..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.conf import settings
print(f"CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DEBUG: {settings.DEBUG}")
EOF

echo ""
echo "4. Testing frontend to backend connectivity..."
curl -s http://localhost:3001/ | head -20
echo ""

echo ""
echo "5. Checking backend logs for authentication errors..."
docker compose -f docker-compose.prod.yml logs backend --tail=50 | grep -i "auth\|login\|cors" || echo "No auth-related errors"

echo ""
echo "6. Verifying backend health..."
curl -s http://localhost:8001/health/ | python3 -m json.tool

echo ""
echo "=========================================="
echo "Diagnostics Complete"
echo "=========================================="
