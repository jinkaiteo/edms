#!/bin/bash
#
# Verify environment variable and force complete rebuild
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Verify and Force Frontend Rebuild${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check docker-compose file
echo -e "${BLUE}1. Checking docker-compose.prod.yml...${NC}"
COMPOSE_API_URL=$(grep -A 2 "frontend:" docker-compose.prod.yml | grep "REACT_APP_API_URL" | head -1 | cut -d'=' -f2)
echo "REACT_APP_API_URL in docker-compose: $COMPOSE_API_URL"

if [[ "$COMPOSE_API_URL" == "/api/v1" ]]; then
    echo -e "${GREEN}✅ Correct in docker-compose.prod.yml${NC}"
else
    echo -e "${RED}❌ WRONG in docker-compose.prod.yml: $COMPOSE_API_URL${NC}"
    echo "Expected: /api/v1"
    exit 1
fi
echo ""

# Check running container
echo -e "${BLUE}2. Checking running container environment...${NC}"
CONTAINER_API_URL=$(docker compose -f docker-compose.prod.yml exec frontend env 2>/dev/null | grep REACT_APP_API_URL | cut -d'=' -f2)
echo "REACT_APP_API_URL in container: $CONTAINER_API_URL"

if [[ "$CONTAINER_API_URL" == "/api/v1" ]]; then
    echo -e "${GREEN}✅ Correct in running container${NC}"
else
    echo -e "${YELLOW}⚠️  Container has old value: $CONTAINER_API_URL${NC}"
    echo "Container needs rebuild!"
fi
echo ""

# Force complete rebuild
echo -e "${BLUE}3. Forcing complete rebuild...${NC}"
echo ""

echo -e "${YELLOW}Stopping all services...${NC}"
docker compose -f docker-compose.prod.yml down

echo -e "${YELLOW}Removing frontend image...${NC}"
docker rmi edms-staging-frontend 2>/dev/null || echo "Image not found (OK)"

echo -e "${YELLOW}Rebuilding frontend with no cache...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo -e "${YELLOW}Starting all services...${NC}"
docker compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}✅ Complete rebuild done${NC}"
echo ""

# Wait for services
echo -e "${BLUE}4. Waiting for services to start (45 seconds)...${NC}"
sleep 45

# Verify
echo -e "${BLUE}5. Final verification...${NC}"
FINAL_API_URL=$(docker compose -f docker-compose.prod.yml exec frontend env 2>/dev/null | grep REACT_APP_API_URL | cut -d'=' -f2)
echo "REACT_APP_API_URL in new container: $FINAL_API_URL"

if [[ "$FINAL_API_URL" == "/api/v1" ]]; then
    echo -e "${GREEN}✅ SUCCESS! Container has correct API URL${NC}"
else
    echo -e "${RED}❌ FAILED! Container still has: $FINAL_API_URL${NC}"
    exit 1
fi

# Check services
echo ""
echo -e "${BLUE}6. Service Status:${NC}"
docker compose -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Rebuild Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Now test in browser:"
echo "  1. Clear browser cache: Ctrl+Shift+R"
echo "  2. Open: http://172.28.1.148"
echo "  3. Login: admin / test123"
echo "  4. Check Network tab (F12)"
echo ""
echo "Expected: API calls to /api/v1/... (NOT localhost:8000)"
