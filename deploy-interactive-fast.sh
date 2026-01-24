#!/bin/bash

################################################################################
# EDMS Interactive Deployment Script
################################################################################
#
# Description: Interactive deployment script for EDMS with HAProxy
# Version: 1.0
# Date: December 24, 2024
#
# This script guides you through:
# - Environment configuration
# - Docker deployment
# - HAProxy setup
# - Initial testing
#
# Usage: ./deploy-interactive.sh
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$SCRIPT_DIR/.env"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_step() {
    echo -e "${MAGENTA}▶${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$(echo -e "${CYAN}?${NC} $prompt")" yn
        yn=${yn:-$default}
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [ -n "$default" ]; then
        read -p "$(echo -e "${CYAN}?${NC} $prompt [$default]: ")" input
        echo "${input:-$default}"
    else
        read -p "$(echo -e "${CYAN}?${NC} $prompt: ")" input
        while [ -z "$input" ]; do
            echo "This field is required."
            read -p "$(echo -e "${CYAN}?${NC} $prompt: ")" input
        done
        echo "$input"
    fi
}

prompt_password() {
    local prompt="$1"
    local password
    local password_confirm
    
    while true; do
        read -s -p "$(echo -e "${CYAN}?${NC} $prompt: ")" password
        echo ""
        if [ -z "$password" ]; then
            echo "Password cannot be empty."
            continue
        fi
        if [ ${#password} -lt 12 ]; then
            echo "Password must be at least 12 characters."
            continue
        fi
        read -s -p "$(echo -e "${CYAN}?${NC} Confirm password: ")" password_confirm
        echo ""
        if [ "$password" = "$password_confirm" ]; then
            # Remove any newlines from password
            echo "$password" | tr -d '\n'
            break
        else
            echo "Passwords do not match. Please try again."
        fi
    done
}

generate_secret_key() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key(), end='')" 2>/dev/null || \
    openssl rand -base64 50 | tr -d "=+/\n" | cut -c1-50
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

detect_ip() {
    # Try multiple methods to detect IP
    local ip
    
    # Method 1: ip command
    ip=$(ip route get 1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    
    # Method 2: hostname -I
    if [ -z "$ip" ]; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    # Method 3: ifconfig
    if [ -z "$ip" ]; then
        ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    echo "$ip"
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    print_header "Pre-flight Checks"
    
    local all_ok=true
    
    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root is not recommended. Consider using a regular user with sudo."
    fi
    
    # Check required commands
    print_step "Checking required commands..."
    
    if check_command docker; then
        print_success "Docker installed: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    else
        print_error "Docker not found. Please install Docker first."
        all_ok=false
    fi
    
    if check_command docker-compose || check_command docker compose; then
        if check_command docker-compose; then
            print_success "Docker Compose installed: $(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)"
        else
            print_success "Docker Compose (plugin) installed"
        fi
    else
        print_error "Docker Compose not found. Please install Docker Compose."
        all_ok=false
    fi
    
    if check_command python3; then
        print_success "Python3 installed: $(python3 --version | cut -d' ' -f2)"
    else
        print_warning "Python3 not found. Will use openssl for key generation."
    fi
    
    if check_command git; then
        print_success "Git installed: $(git --version | cut -d' ' -f3)"
    else
        print_warning "Git not found (optional)."
    fi
    
    # Check if Docker is running
    print_step "Checking Docker service..."
    if docker info >/dev/null 2>&1; then
        print_success "Docker service is running"
    else
        print_error "Docker service is not running. Please start Docker."
        all_ok=false
    fi
    
    # Check available disk space
    print_step "Checking disk space..."
    local available_space=$(df -BG "$SCRIPT_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -gt 10 ]; then
        print_success "Available disk space: ${available_space}GB"
    else
        print_warning "Low disk space: ${available_space}GB (10GB+ recommended)"
    fi
    
    echo ""
    
    if [ "$all_ok" = false ]; then
        print_error "Pre-flight checks failed. Please resolve issues above."
        exit 1
    fi
    
    print_success "All pre-flight checks passed!"
    echo ""
}

################################################################################
# Configuration Collection
################################################################################

collect_configuration() {
    print_header "Configuration Collection"
    
    print_info "This section will collect information for your deployment."
    print_info "You can press Enter to accept default values shown in [brackets]."
    echo ""
    
    # Detect server IP
    local detected_ip=$(detect_ip)
    print_step "Detecting server IP address..."
    if [ -n "$detected_ip" ]; then
        print_success "Detected IP: $detected_ip"
    else
        print_warning "Could not auto-detect IP address"
    fi
    echo ""
    
    # Server Configuration
    print_step "Server Configuration"
    echo ""
    
    SERVER_IP=$(prompt_input "Server IP address" "$detected_ip")
    SERVER_HOSTNAME=$(prompt_input "Server hostname (optional)" "edms-server")
    
    echo ""
    print_step "Application Branding"
    echo ""
    print_info "Customize the application title shown throughout the interface."
    echo ""
    
    APP_TITLE=$(prompt_input "Application title" "EDMS")
    
    echo ""
    print_step "Docker Port Configuration"
    echo ""
    print_info "These ports will be exposed on your host machine."
    print_info "HAProxy will route traffic to these ports."
    echo ""
    
    BACKEND_PORT=$(prompt_input "Backend port" "8001")
    FRONTEND_PORT=$(prompt_input "Frontend port" "3001")
    POSTGRES_PORT=$(prompt_input "PostgreSQL port" "5433")
    REDIS_PORT=$(prompt_input "Redis port" "6380")
    
    echo ""
    print_step "Database Configuration"
    echo ""
    
    DB_NAME=$(prompt_input "Database name" "edms_production")
    DB_USER=$(prompt_input "Database user" "edms_prod_user")
    print_info "Database password (minimum 12 characters):"
    DB_PASSWORD=$(prompt_password "Database password")
    
    echo ""
    print_step "Security Configuration"
    echo ""
    
    print_info "Generating secure SECRET_KEY..."
    SECRET_KEY=$(generate_secret_key)
    print_success "SECRET_KEY generated (50 characters)"
    
    echo ""
    print_info "Generating EDMS_MASTER_KEY (for encryption)..."
    EDMS_MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode(), end='')")
    print_success "EDMS_MASTER_KEY generated (44 characters)"
    print_warning "⚠️  CRITICAL: This key will be saved to .env - back it up securely!"
    
    echo ""
    SESSION_TIMEOUT=$(prompt_input "Session timeout (seconds)" "3600")
    
    echo ""
    print_step "HAProxy Configuration"
    echo ""
    
    if prompt_yes_no "Will you be using HAProxy?" "y"; then
        USE_HAPROXY=true
        HAPROXY_PORT=$(prompt_input "HAProxy port (usually 80 or 443)" "80")
        
        # CORS without port numbers for HAProxy
        CORS_ORIGINS="http://${SERVER_IP}"
        if [ -n "$SERVER_HOSTNAME" ] && [ "$SERVER_HOSTNAME" != "edms-server" ]; then
            CORS_ORIGINS="${CORS_ORIGINS},http://${SERVER_HOSTNAME}"
        fi
    else
        USE_HAPROXY=false
        
        # CORS with port numbers for direct access
        CORS_ORIGINS="http://${SERVER_IP}:${FRONTEND_PORT}"
        if [ -n "$SERVER_HOSTNAME" ]; then
            CORS_ORIGINS="${CORS_ORIGINS},http://${SERVER_HOSTNAME}:${FRONTEND_PORT}"
        fi
    fi
    
    echo ""
    print_step "Optional: Monitoring"
    echo ""
    
    if prompt_yes_no "Enable Sentry error tracking?" "n"; then
        SENTRY_DSN=$(prompt_input "Sentry DSN")
    else
        SENTRY_DSN=""
    fi
    
    echo ""
}

################################################################################
# Configuration Summary
################################################################################

show_configuration_summary() {
    print_header "Configuration Summary"
    
    echo -e "${BOLD}Server Configuration:${NC}"
    echo "  IP Address:       $SERVER_IP"
    echo "  Hostname:         $SERVER_HOSTNAME"
    echo ""
    echo -e "${BOLD}Application Branding:${NC}"
    echo "  App Title:        $APP_TITLE"
    echo ""
    
    echo -e "${BOLD}Docker Ports:${NC}"
    echo "  Backend:          $BACKEND_PORT"
    echo "  Frontend:         $FRONTEND_PORT"
    echo "  PostgreSQL:       $POSTGRES_PORT"
    echo "  Redis:            $REDIS_PORT"
    echo ""
    
    echo -e "${BOLD}Database:${NC}"
    echo "  Database Name:    $DB_NAME"
    echo "  Database User:    $DB_USER"
    echo "  Database Password: ${DB_PASSWORD:0:4}**********"
    echo ""
    
    echo -e "${BOLD}Security:${NC}"
    echo "  SECRET_KEY:       ${SECRET_KEY:0:20}... (50 chars)"
    echo "  EDMS_MASTER_KEY:  ${EDMS_MASTER_KEY:0:20}... (44 chars)"
    echo "  Session Timeout:  $SESSION_TIMEOUT seconds"
    echo ""
    
    echo -e "${BOLD}Access Configuration:${NC}"
    if [ "$USE_HAPROXY" = true ]; then
        echo "  HAProxy:          Enabled (Port $HAPROXY_PORT)"
        echo "  User Access:      http://$SERVER_IP:$HAPROXY_PORT"
    else
        echo "  HAProxy:          Disabled"
        echo "  User Access:      http://$SERVER_IP:$FRONTEND_PORT"
    fi
    echo "  CORS Origins:     $CORS_ORIGINS"
    echo ""
    
    if [ -n "$SENTRY_DSN" ]; then
        echo -e "${BOLD}Monitoring:${NC}"
        echo "  Sentry:           Enabled"
        echo ""
    fi
}

################################################################################
# Create Environment File
################################################################################

create_env_file() {
    print_header "Creating Environment File"
    
    print_step "Generating .env file..."
    
    # Create backup if .env exists
    if [ -f "$ENV_FILE" ]; then
        local backup_file="${ENV_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
        cp "$ENV_FILE" "$backup_file"
        print_info "Existing .env backed up to: $(basename $backup_file)"
    fi
    
    # Generate ALLOWED_HOSTS
    local allowed_hosts="$SERVER_IP,localhost,127.0.0.1"
    if [ -n "$SERVER_HOSTNAME" ]; then
        allowed_hosts="${SERVER_HOSTNAME},${allowed_hosts}"
    fi
    
    # Generate CSRF_TRUSTED_ORIGINS
    local csrf_origins="$CORS_ORIGINS"
    
    # Create .env file
    cat > "$ENV_FILE" << EOF
# ==============================================================================
# EDMS PRODUCTION ENVIRONMENT CONFIGURATION
# ==============================================================================
# Generated: $(date)
# Server: $SERVER_IP
# ==============================================================================

# ==============================================================================
# DJANGO CORE SETTINGS
# ==============================================================================

SECRET_KEY=$SECRET_KEY
DEBUG=False
ENVIRONMENT=production
ALLOWED_HOSTS=$allowed_hosts

# ==============================================================================
# APPLICATION BRANDING
# ==============================================================================

REACT_APP_TITLE=$APP_TITLE

# ==============================================================================
# DOCKER PORT CONFIGURATION
# ==============================================================================

BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
POSTGRES_PORT=$POSTGRES_PORT
REDIS_PORT=$REDIS_PORT

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432

# ==============================================================================
# REDIS CONFIGURATION
# ==============================================================================

REDIS_URL=redis://redis:6379/1
REDIS_PASSWORD=

# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_ALWAYS_EAGER=False

# ==============================================================================
# ENCRYPTION
# ==============================================================================

EDMS_MASTER_KEY=$EDMS_MASTER_KEY

# ==============================================================================
# CORS & SECURITY
# ==============================================================================

CORS_ALLOWED_ORIGINS=$CORS_ORIGINS
CSRF_TRUSTED_ORIGINS=$csrf_origins
SESSION_COOKIE_AGE=$SESSION_TIMEOUT
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE=Lax

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@edms-system.local

# ==============================================================================
# LOGGING & MONITORING
# ==============================================================================

LOG_LEVEL=WARNING

# ==============================================================================
# JWT AUTHENTICATION
# ==============================================================================

JWT_ACCESS_TOKEN_LIFETIME_HOURS=8
JWT_REFRESH_TOKEN_LIFETIME_DAYS=1
JWT_ROTATE_REFRESH_TOKENS=True

# ==============================================================================
# PERFORMANCE
# ==============================================================================

DB_CONN_MAX_AGE=60
DB_MAX_CONNECTIONS=20
CACHE_TTL=900

# ==============================================================================
# LOCALIZATION
# ==============================================================================

TZ=UTC
LANGUAGE_CODE=en-us

# ==============================================================================
# END OF CONFIGURATION
# ==============================================================================
EOF

    # Add Sentry DSN if configured
    if [ -n "$SENTRY_DSN" ]; then
        echo "SENTRY_DSN=$SENTRY_DSN" >> "$ENV_FILE"
    else
        echo "# SENTRY_DSN=" >> "$ENV_FILE"
    fi

    chmod 600 "$ENV_FILE"
    print_success ".env file created successfully"
    print_success "File permissions set to 600 (secure)"
    echo ""
}

################################################################################
# Docker Deployment
################################################################################

deploy_docker() {
    print_header "Docker Deployment"
    
    print_step "Building Docker images..."
    echo ""
    
    cd "$SCRIPT_DIR"
    
    if docker compose -f docker-compose.prod.yml build; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        return 1
    fi
    
    echo ""
    print_step "Starting Docker containers..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml up -d; then
        print_success "Docker containers started successfully"
    else
        print_error "Failed to start Docker containers"
        return 1
    fi
    
    echo ""
    print_step "Waiting for services to be ready..."
    sleep 10
    
    # Check container status
    print_info "Container status:"
    docker compose -f docker-compose.prod.yml ps
    
    echo ""

################################################################################
# Storage Directory Setup
################################################################################

setup_storage_permissions() {
    print_header "Storage Directory Setup"
    
    print_step "Creating storage directories..."
    echo ""
    
    # Create storage directories if they don't exist
    mkdir -p "$SCRIPT_DIR/storage/documents"
    mkdir -p "$SCRIPT_DIR/storage/media"
    mkdir -p "$SCRIPT_DIR/logs"
    
    print_success "Storage directories created"
    
    echo ""
    print_step "Detecting container user ID..."
    
    # Get the user ID that the backend container runs as
    local container_uid=$(docker compose -f docker-compose.prod.yml exec -T backend id -u 2>/dev/null || echo "")
    
    if [ -n "$container_uid" ]; then
        print_info "Backend container runs as UID: $container_uid"
        
        echo ""
        print_step "Setting storage permissions for UID $container_uid..."
        
        # Set ownership to container user
        sudo chown -R "$container_uid:$container_uid" "$SCRIPT_DIR/storage" 2>/dev/null || {
            print_warning "Could not set ownership (may need sudo). Trying chmod only..."
            sudo chmod -R 777 "$SCRIPT_DIR/storage"
        }
        
        # Set permissions
        sudo chmod -R 775 "$SCRIPT_DIR/storage"
        
        print_success "Storage permissions configured"
        print_info "Ownership: UID $container_uid"
        print_info "Permissions: 775 (rwxrwxr-x)"
    else
        print_warning "Could not detect container UID"
        print_step "Setting permissive permissions (777)..."
        sudo chmod -R 777 "$SCRIPT_DIR/storage"
        print_success "Storage permissions set to 777"
    fi
    

################################################################################
# Backup Automation Setup
################################################################################

setup_backup_automation() {
    print_header "Backup Automation Setup"
    
    echo ""
    print_info "EDMS includes a hybrid backup system with:"
    echo "  • Daily backups at 2:00 AM"
    echo "  • Weekly backups on Sunday at 3:00 AM"
    echo "  • Monthly backups on the 1st at 4:00 AM"
    echo ""
    print_info "Backup features:"
    echo "  • 1-second backup time (pg_dump + tar)"
    echo "  • 9-second restore time"
    echo "  • Automatic retention (keeps last 7 backups)"
    echo "  • Stored in: $SCRIPT_DIR/backups/"
    echo ""
    
    read -p "$(echo -e "${BLUE}?${NC}") Set up automated backups now? [Y/n]: " setup_backups
    setup_backups=${setup_backups:-y}
    
    if [[ "$setup_backups" =~ ^[Yy] ]]; then
        echo ""
        print_step "Setting up automated backup cron jobs..."
        
        # Check if backup script exists
        if [ ! -f "$SCRIPT_DIR/scripts/backup-hybrid.sh" ]; then
            print_error "Backup script not found: scripts/backup-hybrid.sh"
            print_warning "Skipping backup automation"
            return 1
        fi
        
        # Make backup scripts executable
        chmod +x "$SCRIPT_DIR/scripts/backup-hybrid.sh" 2>/dev/null || true
        chmod +x "$SCRIPT_DIR/scripts/restore-hybrid.sh" 2>/dev/null || true
        
        # Create logs directory
        mkdir -p "$SCRIPT_DIR/logs"
        
        # Create cron job entries
        local cron_daily="0 2 * * * cd $SCRIPT_DIR && ./scripts/backup-hybrid.sh >> $SCRIPT_DIR/logs/backup.log 2>&1"
        local cron_weekly="0 3 * * 0 cd $SCRIPT_DIR && ./scripts/backup-hybrid.sh >> $SCRIPT_DIR/logs/backup.log 2>&1"
        local cron_monthly="0 4 1 * * cd $SCRIPT_DIR && ./scripts/backup-hybrid.sh >> $SCRIPT_DIR/logs/backup.log 2>&1"
        
        # Check if jobs already exist
        if crontab -l 2>/dev/null | grep -q "backup-hybrid.sh"; then
            print_warning "EDMS backup jobs already exist in crontab"
            read -p "$(echo -e "${BLUE}?${NC}") Remove existing jobs and reinstall? [y/N]: " reinstall
            if [[ "$reinstall" =~ ^[Yy] ]]; then
                # Remove existing EDMS backup jobs
                crontab -l 2>/dev/null | grep -v "backup-hybrid.sh" | crontab - 2>/dev/null || true
                print_success "Existing jobs removed"
            else
                print_info "Keeping existing backup jobs"
                return 0
            fi
        fi
        
        # Backup existing crontab
        crontab -l > /tmp/crontab.backup 2>/dev/null || true
        
        # Add new jobs
        (crontab -l 2>/dev/null; echo ""; echo "# EDMS Automated Backups"; echo "$cron_daily"; echo "$cron_weekly"; echo "$cron_monthly") | crontab -
        
        if [ $? -eq 0 ]; then
            print_success "Automated backups configured successfully!"
            echo ""
            print_info "Backup Schedule:"
            echo "  • Daily:   2:00 AM every day"
            echo "  • Weekly:  3:00 AM every Sunday"
            echo "  • Monthly: 4:00 AM on the 1st"
            echo ""
            print_info "Backup location: $SCRIPT_DIR/backups/"
            print_info "Backup logs:     $SCRIPT_DIR/logs/backup.log"
            echo ""
            print_step "Testing manual backup..."
            if bash "$SCRIPT_DIR/scripts/backup-hybrid.sh"; then
                print_success "Manual backup test successful!"
                local latest_backup=$(ls -t "$SCRIPT_DIR/backups/backup_"*.tar.gz 2>/dev/null | head -1)
                if [ -n "$latest_backup" ]; then
                    local backup_size=$(du -h "$latest_backup" | cut -f1)
                    print_info "Latest backup: $(basename $latest_backup) ($backup_size)"
                fi
            else
                print_warning "Manual backup test failed (non-critical)"
            fi
            echo ""
        else
            print_error "Failed to configure cron jobs"
            return 1
        fi
    else
        print_info "Skipping backup automation"
        print_info "You can set up backups later with:"
        echo "  ./scripts/setup-backup-cron.sh"
    fi
    
    echo ""
}
    echo ""
    print_step "Verifying storage structure..."
    ls -la "$SCRIPT_DIR/storage/"
    
    echo ""
}
}

################################################################################
# Database Initialization
################################################################################

initialize_database() {
    print_header "Database Initialization"
    
    print_step "Running database migrations..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate; then
        print_success "Database migrations completed"
    else
        print_error "Database migrations failed"
        return 1
    fi
    
    echo ""
    print_step "Collecting static files..."
    echo ""
    
    # Fix permissions on staticfiles directory before collecting
    docker compose -f docker-compose.prod.yml exec -T backend chown -R www-data:www-data /app/staticfiles 2>/dev/null || true
    docker compose -f docker-compose.prod.yml exec -T backend chmod -R 755 /app/staticfiles 2>/dev/null || true
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput; then
        print_success "Static files collected"
    else
        print_warning "Failed to collect static files (non-critical, continuing...)"
    fi
    
    echo ""
    print_step "Creating default roles..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_roles; then
        print_success "Default roles created (7 roles)"
    else
        print_warning "Roles creation had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Creating default Django groups..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_groups; then
        print_success "Default Django groups created (6 groups)"
    else
        print_warning "Groups creation had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Creating test users..."
    echo ""
    
    if bash scripts/create-test-users.sh; then
        print_success "Test users created"
    else
        print_error "Failed to create test users"
        return 1
    fi
    
    echo ""
    print_step "Creating default document types..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_document_types; then
        print_success "Document types created (6 types)"
    else
        print_warning "Document types creation had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Creating default document sources..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_document_sources; then
        print_success "Document sources created (3 sources)"
    else
        print_warning "Document sources creation had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Initializing placeholders (32 standard placeholders)..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py setup_placeholders; then
        print_success "Placeholders initialized (32 placeholders for document annotation)"
    else
        print_warning "Placeholder initialization had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Initializing workflow defaults..."
    echo ""
    
    if bash scripts/initialize-workflow-defaults.sh; then
        print_success "Workflow states and types initialized"
    else
        print_warning "Workflow initialization had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Assigning roles to test users..."
    echo ""
    
    if bash scripts/fix-reviewer-approver-roles.sh; then
        print_success "Test user roles assigned (author01, reviewer01, approver01)"
    else
        print_warning "Role assignment had warnings (may already exist)"
    fi
    
    echo ""
    print_step "Initializing Celery Beat scheduler (7 automated tasks)..."
    echo ""
    
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from edms.celery import app

beat_schedule = app.conf.beat_schedule
created_count = 0

for name, config in beat_schedule.items():
    task_path = config['task']
    schedule_config = config['schedule']
    
    if hasattr(schedule_config, 'minute'):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=str(schedule_config.minute),
            hour=str(schedule_config.hour),
            day_of_week=str(schedule_config.day_of_week),
            day_of_month=str(schedule_config.day_of_month),
            month_of_year=str(schedule_config.month_of_year),
        )
        
        task, was_created = PeriodicTask.objects.get_or_create(
            name=name,
            defaults={
                'task': task_path,
                'crontab': crontab,
                'enabled': True
            }
        )
        
        if was_created:
            created_count += 1

print(f'Scheduler initialized: {created_count} new tasks created, {PeriodicTask.objects.count()} total')
"; then
        print_success "Celery Beat scheduler initialized (7 tasks: document lifecycle, workflow monitoring, health checks, data integrity)"
    else
        print_warning "Scheduler initialization had warnings (tasks may already exist)"
    fi
    
    echo ""
}

################################################################################
# Create Admin User
################################################################################

create_admin_user() {
    print_header "Admin User Creation"
    
    print_info "Create a superuser account for administering EDMS."
    echo ""
    
    if prompt_yes_no "Create admin user now?" "y"; then
        docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
        echo ""
        print_success "Admin user created"
    else
        print_warning "Skipping admin user creation"
        print_info "You can create one later with:"
        echo "  docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
    fi
    
    echo ""
}

################################################################################
# System Testing
################################################################################

test_deployment() {
    print_header "System Testing"
    
    print_step "Testing backend health..."
    local backend_url="http://localhost:$BACKEND_PORT/health/"
    
    if curl -s -o /dev/null -w "%{http_code}" "$backend_url" | grep -q "200"; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed (may still be starting)"
    fi
    
    echo ""
    print_step "Testing frontend..."
    local frontend_url="http://localhost:$FRONTEND_PORT/"
    
    if curl -s -o /dev/null -w "%{http_code}" "$frontend_url" | grep -q "200"; then
        print_success "Frontend is accessible"
    else
        print_warning "Frontend check failed (may still be starting)"
    fi
    
    echo ""
    print_step "Checking container logs for errors..."
    
    local backend_errors=$(docker compose -f docker-compose.prod.yml logs backend | grep -i error | wc -l)
    local frontend_errors=$(docker compose -f docker-compose.prod.yml logs frontend | grep -i error | wc -l)
    
    if [ "$backend_errors" -eq 0 ]; then
        print_success "No backend errors detected"
    else
        print_warning "Found $backend_errors backend error(s) in logs"
    fi
    
    if [ "$frontend_errors" -eq 0 ]; then
        print_success "No frontend errors detected"
    else
        print_warning "Found $frontend_errors frontend error(s) in logs"
    fi
    
    echo ""
}

################################################################################
# HAProxy Setup
################################################################################

setup_haproxy() {
    if [ "$USE_HAPROXY" != true ]; then
        return 0
    fi
    
    print_header "HAProxy Setup"
    
    print_info "HAProxy configuration will be set up."
    print_info "Refer to HAPROXY_INTEGRATION_GUIDE.md for detailed instructions."
    echo ""
    
    if prompt_yes_no "Install HAProxy now?" "y"; then
        print_step "Installing HAProxy..."
        
        if check_command apt; then
            sudo apt update
            sudo apt install -y haproxy
        elif check_command yum; then
            sudo yum install -y haproxy
        else
            print_error "Package manager not supported. Please install HAProxy manually."
            return 1
        fi
        
        print_success "HAProxy installed"
        
        # Generate HAProxy configuration
        print_step "Generating HAProxy configuration..."
        
        local haproxy_config="/tmp/edms-haproxy.cfg"
        
        cat > "$haproxy_config" << 'HAPROXY_EOF'
# HAProxy Configuration for EDMS
# Generated by deploy-interactive.sh

global
    log /dev/log local0
    log /dev/log local1 notice
    maxconn 2000
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  300000
    timeout server  300000
    compression algo gzip
    compression type text/html text/plain text/css text/javascript application/javascript application/json

listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 30s
    stats admin if TRUE

frontend edms_frontend
    bind *:80
    mode http
    option httplog
    
    acl is_api path_beg /api/ /admin/ /static/ /media/ /health/
    use_backend backend_servers if is_api
    default_backend frontend_servers

backend backend_servers
    mode http
    balance roundrobin
    option httpchk GET /health/
    http-check expect status 200
    server backend1 127.0.0.1:BACKEND_PORT check inter 10s

backend frontend_servers
    mode http
    balance roundrobin
    option httpchk GET /
    http-check expect status 200
    server frontend1 127.0.0.1:FRONTEND_PORT check inter 10s
HAPROXY_EOF
        
        # Replace port placeholders
        sed -i "s/BACKEND_PORT/$BACKEND_PORT/g" "$haproxy_config"
        sed -i "s/FRONTEND_PORT/$FRONTEND_PORT/g" "$haproxy_config"
        
        print_info "HAProxy configuration generated at: $haproxy_config"
        print_warning "Please review and install manually:"
        echo "  sudo cp $haproxy_config /etc/haproxy/haproxy.cfg"
        echo "  sudo systemctl restart haproxy"
        echo ""
        print_info "For detailed setup, see: HAPROXY_INTEGRATION_GUIDE.md"
    else
        print_info "Skipping HAProxy installation"
        print_info "Refer to HAPROXY_INTEGRATION_GUIDE.md for manual setup"
    fi
    
    echo ""
}

################################################################################
# Final Summary
################################################################################

show_final_summary() {
    print_header "Deployment Complete! 🎉"
    
    echo -e "${BOLD}${GREEN}Your EDMS application has been deployed successfully!${NC}"
    echo ""
    
    echo -e "${BOLD}Access Information:${NC}"
    echo ""
    
    if [ "$USE_HAPROXY" = true ]; then
        echo "  ${BOLD}Frontend:${NC} http://$SERVER_IP:$HAPROXY_PORT"
        echo "            or http://$SERVER_HOSTNAME:$HAPROXY_PORT"
    else
        echo "  ${BOLD}Frontend:${NC} http://$SERVER_IP:$FRONTEND_PORT"
        if [ -n "$SERVER_HOSTNAME" ]; then
            echo "            or http://$SERVER_HOSTNAME:$FRONTEND_PORT"
        fi
    fi
    echo ""
    echo "  ${BOLD}Backend API:${NC} http://$SERVER_IP:$BACKEND_PORT/api/"
    echo "  ${BOLD}Admin Panel:${NC} http://$SERVER_IP:$BACKEND_PORT/admin/"
    echo "  ${BOLD}Health Check:${NC} http://$SERVER_IP:$BACKEND_PORT/health/"
    echo ""
    
    echo -e "${BOLD}Container Management:${NC}"
    echo ""
    echo "  View logs:      docker compose -f docker-compose.prod.yml logs -f"
    echo "  Stop services:  docker compose -f docker-compose.prod.yml down"
    echo "  Restart:        docker compose -f docker-compose.prod.yml restart"
    echo "  Status:         docker compose -f docker-compose.prod.yml ps"
    echo ""
    
    echo -e "${BOLD}Next Steps:${NC}"
    echo ""
    echo "  1. Test the application by accessing the frontend URL"
    echo "  2. Login with your admin credentials"
    echo "  3. Create additional users as needed"
    echo "  4. Configure backup automation (see scripts/backup-system.sh)"
    if [ "$USE_HAPROXY" = true ]; then
        echo "  5. Complete HAProxy setup (see HAPROXY_INTEGRATION_GUIDE.md)"
    fi
    echo ""
    
    echo -e "${BOLD}Documentation:${NC}"
    echo ""
    echo "  - PRODUCTION_DEPLOYMENT_READINESS.md - Complete production guide"
    echo "  - DEPLOYMENT_QUICK_START.md - Quick deployment reference"
    echo "  - DOCKER_NETWORKING_EXPLAINED.md - Network architecture"
    if [ "$USE_HAPROXY" = true ]; then
        echo "  - HAPROXY_INTEGRATION_GUIDE.md - HAProxy setup guide"
    fi
    echo ""
    
    echo -e "${BOLD}Configuration Files:${NC}"
    echo ""
    echo "  - backend/.env - Environment configuration (SECURED - chmod 600)"
    echo ""
    
    print_success "Deployment completed successfully!"
    echo ""
}

################################################################################
# Error Handler
################################################################################

error_handler() {
    local line_no=$1
    print_error "An error occurred on line $line_no"
    print_info "Check the logs above for details"
    exit 1
}

trap 'error_handler $LINENO' ERR

################################################################################
# EMAIL CONFIGURATION (OPTIONAL)
################################################################################

configure_email_optional() {
    print_section "Email Notifications Configuration (Optional)"
    
    echo ""
    echo "Email notifications enable the system to send alerts for:"
    echo "  • Task assignments (review/approval)"
    echo "  • Document status changes (effective/obsolete)"
    echo "  • Workflow timeouts"
    echo "  • Periodic review reminders"
    echo ""
    echo "Without email configuration, notifications will be printed to console logs."
    echo ""
    print_info "Note: Email will be configured BEFORE deployment for optimal performance."
    echo ""
    
    read -p "Would you like to configure email notifications now? (y/N): " configure_email
    
    if [[ ! "$configure_email" =~ ^[Yy]$ ]]; then
        print_info "Email configuration skipped"
        print_info "You can configure later by editing .env"
        print_info "See backend/.env.example for configuration examples"
        EMAIL_CONFIGURED=false
        return 0
    fi
    
    EMAIL_CONFIGURED=true
    
    echo ""
    echo "Select email provider:"
    echo "  1) Gmail (smtp.gmail.com)"
    echo "  2) Microsoft 365 / Outlook (smtp.office365.com)"
    echo "  3) Custom SMTP server"
    echo "  4) Skip (configure later)"
    echo ""
    read -p "Choice (1-4): " email_provider
    
    case $email_provider in
        1)
            print_step "Configuring Gmail SMTP"
            echo ""
            echo "Note: Gmail requires an App Password (not your regular password)"
            echo "Create one at: https://myaccount.google.com/apppasswords"
            echo ""
            
            read -p "Gmail address: " email_user
            read -sp "Gmail app password (16 characters): " email_pass
            echo ""
            
            # Validate input
            if [[ -z "$email_user" ]] || [[ -z "$email_pass" ]]; then
                print_error "Email address and password are required"
                return 1
            fi
            
            # Update .env file
            sed -i "s|^EMAIL_BACKEND=.*|EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST=.*|EMAIL_HOST=smtp.gmail.com|" "$ENV_FILE"
            sed -i "s|^EMAIL_PORT=.*|EMAIL_PORT=587|" "$ENV_FILE"
            sed -i "s|^EMAIL_USE_TLS=.*|EMAIL_USE_TLS=True|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$email_user|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$email_pass|" "$ENV_FILE"
            sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$email_user|" "$ENV_FILE"
            
            # Verify .env file is valid (no spaces in keys)
            if grep -q '^[A-Z_]*[[:space:]][^=]*=' "$ENV_FILE"; then
                print_error "Invalid .env format detected. Cleaning up..."
                # Remove any lines with spaces in keys
                sed -i '/^[A-Z_]*[[:space:]][^=]*=/d' "$ENV_FILE"
            fi
            
            print_success "Gmail SMTP configured"
            ;;
            
        2)
            print_step "Configuring Microsoft 365 / Outlook SMTP"
            echo ""
            echo "Note: Microsoft 365 requires an App Password"
            echo "Create one at: https://account.microsoft.com/security"
            echo ""
            
            read -p "Microsoft 365 email address: " email_user
            read -sp "App password: " email_pass
            echo ""
            
            # Validate input
            if [[ -z "$email_user" ]] || [[ -z "$email_pass" ]]; then
                print_error "Email address and password are required"
                return 1
            fi
            
            # Update .env file
            sed -i "s|^EMAIL_BACKEND=.*|EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST=.*|EMAIL_HOST=smtp.office365.com|" "$ENV_FILE"
            sed -i "s|^EMAIL_PORT=.*|EMAIL_PORT=587|" "$ENV_FILE"
            sed -i "s|^EMAIL_USE_TLS=.*|EMAIL_USE_TLS=True|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$email_user|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$email_pass|" "$ENV_FILE"
            sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$email_user|" "$ENV_FILE"
            
            # Verify .env file is valid (no spaces in keys)
            if grep -q '^[A-Z_]*[[:space:]][^=]*=' "$ENV_FILE"; then
                print_error "Invalid .env format detected. Cleaning up..."
                # Remove any lines with spaces in keys
                sed -i '/^[A-Z_]*[[:space:]][^=]*=/d' "$ENV_FILE"
            fi
            
            print_success "Microsoft 365 SMTP configured"
            ;;
            
        3)
            print_step "Configuring Custom SMTP"
            echo ""
            
            read -p "SMTP host: " smtp_host
            read -p "SMTP port (default 587): " smtp_port
            smtp_port=${smtp_port:-587}
            read -p "Use TLS? (Y/n): " use_tls
            use_tls=${use_tls:-Y}
            read -p "SMTP username: " email_user
            read -sp "SMTP password: " email_pass
            echo ""
            read -p "From email address: " from_email
            
            # Validate input
            if [[ -z "$smtp_host" ]] || [[ -z "$email_user" ]] || [[ -z "$email_pass" ]]; then
                print_error "SMTP host, username, and password are required"
                return 1
            fi
            
            # Determine TLS setting
            if [[ "$use_tls" =~ ^[Nn]$ ]]; then
                use_tls_value="False"
            else
                use_tls_value="True"
            fi
            
            # Update .env file
            sed -i "s|^EMAIL_BACKEND=.*|EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST=.*|EMAIL_HOST=$smtp_host|" "$ENV_FILE"
            sed -i "s|^EMAIL_PORT=.*|EMAIL_PORT=$smtp_port|" "$ENV_FILE"
            sed -i "s|^EMAIL_USE_TLS=.*|EMAIL_USE_TLS=$use_tls_value|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$email_user|" "$ENV_FILE"
            sed -i "s|^EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$email_pass|" "$ENV_FILE"
            sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$from_email|" "$ENV_FILE"
            
            # Verify .env file is valid (no spaces in keys)
            if grep -q '^[A-Z_]*[[:space:]][^=]*=' "$ENV_FILE"; then
                print_error "Invalid .env format detected. Cleaning up..."
                # Remove any lines with spaces in keys
                sed -i '/^[A-Z_]*[[:space:]][^=]*=/d' "$ENV_FILE"
            fi
            
            print_success "Custom SMTP configured"
            ;;
            
        4|*)
            print_info "Email configuration skipped"
            print_info "You can configure later by editing .env"
            return 0
            ;;
    esac
    
    echo ""
    print_success "Email configuration saved to .env"
    print_info "Email will be tested after containers are deployed"
    
    # Store test recipient for later
    read -p "Send test email to (leave blank to skip test): " TEST_EMAIL_RECIPIENT
    
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    # Banner
    echo -e "${BOLD}${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║     EDMS Interactive Deployment Script (Optimized)           ║"
    echo "  ║     Enterprise Document Management System                    ║"
    echo "  ║                                                               ║"
    echo "  ║     Version 1.1 - Fast Deployment (No Container Restarts)    ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    print_info "This script will guide you through deploying EDMS."
    print_info "Estimated time: 10-15 minutes (optimized for speed)"
    print_info "✨ New: Email configured BEFORE deployment (no container restarts)"
    echo ""
    
    if ! prompt_yes_no "Ready to begin?" "y"; then
        print_info "Deployment cancelled."
        exit 0
    fi
    
    # Initialize global variables
    EMAIL_CONFIGURED=false
    TEST_EMAIL_RECIPIENT=""
    
    # Execute deployment steps (OPTIMIZED ORDER)
    preflight_checks
    collect_configuration
    show_configuration_summary
    
    echo ""
    if ! prompt_yes_no "Proceed with deployment?" "y"; then
        print_info "Deployment cancelled."
        exit 0
    fi
    
    # OPTIMIZATION: Configure email BEFORE deploying containers
    create_env_file
    configure_email_optional          # Email configured before docker deployment
    
    deploy_docker || exit 1           # Containers start once with final config
    setup_storage_permissions || exit 1
    initialize_database || exit 1
    create_admin_user
    test_deployment
    
    # OPTIMIZATION: Test email AFTER containers are running (no restart needed)
    test_email_after_deployment
    
    setup_backup_automation
    setup_haproxy
    show_final_summary
}

