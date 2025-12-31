#!/bin/bash
#
# Check backend health and API endpoints
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Backend Health Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check backend container status
echo -e "${BLUE}1. Backend Container Status:${NC}"
docker compose -f docker-compose.prod.yml ps backend
echo ""

# Check backend logs
echo -e "${BLUE}2. Recent Backend Logs:${NC}"
docker compose -f docker-compose.prod.yml logs backend --tail=30
echo ""

# Test backend directly (bypass HAProxy)
echo -e "${BLUE}3. Direct Backend Tests:${NC}"

echo -n "  Health endpoint (8001): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo -n "  API root (8001): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/ 2>/dev/null)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "401" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo -n "  Auth token endpoint (8001): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/v1/auth/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' 2>/dev/null)
if [ "$STATUS" = "400" ] || [ "$STATUS" = "401" ]; then
    echo -e "${GREEN}✅ $STATUS (expected for invalid creds)${NC}"
elif [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo ""

# Test through HAProxy
echo -e "${BLUE}4. HAProxy Backend Tests:${NC}"

echo -n "  Health through HAProxy: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo -n "  API root through HAProxy: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/ 2>/dev/null)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "401" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo -n "  Auth token through HAProxy: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/v1/auth/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' 2>/dev/null)
if [ "$STATUS" = "400" ] || [ "$STATUS" = "401" ]; then
    echo -e "${GREEN}✅ $STATUS (expected for invalid creds)${NC}"
elif [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ $STATUS${NC}"
else
    echo -e "${RED}❌ $STATUS${NC}"
fi

echo ""

# Check HAProxy backend status
echo -e "${BLUE}5. HAProxy Backend Status:${NC}"
echo "Check stats page: http://172.28.1.148:8404/stats"
echo "Username: admin"
echo "Password: admin_changeme"
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo "If backend is UP but HAProxy can't reach it:"
echo "  - Check backend is listening on 127.0.0.1:8001"
echo "  - Check HAProxy stats page for backend status"
echo "  - Restart backend: docker compose -f docker-compose.prod.yml restart backend"
echo ""
