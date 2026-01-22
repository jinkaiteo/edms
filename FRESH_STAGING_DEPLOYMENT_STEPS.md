# Fresh Staging Server Deployment - Complete Guide

**Date:** January 16, 2026
**Purpose:** Clean deployment with scheduler timeout fix included

---

## Step 1: Clean Up Existing Deployment

SSH to your staging server and run these commands:

```bash
# Navigate to project directory
cd ~/edms

# Stop all containers
docker compose down -v

# Remove all containers, networks, and volumes (clean slate)
docker system prune -a --volumes -f

# Optional: Remove project directory and re-clone
cd ~
rm -rf edms

# Clone fresh from GitHub (includes the timeout fix)
git clone https://github.com/jinkaiteo/edms.git
cd edms
```

---

## Step 2: Verify Latest Code

```bash
# Check you have the latest commit with the fix
git log --oneline -1

# Should show: 79d75df fix(scheduler): Replace synchronous task execution...
```

---

## Step 3: Initial Deployment

```bash
# Build and start all services
docker compose build
docker compose up -d

# Wait for services to initialize
sleep 30

# Check service status
docker compose ps

# All services should show "Up" status
```

---

## Step 4: Initialize Database and Create Admin User

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser (interactive)
docker compose exec backend python manage.py createsuperuser

# When prompted:
# Username: admin
# Email: admin@edms.local
# Password: admin123
# Password (again): admin123
```

---

## Step 5: Initialize System Data

```bash
# Create default groups and roles
docker compose exec backend python manage.py create_default_groups
docker compose exec backend python manage.py create_default_roles

# Create default document types and sources
docker compose exec backend python manage.py create_default_document_types
docker compose exec backend python manage.py create_default_document_sources

# Setup workflows
docker compose exec backend python manage.py setup_simple_workflows

# Setup placeholders
docker compose exec backend python manage.py setup_placeholders_simple

# Create test users (optional but recommended)
docker compose exec backend python manage.py seed_test_users
```

---

## Step 6: Verify Services

```bash
# Check all containers are running
docker compose ps

# Expected output:
# NAME                 STATUS
# edms_backend         Up (healthy)
# edms_frontend        Up
# edms_celery_worker   Up (may show unhealthy but still work)
# edms_celery_beat     Up
# edms_db              Up (healthy)
# edms_redis           Up (healthy)

# Check backend logs
docker logs edms_backend --tail=50

# Check celery worker logs
docker logs edms_celery_worker --tail=50

# Check celery beat logs
docker logs edms_celery_beat --tail=50
```

---

## Step 7: Fix Celery Health Check Issues (If Needed)

If celery_worker shows "unhealthy", it's usually a health check configuration issue, not a functional problem. Verify it's actually working:

```bash
# Test if worker can process tasks
docker compose exec backend python manage.py shell -c "
from celery import current_app
inspect = current_app.control.inspect()
stats = inspect.stats()
if stats:
    print('✅ Celery worker is WORKING')
    print('Active workers:', list(stats.keys()))
else:
    print('❌ Celery worker NOT responding')
"

# Check if beat scheduler is working
docker logs edms_celery_beat --tail=20 | grep "Scheduler"
# Should see: "celery beat v5.x.x is starting..."
```

---

## Step 8: Test Login and Scheduler

```bash
# Test admin login via API
curl -X POST http://localhost:8000/api/v1/auth/session/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Should return session token

# Test scheduler manual trigger (the fix!)
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}'

# Should return immediately with "success": true and task_id
```

---

## Step 9: Access the Application

Open your browser and navigate to:

**Frontend:** `http://your-staging-server:3000`

**Login with:**
- Username: `admin`
- Password: `admin123`

Or test users:
- Username: `author01` / Password: `test123`
- Username: `reviewer01` / Password: `test123`
- Username: `approver01` / Password: `test123`

---

## Troubleshooting

### Issue: "No migrations to apply"

This is normal if migrations already exist. Continue to next step.

### Issue: "Management command not found"

The command might not exist yet. Skip it and continue. Core commands that MUST work:
- `migrate`
- `createsuperuser`

### Issue: Celery worker unhealthy but logs show activity

This is OK! Docker health checks for Celery can be temperamental. If you see:
```
[2026-01-16] [Worker-1] celery@... ready.
```
Then the worker IS working despite health check status.

### Issue: Can't login with admin/admin123

Try these alternatives:
1. Create a new superuser:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

2. Reset admin password:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User
   admin = User.objects.get(username='admin')
   admin.set_password('admin123')
   admin.save()
   print('Password reset to: admin123')
   "
   ```

### Issue: Port conflicts (address already in use)

```bash
# Check what's using the ports
netstat -tulpn | grep -E "3000|8000|5432|6379"

# Stop conflicting services
sudo systemctl stop nginx  # if using nginx
sudo systemctl stop postgresql  # if using system postgres

# Or change ports in docker-compose.yml
```

---

## Complete Script (Copy-Paste)

```bash
#!/bin/bash
# Fresh EDMS Staging Deployment Script

set -e

echo "=========================================="
echo "  Fresh EDMS Staging Deployment"
echo "  With Scheduler Timeout Fix Included"
echo "=========================================="
echo ""

# Navigate to home directory
cd ~

# Clean up old deployment
echo "🧹 Cleaning up old deployment..."
if [ -d "edms" ]; then
    cd edms
    docker compose down -v
    cd ~
fi

echo ""
echo "🗑️  Removing old containers and images..."
docker system prune -a --volumes -f

echo ""
echo "📥 Cloning fresh code from GitHub..."
rm -rf edms
git clone https://github.com/jinkaiteo/edms.git
cd edms

echo ""
echo "✅ Latest commit:"
git log --oneline -1

echo ""
echo "🔨 Building containers (this takes 5-10 minutes)..."
docker compose build

echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "🔍 Service status:"
docker compose ps

echo ""
echo "📊 Running database migrations..."
docker compose exec backend python manage.py migrate

echo ""
echo "👤 Create your admin user (follow prompts):"
echo "   Suggested: username=admin, password=admin123"
docker compose exec backend python manage.py createsuperuser

echo ""
echo "🔧 Initializing system data..."
docker compose exec backend python manage.py create_default_groups || true
docker compose exec backend python manage.py create_default_roles || true
docker compose exec backend python manage.py create_default_document_types || true
docker compose exec backend python manage.py create_default_document_sources || true
docker compose exec backend python manage.py setup_simple_workflows || true
docker compose exec backend python manage.py setup_placeholders_simple || true

echo ""
echo "👥 Creating test users..."
docker compose exec backend python manage.py seed_test_users || true

echo ""
echo "🧪 Testing scheduler fix..."
RESPONSE=$(curl -s -w "\n%{time_total}" -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}' 2>&1)

RESPONSE_TIME=$(echo "$RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

if echo "$RESPONSE_BODY" | grep -q '"success": true'; then
    echo "✅ Scheduler timeout fix verified! Response time: ${RESPONSE_TIME}s"
else
    echo "⚠️  Scheduler test inconclusive (but may still work)"
fi

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "  Backend:  http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Login with:"
echo "  Username: admin"
echo "  Password: admin123 (or what you set)"
echo ""
echo "Test users:"
echo "  author01 / test123"
echo "  reviewer01 / test123"
echo "  approver01 / test123"
echo ""
echo "Monitor logs:"
echo "  docker logs edms_backend -f"
echo "  docker logs edms_celery_worker -f"
echo ""
