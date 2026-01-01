#!/bin/bash
#
# Test Celery tasks on staging server
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Test Celery Tasks on Staging${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will:"
echo "  1. Pull latest code with task fixes"
echo "  2. Restart Celery services"
echo "  3. Check registered tasks"
echo "  4. Test task execution"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Pull latest
echo -e "${BLUE}1. Pulling latest code...${NC}"
git pull origin develop
echo -e "${GREEN}✅ Code updated${NC}"
echo ""

# Restart Celery services
echo -e "${BLUE}2. Restarting Celery services...${NC}"
docker compose -f docker-compose.prod.yml restart celery_worker celery_beat
echo -e "${GREEN}✅ Services restarted${NC}"
echo ""

# Wait for startup
echo -e "${BLUE}3. Waiting for services to start (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

# Check registered tasks
echo -e "${BLUE}4. Checking registered tasks...${NC}"
echo ""
docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered || echo "Could not inspect tasks"
echo ""

# Check for our specific tasks
echo -e "${BLUE}5. Looking for notification service tasks...${NC}"
TASKS=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered 2>/dev/null | grep -E "process_notification_queue|send_daily_summary" || echo "")

if [ -z "$TASKS" ]; then
    echo -e "${RED}❌ Notification tasks not found in registered tasks${NC}"
    echo ""
    echo "Checking worker logs for errors:"
    docker compose -f docker-compose.prod.yml logs celery_worker --tail=30 | grep -i error
else
    echo -e "${GREEN}✅ Found notification service tasks:${NC}"
    echo "$TASKS"
fi
echo ""

# Check Beat logs for scheduling
echo -e "${BLUE}6. Checking Celery Beat scheduling...${NC}"
BEAT_LOGS=$(docker compose -f docker-compose.prod.yml logs celery_beat --tail=20 | grep "Scheduler: Sending" || echo "No recent scheduling activity")
if [ "$BEAT_LOGS" = "No recent scheduling activity" ]; then
    echo -e "${YELLOW}⚠️ No recent scheduling activity (tasks may be scheduled for later)${NC}"
else
    echo -e "${GREEN}✅ Beat is scheduling tasks:${NC}"
    echo "$BEAT_LOGS"
fi
echo ""

# Check worker health
echo -e "${BLUE}7. Testing worker health...${NC}"
PING_RESULT=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect ping 2>&1)
if echo "$PING_RESULT" | grep -q "pong"; then
    echo -e "${GREEN}✅ Worker responds to ping${NC}"
else
    echo -e "${RED}❌ Worker does not respond to ping${NC}"
fi
echo ""

# Service status
echo -e "${BLUE}8. Final service status:${NC}"
docker compose -f docker-compose.prod.yml ps celery_worker celery_beat
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Summary:"
echo "  - Pull the output above to verify tasks are registered"
echo "  - Worker should respond to ping"
echo "  - Beat should show scheduling activity (or wait for scheduled times)"
echo ""
echo "To manually trigger a task for testing:"
echo "  docker compose -f docker-compose.prod.yml exec backend python manage.py shell"
echo "  >>> from apps.scheduler.notification_service import process_notification_queue"
echo "  >>> result = process_notification_queue.delay()"
echo "  >>> print(result.id)"
echo ""
