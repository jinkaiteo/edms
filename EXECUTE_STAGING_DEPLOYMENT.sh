#!/bin/bash
################################################################################
# Execute Staging Deployment - Frontend Update
# Commit 29e6433 already on GitHub - ready to deploy
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 EDMS Staging Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Deploying: Authentication redirect (commit 29e6433)"
echo "🎯 Target: lims@172.28.1.148:/home/lims/edms-staging"
echo "⏱️  Expected time: ~4 minutes"
echo ""
read -p "Press ENTER to start deployment..."

ssh lims@172.28.1.148 << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📥 Step 1/5: Pulling code from GitHub"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    git fetch origin
    git checkout develop
    git pull origin develop
    echo "✅ Latest code pulled"
    
    echo ""
    echo "📊 Current commit:"
    git log -1 --oneline
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛑 Step 2/5: Stopping frontend container"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker compose -f docker-compose.prod.yml stop frontend
    echo "✅ Frontend stopped"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 Step 3/5: Rebuilding frontend (2-3 minutes)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    echo "✅ Frontend rebuilt"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Step 4/5: Starting frontend container"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker compose -f docker-compose.prod.yml up -d frontend
    sleep 15
    echo "✅ Frontend started"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Step 5/5: Verifying deployment"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Container status:"
    docker compose -f docker-compose.prod.yml ps frontend
    
    echo ""
    echo "Testing HTTP response..."
    if curl -f http://localhost:3001/ > /dev/null 2>&1; then
        echo "✅ Frontend is responding!"
    else
        echo "⚠️  Frontend may need more time (try again in 30 seconds)"
    fi
    
    echo ""
    echo "Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=5 frontend
ENDSSH

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend URL: http://172.28.1.148:3001"
echo ""
echo "🧪 Testing Instructions:"
echo "   1. Open incognito browser"
echo "   2. Go to: http://172.28.1.148:3001"
echo "   3. Try accessing document management"
echo "   4. Should redirect to login ✅"
echo ""
echo "⚠️  IMPORTANT: Clear browser cache or use incognito mode!"
echo "   • Ctrl+Shift+R (Windows/Linux)"
echo "   • Cmd+Shift+R (Mac)"
echo ""
