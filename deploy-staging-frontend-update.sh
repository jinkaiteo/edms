#!/bin/bash

################################################################################
# EDMS Staging Deployment - Frontend Update
################################################################################
# Purpose: Deploy recent frontend authentication changes to staging server
# Target: lims@172.28.1.148:/home/lims/edms-staging
# Changes: Authentication redirect in DocumentManagement component
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Staging server configuration
STAGING_SERVER="172.28.1.148"
STAGING_USER="lims"
STAGING_PATH="/home/lims/edms-staging"
BRANCH="develop"

# Logging
DEPLOY_LOG="staging-frontend-deploy-$(date +%Y%m%d-%H%M%S).log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

################################################################################
# Pre-Deployment Checks
################################################################################

print_header "Pre-Deployment Checks"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "frontend" ]; then
    print_error "This script must be run from the EDMS root directory"
    exit 1
fi

print_success "Running from correct directory"

# Check git status
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes. Consider committing first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_success "Git status checked"

# Check SSH connection
print_info "Testing connection to staging server..."
if ssh -o ConnectTimeout=10 ${STAGING_USER}@${STAGING_SERVER} "echo 'Connected'" > /dev/null 2>&1; then
    print_success "Connection successful"
else
    print_error "Cannot connect to staging server"
    print_info "Please ensure SSH access is configured"
    exit 1
fi

# Check what commits will be deployed
print_info "Recent commits to be deployed:"
git log --oneline -5 --color=always

echo ""
read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelled"
    exit 0
fi

################################################################################
# Deployment Process
################################################################################

print_header "Step 1: Pull Latest Code on Staging"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "📥 Pulling latest code from develop branch..."
    git fetch origin
    git checkout develop
    git pull origin develop
    
    echo "✓ Code updated successfully"
    echo ""
    echo "Recent commits:"
    git log --oneline -3
ENDSSH

print_success "Code pulled successfully"

################################################################################

print_header "Step 2: Rebuild Frontend Container"

print_info "This will rebuild the frontend with the new authentication changes..."
print_warning "Expected downtime: ~3-5 minutes"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "🛑 Stopping frontend container..."
    docker compose -f docker-compose.prod.yml stop frontend
    
    echo "🔨 Rebuilding frontend image..."
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    
    echo "✓ Frontend image rebuilt"
ENDSSH

print_success "Frontend container rebuilt"

################################################################################

print_header "Step 3: Start Frontend Container"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "🚀 Starting frontend container..."
    docker compose -f docker-compose.prod.yml up -d frontend
    
    echo "⏳ Waiting for frontend to be ready..."
    sleep 10
    
    echo "📊 Container status:"
    docker compose -f docker-compose.prod.yml ps frontend
ENDSSH

print_success "Frontend container started"

################################################################################

print_header "Step 4: Verification"

print_info "Running post-deployment checks..."

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-staging
    
    echo "1. Checking frontend container health..."
    if docker compose -f docker-compose.prod.yml ps frontend | grep -q "Up"; then
        echo "   ✓ Frontend container is running"
    else
        echo "   ✗ Frontend container is not running!"
        exit 1
    fi
    
    echo ""
    echo "2. Checking frontend logs for errors..."
    echo "   Last 10 lines of frontend logs:"
    docker compose -f docker-compose.prod.yml logs --tail=10 frontend
    
    echo ""
    echo "3. Testing frontend HTTP response..."
    if curl -f http://localhost:3001/ > /dev/null 2>&1; then
        echo "   ✓ Frontend is responding on port 3001"
    else
        echo "   ✗ Frontend is not responding!"
        exit 1
    fi
    
    echo ""
    echo "4. Checking backend connectivity..."
    if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
        echo "   ✓ Backend is responding"
    else
        echo "   ⚠ Backend health check failed (may need attention)"
    fi
ENDSSH

print_success "Verification complete"

################################################################################

print_header "Step 5: Clear Browser Cache Reminder"

print_warning "IMPORTANT: Frontend JavaScript has been rebuilt!"
print_info "Users must clear browser cache or use incognito mode to see changes"
print_info ""
print_info "Instructions for users:"
echo "  1. Open the staging frontend in browser"
echo "  2. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) for hard reload"
echo "  3. Or use Incognito/Private browsing mode"

################################################################################

print_header "Deployment Summary"

# Save deployment log
{
    echo "Staging Frontend Deployment"
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Server: ${STAGING_USER}@${STAGING_SERVER}"
    echo "Path: ${STAGING_PATH}"
    echo "Branch: ${BRANCH}"
    echo ""
    echo "Changes deployed:"
    git log --oneline -5
    echo ""
    echo "Frontend rebuilt: Yes"
    echo "Status: Success"
} > "$DEPLOY_LOG"

print_success "Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Server: ${STAGING_SERVER}"
echo "  • Frontend: http://${STAGING_SERVER}:3001"
echo "  • Backend API: http://${STAGING_SERVER}:8001/api/v1"
echo "  • Changes: Authentication redirect added to DocumentManagement"
echo ""
print_info "Test the deployment:"
echo "  1. Open: http://${STAGING_SERVER}:3001"
echo "  2. Navigate to document management without login"
echo "  3. Should redirect to login page"
echo "  4. Login and verify access works"
echo ""
print_info "Deployment log saved: $DEPLOY_LOG"

################################################################################
# Optional: Test deployment
################################################################################

echo ""
read -p "Would you like to run additional tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_header "Running Additional Tests"
    
    ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
        set -e
        cd /home/lims/edms-staging
        
        echo "📊 All containers status:"
        docker compose -f docker-compose.prod.yml ps
        
        echo ""
        echo "📈 Resource usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        
        echo ""
        echo "🔍 Frontend environment variables:"
        docker compose -f docker-compose.prod.yml exec frontend env | grep REACT_APP || echo "No REACT_APP vars (expected for production build)"
ENDSSH
    
    print_success "Additional tests completed"
fi

print_header "Deployment Complete! 🎉"
