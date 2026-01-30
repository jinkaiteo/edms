#!/bin/bash
# Quick deployment script for superuser protection hotfix
# Run this on production server

echo "=========================================="
echo "DEPLOYING SUPERUSER PROTECTION HOTFIX"
echo "=========================================="
echo ""

# Navigate to project directory (adjust path if needed)
cd /home/ubuntu/edms || cd /opt/edms || cd ~/edms

echo "✅ Current directory: $(pwd)"
echo ""

# Backup current commit
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "📌 Current commit: $CURRENT_COMMIT"
echo ""

# Pull latest changes
echo "📥 Pulling latest changes from main..."
git fetch origin main
git checkout main
git pull origin main

NEW_COMMIT=$(git rev-parse HEAD)
echo "📌 New commit: $NEW_COMMIT"
echo ""

# Show what changed
echo "📋 Changes in this deployment:"
git log --oneline $CURRENT_COMMIT..$NEW_COMMIT
echo ""

# Restart backend only (no frontend changes)
echo "🔄 Restarting backend container..."
docker compose -f docker-compose.prod.yml restart backend

echo ""
echo "⏳ Waiting for backend to be healthy..."
sleep 10

# Check health
echo "🏥 Checking backend health..."
docker compose -f docker-compose.prod.yml ps backend

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Test: Try to deactivate your superuser account"
echo "2. Expected: Error message blocking the action"
echo "3. Recommended: Create a backup superuser"
echo ""
echo "Rollback command if needed:"
echo "git checkout $CURRENT_COMMIT && docker compose -f docker-compose.prod.yml restart backend"
