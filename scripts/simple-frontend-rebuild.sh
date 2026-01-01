#!/bin/bash
#
# Simple frontend rebuild - no complicated checks, just rebuild
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Simple Frontend Rebuild${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${BLUE}Step 1: Stopping all services...${NC}"
docker compose -f docker-compose.prod.yml down
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

echo -e "${BLUE}Step 2: Removing old frontend image...${NC}"
docker rmi edms-staging-frontend 2>/dev/null && echo -e "${GREEN}✅ Old image removed${NC}" || echo -e "${YELLOW}⚠️ No old image to remove (OK)${NC}"
echo ""

echo -e "${BLUE}Step 3: Rebuilding frontend (no cache)...${NC}"
echo "This will take 2-3 minutes..."
docker compose -f docker-compose.prod.yml build --no-cache frontend
echo -e "${GREEN}✅ Frontend rebuilt${NC}"
echo ""

echo -e "${BLUE}Step 4: Starting all services...${NC}"
docker compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo -e "${BLUE}Step 5: Waiting for services to be healthy (60 seconds)...${NC}"
for i in {60..1}; do
    echo -ne "  Waiting... $i seconds remaining\r"
    sleep 1
done
echo ""
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

echo -e "${BLUE}Step 6: Checking service status...${NC}"
docker compose -f docker-compose.prod.yml ps
echo ""

echo -e "${BLUE}Step 7: Verifying environment variable in container...${NC}"
docker compose -f docker-compose.prod.yml exec frontend env | grep REACT_APP_API_URL || echo "Could not read environment"
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Rebuild Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "🧪 TEST IN BROWSER:"
echo "  1. Close all browser tabs for http://172.28.1.148"
echo "  2. Clear browser cache completely:"
echo "     - Chrome: Ctrl+Shift+Delete → Clear browsing data"
echo "     - Firefox: Ctrl+Shift+Delete → Clear all"
echo "  3. Open NEW browser tab: http://172.28.1.148"
echo "  4. Login: admin / test123"
echo "  5. Open DevTools Network tab (F12 → Network)"
echo "  6. Look for XHR requests to /api/v1/ (NOT localhost:8000)"
echo ""
echo "If you still see localhost:8000:"
echo "  - Try a different browser (or incognito mode)"
echo "  - The old JavaScript may be cached"
echo ""