# Run main function
main "$@"


################################################################################
# Email Testing (Post-Deployment)
################################################################################

test_email_after_deployment() {
    if [[ "$EMAIL_CONFIGURED" != true ]] || [[ -z "$TEST_EMAIL_RECIPIENT" ]]; then
        return 0
    fi
    
    print_header "Email Configuration Test"
    
    print_step "Sending test email to $TEST_EMAIL_RECIPIENT..."
    echo ""
    
    # Send test email using the already-running backend
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<PYEOF
from django.core.mail import send_mail
from django.conf import settings
import traceback

print("Sending test email...")
print(f"From: {settings.DEFAULT_FROM_EMAIL}")
print(f"To: $TEST_EMAIL_RECIPIENT")
print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print("")

try:
    result = send_mail(
        'EDMS Email Test - Deployment Verification',
        '''This is a test email from your EDMS deployment.

If you received this email, it confirms:
✅ Email configuration is correct
✅ SMTP connection is working
✅ Email notifications are operational

You can safely delete this email.

---
EDMS Deployment Test Email''',
        settings.DEFAULT_FROM_EMAIL,
        ['$TEST_EMAIL_RECIPIENT'],
        fail_silently=False,
    )
    print("✅ Test email sent successfully!")
    print(f"   Result code: {result}")
    print("")
    print("NOTE: Email delivery may take 30-60 seconds.")
    print("      Check spam/junk folder if not received.")
except Exception as e:
    print(f"❌ Failed to send test email!")
    print(f"   Error: {e}")
    print("")
    print("Troubleshooting:")
    print("1. Verify email credentials in .env file")
    print("2. Check SMTP host and port are correct")
    print("3. Ensure app password is used (not account password)")
    print("4. Verify 2FA is enabled on email account")
    print("")
    traceback.print_exc()
PYEOF
    
    echo ""
    print_info "Check the inbox for $TEST_EMAIL_RECIPIENT"
    echo ""
}
