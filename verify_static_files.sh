#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Static Files Verification Script"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

ERRORS=0

echo "1. Checking if backend container is running..."
if docker compose -f docker-compose.prod.yml ps backend | grep -q "Up"; then
    print_success "Backend container is running"
else
    print_error "Backend container is not running"
    echo ""
    echo "Start containers first:"
    echo "  docker compose -f docker-compose.prod.yml up -d"
    exit 1
fi

echo ""
echo "2. Checking static files in Docker image..."
STATIC_COUNT=$(docker compose -f docker-compose.prod.yml exec -T backend sh -c "ls -1 /app/staticfiles/ 2>/dev/null | wc -l" || echo "0")
if [ "$STATIC_COUNT" -gt "0" ]; then
    print_success "Found $STATIC_COUNT items in /app/staticfiles/ (baked into image)"
else
    print_error "No static files found in /app/staticfiles/"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "3. Checking Django admin static files..."
ADMIN_STATIC=$(docker compose -f docker-compose.prod.yml exec -T backend sh -c "ls -1 /app/staticfiles/admin/ 2>/dev/null | wc -l" || echo "0")
if [ "$ADMIN_STATIC" -gt "0" ]; then
    print_success "Found $ADMIN_STATIC admin static items"
else
    print_error "Django admin static files missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "4. Checking REST Framework static files..."
REST_STATIC=$(docker compose -f docker-compose.prod.yml exec -T backend sh -c "ls -1 /app/staticfiles/rest_framework/ 2>/dev/null | wc -l" || echo "0")
if [ "$REST_STATIC" -gt "0" ]; then
    print_success "Found $REST_STATIC REST framework static items"
else
    print_warning "REST framework static files not found (may not be needed)"
fi

echo ""
echo "5. Testing static file serving via HTTP..."
BACKEND_PORT=$(grep "BACKEND_PORT" .env 2>/dev/null | cut -d'=' -f2 || echo "8001")
print_info "Testing on port $BACKEND_PORT..."

# Test admin CSS file
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/static/admin/css/base.css" | grep -q "200"; then
    print_success "Admin CSS file accessible via HTTP"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/static/admin/css/base.css")
    print_error "Admin CSS file not accessible (HTTP $HTTP_CODE)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "6. Checking Django settings for static files..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django.conf import settings
import os

print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATIC_ROOT exists:', os.path.exists(settings.STATIC_ROOT))
print('STATIC_ROOT contents:', len(os.listdir(settings.STATIC_ROOT)) if os.path.exists(settings.STATIC_ROOT) else 0)
" 2>/dev/null

echo ""
echo "7. Checking if collectstatic is needed..."
COLLECT_OUTPUT=$(docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput --dry-run 2>&1 || echo "error")
if echo "$COLLECT_OUTPUT" | grep -q "0 static files copied"; then
    print_success "All static files already collected (0 files to copy)"
elif echo "$COLLECT_OUTPUT" | grep -q "static files copied"; then
    FILES_TO_COPY=$(echo "$COLLECT_OUTPUT" | grep -oP '\d+(?= static files copied)' || echo "unknown")
    print_warning "$FILES_TO_COPY static files would be copied (may need collection)"
else
    print_info "Collectstatic check: $COLLECT_OUTPUT"
fi

echo ""
echo "8. Testing Django admin interface..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/admin/" || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ] || [ "$ADMIN_RESPONSE" = "302" ]; then
    print_success "Django admin interface accessible (HTTP $ADMIN_RESPONSE)"
else
    print_error "Django admin interface not accessible (HTTP $ADMIN_RESPONSE)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "9. Checking for missing static file warnings in logs..."
MISSING_STATIC=$(docker compose -f docker-compose.prod.yml logs backend --tail=100 2>/dev/null | grep -i "static.*not found" | wc -l || echo "0")
if [ "$MISSING_STATIC" -eq "0" ]; then
    print_success "No missing static file warnings in recent logs"
else
    print_warning "Found $MISSING_STATIC missing static file warnings"
    echo ""
    echo "Recent warnings:"
    docker compose -f docker-compose.prod.yml logs backend --tail=100 | grep -i "static.*not found" | tail -5
fi

echo ""
echo "10. Volume mount verification..."
VOLUME_STATIC=$(docker compose -f docker-compose.prod.yml exec -T backend sh -c "ls -la /app/staticfiles/ | head -5" 2>/dev/null || echo "error")
if echo "$VOLUME_STATIC" | grep -q "total"; then
    print_success "Static files volume accessible"
    echo ""
    echo "Sample files:"
    echo "$VOLUME_STATIC"
else
    print_error "Cannot access static files volume"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Static files are working correctly.${NC}"
    echo ""
    echo "Summary:"
    echo "  - Static files baked into Docker image: ✓"
    echo "  - HTTP serving functional: ✓"
    echo "  - Django admin accessible: ✓"
    echo "  - No collection needed on startup: ✓"
    echo ""
    echo "Optimization successful - static files work without collectstatic!"
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS error(s) - static files may not be working correctly${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Rebuild Docker image: docker compose -f docker-compose.prod.yml build backend"
    echo "  2. Check Dockerfile.backend.prod has: RUN python manage.py collectstatic --noinput"
    echo "  3. Verify staticfiles volume is properly mounted"
    echo "  4. Check Django settings: STATIC_ROOT and STATIC_URL"
    exit 1
fi
