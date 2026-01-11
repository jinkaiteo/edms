#!/bin/bash
# Local Deployment Test Script - Fixed version
set -e

echo "=========================================="
echo "🧪 EDMS Local Deployment Test"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Stop ALL containers completely
echo "Step 1: Stopping all containers..."
docker compose down -v
sleep 2
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 2: Remove volumes completely (this is critical!)
echo "Step 2: Removing all volumes for clean slate..."
docker volume ls | grep qms_04 | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true
echo -e "${GREEN}✓ Volumes removed${NC}"
echo ""

# Step 3: Start fresh database
echo "Step 3: Starting fresh database..."
docker compose up -d db
echo "Waiting for database to initialize (15 seconds)..."
sleep 15
echo -e "${GREEN}✓ Fresh database started${NC}"
echo ""

# Step 4: Build backend (to include latest code changes)
echo "Step 4: Building backend service..."
docker compose build backend
echo -e "${GREEN}✓ Backend built${NC}"
echo ""

# Step 5: Start all services
echo "Step 5: Starting all services..."
docker compose up -d
echo "Waiting for services to start (20 seconds)..."
sleep 20
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 6: Check service health
echo "Step 6: Checking service health..."
echo "Services status:"
docker compose ps
echo ""

# Step 7: Apply migrations
echo "Step 7: Applying database migrations..."
docker compose exec -T backend python3 manage.py migrate --noinput
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations applied successfully${NC}"
else
    echo -e "${RED}✗ Migration failed!${NC}"
    echo "Checking database state..."
    docker compose logs db --tail 20
    exit 1
fi
echo ""

# Step 8: Collect static files
echo "Step 8: Collecting static files..."
docker compose exec -T backend python3 manage.py collectstatic --noinput 2>&1 | grep -v "^$" || echo "Static files collected"
echo -e "${GREEN}✓ Static files ready${NC}"
echo ""

# Step 9: Create superuser
echo "Step 9: Creating admin user..."
docker compose exec -T backend python3 manage.py shell << PYTHON
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✓ Admin user created')
else:
    print('✓ Admin user already exists')
PYTHON
echo ""

# Step 10: Initialize system defaults
echo "Step 10: Initializing system defaults..."
docker compose exec -T backend python3 << PYTHON
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
django.setup()

# Initialize roles
from apps.users.models import Role, User
admin_user = User.objects.get(username='admin')

roles = [
    {'code': 'AUTHOR', 'name': 'Author', 'description': 'Can create and edit documents'},
    {'code': 'REVIEWER', 'name': 'Reviewer', 'description': 'Can review documents'},
    {'code': 'APPROVER', 'name': 'Approver', 'description': 'Can approve documents'},
]

for role_data in roles:
    Role.objects.get_or_create(
        code=role_data['code'],
        defaults={
            'name': role_data['name'],
            'description': role_data['description'],
            'created_by': admin_user
        }
    )
print('✓ Roles initialized')

# Initialize groups
from django.contrib.auth.models import Group
groups = ['Authors', 'Reviewers', 'Approvers', 'Administrators']
for group_name in groups:
    Group.objects.get_or_create(name=group_name)
print('✓ Groups initialized')
PYTHON
echo -e "${GREEN}✓ System initialized${NC}"
echo ""

# Step 11: Test backend health
echo "Step 11: Testing backend health..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/ 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check passed (200 OK)${NC}"
else
    echo -e "${YELLOW}⚠ Backend health check returned: $BACKEND_HEALTH${NC}"
    echo "Backend logs:"
    docker compose logs backend --tail 30
fi
echo ""

# Step 12: Test frontend
echo "Step 12: Testing frontend..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Frontend accessible (200 OK)${NC}"
else
    echo -e "${YELLOW}⚠ Frontend returned: $FRONTEND_HEALTH (may need a moment to build)${NC}"
fi
echo ""

# Step 13: Test API endpoints
echo "Step 13: Testing API endpoints..."
API_TEST=$(curl -s http://localhost:8000/api/v1/ 2>/dev/null || echo "FAILED")
if [[ "$API_TEST" == *"api"* ]] || [[ "$API_TEST" == *"authentication"* ]]; then
    echo -e "${GREEN}✓ API endpoints accessible${NC}"
else
    echo -e "${YELLOW}⚠ API may not be ready yet${NC}"
fi
echo ""

# Step 14: Check Celery services
echo "Step 14: Checking Celery services..."
if docker compose ps celery_worker 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✓ Celery worker running${NC}"
else
    echo -e "${YELLOW}⚠ Celery worker not running${NC}"
fi

if docker compose ps celery_beat 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✓ Celery beat running${NC}"
else
    echo -e "${YELLOW}⚠ Celery beat not running${NC}"
fi
echo ""

# Final Summary
echo "=========================================="
echo "📊 Local Deployment Test Complete"
echo "=========================================="
echo ""
echo "Services:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  Admin:    http://localhost:8000/admin"
echo ""
echo -e "${GREEN}Admin Credentials:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo -e "${GREEN}✓ Fresh deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Test document workflows manually"
echo "3. Check logs: docker compose logs backend -f"
echo "4. If all works → Deploy to staging"
echo ""
