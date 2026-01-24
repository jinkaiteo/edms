#!/bin/bash
# Fix backend unhealthy container issue

echo "════════════════════════════════════════════════════════════════"
echo "  Backend Unhealthy - Quick Fix Guide"
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

echo "Common causes of 'container is unhealthy':"
echo "  1. Health check endpoint /health/ returns non-200"
echo "  2. Migration failures during startup"
echo "  3. Database connection issues"
echo "  4. Missing SECRET_KEY or other env vars"
echo "  5. Port already in use"
echo ""

print_step "Step 1: Check what's actually failing..."
echo ""

# Get backend logs
print_info "Last 30 lines of backend logs:"
docker compose -f docker-compose.prod.yml logs backend --tail=30

echo ""
echo "════════════════════════════════════════════════════════════════"
print_step "Step 2: Test health endpoint manually..."
echo ""

# Try to test health endpoint
if docker compose -f docker-compose.prod.yml ps backend | grep -q "Up"; then
    print_info "Container is running, testing health endpoint..."
    
    docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health/ 2>&1
    HEALTH_STATUS=$?
    
    if [ $HEALTH_STATUS -eq 0 ]; then
        print_success "Health endpoint responds correctly!"
        echo ""
        print_info "The issue might be timing - container is healthy now."
        echo "Try: docker compose -f docker-compose.prod.yml up -d"
    else
        print_error "Health endpoint not responding"
        echo ""
        print_info "Checking if gunicorn is running..."
        docker compose -f docker-compose.prod.yml exec -T backend ps aux | grep gunicorn || print_error "Gunicorn not running"
    fi
else
    print_error "Backend container not running at all"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
print_step "Step 3: Common fix - Increase health check timeout..."
echo ""

echo "The health check might be timing out. Current settings:"
echo "  interval: 30s"
echo "  timeout: 10s"
echo "  retries: 3"
echo ""
echo "Backend startup sequence:"
echo "  1. Run migrations (can take 10-30s)"
echo "  2. Load initial_users.json (1-2s)"
echo "  3. Start gunicorn (2-5s)"
echo "  Total: 13-37 seconds"
echo ""
print_info "Health check might fail if migrations take >10s"

echo ""
echo "════════════════════════════════════════════════════════════════"
print_step "Recommended Fixes:"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Fix 1: Add start_period to backend healthcheck (RECOMMENDED)"
echo "------"
echo "This gives the container time to start before health checks begin."
echo ""
echo "Edit docker-compose.prod.yml, backend healthcheck section:"
echo ""
echo "  healthcheck:"
echo "    test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:8000/health/\"]"
echo "    interval: 30s"
echo "    timeout: 10s"
echo "    retries: 3"
echo "    start_period: 60s  # Add this line"
echo ""
echo "Then: docker compose down && docker compose up -d"
echo ""

echo "Fix 2: Check if migrations are failing"
echo "------"
echo "docker compose -f docker-compose.prod.yml logs backend | grep -i 'migrate'"
echo ""

echo "Fix 3: Check if SECRET_KEY is set"
echo "------"
echo "grep SECRET_KEY .env"
echo "# If empty or missing, generate new one:"
echo "python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
echo ""

echo "Fix 4: Check database connection"
echo "------"
echo "docker compose -f docker-compose.prod.yml logs db --tail=20"
echo "docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell"
echo ""

echo "Fix 5: Manual health check test"
echo "------"
echo "docker compose -f docker-compose.prod.yml up -d db redis"
echo "docker compose -f docker-compose.prod.yml up backend"
echo "# Watch logs in real-time to see where it fails"
echo ""

echo "════════════════════════════════════════════════════════════════"
print_step "Quick automated fix:"
echo "════════════════════════════════════════════════════════════════"
echo ""

read -p "Would you like to apply the start_period fix now? (y/N): " apply_fix

if [[ "$apply_fix" =~ ^[Yy]$ ]]; then
    print_info "Backing up docker-compose.prod.yml..."
    cp docker-compose.prod.yml docker-compose.prod.yml.backup
    
    print_info "Adding start_period: 60s to backend healthcheck..."
    
    # Add start_period if not already present
    if grep -A5 "backend:" docker-compose.prod.yml | grep -q "start_period"; then
        print_info "start_period already present"
    else
        # Use sed to add start_period after retries line
        sed -i '/backend:/,/healthcheck:/{ /retries: 3/a\      start_period: 60s' docker-compose.prod.yml
        print_success "Added start_period: 60s"
    fi
    
    print_info "Restarting containers..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
    
    print_info "Waiting for backend to become healthy (max 90s)..."
    
    WAIT_COUNT=0
    while [ $WAIT_COUNT -lt 18 ]; do
        if docker compose -f docker-compose.prod.yml ps backend | grep -q "healthy"; then
            echo ""
            print_success "Backend is now healthy!"
            echo ""
            docker compose -f docker-compose.prod.yml ps
            exit 0
        fi
        echo -n "."
        sleep 5
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done
    
    echo ""
    print_error "Backend still not healthy after 90s"
    echo ""
    print_info "Check logs for errors:"
    echo "  docker compose -f docker-compose.prod.yml logs backend"
else
    echo ""
    print_info "Manual fix not applied. Try one of the fixes above."
fi

echo ""
