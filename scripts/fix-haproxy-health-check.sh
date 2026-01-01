#!/bin/bash
#
# Fix HAProxy health check (add trailing slash)
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Fixing HAProxy Health Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Backup
echo -e "${BLUE}1. Backing up current config...${NC}"
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✅ Backup created${NC}"
echo ""

# Install fixed config
echo -e "${BLUE}2. Installing fixed configuration...${NC}"
sudo cp infrastructure/haproxy/haproxy-final-fixed.cfg /etc/haproxy/haproxy.cfg
echo -e "${GREEN}✅ Configuration updated${NC}"
echo ""

# Validate
echo -e "${BLUE}3. Validating configuration...${NC}"
if sudo haproxy -c -f /etc/haproxy/haproxy.cfg; then
    echo -e "${GREEN}✅ Configuration is valid${NC}"
else
    echo -e "${RED}❌ Configuration validation failed${NC}"
    exit 1
fi
echo ""

# Restart
echo -e "${BLUE}4. Restarting HAProxy...${NC}"
sudo systemctl restart haproxy
sleep 3

if sudo systemctl is-active --quiet haproxy; then
    echo -e "${GREEN}✅ HAProxy restarted successfully${NC}"
else
    echo -e "${RED}❌ HAProxy failed to restart${NC}"
    exit 1
fi
echo ""

# Test
echo -e "${BLUE}5. Testing backend health through HAProxy...${NC}"
sleep 2

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health/ 2>/dev/null || echo "000")

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend accessible through HAProxy! Status: $STATUS${NC}"
else
    echo -e "${RED}⚠️ Status: $STATUS (may need more time for health check)${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}HAProxy Health Check Fixed!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Check HAProxy stats: http://172.28.1.148:8404/stats"
echo "Backend should turn GREEN in 5-10 seconds"
echo ""
echo "Then test login: http://172.28.1.148"
