#!/bin/bash

################################################################################
# Fresh Staging Deployment - Complete Setup
################################################################################
# This script sets up EDMS on a clean staging server from scratch
# with all fixes applied correctly
################################################################################

set -e

echo "=========================================="
echo "EDMS Fresh Staging Deployment"
echo "=========================================="
echo "Date: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running as correct user
if [ "$USER" = "root" ]; then
    print_error "Do not run as root. Run as 'lims' user."
    exit 1
fi

print_step "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { print_error "Docker not installed"; exit 1; }
command -v git >/dev/null 2>&1 || { print_error "Git not installed"; exit 1; }
print_success "Prerequisites OK"

echo ""
print_step "Step 1: Clean up old deployment (if exists)"
cd ~
if [ -d "edms" ]; then
    print_warning "Old edms directory exists. Backing up..."
    mv edms edms.backup.$(date +%Y%m%d_%H%M%S)
fi

if docker compose ps 2>/dev/null | grep -q "edms"; then
    print_warning "Old containers running. Stopping..."
    cd edms.backup.* 2>/dev/null && docker compose down -v || true
fi

print_success "Cleanup complete"

echo ""
print_step "Step 2: Clone repository"
cd ~
git clone https://github.com/jinkaiteo/edms.git
cd edms
print_success "Repository cloned"

echo ""
print_step "Step 3: Create .env file with correct settings"
cat > .env << 'ENVEOF'
# ==============================================================================
# EDMS STAGING ENVIRONMENT CONFIGURATION
# ==============================================================================

# ==============================================================================
# DJANGO CORE SETTINGS
# ==============================================================================

SECRET_KEY=$(openssl rand -base64 48)
DEBUG=False
ENVIRONMENT=staging
ALLOWED_HOSTS=edms-server,172.25.223.190,localhost,127.0.0.1

# ==============================================================================
# APPLICATION BRANDING
# ==============================================================================

REACT_APP_TITLE=EDMS Staging

# ==============================================================================
# DOCKER PORT CONFIGURATION
# ==============================================================================

BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
REDIS_PORT=6380

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DB_NAME=edms_staging
DB_USER=edms_staging_user
DB_PASSWORD=password1234
DB_HOST=db
DB_PORT=5432

# ==============================================================================
# REDIS CONFIGURATION
# ==============================================================================

REDIS_URL=redis://redis:6379/1
REDIS_PASSWORD=

# ==============================================================================
# CELERY CONFIGURATION - CRITICAL FIX
# ==============================================================================

CELERY_BROKER_URL=redis://redis:6379/0
# DO NOT SET CELERY_RESULT_BACKEND here - it's configured in settings/base.py as django-db

# ==============================================================================
# ENCRYPTION
# ==============================================================================

EDMS_MASTER_KEY=$(openssl rand -base64 32)

# ==============================================================================
# CORS & SECURITY
# ==============================================================================

CORS_ALLOWED_ORIGINS=http://172.25.223.190:3001,http://edms-server:3001
CSRF_TRUSTED_ORIGINS=http://172.25.223.190:3001,http://edms-server:3001
SESSION_COOKIE_AGE=3600
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE=Lax

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=jinkaiteo.tikva@gmail.com
EMAIL_HOST_PASSWORD=wpxatoqshfwubfsy
DEFAULT_FROM_EMAIL=jinkaiteo.tikva@gmail.com

# ==============================================================================
# LOGGING & MONITORING
# ==============================================================================

LOG_LEVEL=INFO

# ==============================================================================
# JWT AUTHENTICATION
# ==============================================================================

JWT_ACCESS_TOKEN_LIFETIME_HOURS=8
JWT_REFRESH_TOKEN_LIFETIME_DAYS=1
JWT_ROTATE_REFRESH_TOKENS=True

# ==============================================================================
# PERFORMANCE
# ==============================================================================

DB_CONN_MAX_AGE=60
DB_MAX_CONNECTIONS=20
CACHE_TTL=900

# ==============================================================================
# LOCALIZATION
# ==============================================================================

TZ=UTC
LANGUAGE_CODE=en-us
ENVEOF

print_success ".env file created"

echo ""
print_step "Step 4: Verify settings/base.py has correct configuration"
echo "Checking CELERY_RESULT_BACKEND..."

if grep -q "CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND'" backend/edms/settings/base.py; then
    print_error "Found problematic line in settings/base.py"
    print_warning "The duplicate CELERY_RESULT_BACKEND line should already be removed from latest code"
    print_warning "If not, the git pull didn't work correctly"
fi

# Verify the correct line exists
if grep -q 'CELERY_RESULT_BACKEND = "django-db"' backend/edms/settings/base.py; then
    print_success "Correct CELERY_RESULT_BACKEND configuration found"
else
    print_error "Missing django-db configuration"
    exit 1
fi

# Add CELERY_BEAT_SCHEDULER if missing
if ! grep -q "CELERY_BEAT_SCHEDULER" backend/edms/settings/base.py; then
    print_warning "Adding CELERY_BEAT_SCHEDULER setting..."
    cat >> backend/edms/settings/base.py << 'PYEOF'

# Celery Beat Scheduler - Use database for task execution tracking
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
PYEOF
    print_success "CELERY_BEAT_SCHEDULER added"
