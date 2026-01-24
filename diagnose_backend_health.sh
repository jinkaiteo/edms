#!/bin/bash
# Diagnose backend container health issues

echo "════════════════════════════════════════════════════════════════"
echo "  Backend Container Health Diagnosis"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_error() { echo -e "${RED}✗${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "1. Container Status"
echo "-------------------"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "2. Backend Container Logs (Last 50 Lines)"
echo "-------------------"
docker compose -f docker-compose.prod.yml logs backend --tail=50

echo ""
echo "3. Backend Health Check Details"
echo "-------------------"
docker inspect edms_prod_backend --format='{{json .State.Health}}' | jq '.' 2>/dev/null || echo "No health check data"

echo ""
echo "4. Check Database Connection"
echo "-------------------"
print_info "Testing database container..."
if docker compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    print_success "Database container is running"
    
    # Test if backend can reach database
    print_info "Testing database connectivity from backend..."
    docker compose -f docker-compose.prod.yml exec -T backend sh -c "
        echo 'Testing PostgreSQL connection...'
        python manage.py shell -c \"
from django.db import connection
try:
    connection.ensure_connection()
    print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
\" 2>&1
    " 2>/dev/null || print_error "Cannot test database connection"
else
    print_error "Database container not running"
fi

echo ""
echo "5. Check Redis Connection"
echo "-------------------"
print_info "Testing Redis container..."
if docker compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
    print_success "Redis container is running"
else
    print_error "Redis container not running"
fi

echo ""
echo "6. Check Environment Variables"
echo "-------------------"
print_info "Checking critical environment variables..."
docker compose -f docker-compose.prod.yml exec -T backend env | grep -E "^DB_|^REDIS_|^SECRET_KEY|^EMAIL_" | sort || print_error "Cannot read environment"

echo ""
echo "7. Check .env File"
echo "-------------------"
if [ -f ".env" ]; then
    print_success ".env file exists"
    echo "Critical settings:"
    grep -E "^DB_|^REDIS_|^SECRET_KEY|^EMAIL_BACKEND" .env
else
    print_error ".env file not found"
fi

echo ""
echo "8. Check Backend Process"
echo "-------------------"
print_info "Checking if gunicorn is running..."
docker compose -f docker-compose.prod.yml exec -T backend ps aux 2>/dev/null | grep -E "gunicorn|python" || print_error "Cannot check processes"

echo ""
echo "9. Check Port Availability"
echo "-------------------"
print_info "Testing backend port..."
BACKEND_PORT=$(grep "BACKEND_PORT" .env 2>/dev/null | cut -d'=' -f2 || echo "8001")
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/health/" | grep -q "200"; then
    print_success "Backend health endpoint responding on port $BACKEND_PORT"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/health/" 2>/dev/null || echo "000")
    print_error "Backend health endpoint not responding (HTTP $HTTP_CODE)"
fi

echo ""
echo "10. Migration Status"
echo "-------------------"
print_info "Checking if migrations ran successfully..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py showmigrations 2>&1 | head -20 || print_error "Cannot check migrations"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Common Issues & Solutions"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Analyze logs for common issues
LOGS=$(docker compose -f docker-compose.prod.yml logs backend --tail=100 2>/dev/null)

if echo "$LOGS" | grep -q "relation.*does not exist"; then
    echo "❌ ISSUE: Database tables missing"
    echo "   SOLUTION: Run migrations"
    echo "   docker compose -f docker-compose.prod.yml exec backend python manage.py migrate"
    echo ""
fi

if echo "$LOGS" | grep -q "could not connect to server"; then
    echo "❌ ISSUE: Cannot connect to database"
    echo "   SOLUTION: Check database container and credentials"
    echo "   docker compose -f docker-compose.prod.yml ps db"
    echo "   Check DB_* variables in .env"
    echo ""
fi

if echo "$LOGS" | grep -q "SECRET_KEY"; then
    echo "❌ ISSUE: SECRET_KEY not set or invalid"
    echo "   SOLUTION: Generate new SECRET_KEY"
    echo "   python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    echo ""
fi

if echo "$LOGS" | grep -q "Redis.*Connection refused"; then
    echo "❌ ISSUE: Cannot connect to Redis"
    echo "   SOLUTION: Check Redis container"
    echo "   docker compose -f docker-compose.prod.yml ps redis"
    echo "   Check REDIS_URL in .env"
    echo ""
fi

if echo "$LOGS" | grep -q "collectstatic"; then
    echo "⚠ WARNING: Collectstatic in logs (should be skipped now)"
    echo "   This is normal if you haven't pulled latest changes"
    echo ""
fi

if echo "$LOGS" | grep -q "Address already in use"; then
    echo "❌ ISSUE: Port already in use"
    echo "   SOLUTION: Stop conflicting service or change port"
    echo "   sudo lsof -i :8001"
    echo ""
fi

echo ""
echo "Quick Fixes:"
echo "------------"
echo "1. Restart backend:     docker compose -f docker-compose.prod.yml restart backend"
echo "2. View live logs:      docker compose -f docker-compose.prod.yml logs -f backend"
echo "3. Rebuild image:       docker compose -f docker-compose.prod.yml build backend"
echo "4. Full reset:          docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d"
echo ""
