#!/bin/bash
#
# Force rebuild backend container with latest code
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Force Rebuild Backend Container${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Pull latest code
echo -e "${BLUE}1. Pulling latest code from git...${NC}"
git pull origin develop
echo -e "${GREEN}✅ Code updated${NC}"
echo ""

# Step 2: Stop backend
echo -e "${BLUE}2. Stopping backend container...${NC}"
docker compose -f docker-compose.prod.yml stop backend
echo -e "${GREEN}✅ Backend stopped${NC}"
echo ""

# Step 3: Remove old container
echo -e "${BLUE}3. Removing old backend container...${NC}"
docker compose -f docker-compose.prod.yml rm -f backend
echo -e "${GREEN}✅ Old container removed${NC}"
echo ""

# Step 4: Rebuild without cache
echo -e "${BLUE}4. Rebuilding backend (no cache)...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache backend
echo -e "${GREEN}✅ Backend rebuilt${NC}"
echo ""

# Step 5: Start backend
echo -e "${BLUE}5. Starting backend container...${NC}"
docker compose -f docker-compose.prod.yml up -d backend
echo -e "${GREEN}✅ Backend started${NC}"
echo ""

# Step 6: Wait and check status
echo -e "${BLUE}6. Waiting for backend to start (30 seconds)...${NC}"
sleep 30

echo -e "${BLUE}7. Checking backend status...${NC}"
docker compose -f docker-compose.prod.yml ps backend
echo ""

# Step 8: Test backend
echo -e "${BLUE}8. Testing backend health...${NC}"
sleep 5

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend is healthy! Status: $STATUS${NC}"
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Success! Backend is running.${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "Test login at: http://172.28.1.148"
else
    echo -e "${RED}❌ Backend health check failed. Status: $STATUS${NC}"
    echo ""
    echo "Check logs:"
    echo "  docker compose -f docker-compose.prod.yml logs backend --tail=50"
fi
