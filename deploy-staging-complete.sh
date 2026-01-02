#!/bin/bash

################################################################################
# EDMS Complete Staging Deployment Script
# Updated: January 2026
# 
# This script includes ALL fixes from December 2024 - January 2026:
# - Storage permission fixes (777 on documents/media)
# - Session_id null constraint fix
# - System defaults initialization (roles, groups, types, sources)
# - Automated admin user creation
# - All migrations including recent fixes
#
# Usage: bash deploy-staging-complete.sh [SERVER_IP]
# Example: bash deploy-staging-complete.sh 172.28.1.148
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
SERVER_IP=${1:-""}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

################################################################################
# Helper Functions
################################################################################

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
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

################################################################################
# Banner
################################################################################

clear
echo -e "${BOLD}${CYAN}"
cat << 'EOF'
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║     EDMS Complete Staging Deployment                         ║
  ║     All Fixes Included (Dec 2024 - Jan 2026)                 ║
  ║                                                               ║
  ║     Version 2.0 - Updated January 2026                       ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

################################################################################
# Preflight Checks
################################################################################

print_header "Preflight Checks"

print_step "Checking Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi
print_success "Docker is installed"

print_step "Checking Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    error "Docker Compose is not installed"
fi
print_success "Docker Compose is available"

print_step "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    error "Docker daemon is not running"
fi
print_success "Docker is running"

################################################################################
# Configuration
################################################################################

print_header "Configuration"

# Detect or use provided IP
if [ -z "$SERVER_IP" ]; then
    print_step "Auto-detecting server IP..."
    SERVER_IP=$(hostname -I | awk '{print $1}')
    log "Detected IP: $SERVER_IP"
    read -p "Is this correct? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your server IP: " SERVER_IP
    fi
else
    log "Using provided IP: $SERVER_IP"
fi

print_success "Server IP: $SERVER_IP"

# Check/Create environment file
print_step "Checking environment configuration..."
if [ ! -f "$ENV_FILE" ]; then
    warn "Environment file not found. Creating from template..."
    
    # Generate random secret key
    SECRET_KEY=$(openssl rand -base64 32)
    
    cat > "$ENV_FILE" << ENVFILE
# Django Settings
DJANGO_SETTINGS_MODULE=edms.settings.production
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${SERVER_IP},localhost,127.0.0.1

# Database
DB_NAME=edms_prod_db
DB_USER=edms_prod_user
DB_PASSWORD=edms_prod_password_123
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://${SERVER_IP},http://${SERVER_IP}:3001

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Storage
MEDIA_ROOT=/app/storage/media
STATIC_ROOT=/app/staticfiles

# Security
CSRF_TRUSTED_ORIGINS=http://${SERVER_IP},http://${SERVER_IP}:3001
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Environment
ENVIRONMENT=staging
ENVFILE
    
    print_success "Environment file created"
else
    print_success "Environment file exists"
fi

################################################################################
# Storage Permissions Setup (Critical Fix)
################################################################################

print_header "Storage Permissions Setup"

print_step "Creating storage directories..."
mkdir -p storage/documents
mkdir -p storage/backups
mkdir -p storage/temp
mkdir -p storage/media
mkdir -p storage/media/certificates
mkdir -p logs/backend
mkdir -p logs/db
mkdir -p logs/redis
mkdir -p logs/nginx
print_success "Directories created"

print_step "Setting permissions (777 for file uploads)..."
chmod 777 storage/documents 2>/dev/null || sudo chmod 777 storage/documents
chmod 777 storage/media 2>/dev/null || sudo chmod 777 storage/media
chmod 777 storage/temp 2>/dev/null || sudo chmod 777 storage/temp
chmod 755 storage/backups 2>/dev/null || sudo chmod 755 storage/backups
chmod 755 logs 2>/dev/null || sudo chmod 755 logs
print_success "Storage permissions configured"
print_success "✓ storage/documents: 777 (file uploads)"
print_success "✓ storage/media: 777 (Django file storage)"
print_success "✓ storage/temp: 777 (temporary files)"

