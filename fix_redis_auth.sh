#!/bin/bash
# Fix Redis authentication error

echo "════════════════════════════════════════════════════════════════"
echo "  Redis Authentication Fix"
echo "════════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_error() { echo -e "${RED}✗${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

echo "ERROR IDENTIFIED:"
echo "  redis.exceptions.AuthenticationError: Authentication required."
echo ""
echo "ISSUE: Redis URL in .env includes password, but Redis container has no password set"
echo ""

print_info "Checking current Redis configuration..."
echo ""

if [ -f ".env" ]; then
    echo "Current REDIS_URL in .env:"
    grep "REDIS_URL" .env
    echo ""
    echo "Current CELERY_BROKER_URL in .env:"
    grep "CELERY_BROKER_URL" .env
    echo ""
else
    print_error ".env file not found"
    exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  Solution Options"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Option 1: Remove password from Redis URLs (RECOMMENDED for staging)"
echo "--------"
echo "Change in .env:"
echo "  FROM: REDIS_URL=redis://:some_password@redis:6379/1"
echo "  TO:   REDIS_URL=redis://redis:6379/1"
echo ""
echo "  FROM: CELERY_BROKER_URL=redis://:some_password@redis:6379/0"
echo "  TO:   CELERY_BROKER_URL=redis://redis:6379/0"
echo ""

echo "Option 2: Add password to Redis container (better for production)"
echo "--------"
echo "This requires modifying docker-compose.prod.yml"
echo ""

read -p "Apply Option 1 (remove password from URLs)? (y/N): " apply_fix

if [[ "$apply_fix" =~ ^[Yy]$ ]]; then
    print_info "Backing up .env..."
    cp .env .env.backup.redis
    
    print_info "Removing password from Redis URLs..."
    
    # Remove password from REDIS_URL
    sed -i 's|redis://:[^@]*@redis:|redis://redis:|g' .env
    
    # Remove password from CELERY_BROKER_URL
    sed -i 's|redis://:[^@]*@redis:|redis://redis:|g' .env
    
    print_success "Updated .env file"
    echo ""
    
    echo "New configuration:"
    grep -E "REDIS_URL|CELERY_BROKER_URL" .env
    echo ""
    
    print_info "Restarting containers..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
    
    print_info "Waiting for backend to become healthy (60s)..."
    sleep 60
    
    echo ""
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    if docker compose -f docker-compose.prod.yml ps backend | grep -q "healthy"; then
        print_success "Backend is now healthy!"
        echo ""
        print_info "Test the health endpoint:"
        echo "  curl http://localhost:8001/health/"
    else
        print_error "Backend still unhealthy. Check logs:"
        echo "  docker compose -f docker-compose.prod.yml logs backend --tail=50"
    fi
else
    echo ""
    print_info "Fix not applied. To apply manually:"
    echo ""
    echo "1. Edit .env file:"
    echo "   nano .env"
    echo ""
    echo "2. Find these lines and remove the password part (:[^@]*@):"
    echo "   REDIS_URL=redis://redis:6379/1"
    echo "   CELERY_BROKER_URL=redis://redis:6379/0"
    echo ""
    echo "3. Restart containers:"
    echo "   docker compose down && docker compose up -d"
fi

echo ""
