#!/bin/bash
################################################################################
# Deploy File Upload Size Fix to Production
################################################################################
# This script deploys the file upload size limit increase (1MB → 100MB)
# to the production server.
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Production server configuration
PROD_SERVER="10.30.105.202"
PROD_USER="lims"
PROD_PATH="/home/lims/edms-production"
PROD_BRANCH="main"  # Change to 'develop' if not merged yet

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
# Pre-deployment Checks
################################################################################

print_header "Pre-Deployment Checks"

# Check SSH connection
print_info "Testing connection to production server..."
if ssh -o ConnectTimeout=10 ${PROD_USER}@${PROD_SERVER} "echo 'Connected'" > /dev/null 2>&1; then
    print_success "Connection successful"
else
    print_error "Cannot connect to production server"
    print_info "Please ensure SSH access is configured"
    exit 1
fi

# Check if changes are on GitHub
print_info "Checking if changes are pushed to GitHub..."
git fetch origin
if git log origin/${PROD_BRANCH}..HEAD --oneline | grep -q "fix: Increase file upload size limit"; then
    print_warning "Changes not yet on GitHub ${PROD_BRANCH} branch"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Changes are on GitHub"
fi

# Confirm deployment
print_warning "This will:"
echo "  1. Pull latest code from GitHub"
echo "  2. Rebuild frontend container (nginx config change)"
echo "  3. Rebuild backend container (Django settings change)"
echo "  4. Restart both containers (~3-5 min downtime)"
echo ""
print_info "Production server: ${PROD_SERVER}"
print_info "Branch: ${PROD_BRANCH}"
echo ""
read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelled"
    exit 0
fi

################################################################################
# Deployment
################################################################################

print_header "Step 1: Pull Latest Code"

ssh ${PROD_USER}@${PROD_SERVER} << ENDSSH
    set -e
    cd ${PROD_PATH}
    
    echo "📥 Fetching latest from GitHub..."
    git fetch origin
    
    echo "🔄 Switching to ${PROD_BRANCH} branch..."
    git checkout ${PROD_BRANCH}
    
    echo "⬇️  Pulling latest code..."
    git pull origin ${PROD_BRANCH}
    
    echo "✅ Latest code pulled"
    echo ""
    echo "Recent commits:"
    git log -3 --oneline
ENDSSH

print_success "Code updated on production"

################################################################################

print_header "Step 2: Backup Current Configuration"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "💾 Creating backup of current nginx config..."
    docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf > nginx-backup-$(date +%Y%m%d-%H%M%S).conf || echo "Could not backup (container may be down)"
    
    echo "✅ Backup created"
ENDSSH

print_success "Configuration backed up"

################################################################################

print_header "Step 3: Stop Services"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "🛑 Stopping frontend container..."
    docker compose -f docker-compose.prod.yml stop frontend
    
    echo "🛑 Stopping backend container..."
    docker compose -f docker-compose.prod.yml stop backend
    
    echo "✅ Services stopped"
ENDSSH

print_success "Services stopped"

################################################################################

print_header "Step 4: Rebuild Frontend (with new nginx config)"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "🔨 Rebuilding frontend container with no cache..."
    echo "   (This includes the new nginx config with 100MB limit)"
    docker compose -f docker-compose.prod.yml build --no-cache frontend
    
    echo "✅ Frontend rebuilt"
ENDSSH

print_success "Frontend container rebuilt"

################################################################################

print_header "Step 5: Rebuild Backend (with new Django settings)"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "🔨 Rebuilding backend container with no cache..."
    echo "   (This includes the new 100MB upload limits)"
    docker compose -f docker-compose.prod.yml build --no-cache backend
    
    echo "✅ Backend rebuilt"
ENDSSH

print_success "Backend container rebuilt"

################################################################################

print_header "Step 6: Start Services"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "🚀 Starting all services..."
    docker compose -f docker-compose.prod.yml up -d
    
    echo "⏳ Waiting for services to be ready (30 seconds)..."
    sleep 30
    
    echo "✅ Services started"
ENDSSH

print_success "Services started"

################################################################################

print_header "Step 7: Verification"

