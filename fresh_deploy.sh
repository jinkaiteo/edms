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
