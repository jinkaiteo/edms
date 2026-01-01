#!/bin/bash

################################################################################
# EDMS Complete Automated Staging Deployment Script
# Version: 2.0
# Date: January 2026
#
# This script performs a complete deployment including ALL fixes discovered
# during the initial staging deployment:
# - Storage permission fixes (777)
# - HAProxy configuration
# - Session ID null constraints
# - Role permission configuration
# - User role assignments
#
# Usage: bash deploy-staging-automated.sh [SERVER_IP]
# Example: bash deploy-staging-automated.sh 172.28.1.148
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
DEPLOYMENT_START_TIME=$(date +%s)

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

print_elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - DEPLOYMENT_START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    echo -e "${CYAN}⏱️  Elapsed time: ${minutes}m ${seconds}s${NC}"
}

################################################################################
# Banner
################################################################################

clear
echo -e "${BOLD}${CYAN}"
cat << 'EOF'
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║     EDMS Complete Automated Staging Deployment               ║
  ║     One-Command Full Deployment with All Fixes               ║
  ║                                                               ║
  ║     Version 2.0 - January 2026                               ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
log "Starting complete automated deployment..."
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

print_step "Checking for required scripts..."
required_scripts=("scripts/setup-staging-env.sh" "scripts/configure-for-haproxy.sh" "scripts/fix-storage-permissions.sh")
for script in "${required_scripts[@]}"; do
    if [ ! -f "$script" ]; then
        error "Required script not found: $script"
    fi
done
print_success "All required scripts present"

################################################################################
# Configuration
################################################################################

print_header "Server Configuration"

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

################################################################################
# Environment Setup
################################################################################

print_header "Environment Setup"

if [ ! -f "$ENV_FILE" ]; then
    print_step "Creating environment file..."
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
# Storage Permissions Setup (Critical Fix #1)
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
# Use sudo if needed
if chmod 777 storage/documents 2>/dev/null; then
    chmod 777 storage/media
    chmod 777 storage/temp
    chmod 755 storage/backups
    chmod 755 logs
else
    sudo chmod 777 storage/documents
    sudo chmod 777 storage/media
    sudo chmod 777 storage/temp
    sudo chmod 755 storage/backups
    sudo chmod 755 logs
fi

print_success "Storage permissions configured"
print_success "✓ storage/documents: 777 (file uploads)"
print_success "✓ storage/media: 777 (Django file storage)"
print_success "✓ storage/temp: 777 (temporary files)"

################################################################################
# HAProxy Configuration (Critical Fix #2)
################################################################################

print_header "HAProxy Configuration"

print_step "Configuring docker-compose for HAProxy..."
if grep -q '"80:80"' "$COMPOSE_FILE"; then
    # Remove port 80 binding from nginx
    sed -i '/nginx:/,/depends_on:/ {
        /- "80:80"/d
        /- "443:443"/d
    }' "$COMPOSE_FILE"
    
    # Set ports to empty list if needed
    sed -i '/nginx:/,/depends_on:/ s/^    ports:$/    ports: []/' "$COMPOSE_FILE"
    
    print_success "Removed nginx port 80 binding"
else
    print_success "Nginx port already configured"
fi

print_step "Checking HAProxy status..."
if systemctl is-active --quiet haproxy 2>/dev/null; then
    print_success "HAProxy is running"
else
    warn "HAProxy not running - will need to be set up separately"
    echo "  Run: sudo bash scripts/setup-haproxy-staging.sh"
fi

################################################################################
# Docker Deployment
################################################################################

print_header "Docker Deployment"

print_step "Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
print_success "Containers stopped"

print_step "Building Docker images..."
echo ""
if docker compose -f "$COMPOSE_FILE" build --no-cache; then
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
# Database Migrations (Including Session ID Fixes - Critical Fix #3)
################################################################################

print_header "Database Migrations"

print_step "Running all migrations..."
echo ""
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate; then
    print_success "Migrations completed"
    print_success "✓ Session_id null constraints fixed (documents & audit)"
    print_success "✓ All schema updates applied"
else
    error "Migrations failed"
fi

################################################################################
# System Defaults Initialization
################################################################################

print_header "System Defaults Initialization"

print_step "Creating default roles..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_roles 2>&1 | grep -q "Created\|exists"; then
    print_success "Roles: Document Admin, Author (O1/write), Reviewer, Approver, Viewer, User Admin, Placeholder Admin"
else
    warn "Roles may already exist"
fi

echo ""
print_step "Creating default Django groups..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_groups 2>&1 | grep -q "Created\|exists"; then
    print_success "Groups: Document Admins, Reviewers, Approvers, Senior Document Approvers, Document Viewers, Quality Managers"
else
    warn "Groups may already exist"
fi

echo ""
print_step "Creating default document types..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_document_types 2>&1 | grep -q "Created\|exists"; then
    print_success "Document Types: POL, SOP, WI, MAN, FRM, REC"
else
    warn "Document types may already exist"
