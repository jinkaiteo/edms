#!/bin/bash
#
# Final frontend rebuild with build args
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Final Frontend Rebuild with Build Args${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}This fix adds REACT_APP_API_URL as a Docker build argument${NC}"
echo -e "${YELLOW}so it gets baked into the JavaScript at build time.${NC}"
echo ""

# Stop frontend
echo -e "${BLUE}1. Stopping frontend...${NC}"
docker compose -f docker-compose.prod.yml stop frontend
echo -e "${GREEN}✅ Stopped${NC}"
echo ""

# Remove frontend container and image
echo -e "${BLUE}2. Removing old frontend container and image...${NC}"
docker compose -f docker-compose.prod.yml rm -f frontend
docker rmi edms-staging-frontend 2>/dev/null && echo -e "${GREEN}✅ Image removed${NC}" || echo -e "${YELLOW}⚠️ No image to remove${NC}"
echo ""

# Rebuild with build args
echo -e "${BLUE}3. Rebuilding frontend with build args...${NC}"
echo "Build arg: REACT_APP_API_URL=/api/v1"
docker compose -f docker-compose.prod.yml build --no-cache --build-arg REACT_APP_API_URL=/api/v1 frontend
echo -e "${GREEN}✅ Rebuilt with build args${NC}"
echo ""

# Start frontend
echo -e "${BLUE}4. Starting frontend...${NC}"
docker compose -f docker-compose.prod.yml up -d frontend
echo -e "${GREEN}✅ Started${NC}"
echo ""

# Wait
echo -e "${BLUE}5. Waiting for frontend to be healthy (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

# Verify
echo -e "${BLUE}6. Verification:${NC}"
docker compose -f docker-compose.prod.yml ps frontend
echo ""

# Test
echo -e "${BLUE}7. Testing...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/ 2>/dev/null)
echo "Frontend direct access: $STATUS"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "Frontend through HAProxy: $STATUS"
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Rebuild Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "🧪 IMPORTANT: Clear your browser cache!"
echo ""
echo "The JavaScript bundle has changed."
echo "You MUST clear cache or use incognito mode:"
echo ""
echo "  Chrome Incognito: Ctrl+Shift+N"
echo "  Firefox Private: Ctrl+Shift+P"
echo ""
echo "Then open: http://172.28.1.148"
echo "Login: admin / test123"
echo ""
echo "Check Network tab - should see /api/v1/ not localhost:8000"
echo ""
