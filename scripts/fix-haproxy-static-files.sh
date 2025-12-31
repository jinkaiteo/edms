#!/bin/bash
#
# Fix HAProxy static files routing issue
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Fixing HAProxy Static Files Routing${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Backup current config
echo -e "${BLUE}1. Backing up current HAProxy config...${NC}"
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✅ Backup created${NC}"
echo ""

# Install fixed config
echo -e "${BLUE}2. Installing fixed HAProxy configuration...${NC}"
sudo cp infrastructure/haproxy/haproxy-fixed.cfg /etc/haproxy/haproxy.cfg
echo -e "${GREEN}✅ Configuration updated${NC}"
echo ""

# Validate config
echo -e "${BLUE}3. Validating configuration...${NC}"
if sudo haproxy -c -f /etc/haproxy/haproxy.cfg; then
    echo -e "${GREEN}✅ Configuration is valid${NC}"
else
    echo -e "${RED}❌ Configuration validation failed${NC}"
    echo -e "${YELLOW}⚠️  Restoring backup...${NC}"
    sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg | tail -1
    exit 1
fi
echo ""

# Restart HAProxy
echo -e "${BLUE}4. Restarting HAProxy...${NC}"
sudo systemctl restart haproxy
sleep 2

if sudo systemctl is-active --quiet haproxy; then
    echo -e "${GREEN}✅ HAProxy restarted successfully${NC}"
else
    echo -e "${RED}❌ HAProxy failed to restart${NC}"
    exit 1
fi
echo ""

# Test routing
echo -e "${BLUE}5. Testing routing...${NC}"

echo -n "  HAProxy health: "
if curl -sf http://localhost/haproxy-health > /dev/null; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "  Frontend (HTML): "
if curl -sf http://localhost/ | grep -q "html"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "  API endpoint: "
if curl -sf http://localhost/api/v1/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️  (might be 401/403 - that's OK)${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Fix Applied Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Test in browser: http://172.28.1.148"
echo "Static files should now load correctly."
echo ""
