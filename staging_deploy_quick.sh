#!/bin/bash
# Quick deployment script for staging server
# Run this ON THE STAGING SERVER after SSH

set -e

echo "=========================================="
echo "  Deploying Scheduler Timeout Fix"
echo "  Commit: 79d75df"
echo "=========================================="
echo ""

# Navigate to project directory
if [ -d "/home/edms/edms" ]; then
    cd /home/edms/edms
elif [ -d "$HOME/edms" ]; then
    cd $HOME/edms
else
    echo "❌ Error: Project directory not found"
    echo "Please update the script with your project path"
    exit 1
fi

echo "📍 Working directory: $(pwd)"
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git fetch origin
git pull origin main

# Verify commit
CURRENT_COMMIT=$(git log --oneline -1)
echo "✅ Current commit: $CURRENT_COMMIT"

if ! echo "$CURRENT_COMMIT" | grep -q "79d75df"; then
    echo "⚠️  Warning: Expected commit 79d75df not found"
    echo "Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# Stop services
echo ""
echo "🛑 Stopping services..."
docker compose down

# Rebuild containers
echo ""
echo "🔨 Rebuilding backend and frontend containers..."
echo "   This may take 2-3 minutes..."
docker compose build backend frontend

# Start services
echo ""
echo "🚀 Starting all services..."
docker compose up -d

# Wait for initialization
echo ""
echo "⏳ Waiting for services to initialize (20 seconds)..."
sleep 20

# Check status
echo ""
echo "🔍 Checking service status..."
docker compose ps

# Test the fix
echo ""
echo "🧪 Testing manual trigger..."
RESPONSE=$(curl -s -w "\n%{time_total}" -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}' 2>&1)

RESPONSE_TIME=$(echo "$RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

echo ""
if echo "$RESPONSE_BODY" | grep -q '"success": true'; then
    echo "✅ Test PASSED!"
    echo "   Response time: ${RESPONSE_TIME}s"
    echo "   Status: $(echo "$RESPONSE_BODY" | grep -o '"status": "[^"]*"')"
    echo "   Task ID: $(echo "$RESPONSE_BODY" | grep -o '"task_id": "[^"]*"' | head -c 50)..."
else
    echo "❌ Test FAILED - Check logs"
    echo "Response: $RESPONSE_BODY"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "✅ Next steps:"
echo "   1. Open admin dashboard and test manual trigger"
echo "   2. Verify no timeout errors occur (should respond in <1 second)"
echo "   3. Monitor logs for any issues"
echo ""
echo "📊 Monitoring commands:"
echo "   docker logs edms_backend --tail=100 -f"
echo "   docker logs edms_celery_worker --tail=100 -f"
echo ""
echo "📚 Full guide: STAGING_DEPLOYMENT_GUIDE.md"
echo ""
