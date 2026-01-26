#!/bin/bash
# Complete fix for DB password issue

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Database Password Issue - Complete Fix"
echo "════════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_error() { echo -e "${RED}✗${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_step() { echo -e "${BLUE}▶${NC} $1"; }

echo "1. Diagnosing current state..."
echo ""

# Check .env file
if [ -f ".env" ]; then
    print_info "Checking .env file for DB_PASSWORD..."
    
    # Show exact bytes of DB_PASSWORD line
    echo "DB_PASSWORD line (with special chars visible):"
    grep -A1 "^DB_PASSWORD=" .env | cat -A
    
    echo ""
    DB_PASS=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    if [ -z "$DB_PASS" ]; then
        print_error "DB_PASSWORD is EMPTY in .env!"
    else
        print_success "DB_PASSWORD is set in .env (length: ${#DB_PASS})"
    fi
else
    print_error ".env file not found!"
    exit 1
fi

echo ""
echo "2. Checking what backend container sees..."
if docker compose ps backend | grep -q "Up"; then
    BACKEND_PASS=$(docker compose exec -T backend env | grep "^DB_PASSWORD=" | cut -d'=' -f2)
    if [ -z "$BACKEND_PASS" ]; then
        print_error "Backend container has EMPTY DB_PASSWORD!"
    else
        print_success "Backend container has DB_PASSWORD (length: ${#BACKEND_PASS})"
    fi
else
    print_info "Backend container not running"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
print_step "SOLUTION"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "The issue is likely one of:"
echo "  1. .env file has empty DB_PASSWORD"
echo "  2. .env file has newlines/whitespace in DB_PASSWORD"
echo "  3. Containers not recreated after .env update"
echo ""

read -p "Do you want to fix this now? (y/N): " fix_now

if [[ ! "$fix_now" =~ ^[Yy]$ ]]; then
    echo "Exiting. No changes made."
    exit 0
fi

echo ""
print_step "Step 1: Create proper .env file"
echo ""

# Prompt for new password
while true; do
    read -s -p "Enter database password (minimum 12 characters): " new_password
    echo ""
    
    if [ ${#new_password} -lt 12 ]; then
        print_error "Password too short. Must be at least 12 characters."
        continue
    fi
    
    read -s -p "Confirm password: " password_confirm
    echo ""
    
    if [ "$new_password" = "$password_confirm" ]; then
        print_success "Password accepted"
        break
    else
        print_error "Passwords do not match. Try again."
    fi
done

echo ""
print_step "Step 2: Update .env file"

# Backup current .env
cp .env .env.backup.$(date +%s)
print_info "Backed up .env"

# Update DB_PASSWORD in .env (ensuring no newlines)
sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$new_password|" .env

# Verify the change
print_info "Verifying .env update..."
if grep -q "^DB_PASSWORD=$new_password" .env; then
    print_success "DB_PASSWORD updated in .env"
else
    print_error "Failed to update .env"
    exit 1
fi

echo ""
print_step "Step 3: Recreate containers"

# Stop all containers
docker compose -f docker-compose.prod.yml down

# Remove database volume (has wrong password)
print_info "Removing database volume with old password..."
docker volume rm edms_postgres_prod_data 2>/dev/null || true

# Start containers with new password
print_info "Starting containers with new password..."
docker compose -f docker-compose.prod.yml up -d db redis

# Wait for database
print_info "Waiting for PostgreSQL to initialize (30s)..."
sleep 30

# Verify PostgreSQL has correct password
POSTGRES_PASS=$(docker compose exec -T db env | grep "^POSTGRES_PASSWORD=" | cut -d'=' -f2)
print_info "PostgreSQL password: $POSTGRES_PASS"
print_info "Expected password:   $new_password"

if [ "$POSTGRES_PASS" = "$new_password" ]; then
    print_success "PostgreSQL has correct password!"
else
    print_error "PostgreSQL password mismatch!"
    exit 1
fi

# Start backend
print_info "Starting backend..."
docker compose -f docker-compose.prod.yml up -d backend

# Wait for backend
print_info "Waiting for backend (15s)..."
sleep 15

# Test database connection
print_info "Testing database connection..."
if docker compose exec -T backend python manage.py check --database default; then
    print_success "Database connection successful!"
else
    print_error "Database connection failed"
    echo ""
    echo "Backend logs:"
    docker compose logs backend --tail=30
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
print_success "DATABASE PASSWORD FIXED!"
echo "════════════════════════════════════════════════════════════════"
echo ""

print_info "Next steps:"
echo "  1. Continue deployment: ./deploy-interactive.sh"
echo "     (It will detect containers are already running)"
echo ""
echo "  2. Or manually run migrations:"
echo "     docker compose exec backend python manage.py migrate"
echo ""

