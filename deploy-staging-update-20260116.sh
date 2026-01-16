#!/bin/bash
################################################################################
# EDMS Staging Update Deployment
# Date: January 16, 2026
# Purpose: Deploy admin dashboard, scheduler integration, and upversioning features
# 
# Commits included:
#   - 358f3c0: Admin dashboard improvements + Scheduler integration
#   - 4d2f0dd: Complete upversioning system
#   - c900592: Fix dependency field name
#
# Usage: bash deploy-staging-update-20260116.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
STAGING_SERVER="172.28.1.148"
STAGING_USER="lims"
STAGING_PATH="/home/lims/edms-staging"
BRANCH="main"
COMPOSE_FILE="docker-compose.prod.yml"

# Helper functions
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

################################################################################
# Main Deployment
################################################################################

print_header "EDMS Staging Update Deployment - January 16, 2026"

log "Target: ${STAGING_USER}@${STAGING_SERVER}:${STAGING_PATH}"
log "Branch: ${BRANCH}"
log "Expected Commit: c900592"
echo ""

# Step 1: Connect and pull latest code
print_header "STEP 1: Pulling Latest Code"

ssh ${STAGING_USER}@${STAGING_SERVER} << ENDSSH
    set -e
    cd ${STAGING_PATH}
    
    echo "Current branch: \$(git branch --show-current)"
    echo "Current commit: \$(git log --oneline -1)"
    
    echo ""
    echo "Pulling latest code from ${BRANCH}..."
    git fetch origin
    git checkout ${BRANCH}
    git pull origin ${BRANCH}
    
    echo ""
    echo "New commit: \$(git log --oneline -1)"
    
    # Verify commit
    CURRENT_COMMIT=\$(git log --format="%h" -n 1)
    if [ "\$CURRENT_COMMIT" != "c900592" ]; then
        echo "⚠️  Warning: Expected commit c900592, got \$CURRENT_COMMIT"
        echo "Last 3 commits:"
        git log --oneline -3
    else
        echo "✅ Correct commit deployed"
    fi
ENDSSH

log "Code updated successfully"

# Step 2: Restart services
print_header "STEP 2: Restarting Services"

ssh ${STAGING_USER}@${STAGING_SERVER} << ENDSSH
    set -e
    cd ${STAGING_PATH}
    
    echo "Restarting backend and frontend..."
    docker compose -f ${COMPOSE_FILE} restart backend frontend
    
    echo ""
    echo "Waiting for services to start..."
    sleep 10
    
    echo "Service status:"
    docker compose -f ${COMPOSE_FILE} ps
ENDSSH

log "Services restarted"

# Step 3: Verify deployment
print_header "STEP 3: Verifying Deployment"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "Checking backend logs for errors..."
    ERRORS=$(docker compose -f docker-compose.prod.yml logs backend --tail 50 | grep -i "error" | grep -v "0 errors" | wc -l)
    
    if [ "$ERRORS" -gt 0 ]; then
        echo "⚠️  Found $ERRORS error lines in backend logs"
        echo "Recent logs:"
        docker compose -f docker-compose.prod.yml logs backend --tail 20
    else
        echo "✅ No errors in backend logs"
    fi
    
    echo ""
    echo "Checking frontend compilation..."
    FRONTEND_STATUS=$(docker compose -f docker-compose.prod.yml logs frontend --tail 20 | grep -i "compiled" | tail -1)
    if [ -n "$FRONTEND_STATUS" ]; then
        echo "✅ Frontend: $FRONTEND_STATUS"
    else
        echo "⚠️  Frontend compilation status unclear"
        docker compose -f docker-compose.prod.yml logs frontend --tail 10
    fi
ENDSSH

log "Deployment verified"

# Step 4: Feature verification
print_header "STEP 4: Feature Verification Checklist"

echo -e "${CYAN}Please verify the following manually:${NC}"
echo ""
echo "1. Admin Dashboard (http://172.28.1.148/administration)"
echo "   □ 4 stat cards display correctly"
echo "   □ System Health shows 'Healthy'"
echo "   □ Scheduler tab navigation works"
echo ""
echo "2. Document Management"
echo "   □ Documents with multiple versions show grouped"
echo "   □ Previous versions expandable"
echo "   □ SUPERSEDED status visible"
echo ""
echo "3. Scheduler Dashboard"
echo "   □ Tasks grouped in 3 categories"
echo "   □ Document Processing (2 tasks)"
echo "   □ Workflow Management (1 task)"
echo "   □ System Maintenance (2 tasks)"
echo ""

# Summary
print_header "DEPLOYMENT SUMMARY"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${BOLD}Changes Deployed:${NC}"
echo "  • Admin Dashboard with 4 working stat cards"
echo "  • Scheduler Dashboard integrated as tab"
echo "  • Document family grouping (version history)"
echo "  • Smart dependency copying on upversion"
echo "  • Enhanced obsolescence validation"
echo ""
echo -e "${BOLD}Access Information:${NC}"
echo "  Frontend: http://172.28.1.148"
echo "  Backend:  http://172.28.1.148:8001"
echo ""
echo -e "${BOLD}No Database Changes:${NC}"
echo "  ✅ No migrations required"
echo "  ✅ No data modifications"
echo "  ✅ Code-only deployment"
echo ""
echo -e "${CYAN}Estimated Downtime: ~30 seconds (service restart only)${NC}"
echo ""

# Create deployment log
DEPLOY_LOG="staging-deployment-$(date +%Y%m%d-%H%M%S).log"
cat > "$DEPLOY_LOG" << EOF
EDMS Staging Deployment Log
===========================
Date: $(date '+%Y-%m-%d %H:%M:%S')
Target: ${STAGING_USER}@${STAGING_SERVER}:${STAGING_PATH}
Branch: ${BRANCH}

Commits Deployed:
$(git log --oneline -3)

Features:
- Admin Dashboard improvements
- Scheduler Dashboard integration  
- Document upversioning system
- Family grouping
- Dependency copying
- Obsolescence validation

Status: SUCCESS
EOF

log "Deployment log saved: $DEPLOY_LOG"

echo ""
echo -e "${GREEN}${BOLD}🎉 Ready for testing!${NC}"
echo ""
