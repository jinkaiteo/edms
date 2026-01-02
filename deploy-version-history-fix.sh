#!/bin/bash
# Deploy VERSION_HISTORY timezone fix to staging
# Date: 2026-01-02

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "DEPLOY VERSION_HISTORY TIMEZONE FIX"
print_info "Target: lims@172.28.1.148:/home/lims/edms-staging"
print_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

print_header "STEP 1: Pull Latest Changes"

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Current commit:"
git log --oneline -1

echo ""
echo "Pulling latest changes..."
git pull origin develop

echo ""
echo "New commit:"
git log --oneline -1

echo ""
echo "Changes:"
git diff HEAD~2 --stat | grep -E "(services\.py|test-version-history)"
ENDSSH

print_success "Code updated"

print_header "STEP 2: Rebuild Backend Container"

print_info "Rebuilding backend with VERSION_HISTORY fix..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Stopping backend..."
docker compose -f docker-compose.prod.yml stop backend

echo ""
echo "Rebuilding backend image..."
docker compose -f docker-compose.prod.yml build backend

echo ""
echo "Starting backend..."
docker compose -f docker-compose.prod.yml up -d backend

echo ""
echo "Waiting for backend to be healthy..."
sleep 10

echo ""
echo "Backend status:"
docker compose -f docker-compose.prod.yml ps backend
ENDSSH

print_success "Backend rebuilt and started"

print_header "STEP 3: Verify VERSION_HISTORY Fix"

print_info "Testing VERSION_HISTORY timezone..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Running test script..."
bash test-version-history-timezone.sh
ENDSSH

print_success "VERSION_HISTORY fix verified"

print_header "DEPLOYMENT COMPLETE"

echo ""
print_success "VERSION_HISTORY timezone fix deployed successfully!"
echo ""
print_info "Changes Deployed:"
echo "  ✅ VERSION_HISTORY dates now show 'MM/DD/YYYY UTC'"
echo "  ✅ Generated timestamp shows 'MM/DD/YYYY HH:MM AM/PM UTC'"
echo "  ✅ All timestamp placeholders now consistent"
echo ""
print_info "Next Steps:"
echo "  1. Download a document with version history"
echo "  2. Verify dates show 'UTC' suffix"
echo "  3. Confirm consistency with other timestamps"
echo ""

# Save deployment log
DEPLOY_LOG="version-history-deployment-$(date +%Y%m%d-%H%M%S).log"
echo "VERSION_HISTORY timezone fix deployment" > "$DEPLOY_LOG"
echo "Date: $(date)" >> "$DEPLOY_LOG"
echo "Target: lims@172.28.1.148:/home/lims/edms-staging" >> "$DEPLOY_LOG"
echo "Status: SUCCESS" >> "$DEPLOY_LOG"

print_info "Deployment log: $DEPLOY_LOG"
