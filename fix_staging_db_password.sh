#!/bin/bash
################################################################################
# Fix DB_PASSWORD Issue on Staging Server
################################################################################
# This script fixes the DB_PASSWORD newline corruption issue that occurs
# when deploy-interactive.sh creates a .env file with password split across
# multiple lines.
#
# Usage: 
#   1. Copy this script to your staging server
#   2. Run: ./fix_staging_db_password.sh
#
# The script will:
#   - Detect corrupted DB_PASSWORD in .env
#   - Prompt for a new valid password
#   - Recreate the database with correct password
#   - Restart all services
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${CYAN}ℹ${NC} $1"; }
print_step() { echo -e "${BLUE}▶${NC} $1"; }

################################################################################
# Step 1: Diagnose the Issue
################################################################################

diagnose_issue() {
    print_header "Diagnosing DB_PASSWORD Issue"
    
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        echo "Please run this script from the EDMS project root directory."
        exit 1
    fi
    
    print_step "Checking .env file for DB_PASSWORD corruption..."
    echo ""
    
    # Show the DB_PASSWORD section with special characters visible
    echo "Current DB_PASSWORD section in .env:"
    echo "----------------------------------------"
    grep -A3 "^DB_PASSWORD" .env | cat -A
    echo "----------------------------------------"
    echo ""
    
    # Extract DB_PASSWORD value (only first line after =)
    DB_PASS=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    
    if [ -z "$DB_PASS" ]; then
        print_error "DB_PASSWORD is EMPTY (corrupted with newline)"
        echo ""
        echo "This is the bug! The password is on the next line:"
        grep -A1 "^DB_PASSWORD=" .env
        echo ""
        CORRUPTED=true
    else
        print_success "DB_PASSWORD appears valid in .env (length: ${#DB_PASS} characters)"
        CORRUPTED=false
    fi
    
    echo ""
    print_step "Checking backend container environment..."
    
    if docker compose -f docker-compose.prod.yml ps backend 2>/dev/null | grep -q "Up"; then
        BACKEND_PASS=$(docker compose -f docker-compose.prod.yml exec -T backend env 2>/dev/null | grep "^DB_PASSWORD=" | cut -d'=' -f2)
        if [ -z "$BACKEND_PASS" ]; then
            print_error "Backend container has EMPTY DB_PASSWORD"
            CORRUPTED=true
        else
            print_success "Backend container has DB_PASSWORD (length: ${#BACKEND_PASS} characters)"
        fi
    else
        print_info "Backend container not running"
    fi
    
    echo ""
    
    if [ "$CORRUPTED" = true ]; then
        print_error "DB_PASSWORD CORRUPTION DETECTED!"
        echo ""
        echo "Root Cause:"
        echo "  The deploy-interactive.sh script had a bug that added newlines"
        echo "  to passwords, causing the .env file to have this format:"
        echo ""
        echo "    DB_PASSWORD="
        echo "    actual_password_here"
        echo ""
        echo "  This causes PostgreSQL connection failures because Django reads"
        echo "  an empty password (first line) while PostgreSQL expects the actual password."
        return 0
    else
        print_success "No DB_PASSWORD corruption detected"
        echo ""
        print_info "Your .env file looks correct. If you're still having database"
        print_info "connection issues, they may be caused by something else."
        echo ""
        read -p "Do you want to continue and reset the password anyway? (y/N): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
            echo "Exiting."
            exit 0
        fi
    fi
}

################################################################################
# Step 2: Get New Password
################################################################################

