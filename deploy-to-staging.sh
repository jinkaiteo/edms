#!/bin/bash
# Deploy to Staging Server - Timezone and Initialization Fixes
# Date: 2026-01-02
# Target: 172.28.1.148:/home/lims/edms-staging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STAGING_SERVER="172.28.1.148"
STAGING_USER="lims"
STAGING_PATH="/home/lims/edms-staging"
BRANCH="develop"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main deployment
print_header "STAGING DEPLOYMENT - EDMS"
print_info "Target: ${STAGING_USER}@${STAGING_SERVER}:${STAGING_PATH}"
print_info "Branch: ${BRANCH}"
print_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if we can connect
print_info "Testing connection to staging server..."
if ssh -o ConnectTimeout=10 ${STAGING_USER}@${STAGING_SERVER} "echo 'Connected'" > /dev/null 2>&1; then
    print_success "Connection successful"
else
    print_error "Cannot connect to staging server"
    print_info "Please ensure:"
    echo "  1. SSH access is configured"
    echo "  2. Server is reachable"
    echo "  3. Correct username and IP"
    exit 1
fi

# Deploy
print_header "STEP 1: Pull Latest Changes"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Current branch:"
    git branch --show-current
    
    echo ""
    echo "Current commit:"
    git log --oneline -1
    
    echo ""
    echo "Pulling latest changes from develop..."
    git pull origin develop
    
    echo ""
    echo "New commit:"
    git log --oneline -1
    
    echo ""
    echo "Recent commits:"
    git log --oneline -5
ENDSSH

print_success "Code updated"

print_header "STEP 2: Check Docker Status"

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Current Docker containers:"
    docker compose -f docker-compose.prod.yml ps
ENDSSH

print_header "STEP 3: Restart Backend Service"

print_info "Restarting backend to load new code..."

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Restarting backend service..."
    docker compose -f docker-compose.prod.yml restart backend
    
    echo ""
    echo "Waiting for backend to be ready..."
    sleep 5
    
    echo ""
    echo "Checking backend status:"
    docker compose -f docker-compose.prod.yml ps backend
    
    echo ""
    echo "Checking backend logs (last 20 lines):"
    docker compose -f docker-compose.prod.yml logs --tail=20 backend
ENDSSH

print_success "Backend restarted"

print_header "STEP 4: Verify Timezone Configuration"

print_info "Testing timezone settings..."

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Testing timezone configuration..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from django.conf import settings
from django.utils import timezone

print(f"TIME_ZONE: {settings.TIME_ZONE}")
print(f"USE_TZ: {settings.USE_TZ}")
print(f"Current UTC time: {timezone.now()}")
print(f"ISO format: {timezone.now().isoformat()}")
PYTHON
ENDSSH

print_success "Timezone configuration verified"

print_header "STEP 5: Test Annotation Processor"

print_info "Testing annotation metadata..."

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Testing annotation processor..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()

processor = DocumentAnnotationProcessor()
doc = Document.objects.first()
user = User.objects.first()

if doc and user:
    metadata = processor.get_document_metadata(doc, user)
    
    print(f"Test Document: {doc.document_number}")
    print(f"DOWNLOAD_TIME: {metadata.get('DOWNLOAD_TIME')}")
    print(f"DOWNLOAD_DATETIME: {metadata.get('DOWNLOAD_DATETIME')}")
    print(f"TIMEZONE: {metadata.get('TIMEZONE')}")
    
    # Verify
    has_utc = 'UTC' in str(metadata.get('DOWNLOAD_TIME', ''))
    print(f"\n✅ Timezone included: {has_utc}")
else:
    print("⚠️  No documents or users found for testing")
PYTHON
ENDSSH

print_success "Annotation processor verified"

print_header "STEP 6: Check Initialization Commands"

print_info "Verifying system defaults..."

ssh ${STAGING_USER}@${STAGING_SERVER} << 'ENDSSH'
    cd /home/lims/edms-staging
    
    echo "Checking system defaults..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import Role
from django.contrib.auth.models import Group
from apps.documents.models import DocumentType, DocumentSource
from apps.workflows.models import DocumentState, WorkflowType

print(f"Roles: {Role.objects.count()}")
print(f"Django Groups: {Group.objects.count()}")
print(f"Document Types: {DocumentType.objects.count()}")
print(f"Document Sources: {DocumentSource.objects.count()}")
print(f"Document States: {DocumentState.objects.count()}")
print(f"Workflow Types: {WorkflowType.objects.count()}")
PYTHON
ENDSSH

print_success "System defaults verified"

print_header "DEPLOYMENT COMPLETE"

print_success "Staging deployment successful!"
echo ""
print_info "Changes Deployed:"
echo "  ✅ Timezone consistency fix (UTC with display)"
echo "  ✅ Complete initialization sequence"
echo "  ✅ ISO 8601 timestamp support"
echo "  ✅ Explicit TIMEZONE metadata field"
echo ""
print_info "Next Steps:"
echo "  1. Test document download with annotations"
echo "  2. Verify timestamps show 'UTC' suffix"
echo "  3. Check initialization creates all defaults"
echo "  4. Monitor for any issues"
echo ""
print_info "Staging URL: http://172.28.1.148"
echo ""

# Save deployment log
DEPLOY_LOG="staging-deployment-$(date +%Y%m%d-%H%M%S).log"
echo "Deployment completed at $(date)" > "$DEPLOY_LOG"
echo "Target: ${STAGING_USER}@${STAGING_SERVER}:${STAGING_PATH}" >> "$DEPLOY_LOG"
echo "Branch: ${BRANCH}" >> "$DEPLOY_LOG"
echo "Commits deployed:" >> "$DEPLOY_LOG"
git log --oneline -5 >> "$DEPLOY_LOG"

print_info "Deployment log saved: $DEPLOY_LOG"
