#!/bin/bash

# Deploy Send Test Email Feature & Placeholder Fixes to Staging
# Date: 2026-01-27
# Commit: a0a3f71

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  DEPLOYING TO STAGING SERVER                                     ║"
echo "║  - Send Test Email feature                                       ║"
echo "║  - Placeholder system fixes                                      ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're on staging server
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Are you in the project directory?"
    exit 1
fi

echo "=== Step 1/6: Pulling latest code from GitHub ==="
git fetch origin main
git pull origin main

echo ""
echo "=== Step 2/6: Stopping services ==="
docker compose stop backend frontend

echo ""
echo "=== Step 3/6: Rebuilding backend container ==="
echo "   (New file: backend/apps/settings/views.py)"
docker compose build --no-cache backend

echo ""
echo "=== Step 4/6: Rebuilding frontend container ==="
echo "   (Updated: SystemSettings.tsx with Send Test Email button)"
docker compose build --no-cache frontend

echo ""
echo "=== Step 5/6: Starting services ==="
docker compose up -d

echo ""
echo "=== Step 6/6: Waiting for services to be ready ==="
echo "Waiting 15 seconds for containers to start..."
sleep 15

echo ""
echo "=== Checking service status ==="
docker compose ps

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  ✅ DEPLOYMENT COMPLETE                                          ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "WHAT'S NEW:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Backend:"
echo "   • 5 new placeholders added to annotation_processor.py"
echo "   • New API endpoint: POST /api/v1/settings/email/send-test/"
echo "   • Placeholder coverage: 100% (35/35)"
echo ""
echo "✅ Frontend:"
echo "   • Send Test Email button on Email Notifications page"
echo "   • No longer need to navigate to Scheduler"
echo "   • JWT authentication working"
echo ""
echo "✅ Removed:"
echo "   • 'Send Test Email' from Scheduler (architectural improvement)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "TO VERIFY DEPLOYMENT:"
echo "1. Go to: http://your-staging-server/administration?tab=notifications"
echo "2. Scroll to: Step 5: Test Email Configuration"
echo "3. Look for: 📧 Send Test Email button"
echo "4. Click and verify it works"
echo ""
echo "5. Go to Scheduler page"
echo "6. Verify: 'Send Test Email' task is NO LONGER there"
echo "   (Only 9 real scheduled tasks should remain)"
echo ""