get_new_password() {
    print_header "Password Setup"
    
    print_info "Enter a new database password (minimum 12 characters)"
    echo ""
    
    while true; do
        read -s -p "$(echo -e "${CYAN}?${NC} New database password: ")" new_password
        echo ""
        
        if [ -z "$new_password" ]; then
            print_error "Password cannot be empty."
            continue
        fi
        
        if [ ${#new_password} -lt 12 ]; then
            print_error "Password too short. Must be at least 12 characters."
            continue
        fi
        
        read -s -p "$(echo -e "${CYAN}?${NC} Confirm password: ")" password_confirm
        echo ""
        
        if [ "$new_password" = "$password_confirm" ]; then
            print_success "Password accepted"
            NEW_PASSWORD="$new_password"
            break
        else
            print_error "Passwords do not match. Try again."
        fi
    done
    
    echo ""
}

################################################################################
# Step 3: Backup Existing .env
################################################################################

backup_env() {
    print_header "Backup Current Configuration"
    
    local backup_file=".env.backup.$(date +%Y%m%d-%H%M%S)"
    cp .env "$backup_file"
    print_success "Backed up .env to: $backup_file"
    echo ""
}

################################################################################
# Step 4: Fix .env File
################################################################################

fix_env_file() {
    print_header "Fixing .env File"
    
    print_step "Updating DB_PASSWORD in .env..."
    
    # Method 1: Use sed to replace the DB_PASSWORD line
    # This handles both corrupted (empty) and valid passwords
    sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$NEW_PASSWORD|" .env
    
    # Verify the fix
    FIXED_PASS=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    
    if [ "$FIXED_PASS" = "$NEW_PASSWORD" ]; then
        print_success "DB_PASSWORD updated in .env"
    else
        print_error "Failed to update DB_PASSWORD in .env"
        echo "Expected: $NEW_PASSWORD"
        echo "Got:      $FIXED_PASS"
        exit 1
    fi
    
    # Show the fixed section
    echo ""
    print_info "Updated .env DB_PASSWORD section:"
    echo "----------------------------------------"
    grep -A2 "^DB_PASSWORD=" .env | cat -A
    echo "----------------------------------------"
    echo ""
}

################################################################################
# Step 5: Recreate Database
################################################################################

recreate_database() {
    print_header "Recreating Database"
    
    print_warning "This will delete the existing database and create a new one!"
    print_warning "All data will be lost!"
    echo ""
    read -p "Are you sure you want to continue? (yes/NO): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Operation cancelled."
        exit 0
    fi
    
    echo ""
    print_step "Stopping all containers..."
    docker compose -f docker-compose.prod.yml down
    print_success "Containers stopped"
    
    echo ""
    print_step "Removing old database volume..."
    docker volume rm edms_postgres_prod_data 2>/dev/null || true
    print_success "Old database volume removed"
    
    echo ""
    print_step "Starting database with new password..."
    docker compose -f docker-compose.prod.yml up -d db redis
    
    print_info "Waiting for PostgreSQL to initialize (30 seconds)..."
    sleep 30
    
    # Verify PostgreSQL has correct password
    echo ""
    print_step "Verifying PostgreSQL password..."
    POSTGRES_PASS=$(docker compose -f docker-compose.prod.yml exec -T db env | grep "^POSTGRES_PASSWORD=" | cut -d'=' -f2)
    
    if [ "$POSTGRES_PASS" = "$NEW_PASSWORD" ]; then
        print_success "PostgreSQL configured with correct password!"
    else
        print_error "PostgreSQL password mismatch!"
        echo "Expected: $NEW_PASSWORD"
        echo "Got:      $POSTGRES_PASS"
        exit 1
    fi
    
    echo ""
}

################################################################################
# Step 6: Start Backend and Run Migrations
################################################################################

start_backend() {
    print_header "Starting Backend Services"
    
    print_step "Starting backend, celery_worker, celery_beat..."
    docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
    
    print_info "Waiting for backend to start (20 seconds)..."
    sleep 20
    
    echo ""
    print_step "Testing database connection..."
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py check --database default 2>/dev/null; then
        print_success "Database connection successful!"
    else
        print_error "Database connection failed!"
        echo ""
        echo "Backend logs:"
        docker compose -f docker-compose.prod.yml logs backend --tail=50
        exit 1
    fi
    
    echo ""
    print_step "Running database migrations..."
    if docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate; then
        print_success "Database migrations completed!"
    else
        print_error "Database migrations failed!"
        exit 1
    fi
    
    echo ""
}

################################################################################
# Step 7: Start Frontend
################################################################################

start_frontend() {
    print_header "Starting Frontend"
    
    print_step "Starting frontend container..."
    docker compose -f docker-compose.prod.yml up -d frontend
    
    print_info "Waiting for frontend to build (30 seconds)..."
    sleep 30
    
    print_success "Frontend started"
    echo ""
}

################################################################################
# Step 8: Verify All Services
################################################################################

verify_services() {
    print_header "Verifying Services"
    
    print_step "Checking container status..."
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    print_step "Testing backend health endpoint..."
    sleep 5
    
    # Get the backend port from .env
    BACKEND_PORT=$(grep "^BACKEND_PORT=" .env | cut -d'=' -f2)
    BACKEND_PORT=${BACKEND_PORT:-8001}
    
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${BACKEND_PORT}/health/" | grep -q "200"; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed (may still be starting)"
    fi
    
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    echo -e "${BOLD}${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║     EDMS Staging DB_PASSWORD Fix Script                      ║"
    echo "║                                                               ║"
    echo "║     Fixes the password newline corruption issue              ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    diagnose_issue
    get_new_password
    backup_env
    fix_env_file
    recreate_database
    start_backend
    start_frontend
    verify_services
    
    print_header "Fix Complete!"
    
    print_success "Database password has been fixed and services restarted"
    echo ""
    print_info "Next steps:"
    echo "  1. Continue with deployment: ./deploy-interactive.sh"
    echo "  2. Or manually initialize the system:"
    echo "     • Run: docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
    echo "     • Then access the application"
    echo ""
    print_warning "Important: The database was recreated - you'll need to:"
    echo "  • Create a superuser account"
    echo "  • Reconfigure any settings"
    echo "  • Restore data if you have backups"
    echo ""
}

# Run main function
main "$@"
