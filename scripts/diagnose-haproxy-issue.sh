#!/bin/bash
#
# Diagnose HAProxy startup issue
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}HAProxy Diagnostic Tool${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check HAProxy status
echo -e "${BLUE}1. HAProxy Service Status:${NC}"
systemctl status haproxy.service --no-pager -l
echo ""

# Check HAProxy logs
echo -e "${BLUE}2. Recent HAProxy Logs:${NC}"
journalctl -u haproxy -n 50 --no-pager
echo ""

# Test configuration
echo -e "${BLUE}3. Configuration Test:${NC}"
haproxy -c -f /etc/haproxy/haproxy.cfg
echo ""

# Check if ports are already in use
echo -e "${BLUE}4. Port Usage Check:${NC}"
echo "Port 80:"
netstat -tuln | grep ":80 " || echo "  Not in use"
echo ""
echo "Port 8404:"
netstat -tuln | grep ":8404 " || echo "  Not in use"
echo ""

# Check if Docker services are running
echo -e "${BLUE}5. Docker Services:${NC}"
docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo "  Docker compose not found or not running"
echo ""

# Check permissions
echo -e "${BLUE}6. HAProxy Configuration Permissions:${NC}"
ls -la /etc/haproxy/haproxy.cfg
echo ""

# Check for syntax errors
echo -e "${BLUE}7. Detailed Configuration Check:${NC}"
haproxy -f /etc/haproxy/haproxy.cfg -c -V
