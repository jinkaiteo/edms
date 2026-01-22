#!/bin/bash
# Verify Fresh Local Deployment - v1.2.0

echo "=============================================="
echo "  Local Deployment Verification - v1.2.0"
echo "  $(date)"
echo "=============================================="
echo ""

# Detect which docker-compose file is running
if docker ps | grep -q "edms_prod"; then
    COMPOSE_FILE="docker-compose.prod.yml"
    PREFIX="edms_prod"
    echo "📋 Detected: Production configuration"
else
    COMPOSE_FILE="docker-compose.yml"
    PREFIX="edms"
    echo "📋 Detected: Development configuration"
fi

echo ""
echo "🔍 1. CONTAINER STATUS"
echo "----------------------------------------------"
docker compose -f $COMPOSE_FILE ps
echo ""

echo "🔍 2. DATABASE VERIFICATION"
echo "----------------------------------------------"
docker compose -f $COMPOSE_FILE exec backend python -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM users WHERE is_active = true')
    print(f'✅ Active users: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM placeholder_definitions WHERE is_active = true')
    count = c.fetchone()[0]
    if count == 32:
        print(f'✅ Placeholders: {count} (CORRECT - v1.2.0)')
    else:
        print(f'❌ Placeholders: {count} (EXPECTED 32)')
    
    c.execute('SELECT COUNT(*) FROM documents')
    print(f'✅ Documents: {c.fetchone()[0]} (expected 0 for fresh deployment)')
    
    c.execute('SELECT COUNT(*) FROM document_workflows')
    print(f'✅ Workflows: {c.fetchone()[0]}')
"
echo ""

echo "🔍 3. CELERY BEAT SCHEDULE"
echo "----------------------------------------------"
docker compose -f $COMPOSE_FILE exec backend python -c "
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all()
count = tasks.count()

if count == 5:
    print(f'✅ Scheduled tasks: {count} (CORRECT - v1.2.0)')
else:
    print(f'❌ Scheduled tasks: {count} (EXPECTED 5)')

print('')
print('Task list:')
for task in tasks:
    status = '✅' if task.enabled else '❌'
    print(f'  {status} {task.name}')
"
echo ""

echo "🔍 4. CELERY WORKER STATUS"
echo "----------------------------------------------"
docker compose -f $COMPOSE_FILE exec backend python -c "
from celery import current_app

inspect = current_app.control.inspect()

# Check worker is responding
stats = inspect.stats()
if stats:
    print('✅ Celery worker is active')
    for worker, info in stats.items():
        print(f'   Worker: {worker}')
else:
    print('❌ Celery worker not responding')

print('')

# Check queues
active_queues = inspect.active_queues()
if active_queues:
    print('✅ Worker queues configured:')
    for worker, queues in active_queues.items():
        for q in queues:
            print(f'   - {q[\"name\"]}')
    
    queue_names = [q['name'] for queues in active_queues.values() for q in queues]
    expected_queues = ['celery', 'scheduler', 'documents', 'workflows', 'maintenance']
    
    if set(expected_queues).issubset(set(queue_names)):
        print('✅ All 5 queues present (v1.2.0 fix)')
    else:
        missing = set(expected_queues) - set(queue_names)
        print(f'❌ Missing queues: {missing}')
else:
    print('❌ No active queues found')
"
echo ""

echo "🔍 5. SCHEDULER MANUAL TRIGGER TEST"
echo "----------------------------------------------"
echo "Testing manual trigger (v1.2.0 timeout fix)..."

START_TIME=$(date +%s%3N)

RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}' 2>&1)

END_TIME=$(date +%s%3N)
ELAPSED=$((END_TIME - START_TIME))

if echo "$RESPONSE" | grep -q "success"; then
    if [ $ELAPSED -lt 2000 ]; then
        echo "✅ Manual trigger: WORKING (${ELAPSED}ms - v1.2.0 fix applied)"
    else
        echo "⚠️  Manual trigger: Works but slow (${ELAPSED}ms)"
    fi
    
    TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
    echo "   Task ID: $TASK_ID"
    
    # Wait and check if task executed
    sleep 3
    
    docker compose -f $COMPOSE_FILE exec backend python -c "
from django_celery_results.models import TaskResult

task = TaskResult.objects.filter(task_id='$TASK_ID').first()
if task:
    print(f'✅ Task executed: Status = {task.status}')
else:
    print('⚠️  Task not found in results (may still be processing)')
    "
else
    echo "❌ Manual trigger: FAILED"
    echo "   Response: $RESPONSE"
fi
echo ""

echo "🔍 6. DASHBOARD STATS API"
echo "----------------------------------------------"
docker compose -f $COMPOSE_FILE exec backend python -c "
from apps.api.dashboard_stats import DashboardStatsView
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_active=True).first()

factory = APIRequestFactory()
request = factory.get('/api/v1/dashboard/stats/')
request.user = user

view = DashboardStatsView()
response = view.get(request)

if response.status_code == 200:
    data = response.data
    print('✅ Dashboard API: WORKING')
    print(f'   Total documents: {data.get(\"total_documents\", 0)}')
    print(f'   Placeholders: {data.get(\"placeholders\", 0)}')
    
    if 'stat_cards' in data:
        cards = data['stat_cards']
        print(f'   Active users (24h): {cards.get(\"active_users_24h\", 0)}')
        print(f'   System health: {cards.get(\"system_health\", \"unknown\")}')
    
    # Verify v1.2.0 fixes
    placeholder_count = data.get('placeholders', 0)
    if placeholder_count == 32:
        print('✅ Dashboard shows correct placeholder count (v1.2.0)')
    else:
        print(f'❌ Dashboard shows wrong placeholder count: {placeholder_count} (expected 32)')
else:
    print(f'❌ Dashboard API: ERROR {response.status_code}')
    print(f'   {response.data}')
"
echo ""

echo "🔍 7. VERSION CHECK"
echo "----------------------------------------------"
git log --oneline -1
echo ""
git describe --tags --always 2>/dev/null || echo "No version tag found (run: git tag v1.2.0)"
echo ""

echo "=============================================="
echo "  Verification Summary"
echo "=============================================="
echo ""
echo "✅ Checks Expected to Pass (v1.2.0):"
echo "   1. All 6 containers running"
echo "   2. 32 placeholders initialized"
echo "   3. 5 scheduled tasks created"
echo "   4. Celery worker active with 5 queues"
echo "   5. Manual trigger responds in <2 seconds"
echo "   6. Tasks execute successfully"
echo "   7. Dashboard API returns real data"
echo ""
echo "📋 Next Steps:"
echo "   - If all checks pass: Ready for v1.3.0 development"
echo "   - If any checks fail: Review logs and fix issues"
echo ""
echo "🔍 Detailed Logs:"
echo "   Backend: docker logs ${PREFIX}_backend --tail=100"
echo "   Worker:  docker logs ${PREFIX}_celery_worker --tail=100"
echo "   Beat:    docker logs ${PREFIX}_celery_beat --tail=100"
echo ""
