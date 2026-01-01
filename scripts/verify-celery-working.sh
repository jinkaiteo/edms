#!/bin/bash
#
# Comprehensive Celery verification script
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Celery Comprehensive Verification${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Test 1: Service Status
echo -e "${BLUE}Test 1: Docker Service Health${NC}"
docker compose -f docker-compose.prod.yml ps celery_worker celery_beat
echo ""

# Test 2: Worker Ping
echo -e "${BLUE}Test 2: Worker Responds to Ping${NC}"
PING=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect ping 2>&1)
if echo "$PING" | grep -q "pong"; then
    echo -e "${GREEN}✅ Worker is responsive${NC}"
else
    echo -e "${RED}❌ Worker not responding${NC}"
fi
echo ""

# Test 3: Registered Tasks Count
echo -e "${BLUE}Test 3: Count Registered Tasks${NC}"
TASK_COUNT=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered 2>&1 | grep "^\s*\*" | wc -l)
echo "Total registered tasks: $TASK_COUNT"
if [ "$TASK_COUNT" -gt 20 ]; then
    echo -e "${GREEN}✅ Good number of tasks registered${NC}"
else
    echo -e "${YELLOW}⚠️ Only $TASK_COUNT tasks registered${NC}"
fi
echo ""

# Test 4: Notification Tasks Present
echo -e "${BLUE}Test 4: Notification Service Tasks${NC}"
NOTIF_TASKS=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered 2>&1 | grep "notification_service" || echo "")
if [ -z "$NOTIF_TASKS" ]; then
    echo -e "${RED}❌ Notification tasks not found${NC}"
else
    echo -e "${GREEN}✅ Notification tasks registered:${NC}"
    echo "$NOTIF_TASKS"
fi
echo ""

# Test 5: Worker Active
echo -e "${BLUE}Test 5: Active Worker Processes${NC}"
ACTIVE=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect active 2>&1)
if echo "$ACTIVE" | grep -q "empty"; then
    echo -e "${GREEN}✅ Worker is idle (no tasks running - normal)${NC}"
else
    echo -e "${BLUE}ℹ️ Worker has active tasks:${NC}"
    echo "$ACTIVE"
fi
echo ""

# Test 6: Beat Scheduler Status
echo -e "${BLUE}Test 6: Celery Beat Scheduling${NC}"
BEAT_LOGS=$(docker compose -f docker-compose.prod.yml logs celery_beat --tail=50 | grep "Scheduler: Sending" | tail -5 || echo "")
if [ -z "$BEAT_LOGS" ]; then
    echo -e "${YELLOW}⚠️ No recent scheduling activity (tasks may be scheduled for later)${NC}"
    echo "Next scheduled times:"
    docker compose -f docker-compose.prod.yml logs celery_beat --tail=100 | grep "due at" | tail -5 || echo "No 'due at' messages found"
else
    echo -e "${GREEN}✅ Beat has sent tasks recently:${NC}"
    echo "$BEAT_LOGS"
fi
echo ""

# Test 7: Manual Task Execution
echo -e "${BLUE}Test 7: Manual Task Execution Test${NC}"
echo "Testing process_notification_queue task..."

TASK_RESULT=$(docker compose -f docker-compose.prod.yml exec backend python -c "
from apps.scheduler.notification_service import process_notification_queue
result = process_notification_queue.delay()
print(f'Task ID: {result.id}')
import time
time.sleep(3)
print(f'Task Status: {result.status}')
print(f'Task Result: {result.result}')
" 2>&1)

echo "$TASK_RESULT"

if echo "$TASK_RESULT" | grep -q "SUCCESS\|success"; then
    echo -e "${GREEN}✅ Task executed successfully!${NC}"
elif echo "$TASK_RESULT" | grep -q "PENDING"; then
    echo -e "${YELLOW}⚠️ Task is pending (may need more time)${NC}"
else
    echo -e "${RED}❌ Task execution failed or incomplete${NC}"
fi
echo ""

# Test 8: Worker Stats
echo -e "${BLUE}Test 8: Worker Statistics${NC}"
STATS=$(docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect stats 2>&1 | head -20)
if echo "$STATS" | grep -q "total"; then
    echo -e "${GREEN}✅ Worker statistics available:${NC}"
    echo "$STATS" | grep -E "total|pool"
else
    echo -e "${YELLOW}⚠️ Could not retrieve worker stats${NC}"
fi
echo ""

# Test 9: Redis Connection
echo -e "${BLUE}Test 9: Redis Connection (Celery Broker)${NC}"
REDIS_TEST=$(docker compose -f docker-compose.prod.yml exec backend python -c "
from celery import current_app
try:
    conn = current_app.connection()
    conn.connect()
    print('Redis connection: OK')
    conn.close()
except Exception as e:
    print(f'Redis connection failed: {e}')
" 2>&1)
echo "$REDIS_TEST"
if echo "$REDIS_TEST" | grep -q "OK"; then
    echo -e "${GREEN}✅ Redis connection working${NC}"
else
    echo -e "${RED}❌ Redis connection issue${NC}"
fi
echo ""

# Test 10: Error Check
echo -e "${BLUE}Test 10: Recent Errors in Logs${NC}"
ERRORS=$(docker compose -f docker-compose.prod.yml logs celery_worker --tail=100 | grep -i "error\|exception\|failed" | tail -5 || echo "")
if [ -z "$ERRORS" ]; then
    echo -e "${GREEN}✅ No recent errors in worker logs${NC}"
else
    echo -e "${YELLOW}⚠️ Found some errors (may be old):${NC}"
    echo "$ERRORS"
fi
echo ""

# Summary
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Verification Summary${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Key Indicators:"
echo "  - Worker responds to ping: Check Test 2"
echo "  - Tasks registered: Check Test 3"
echo "  - Notification tasks present: Check Test 4"
echo "  - Manual task execution: Check Test 7"
echo ""
echo "If all tests show ✅ or ℹ️, Celery is working correctly!"
echo ""
echo "To watch Beat scheduling in real-time:"
echo "  docker compose -f docker-compose.prod.yml logs celery_beat -f"
echo ""
echo "To watch Worker executing tasks:"
echo "  docker compose -f docker-compose.prod.yml logs celery_worker -f"
echo ""
