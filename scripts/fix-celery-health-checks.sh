#!/bin/bash
#
# Fix Celery health check issue
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Fix Celery Health Check Issue${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will:"
echo "  1. Pull updated docker-compose.prod.yml with proper health checks"
echo "  2. Restart Celery services"
echo "  3. Wait for new health checks to pass"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Pull latest
echo -e "${BLUE}1. Pulling latest configuration...${NC}"
git pull origin develop
echo -e "${GREEN}✅ Updated${NC}"
echo ""

# Restart celery services
echo -e "${BLUE}2. Restarting Celery services...${NC}"
docker compose -f docker-compose.prod.yml restart celery_worker celery_beat
echo -e "${GREEN}✅ Restarted${NC}"
echo ""

# Wait for health checks
echo -e "${BLUE}3. Waiting for health checks (90 seconds)...${NC}"
echo "   start_period is 40s, so health checks begin after that"
sleep 90
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

# Check status
echo -e "${BLUE}4. Checking service status...${NC}"
docker compose -f docker-compose.prod.yml ps celery_worker celery_beat
echo ""

# Check if still unhealthy
WORKER_STATUS=$(docker compose -f docker-compose.prod.yml ps celery_worker --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)
BEAT_STATUS=$(docker compose -f docker-compose.prod.yml ps celery_beat --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)

echo -e "${BLUE}5. Health Status:${NC}"
echo "   Worker: $WORKER_STATUS"
echo "   Beat: $BEAT_STATUS"
echo ""

if [[ "$WORKER_STATUS" == "healthy" ]]; then
    echo -e "${GREEN}✅ Celery Worker is now healthy!${NC}"
else
    echo -e "${RED}⚠️ Worker still showing: $WORKER_STATUS${NC}"
    echo "   This is OK if tasks are import errors (see CELERY_STATUS_REPORT.md)"
fi

if [[ "$BEAT_STATUS" == "healthy" ]] || [[ "$BEAT_STATUS" == "" ]]; then
    echo -e "${GREEN}✅ Celery Beat health check updated${NC}"
else
    echo -e "${RED}⚠️ Beat still showing: $BEAT_STATUS${NC}"
fi

echo ""
echo -e "${BLUE}Note: Beat may show 'starting' or 'unhealthy' even though it works.${NC}"
echo -e "${BLUE}Check logs to verify it's sending tasks:${NC}"
echo ""
echo "  docker compose -f docker-compose.prod.yml logs celery_beat --tail=20 | grep 'Sending'"
echo ""
