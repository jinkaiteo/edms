#!/bin/bash

# Scheduler Manual Trigger Timeout Fix - Deployment Script
# Fixes the 30-second timeout issue when manually triggering scheduler tasks

set -e

echo "=================================================="
echo "  Scheduler Timeout Fix - Deployment"
echo "=================================================="
echo ""

# Check if running on staging server
if [ ! -d "/home/edms/edms" ]; then
    echo "⚠️  Not on staging server - proceeding with local deployment"
fi

echo "📦 Step 1: Stopping services..."
docker compose down

echo ""
echo "🔨 Step 2: Rebuilding backend container..."
docker compose build backend

echo ""
echo "🔨 Step 3: Rebuilding frontend container..."
docker compose build frontend

echo ""
echo "🚀 Step 4: Starting all services..."
docker compose up -d

echo ""
echo "⏳ Step 5: Waiting for services to be ready..."
sleep 15

echo ""
echo "🔍 Step 6: Checking service status..."
docker compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "=================================================="
echo "  Testing Instructions"
echo "=================================================="
echo ""
echo "1. Open Admin Dashboard: http://your-server/admin/dashboard"
echo "2. Click on 'Scheduled Tasks' widget"
echo "3. Expand any category"
echo "4. Click '▶️ Run Now' button on any task"
echo "5. You should see:"
echo "   ✅ Task queued successfully!"
echo "   Task ID: <uuid>"
echo "   Status: queued"
echo ""
echo "6. The task should execute within seconds"
echo "7. Dashboard will auto-refresh after 2 seconds"
echo "8. NO timeout errors should occur"
echo ""
echo "=================================================="
echo "  Verification Commands"
echo "=================================================="
echo ""
echo "# Check backend logs for task queuing:"
echo "docker logs edms_backend --tail=50 | grep 'queued successfully'"
echo ""
echo "# Check celery worker logs for task execution:"
echo "docker logs edms_celery_worker --tail=50 | grep 'succeeded'"
echo ""
echo "# Test manual trigger via API:"
echo "curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"task_name\": \"perform_system_health_check\"}'"
echo ""
echo "=================================================="
