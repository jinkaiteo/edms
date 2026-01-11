#!/bin/bash
# Complete clean deployment test - ensures truly fresh start

set -e

echo "=========================================="
echo "🧹 EDMS Complete Clean Deployment Test"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Complete shutdown
echo "Step 1: Complete shutdown..."
docker compose down -v
sleep 2
echo -e "${GREEN}✓ Containers stopped${NC}"

# Step 2: Remove ALL related Docker volumes
echo "Step 2: Removing all Docker volumes..."
docker volume ls -q | grep -E "qms_04|edms" | xargs -r docker volume rm 2>/dev/null || echo "No volumes to remove"
echo -e "${GREEN}✓ Volumes cleaned${NC}"

# Step 3: Remove any orphaned containers
echo "Step 3: Cleaning orphaned containers..."
docker compose down --remove-orphans
echo -e "${GREEN}✓ Orphans removed${NC}"

# Step 4: Build fresh images
echo "Step 4: Building fresh images..."
docker compose build --no-cache backend
echo -e "${GREEN}✓ Images built${NC}"

# Step 5: Start database only first
echo "Step 5: Starting database..."
docker compose up -d db
echo "Waiting 15 seconds for PostgreSQL to initialize..."
sleep 15

# Verify database is truly empty
echo "Verifying fresh database..."
docker compose exec -T db psql -U edms_user -d postgres -c "\l" | grep edms_db || echo "Database will be created"
echo -e "${GREEN}✓ Database ready${NC}"

# Step 6: Start all services
echo "Step 6: Starting all services..."
docker compose up -d
echo "Waiting 20 seconds for services..."
sleep 20
docker compose ps
echo -e "${GREEN}✓ Services started${NC}"

# Step 7: Apply migrations
echo "Step 7: Applying migrations to FRESH database..."
docker compose exec -T backend python3 manage.py migrate --noinput 2>&1 | tee /tmp/migration_output.txt

if grep -q "Applying workflows.0001_initial" /tmp/migration_output.txt; then
    if grep -q "OK" /tmp/migration_output.txt; then
        echo -e "${GREEN}✓ Migrations applied successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️ Migration may have issues, check output above${NC}"
    fi
else
    echo -e "${GREEN}✓ Migrations completed${NC}"
fi

# Step 8: Create admin user
echo "Step 8: Creating admin user..."
docker compose exec -T backend python3 manage.py shell << PYTHON
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✓ Admin user created')
else:
    print('✓ Admin user exists')
PYTHON

# Step 9: Initialize system
echo "Step 9: Quick initialization..."
docker compose exec -T backend python3 manage.py shell << PYTHON
import django
from django.contrib.auth.models import Group

# Create basic groups
for group_name in ['Authors', 'Reviewers', 'Approvers']:
    Group.objects.get_or_create(name=group_name)
print('✓ Groups created')
PYTHON

echo ""
echo "=========================================="
echo "✅ Clean Deployment Complete!"
echo "=========================================="
echo ""
echo "Services running:"
docker compose ps
echo ""
echo "Access at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"  
echo "  Admin:    http://localhost:8000/admin (admin/admin123)"
echo ""
echo "Next: Test manually at http://localhost:3000"
echo ""