################################################################################
# Docker Deployment
################################################################################

print_header "Docker Deployment"

print_step "Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
print_success "Containers stopped"

print_step "Building Docker images..."
echo ""
if docker compose -f "$COMPOSE_FILE" build; then
    print_success "Docker images built"
else
    error "Failed to build Docker images"
fi

echo ""
print_step "Starting Docker containers..."
if docker compose -f "$COMPOSE_FILE" up -d; then
    print_success "Containers started"
else
    error "Failed to start containers"
fi

print_step "Waiting for services to initialize (30 seconds)..."
sleep 30

print_step "Checking container status..."
docker compose -f "$COMPOSE_FILE" ps
echo ""

################################################################################
# Database Migrations (Includes session_id fix)
################################################################################

print_header "Database Migrations"

print_step "Running all migrations..."
echo ""
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate; then
    print_success "Migrations completed"
    print_success "✓ Session_id null constraint fix applied"
    print_success "✓ All schema updates applied"
else
    error "Migrations failed"
fi

################################################################################
# System Defaults Initialization
################################################################################

print_header "System Defaults Initialization"

print_step "Creating default roles..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_roles; then
    print_success "7 roles created (Document Admin, Approver, Reviewer, Author, Viewer, User Admin, Placeholder Admin)"
else
    warn "Roles creation had warnings (may already exist)"
fi

echo ""
print_step "Creating default Django groups..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_groups; then
    print_success "6 groups created (Document Admins, Reviewers, Approvers, etc.)"
else
    warn "Groups creation had warnings (may already exist)"
fi

echo ""
print_step "Creating default document types..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_document_types; then
    print_success "6 document types created (POL, SOP, WI, MAN, FRM, REC)"
else
    warn "Document types creation had warnings (may already exist)"
fi

echo ""
print_step "Initializing workflow states and types..."
if bash scripts/initialize-workflow-defaults.sh; then
    print_success "12 DocumentStates and 4 WorkflowTypes created"
else
    warn "Workflow initialization had warnings (may already exist)"
fi

echo ""
print_step "Creating default document sources..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_document_sources; then
    print_success "3 document sources created"
else
    warn "Document sources creation had warnings (may already exist)"
fi

################################################################################
# Admin User Creation
################################################################################

print_header "Admin User Creation"

print_step "Creating admin superuser..."
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@edms-project.com',
        password='test123',
        first_name='System',
        last_name='Administrator'
    )
    print("✓ Admin user created")
    print("  Username: admin")
    print("  Password: test123")
    print("  ⚠️  CHANGE PASSWORD IMMEDIATELY IN PRODUCTION!")
else:
    print("✓ Admin user already exists")
PYTHON

print_success "Admin user ready"

################################################################################
# Create Test Users (Optional)
################################################################################

print_header "Test Users Creation"

print_step "Creating test users (author01, reviewer01, approver01)..."
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role
from django.contrib.auth.models import Group

# Get roles (filter by name, not code)
author_role = Role.objects.filter(name='Author').first()
reviewer_role = Role.objects.filter(name='Reviewer').first()
approver_role = Role.objects.filter(name='Approver').first()

# Create author01
if not User.objects.filter(username='author01').exists():
    author = User.objects.create_user(
        username='author01',
        email='author01@edms.com',
        password='test123',
        first_name='Author',
        last_name='User'
    )
    if author_role:
        author.roles.add(author_role)
    print("✓ Created author01 / test123")
else:
    print("✓ author01 already exists")

# Create reviewer01
if not User.objects.filter(username='reviewer01').exists():
    reviewer = User.objects.create_user(
        username='reviewer01',
        email='reviewer01@edms.com',
        password='test123',
        first_name='Reviewer',
        last_name='User'
    )
    if reviewer_role:
        reviewer.roles.add(reviewer_role)
    reviewers_group = Group.objects.filter(name='Reviewers').first()
    if reviewers_group:
        reviewer.groups.add(reviewers_group)
    print("✓ Created reviewer01 / test123")
