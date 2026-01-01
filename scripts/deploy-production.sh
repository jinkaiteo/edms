#!/bin/bash
# Production Deployment Script for EDMS
# This script deploys the standardized workflow system to production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
BACKUP_DIR="${PROJECT_DIR}/backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

check_requirements() {
    log "Checking deployment requirements..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not available"
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        warn "Production environment file not found at $ENV_FILE"
        warn "Creating from template..."
        cp "${PROJECT_DIR}/.env.production" "$ENV_FILE"
        error "Please configure $ENV_FILE before continuing"
    fi
    
    log "Requirements check passed"
}

backup_existing() {
    log "Creating backup of existing deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if running
    if docker ps | grep -q edms_prod_db; then
        log "Backing up database..."
        docker exec edms_prod_db pg_dump -U edms_prod_user edms_prod_db > "$BACKUP_DIR/database.sql" || warn "Database backup failed"
    fi
    
    # Backup storage directory
    if [[ -d "${PROJECT_DIR}/storage" ]]; then
        log "Backing up storage directory..."
        cp -r "${PROJECT_DIR}/storage" "$BACKUP_DIR/" || warn "Storage backup failed"
    fi
    
    # Backup environment files
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/env.backup"
    fi
    
    log "Backup completed at $BACKUP_DIR"
}

build_images() {
    log "Building production Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build backend with production target
    docker build \
        -f infrastructure/containers/Dockerfile.backend.prod \
        --target production \
        -t edms-backend:production \
        ./backend || error "Backend build failed"
    
    # Build frontend with production target
    docker build \
        -f infrastructure/containers/Dockerfile.frontend.prod \
        --target production \
        -t edms-frontend:production \
        ./frontend || error "Frontend build failed"
    
    log "Images built successfully"
}

setup_storage() {
    log "Setting up storage directories..."
    
    cd "$PROJECT_DIR"
    
    # Create required directories
    mkdir -p storage/documents
    mkdir -p storage/backups
    mkdir -p storage/temp
    mkdir -p logs/backend
    mkdir -p logs/db
    mkdir -p logs/redis
    mkdir -p logs/nginx
    
    # Set proper permissions (755 = owner can write, others can read/execute)
    chmod -R 755 storage/
    chmod -R 755 logs/
    
    log "✓ Storage directories configured with proper permissions"
}

deploy() {
    log "Deploying EDMS production environment..."
    
    cd "$PROJECT_DIR"
    
    # Setup storage directories BEFORE starting containers
    setup_storage
    
    # Load environment variables
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || warn "No existing containers to stop"
    
    # Remove orphaned containers
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans
    
    # Pull latest base images
    log "Pulling latest base images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull db redis nginx || warn "Some base images failed to pull"
    
    # Start services
    log "Starting production services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    sleep 30
    
    # Check service health
    check_health
}

check_health() {
    log "Checking service health..."
    
    cd "$PROJECT_DIR"
    
    # Check database
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db pg_isready -U edms_prod_user; then
        log "✓ Database is healthy"
    else
        error "✗ Database health check failed"
    fi
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q PONG; then
        log "✓ Redis is healthy"
    else
        error "✗ Redis health check failed"
    fi
    
    # Check backend
    sleep 10  # Give backend time to start
    if curl -f -s http://localhost:8001/health/ > /dev/null; then
        log "✓ Backend is healthy"
    else
        error "✗ Backend health check failed"
    fi
    
    # Check frontend
    if curl -f -s http://localhost:3001/health > /dev/null; then
        log "✓ Frontend is healthy"
    else
        error "✗ Frontend health check failed"
    fi
    
    log "All services are healthy"
}