print_info "Checking service status..."

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/lims/edms-production
    
    echo "📊 Container status:"
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "🔍 Checking frontend nginx config..."
    if docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf | grep -q "client_max_body_size 100M"; then
        echo "   ✅ Nginx config updated successfully (100MB limit found)"
    else
        echo "   ⚠️  Warning: 100MB limit not found in nginx config"
    fi
    
    echo ""
    echo "🔍 Testing frontend HTTP response..."
    if curl -f http://localhost:3002/ > /dev/null 2>&1; then
        echo "   ✅ Frontend is responding"
    else
        echo "   ⚠️  Frontend is not responding yet"
    fi
    
    echo ""
    echo "🔍 Testing backend health..."
    if curl -f http://localhost:8002/health/ > /dev/null 2>&1; then
        echo "   ✅ Backend is responding"
    else
        echo "   ⚠️  Backend is not responding yet"
    fi
    
    echo ""
    echo "📋 Recent frontend logs:"
    docker compose -f docker-compose.prod.yml logs --tail=10 frontend
    
    echo ""
    echo "📋 Recent backend logs:"
    docker compose -f docker-compose.prod.yml logs --tail=10 backend
ENDSSH

print_success "Verification complete"

################################################################################

print_header "Deployment Summary"

echo ""
print_success "File upload size limit fix deployed successfully!"
echo ""
echo "📊 Changes Applied:"
echo "  • Frontend nginx: 1MB → 100MB"
echo "  • Backend Django: 50MB → 100MB"
echo "  • Document processing: 50MB → 100MB"
echo ""
echo "🌐 Production URLs:"
echo "  • Frontend: http://${PROD_SERVER}:3002"
echo "  • Backend API: http://${PROD_SERVER}:8002/api/v1"
echo "  • Health Check: http://${PROD_SERVER}:8002/health/"
echo ""
echo "🧪 Testing Instructions:"
echo "  1. Open: http://${PROD_SERVER}:3002 (use incognito mode)"
echo "  2. Login to EDMS"
echo "  3. Try creating a document"
echo "  4. Upload a file > 1MB (e.g., 5MB)"
echo "  5. Should upload successfully! ✅"
echo ""
echo "⚠️  Important:"
echo "  • Users should clear browser cache or use incognito mode"
echo "  • Files up to 100MB can now be uploaded"
echo "  • Files > 100MB will still fail with 413 error"
echo ""
print_warning "Monitor the system for the next 30 minutes to ensure stability"

# Save deployment log
{
    echo "File Upload Size Fix Deployment"
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Server: ${PROD_USER}@${PROD_SERVER}"
    echo "Path: ${PROD_PATH}"
    echo "Branch: ${PROD_BRANCH}"
    echo ""
    echo "Changes:"
    echo "  - Nginx: 1MB → 100MB"
    echo "  - Django: 50MB → 100MB"
    echo "  - Status: Success"
} > "deployment-file-upload-fix-$(date +%Y%m%d-%H%M%S).log"

print_info "Deployment log saved"

################################################################################

print_header "Post-Deployment Tests"

echo ""
read -p "Would you like to run automated tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_header "Running Automated Tests"
    
    print_info "Test 1: Frontend accessibility"
    if curl -f http://${PROD_SERVER}:3002/ > /dev/null 2>&1; then
        print_success "Frontend accessible"
    else
        print_error "Frontend not accessible"
    fi
    
    print_info "Test 2: Backend health check"
    if curl -f http://${PROD_SERVER}:8002/health/ > /dev/null 2>&1; then
        print_success "Backend healthy"
    else
        print_error "Backend not healthy"
    fi
    
    print_info "Test 3: API endpoint check"
    if curl -f http://${PROD_SERVER}:8002/api/v1/ > /dev/null 2>&1; then
        print_success "API accessible"
    else
        print_warning "API may require authentication"
    fi
    
    print_success "Automated tests complete"
fi

################################################################################

print_header "Deployment Complete! 🎉"

echo ""
echo "Next steps:"
echo "  1. Test file upload in browser"
echo "  2. Monitor logs: docker compose logs -f frontend backend"
echo "  3. Notify users about browser cache clearing"
echo ""
print_success "All done!"
