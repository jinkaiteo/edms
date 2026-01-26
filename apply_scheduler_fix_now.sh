#!/bin/bash

echo "=========================================="
echo "Applying Scheduler Fix to Staging"
echo "=========================================="

# Add the setting to base.py
echo "Step 1: Adding CELERY_BEAT_SCHEDULER to settings..."

cat >> backend/edms/settings/base.py << 'SETTING'

# Celery Beat Scheduler - Use database for task execution tracking
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
SETTING

echo "✓ Setting added to base.py"

# Verify it was added
echo ""
echo "Step 2: Verifying setting was added..."
grep "CELERY_BEAT_SCHEDULER" backend/edms/settings/base.py && echo "✓ Verified" || echo "✗ Failed to add setting"

# Restart celery_beat
echo ""
echo "Step 3: Restarting Celery Beat..."
docker compose restart celery_beat

echo "Waiting 10 seconds for restart..."
sleep 10

echo ""
echo "✓ Celery Beat restarted"

# Verify the setting is loaded
echo ""
echo "Step 4: Verifying setting is loaded in Django..."
docker compose exec -T backend python -c "from django.conf import settings; scheduler = getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT SET'); print(f'CELERY_BEAT_SCHEDULER: {scheduler}'); print('✓ Success!' if 'DatabaseScheduler' in scheduler else '✗ Not loaded - may need container rebuild')"

echo ""
echo "=========================================="
echo "Fix Applied!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 30 minutes for tasks to run"
echo "2. Check status with:"
echo "   docker compose exec -T backend python -c \"from django_celery_beat.models import PeriodicTask; [print(f'{t.name}: {t.last_run_at}') for t in PeriodicTask.objects.all()[:3]]\""
echo ""
echo "3. If still shows 'NOT SET', rebuild container:"
echo "   docker compose stop celery_beat"
echo "   docker compose build celery_beat"
echo "   docker compose up -d celery_beat"
echo ""
