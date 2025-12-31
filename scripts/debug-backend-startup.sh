#!/bin/bash
#
# Debug backend startup issues
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Backend Startup Debugging${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check container status
echo -e "${BLUE}1. Container Status:${NC}"
docker compose -f docker-compose.prod.yml ps backend
echo ""

# Get full logs
echo -e "${BLUE}2. Full Backend Logs (last 100 lines):${NC}"
docker compose -f docker-compose.prod.yml logs backend --tail=100
echo ""

# Check if container is restarting
echo -e "${BLUE}3. Container Restart Count:${NC}"
docker inspect edms_prod_backend --format='{{.RestartCount}}' 2>/dev/null || echo "Container not found"
echo ""

# Check environment variables
echo -e "${BLUE}4. Environment Check:${NC}"
echo "DJANGO_SETTINGS_MODULE:"
docker compose -f docker-compose.prod.yml exec backend env | grep DJANGO_SETTINGS_MODULE || echo "  Not set or container not running"
echo ""

# Try to run Django check manually
echo -e "${BLUE}5. Manual Django Check:${NC}"
echo "Attempting to run Django system check..."
docker compose -f docker-compose.prod.yml exec backend python manage.py check 2>&1 || echo "Failed - container not accessible"
echo ""

echo -e "${BLUE}================================================${NC}"
echo "Look for error messages in the logs above."
echo "Common issues:"
echo "  - Missing environment variables"
echo "  - Database connection issues"
echo "  - Import errors"
echo "  - Middleware configuration errors"
echo ""