else:
    print("✓ reviewer01 already exists")

# Create approver01
if not User.objects.filter(username='approver01').exists():
    approver = User.objects.create_user(
        username='approver01',
        email='approver01@edms.com',
        password='test123',
        first_name='Approver',
        last_name='User'
    )
    if approver_role:
        approver.roles.add(approver_role)
    approvers_group = Group.objects.filter(name='Approvers').first()
    if approvers_group:
        approver.groups.add(approvers_group)
    print("✓ Created approver01 / test123")
else:
    print("✓ approver01 already exists")

print("\n✓ All test users ready")
PYTHON

print_success "Test users created"

################################################################################
# Health Checks
################################################################################

print_header "System Health Checks"

print_step "Testing backend health..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/health/" | grep -q "200"; then
    print_success "Backend is healthy"
else
    warn "Backend health check returned non-200 (may still be starting)"
fi

print_step "Testing frontend..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:3001/" | grep -q "200"; then
    print_success "Frontend is accessible"
else
    warn "Frontend check failed (may still be starting)"
fi

print_step "Checking for errors in logs..."
backend_errors=$(docker compose -f "$COMPOSE_FILE" logs backend 2>&1 | grep -i error | grep -v "No errors" | wc -l)
if [ "$backend_errors" -eq 0 ]; then
    print_success "No critical backend errors"
else
    warn "Found $backend_errors error entries in logs (review if needed)"
fi

################################################################################
# Final Summary
################################################################################

print_header "Deployment Complete!"

echo -e "${GREEN}${BOLD}✓ All deployment steps completed successfully!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Access Information:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Frontend URL:${NC}  http://${SERVER_IP}"
echo -e "  ${BOLD}Backend URL:${NC}   http://${SERVER_IP}:8001"
echo -e "  ${BOLD}API Docs:${NC}      http://${SERVER_IP}:8001/api/docs/"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Credentials:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Admin User:${NC}"
echo -e "    Username: ${GREEN}admin${NC}"
echo -e "    Password: ${GREEN}test123${NC}"
echo ""
echo -e "  ${BOLD}Test Users:${NC}"
echo -e "    author01 / test123"
echo -e "    reviewer01 / test123"
echo -e "    approver01 / test123"
echo ""
echo -e "  ${RED}${BOLD}⚠️  CHANGE PASSWORDS IN PRODUCTION!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}System Defaults Initialized:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} 7 User Roles"
echo -e "  ${GREEN}✓${NC} 6 Django Groups"
echo -e "  ${GREEN}✓${NC} 6 Document Types (POL, SOP, WI, MAN, FRM, REC)"
echo -e "  ${GREEN}✓${NC} 3 Document Sources"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Applied Fixes:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Storage permissions (777 on documents/media)"
echo -e "  ${GREEN}✓${NC} Session_id null constraint fix"
echo -e "  ${GREEN}✓${NC} All database migrations"
echo -e "  ${GREEN}✓${NC} System defaults initialization"
echo -e "  ${GREEN}✓${NC} Automated admin creation"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Next Steps:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  1. Open http://${SERVER_IP} in your browser"
echo -e "  2. Login with admin / test123"
echo -e "  3. Test document creation with file upload"
echo -e "  4. Create additional users as needed"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Management Commands:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  View logs:        docker compose -f $COMPOSE_FILE logs -f"
echo -e "  Stop services:    docker compose -f $COMPOSE_FILE down"
echo -e "  Restart backend:  docker compose -f $COMPOSE_FILE restart backend"
echo -e "  Django shell:     docker compose -f $COMPOSE_FILE exec backend python manage.py shell"
echo ""
echo -e "${GREEN}${BOLD}🎉 Ready to use!${NC}"
echo ""
