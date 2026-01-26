#!/bin/bash
# Quick local deployment test

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Local Deployment Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Clean slate
echo "1. Cleaning up..."
docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
rm -f .env

# Run deployment script (non-interactive test mode)
echo ""
echo "2. Running deployment script..."

# Set test defaults
export DB_NAME="edms_test_db"
export DB_USER="edms_test_user"  
export DB_PASSWORD="test_password_123"
export SECRET_KEY="test-secret-key-$(date +%s)"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"

# Create minimal .env for testing
cat > .env << ENVFILE
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@edms-test.local

# Encryption
EDMS_MASTER_KEY=test-master-key-$(date +%s)

# Ports
BACKEND_PORT=8001
FRONTEND_PORT=3001
ENVFILE

echo "✓ Created .env file"
echo ""
echo "3. Checking .env contents..."
echo "DB_PASSWORD in .env:"
grep "^DB_PASSWORD=" .env
echo ""

# Start services
echo "4. Starting Docker services..."
docker compose -f docker-compose.prod.yml up -d db redis

echo ""
echo "5. Waiting for database..."
sleep 10

# Check what db container sees
echo ""
echo "6. Checking PostgreSQL environment in container..."
docker compose -f docker-compose.prod.yml exec -T db env | grep -E "POSTGRES_" || echo "No POSTGRES vars found!"

echo ""
echo "7. Starting backend..."
docker compose -f docker-compose.prod.yml up -d backend

echo ""
echo "8. Waiting for backend startup..."
sleep 15

echo ""
echo "9. Checking backend logs for errors..."
docker compose -f docker-compose.prod.yml logs backend --tail=50 | grep -i "error\|password" || echo "No obvious errors"

echo ""
echo "10. Testing database migration..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate || {
    echo ""
    echo "❌ Migration failed!"
    echo ""
    echo "Backend environment:"
    docker compose -f docker-compose.prod.yml exec -T backend env | grep -E "DB_"
    echo ""
    echo "PostgreSQL environment:"
    docker compose -f docker-compose.prod.yml exec -T db env | grep -E "POSTGRES_"
    echo ""
    echo "Backend logs:"
    docker compose -f docker-compose.prod.yml logs backend --tail=100
    exit 1
}

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Local test PASSED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "If this works, the issue is in the deployment script's .env creation."
echo "If this fails, the issue is in docker-compose.prod.yml configuration."

