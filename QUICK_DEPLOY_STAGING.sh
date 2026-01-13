#!/bin/bash
################################################################################
# Quick Staging Deployment - Frontend Update
# Run this from your local machine with SSH access to staging
################################################################################

set -e

STAGING_SERVER="172.28.1.148"
STAGING_USER="lims"
STAGING_PATH="/home/lims/edms-staging"

echo "🚀 Deploying frontend changes to staging..."
echo ""

# Execute deployment on staging server
ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "📥 1/5 Pulling latest code..."
    git fetch origin
    git checkout develop
    git pull origin develop
    echo "✅ Code updated"
    echo ""
    
    echo "🛑 2/5 Stopping frontend..."
    docker compose -f docker-compose.prod.yml stop frontend
    echo "✅ Frontend stopped"
    echo ""
    
    echo "🔨 3/5 Rebuilding frontend (this takes 2-3 minutes)..."
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    echo "✅ Frontend rebuilt"
    echo ""
    
    echo "🚀 4/5 Starting frontend..."
    docker compose -f docker-compose.prod.yml up -d frontend
    sleep 10
    echo "✅ Frontend started"
    echo ""
    
    echo "✅ 5/5 Verifying deployment..."
    docker compose -f docker-compose.prod.yml ps frontend
    echo ""
    
    if curl -f http://localhost:3001/ > /dev/null 2>&1; then
        echo "✅ Frontend is responding!"
    else
        echo "⚠️  Frontend may need more time to start"
    fi
    
    echo ""
    echo "📊 Recent commits deployed:"
    git log --oneline -3
ENDSSH

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Test the deployment:"
echo "   http://172.28.1.148:3001"
echo ""
echo "⚠️  IMPORTANT: Clear browser cache!"
echo "   Use incognito mode or Ctrl+Shift+R"
echo ""
