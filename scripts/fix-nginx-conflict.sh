#!/bin/bash
#
# Fix nginx container conflict with HAProxy
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Fix Nginx Container Conflict${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${BLUE}The nginx container is trying to use port 80,${NC}"
echo -e "${BLUE}but HAProxy is already using it.${NC}"
echo ""
echo -e "${BLUE}We'll start services WITHOUT the nginx container.${NC}"
echo ""

# Stop everything first
echo -e "${BLUE}Stopping all services...${NC}"
docker compose -f docker-compose.prod.yml down
echo -e "${GREEN}✅ Stopped${NC}"
echo ""

# Start services without nginx
echo -e "${BLUE}Starting services (excluding nginx)...${NC}"
docker compose -f docker-compose.prod.yml up -d db redis backend celery_worker celery_beat frontend
echo -e "${GREEN}✅ Services started (without nginx)${NC}"
echo ""

# Wait for health
echo -e "${BLUE}Waiting for services to be healthy (45 seconds)...${NC}"
sleep 45
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

# Show status
echo -e "${BLUE}Service status:${NC}"
docker compose -f docker-compose.prod.yml ps
echo ""

# Verify HAProxy is still running
echo -e "${BLUE}Checking HAProxy...${NC}"
if sudo systemctl is-active --quiet haproxy; then
    echo -e "${GREEN}✅ HAProxy is running${NC}"
else
    echo -e "${RED}❌ HAProxy is not running${NC}"
    echo "Starting HAProxy..."
    sudo systemctl start haproxy
fi
echo ""

# Test
echo -e "${BLUE}Testing access...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend accessible through HAProxy (Status: $STATUS)${NC}"
else
    echo -e "${RED}⚠️ Status: $STATUS${NC}"
fi
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Services Running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Architecture:"
echo "  User → HAProxy (port 80) → Frontend (port 3001) + Backend (port 8001)"
echo ""
echo "The standalone nginx container is NOT needed."
echo "Frontend container has its own nginx built-in."
echo ""
echo "Test: http://172.28.1.148"