fi

echo ""
print_step "Step 5: Build Docker images"
docker compose build --no-cache
print_success "Docker images built"

echo ""
print_step "Step 6: Start containers"
docker compose up -d
print_success "Containers started"

echo ""
print_step "Step 7: Wait for containers to be healthy"
echo "Waiting 60 seconds for database initialization..."
sleep 60

# Check container health
HEALTHY=0
for i in {1..30}; do
    if docker compose ps | grep -q "healthy.*healthy.*healthy"; then
        HEALTHY=1
        break
    fi
    echo "Waiting for containers to be healthy... ($i/30)"
    sleep 5
done

if [ $HEALTHY -eq 0 ]; then
    print_error "Containers did not become healthy"
    docker compose ps
    exit 1
fi

print_success "Containers healthy"

echo ""
print_step "Step 8: Run database migrations"
docker compose exec -T backend python manage.py migrate --noinput
print_success "Migrations complete"

echo ""
print_step "Step 9: Create superuser"
docker compose exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@edms.local', 'admin')
    print('Superuser created')
else:
    print('Superuser already exists')
"
print_success "Superuser ready (admin/admin)"

echo ""
print_step "Step 10: Initialize system defaults"
docker compose exec -T backend python manage.py shell -c "
# Initialize workflow types and states
from apps.workflows.models import WorkflowType, WorkflowState, WorkflowTransition
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

# Create workflow type
wf_type, _ = WorkflowType.objects.get_or_create(
    code='STANDARD',
    defaults={
        'name': 'Standard Document Review',
        'description': 'Standard review and approval workflow',
        'created_by': admin
    }
)

# Create states
draft, _ = WorkflowState.objects.get_or_create(
    code='DRAFT',
    defaults={'name': 'Draft', 'description': 'Initial draft state'}
)

under_review, _ = WorkflowState.objects.get_or_create(
    code='UNDER_REVIEW',
    defaults={'name': 'Under Review', 'description': 'Document is being reviewed'}
)

approved, _ = WorkflowState.objects.get_or_create(
    code='APPROVED',
    defaults={'name': 'Approved', 'description': 'Document has been approved'}
)

effective, _ = WorkflowState.objects.get_or_create(
    code='EFFECTIVE',
    defaults={'name': 'Effective', 'description': 'Document is effective'}
)

print('✓ Workflow defaults initialized')
"

echo ""
print_step "Step 11: Setup periodic tasks in database"
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from celery import current_app

# Get tasks from celery config
beat_schedule = current_app.conf.beat_schedule or {}

print(f'Setting up {len(beat_schedule)} periodic tasks...')

for task_name, task_config in beat_schedule.items():
    task_path = task_config['task']
    schedule_config = task_config['schedule']
    
    # Create crontab from schedule
    if hasattr(schedule_config, '_orig_minute'):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=schedule_config._orig_minute or '*',
            hour=schedule_config._orig_hour or '*',
            day_of_week=schedule_config._orig_day_of_week or '*',
            day_of_month=schedule_config._orig_day_of_month or '*',
            month_of_year=schedule_config._orig_month_of_year or '*',
        )
        
        pt, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': task_path,
                'crontab': crontab,
                'enabled': True
            }
        )
        
        if created:
            print(f'  ✓ Created: {task_name}')
        else:
            print(f'  - Exists: {task_name}')

print('✓ Periodic tasks setup complete')
"
print_success "Periodic tasks configured"

echo ""
print_step "Step 12: Verify Celery configuration"
docker compose exec -T backend python -c "
from celery import current_app
from django.conf import settings

print('=== CELERY CONFIGURATION ===')
print(f'Django CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}')
print(f'Celery result_backend: {current_app.conf.result_backend}')
print(f'Celery beat_scheduler: {getattr(settings, \"CELERY_BEAT_SCHEDULER\", \"NOT SET\")}')

if current_app.conf.result_backend == 'django-db':
    print('✅ Result backend configured correctly')
else:
    print(f'❌ ERROR: Result backend is {current_app.conf.result_backend}')
    print('   Expected: django-db')
"

echo ""
print_step "Step 13: Trigger test task to verify everything works"
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.tasks import perform_system_health_check
from django_celery_results.models import TaskResult
import time

print('Triggering health check task...')
result = perform_system_health_check.delay()
print(f'Task ID: {result.id}')

print('Waiting 5 seconds...')
time.sleep(5)

# Check if result saved
task_result = TaskResult.objects.filter(task_id=result.id).first()
if task_result:
    print(f'✅ Task result saved to database')
    print(f'   Status: {task_result.status}')
    print(f'   Date: {task_result.date_done}')
else:
    print('❌ Task result NOT saved to database')
"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  Frontend: http://172.25.223.190:3001"
echo "  Backend API: http://172.25.223.190:8001/api/v1/"
echo "  Admin: http://172.25.223.190:8001/admin/"
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "Next steps:"
echo "  1. Login to admin panel"
echo "  2. Go to Scheduler Dashboard"
echo "  3. Click 'Run Now' on any task"
echo "  4. Status should update within 5-10 seconds"
echo ""
echo "Monitoring:"
echo "  docker compose logs -f celery_worker celery_beat"
echo ""
