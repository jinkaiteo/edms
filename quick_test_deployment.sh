#!/bin/bash
# Quick deployment test - uses cached images

set -e

echo "🚀 Quick Deployment Test (using cache)"
echo ""

# Stop and clean
echo "Stopping containers..."
docker compose down -v
docker volume rm qms_04_postgres_data 2>/dev/null || true

# Start services
echo "Starting services..."
docker compose up -d

echo "Waiting 25 seconds for services..."
sleep 25

# Check status
echo ""
echo "Services:"
docker compose ps

# Apply migrations
echo ""
echo "Applying migrations..."
docker compose exec -T backend python3 manage.py migrate --noinput

# Create admin
echo ""
echo "Creating admin..."
docker compose exec -T backend python3 manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Admin created')
PYTHON

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access at:"
echo "  http://localhost:3000 (frontend)"
echo "  http://localhost:8000/admin (admin/admin123)"