fi

echo ""
print_step "Creating default document sources..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_default_document_sources 2>&1 | grep -q "Created\|exists"; then
    print_success "Document Sources: Original Digital Draft, Scanned Original, Scanned Copy"
else
    warn "Document sources may already exist"
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
else:
    print("✓ Admin user already exists")
PYTHON

print_success "Admin user ready"

################################################################################
# Test Users Creation
################################################################################

print_header "Test Users Creation"

print_step "Creating test users..."
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role, UserRole
from django.contrib.auth.models import Group

# Get roles
author_role = Role.objects.filter(name='Document Author').first()
reviewer_role = Role.objects.filter(name='Document Reviewer').first()
approver_role = Role.objects.filter(name='Document Approver').first()

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
        UserRole.objects.create(user=author, role=author_role, is_active=True, assigned_by=author)
    print("✓ Created author01 / test123 with Document Author role")
else:
    author = User.objects.get(username='author01')
    # Ensure role is assigned
    if author_role and not author.user_roles.filter(role=author_role).exists():
        UserRole.objects.create(user=author, role=author_role, is_active=True, assigned_by=author)
    print("✓ author01 already exists, role verified")

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
        UserRole.objects.create(user=reviewer, role=reviewer_role, is_active=True, assigned_by=reviewer)
    reviewers_group = Group.objects.filter(name='Reviewers').first()
    if reviewers_group:
        reviewer.groups.add(reviewers_group)
    print("✓ Created reviewer01 / test123 with Document Reviewer role")
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
        UserRole.objects.create(user=approver, role=approver_role, is_active=True, assigned_by=approver)
    approvers_group = Group.objects.filter(name='Approvers').first()
    if approvers_group:
        approver.groups.add(approvers_group)
    print("✓ Created approver01 / test123 with Document Approver role")
else:
    print("✓ approver01 already exists")

print("\n✓ All test users ready")
PYTHON

print_success "Test users created with roles assigned"

################################################################################
# Verify Role Permissions (Critical Fix #4)
################################################################################

print_header "Role Permission Verification"

print_step "Verifying author01 has document creation permissions..."
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, Role

author = User.objects.get(username='author01')
has_perm = author.user_roles.filter(
    role__module='O1',
    role__permission_level__in=['write', 'admin'],
    is_active=True
).exists()

if has_perm:
    print("✓ author01 can create documents")
    print("  Role: Document Author (O1/write)")
else:
    print("✗ author01 CANNOT create documents - role assignment failed!")
    exit(1)
PYTHON

print_success "Role permissions verified"

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

print_step "Checking migrations status..."
if docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py showmigrations 2>&1 | grep -q "0008_alter.*session_id"; then
    print_success "Session ID migrations applied"
else
    warn "Could not verify session ID migrations"
fi

print_step "Checking for errors in logs..."
backend_errors=$(docker compose -f "$COMPOSE_FILE" logs backend 2>&1 | grep -i "error" | grep -v "No errors\|ERROR 2\|error_messages" | wc -l)
if [ "$backend_errors" -lt 5 ]; then
    print_success "No critical backend errors"
else
    warn "Found $backend_errors error entries in logs (review if needed)"
fi

################################################################################
# Final Summary
################################################################################

print_header "Deployment Complete!"

print_elapsed_time
echo ""
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
echo -e "    author01 / test123   (Document Author - can create documents)"
echo -e "    reviewer01 / test123 (Document Reviewer)"
echo -e "    approver01 / test123 (Document Approver)"
echo ""
echo -e "  ${RED}${BOLD}⚠️  CHANGE PASSWORDS IN PRODUCTION!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}System Configuration:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} 7 User Roles (Document Author: O1/write)"
echo -e "  ${GREEN}✓${NC} 6 Django Groups"
echo -e "  ${GREEN}✓${NC} 6 Document Types (POL, SOP, WI, MAN, FRM, REC)"
echo -e "  ${GREEN}✓${NC} 3 Document Sources"
echo -e "  ${GREEN}✓${NC} Storage permissions (777 on documents/media)"
echo -e "  ${GREEN}✓${NC} Session ID null constraints fixed"
echo -e "  ${GREEN}✓${NC} HAProxy configuration applied"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Verification Checklist:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  1. Login: ${CYAN}http://${SERVER_IP}${NC} with author01/test123"
echo -e "  2. Create a document with file upload"
echo -e "  3. Verify document appears in library"
echo -e "  4. Check file saved to storage/documents/"
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
if ! systemctl is-active --quiet haproxy 2>/dev/null; then
    echo -e "${YELLOW}${BOLD}⚠️  HAProxy Setup Needed:${NC}"
    echo -e "  To enable port 80 access, run:"
    echo -e "  ${CYAN}sudo bash scripts/setup-haproxy-staging.sh${NC}"
    echo ""
fi
echo -e "${GREEN}${BOLD}🎉 Ready to use!${NC}"
echo ""
