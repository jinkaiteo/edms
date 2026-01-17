#!/bin/bash
# Comprehensive EDMS Diagnostic Script
# Run this on your staging server

echo "=============================================="
echo "  EDMS Staging Server Diagnostic"
echo "  $(date)"
echo "=============================================="
echo ""

echo "📋 1. GIT STATUS"
echo "----------------------------------------------"
cd ~/edms
git log --oneline -3
echo ""

echo "📊 2. DATABASE COUNTS"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python -c "
from django.db import connection
from django.utils import timezone
from datetime import timedelta

with connection.cursor() as c:
    print('Database Statistics:')
    
    c.execute('SELECT COUNT(*) FROM users WHERE is_active = true')
    print(f'  Total active users: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM documents')
    print(f'  Total documents: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM placeholder_definitions WHERE is_active = true')
    print(f'  Active placeholders: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM document_workflows WHERE is_terminated = false')
    print(f'  Active workflows: {c.fetchone()[0]}')
    
    c.execute('SELECT COUNT(*) FROM login_audit')
    login_total = c.fetchone()[0]
    print(f'  Total login records: {login_total}')
    
    if login_total > 0:
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        c.execute('SELECT COUNT(DISTINCT user_id) FROM login_audit WHERE timestamp >= %s AND success = true', [twenty_four_hours_ago])
        print(f'  Active users (24h): {c.fetchone()[0]}')
        
        c.execute('SELECT username, timestamp, success FROM login_audit JOIN users ON login_audit.user_id = users.id ORDER BY timestamp DESC LIMIT 5')
        print('  Recent logins:')
        for row in c.fetchall():
            print(f'    {row[0]} at {row[1]} (success={row[2]})')
    else:
        print('  ⚠️  No login records found - stat card will show 0')
"
echo ""

echo "🔧 3. CELERY STATUS"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python -c "
from celery import current_app
inspect = current_app.control.inspect()

stats = inspect.stats()
if stats:
    print('✅ Celery worker is active')
    for worker, info in stats.items():
        print(f'  Worker: {worker}')
else:
    print('❌ Celery worker not responding')
"
echo ""

echo "📅 4. SCHEDULED TASKS"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python -c "
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

tasks = PeriodicTask.objects.all()
print(f'Total scheduled tasks: {tasks.count()}')
print('')

for task in tasks:
    status = '✅' if task.enabled else '❌'
    print(f'{status} {task.name}')
    print(f'   Task: {task.task}')
    print(f'   Enabled: {task.enabled}')
    print(f'   Last run: {task.last_run_at or \"Never\"}')
    if task.last_run_at:
        print(f'   Total runs: {task.total_run_count}')
    print('')
"
echo ""

echo "🚨 5. RECENT ERRORS/WARNINGS"
echo "----------------------------------------------"
echo "Backend logs:"
docker logs edms_prod_backend --tail=50 | grep -i "error\|warning" | tail -10
echo ""
echo "Celery worker logs:"
docker logs edms_prod_celery_worker --tail=50 | grep -i "error\|warning" | tail -10
echo ""

echo "📡 6. API TEST - Dashboard Stats"
echo "----------------------------------------------"
echo "Testing dashboard stats API..."
RESPONSE=$(docker compose -f docker-compose.prod.yml exec backend python -c "
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
    print('✅ API working')
    print(f\"  Total documents: {data.get('total_documents', 0)}\")
    print(f\"  Placeholders: {data.get('placeholders', 0)}\")
    if 'stat_cards' in data:
        print(f\"  Active users (24h): {data['stat_cards'].get('active_users_24h', 0)}\")
        print(f\"  System health: {data['stat_cards'].get('system_health', 'unknown')}\")
else:
    print(f'❌ API error: {response.status_code}')
    print(f'   {response.data}')
" 2>&1)
echo "$RESPONSE"
echo ""

echo "🎯 7. MANUAL TRIGGER TEST"
echo "----------------------------------------------"
echo "Testing scheduler manual trigger..."
TRIGGER_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}' 2>&1)

if echo "$TRIGGER_RESPONSE" | grep -q "success"; then
    echo "✅ Manual trigger working"
    echo "$TRIGGER_RESPONSE" | grep -o '"task_id":"[^"]*"' | head -1
else
    echo "❌ Manual trigger issue:"
    echo "$TRIGGER_RESPONSE"
fi
echo ""

echo "=============================================="
echo "  Diagnostic Complete"
echo "=============================================="
echo ""
echo "📝 Summary:"
echo "  - If placeholders = 32: ✅"
echo "  - If active users (24h) = 0: Login audit empty (expected for fresh deployment)"
echo "  - If manual trigger fails: Check authentication or task registration"
echo ""