run_tests() {
    log "Running production workflow tests..."
    
    cd "$PROJECT_DIR"
    
    # Create test script in container
    cat > test_production_workflow.py << 'EOF'
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.services import get_simple_workflow_service

def test_production_workflow():
    print("🎯 Production Workflow Test")
    print("=" * 40)
    
    try:
        User = get_user_model()
        
        # Get test users
        author = User.objects.get(username='author')
        reviewer = User.objects.get(username='reviewer')
        
        # Get document type and source
        doc_type = DocumentType.objects.first()
        doc_source = DocumentSource.objects.first()
        
        if not doc_type or not doc_source:
            print("❌ No document types or sources found")
            return False
        
        # Create test document
        document = Document.objects.create(
            title='Production Workflow Test',
            description='Testing production deployment',
            document_type=doc_type,
            document_source=doc_source,
            author=author,
            reviewer=reviewer,
            approver=User.objects.get(username='approver'),
            status='DRAFT'
        )
        
        print(f"✅ Created document: {document.document_number}")
        
        # Test workflow service
        workflow_service = get_simple_workflow_service()
        
        # Start workflow
        workflow = workflow_service.start_review_workflow(document, author, reviewer)
        print(f"✅ Started workflow: {workflow.current_state.code}")
        
        # Submit for review
        result = workflow_service.submit_for_review(document, author, 'Production test')
        print(f"✅ Submit for review: {result}")
        
        # Check status
        status = workflow_service.get_document_workflow_status(document)
        print(f"✅ Current state: {status['current_state']}")
        
        # Check history
        history = workflow_service.get_workflow_history(document)
        print(f"✅ History entries: {len(history)}")
        
        print("\n🎉 Production workflow test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Production workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_production_workflow()
    sys.exit(0 if success else 1)
EOF

    # Run test in production container
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
        exec -T backend python /app/test_production_workflow.py || error "Production workflow tests failed"
    
    # Clean up test file
    rm -f test_production_workflow.py
    
    log "Production tests passed"
}

initialize_defaults() {
    log "Initializing system defaults..."
    
    cd "$PROJECT_DIR"
    
    # Check if superuser exists
    log "Checking for superuser..."
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py shell -c "from apps.users.models import User; print(User.objects.filter(is_superuser=True).exists())" 2>/dev/null | grep -q "True"; then
        warn "No superuser found. Creating default admin user..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py shell << 'EOF'
from apps.users.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@edms-project.com',
        password='test123',
        first_name='System',
        last_name='Administrator'
    )
    print("✓ Admin user created: admin / test123")
else:
    print("✓ Admin user already exists")
EOF
    else
        log "✓ Superuser exists"
    fi
    
    # Run default roles creation
    log "Creating default roles..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py create_default_roles
    
    # Run default groups creation
    log "Creating default Django groups..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py create_default_groups
    
    # Run default document types creation
    log "Creating default document types..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py create_default_document_types
    
    # Run default document sources creation
    log "Creating default document sources..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python manage.py create_default_document_sources
    
    log "System defaults initialized successfully"
}

show_info() {
    log "Production deployment completed successfully!"
    echo
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "  Frontend:  http://localhost:3001"
    echo -e "  Backend:   http://localhost:8001"
    echo -e "  API Docs:  http://localhost:8001/api/docs/"
    echo
    echo -e "${BLUE}Database:${NC}"
    echo -e "  Host: localhost:5433"
    echo -e "  Database: edms_prod_db"
    echo -e "  User: edms_prod_user"
    echo
    echo -e "${BLUE}Initialized System Defaults:${NC}"
    echo -e "  ✓ 7 User Roles (Document Admin, Approver, Reviewer, Author, Viewer, User Admin, Placeholder Admin)"
    echo -e "  ✓ 6 Django Groups (Document Admins, Reviewers, Approvers, etc.)"
    echo -e "  ✓ 6 Document Types (POL, SOP, WI, MAN, FRM, REC)"
    echo -e "  ✓ 3 Document Sources (Original Digital Draft, Scanned Original, Scanned Copy)"
    echo
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "  View logs:     docker-compose -f $COMPOSE_FILE logs -f"
    echo -e "  Stop services: docker-compose -f $COMPOSE_FILE down"
    echo -e "  Django shell:  docker-compose -f $COMPOSE_FILE exec backend python manage.py shell"
    echo
    echo -e "${BLUE}Monitoring:${NC}"
    echo -e "  Health check:  curl http://localhost:8001/health/"
    echo -e "  Service status: docker-compose -f $COMPOSE_FILE ps"
    echo
    echo -e "${GREEN}Backup location: $BACKUP_DIR${NC}"
    echo
    echo -e "${YELLOW}⚠️  Default Credentials:${NC}"
    echo -e "  Username: admin"
    echo -e "  Password: test123"
    echo -e "  ${RED}CHANGE THESE IMMEDIATELY IN PRODUCTION!${NC}"
}

# Main execution
main() {
    log "Starting EDMS Production Deployment"
    log "Standardized Workflow System v1.0"
    echo
    
    check_requirements
    backup_existing
    build_images
    deploy
    initialize_defaults
    run_tests
    show_info
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@"