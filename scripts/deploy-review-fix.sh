#!/bin/bash
# Deploy review workflow fix to staging server

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

header() {
    echo ""
    echo -e "${BOLD}${GREEN}========================================${NC}"
    echo -e "${BOLD}${GREEN}$1${NC}"
    echo -e "${BOLD}${GREEN}========================================${NC}"
    echo ""
}

header "🚀 Deploying Review Workflow Fix"

log "This script will:"
echo "  1. Pull latest code with enhanced error handling"
echo "  2. Restart backend container"
echo "  3. Run debug script to verify fix"
echo "  4. Test document submission"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Deployment cancelled"
    exit 1
fi

# Step 1: Pull latest code
header "📥 Step 1: Pulling Latest Code"
log "Pulling from GitHub..."
git pull origin develop

# Step 2: Restart backend
header "🔄 Step 2: Restarting Backend Container"
log "Restarting backend to load new code..."
docker compose -f docker-compose.prod.yml restart backend

log "Waiting for backend to be ready (30 seconds)..."
sleep 30

# Step 3: Check backend health
header "🏥 Step 3: Checking Backend Health"
log "Checking if backend is responding..."
docker compose -f docker-compose.prod.yml exec -T backend python -c "print('✓ Backend Python is running')"

# Step 4: Run debug script
header "🔍 Step 4: Running Debug Script"
log "Testing document and user setup..."
bash scripts/debug-review-workflow.sh

# Step 5: Show backend logs
header "📋 Step 5: Recent Backend Logs"
log "Last 30 lines of backend logs:"
docker compose -f docker-compose.prod.yml logs --tail=30 backend

echo ""
header "✅ Deployment Complete!"
echo ""
log "Next steps:"
echo "  1. Try submitting the document for review again from the frontend"
echo "  2. If you get a 500 error, check backend logs:"
echo "     ${BLUE}docker compose -f docker-compose.prod.yml logs -f backend${NC}"
echo ""
echo "  3. The enhanced error handling will show detailed errors in logs"
echo "  4. Look for lines starting with 'submit_for_review_enhanced' in logs"
echo ""
