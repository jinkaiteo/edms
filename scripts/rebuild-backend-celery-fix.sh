#!/bin/bash
#
# Rebuild backend image with Celery task fixes
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Rebuild Backend with Celery Task Fixes${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will:"
echo "  1. Stop Celery services"
echo "  2. Rebuild backend image (includes celery workers)"
echo "  3. Restart all services"
echo "  4. Verify tasks are registered"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Stop celery services
echo -e "${BLUE}1. Stopping Celery services...${NC}"
docker compose -f docker-compose.prod.yml stop celery_worker celery_beat
echo -e "${GREEN}✅ Stopped${NC}"
echo ""

# Rebuild backend image
echo -e "${BLUE}2. Rebuilding backend image...${NC}"
echo "This will take 2-3 minutes..."
docker compose -f docker-compose.prod.yml build backend celery_worker celery_beat
echo -e "${GREEN}✅ Backend rebuilt${NC}"
echo ""

# Start services
echo -e "${BLUE}3. Starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Wait for startup
echo -e "${BLUE}4. Waiting for services to start (45 seconds)...${NC}"
sleep 45
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

# Check registered tasks
echo -e "${BLUE}5. Checking registered tasks...${NC}"
echo ""
TASKS=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered 2>&1)
echo "$TASKS"
echo ""

# Check for notification tasks
echo -e "${BLUE}6. Verifying notification service tasks...${NC}"
if echo "$TASKS" | grep -q "notification_service"; then
    echo -e "${GREEN}✅ Found notification_service tasks!${NC}"
    echo "$TASKS" | grep "notification_service"
else
    echo -e "${RED}❌ Notification tasks still not found${NC}"
    echo ""
    echo "Checking if file was updated in container:"
    docker compose -f docker-compose.prod.yml exec backend grep -n "process_notification_queue" apps/scheduler/notification_service.py || echo "Task not found in file"
fi
echo ""

# Check worker ping
echo -e "${BLUE}7. Testing worker health...${NC}"
PING=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect ping 2>&1)
if echo "$PING" | grep -q "pong"; then
    echo -e "${GREEN}✅ Worker responds to ping${NC}"
else
    echo -e "${RED}❌ Worker not responding${NC}"
fi
echo ""

# Service status
echo -e "${BLUE}8. Service status:${NC}"
docker compose -f docker-compose.prod.yml ps backend celery_worker celery_beat
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Rebuild Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "If notification tasks are now registered, Celery is fixed!"
echo "If not, there may be a Python syntax error in notification_service.py"
echo ""
