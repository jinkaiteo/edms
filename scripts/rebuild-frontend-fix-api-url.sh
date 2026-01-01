#!/bin/bash
#
# Rebuild frontend with correct API URL
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Rebuild Frontend with Correct API URL${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check current environment variable
echo -e "${BLUE}1. Checking current REACT_APP_API_URL...${NC}"
CURRENT_API_URL=$(grep "REACT_APP_API_URL" docker-compose.prod.yml | grep -v "#" | head -1 | awk -F'=' '{print $2}')
echo "Current: $CURRENT_API_URL"

if [[ "$CURRENT_API_URL" == "/api/v1" ]]; then
    echo -e "${GREEN}✅ Environment variable is correct: /api/v1${NC}"
else
    echo -e "${RED}❌ Environment variable needs fixing${NC}"
    exit 1
fi
echo ""

# Stop frontend
echo -e "${BLUE}2. Stopping frontend container...${NC}"
docker compose -f docker-compose.prod.yml stop frontend
echo -e "${GREEN}✅ Frontend stopped${NC}"
echo ""

# Remove old container
echo -e "${BLUE}3. Removing old frontend container...${NC}"
docker compose -f docker-compose.prod.yml rm -f frontend
echo -e "${GREEN}✅ Old container removed${NC}"
echo ""

# Rebuild frontend with no cache
echo -e "${BLUE}4. Rebuilding frontend (no cache)...${NC}"
echo "This will bake REACT_APP_API_URL=/api/v1 into the build"
docker compose -f docker-compose.prod.yml build --no-cache frontend
echo -e "${GREEN}✅ Frontend rebuilt${NC}"
echo ""

# Start frontend
echo -e "${BLUE}5. Starting frontend container...${NC}"
docker compose -f docker-compose.prod.yml up -d frontend
echo -e "${GREEN}✅ Frontend started${NC}"
echo ""

# Wait for health check
echo -e "${BLUE}6. Waiting for frontend to be healthy (30 seconds)...${NC}"
sleep 30

# Check status
STATUS=$(docker compose -f docker-compose.prod.yml ps frontend --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)
if [[ "$STATUS" == "healthy" ]]; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend status: $STATUS (may need more time)${NC}"
fi
echo ""

# Test frontend
echo -e "${BLUE}7. Testing frontend through HAProxy...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend accessible. Status: $FRONTEND_STATUS${NC}"
else
    echo -e "${RED}❌ Frontend not accessible. Status: $FRONTEND_STATUS${NC}"
fi
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Frontend Rebuilt Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "The frontend has been rebuilt with REACT_APP_API_URL=/api/v1"
echo "All API calls should now use relative paths through HAProxy."
echo ""
echo "Test in browser:"
echo "  1. Clear browser cache (Ctrl+Shift+R)"
echo "  2. Open: http://172.28.1.148"
echo "  3. Login and check browser console for CORS errors"
echo ""
echo "Expected: No more 'localhost:8000' CORS errors"
