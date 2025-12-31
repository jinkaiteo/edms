#!/bin/bash
#
# Update Docker Configuration for HAProxy Integration
# Purpose: Configure EDMS containers to work with HAProxy on port 80
#
# Usage: bash scripts/update-docker-for-haproxy.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
STAGING_IP="172.28.1.148"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running from correct directory
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.prod.yml not found"
    print_info "Please run this script from the repository root"
    exit 1
fi

print_header "Update Docker Configuration for HAProxy"
echo ""
echo "This script will:"
echo "  1. Backup current configuration"
echo "  2. Update docker-compose.prod.yml (REACT_APP_API_URL)"
echo "  3. Update/create .env file with correct settings"
echo "  4. Rebuild frontend container"
echo "  5. Restart all services"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Update cancelled"
    exit 0
fi

# Step 1: Backup current files
print_header "Step 1: Backing up configuration files"

BACKUP_DIR="backups/haproxy_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "$COMPOSE_FILE" ]; then
    cp "$COMPOSE_FILE" "$BACKUP_DIR/"
    print_success "Backed up $COMPOSE_FILE"
fi

if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$BACKUP_DIR/"
    print_success "Backed up $ENV_FILE"
fi

print_info "Backup location: $BACKUP_DIR"

# Step 2: Update docker-compose.prod.yml
print_header "Step 2: Updating docker-compose.prod.yml"

print_info "Updating REACT_APP_API_URL to use relative path..."

# Create a temporary file with the update
sed 's|REACT_APP_API_URL=http://localhost:8001/api/v1|REACT_APP_API_URL=/api/v1|g' "$COMPOSE_FILE" > "${COMPOSE_FILE}.tmp"

# Verify the change was made
if grep -q "REACT_APP_API_URL=/api/v1" "${COMPOSE_FILE}.tmp"; then
    mv "${COMPOSE_FILE}.tmp" "$COMPOSE_FILE"
    print_success "Updated REACT_APP_API_URL to /api/v1"
else
    print_warning "REACT_APP_API_URL might already be set correctly or pattern not found"
    rm -f "${COMPOSE_FILE}.tmp"
fi

# Step 3: Update .env file
print_header "Step 3: Updating .env file"

if [ ! -f "$ENV_FILE" ]; then
    print_info "Creating new .env file..."
    cat > "$ENV_FILE" << 'EOF'
# EDMS Production Environment Configuration
# Generated for HAProxy integration

# Port Configuration
BACKEND_PORT=8001
FRONTEND_PORT=3001

# Environment
ENVIRONMENT=staging
DEBUG=False
DJANGO_SETTINGS_MODULE=edms.settings.production

# Security Keys (IMPORTANT: Change these in production!)
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -base64 32)
EDMS_MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "GENERATE_THIS_MANUALLY")

# Allowed Hosts and CORS (for HAProxy setup)
ALLOWED_HOSTS=172.28.1.148,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://localhost

# Database Configuration
DB_NAME=edms_db
DB_USER=edms_user
DB_PASSWORD=$(openssl rand -base64 24)
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Configuration (optional)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@example.com
# EMAIL_HOST_PASSWORD=your-app-password

EOF
    print_success "Created new .env file"
    print_warning "IMPORTANT: Review and update the generated passwords and keys!"
else
    print_info "Updating existing .env file..."
    
    # Update or add ALLOWED_HOSTS
    if grep -q "^ALLOWED_HOSTS=" "$ENV_FILE"; then
        sed -i 's|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=172.28.1.148,localhost,127.0.0.1|g' "$ENV_FILE"
        print_success "Updated ALLOWED_HOSTS"
    else
        echo "" >> "$ENV_FILE"
        echo "# Allowed Hosts and CORS (for HAProxy setup)" >> "$ENV_FILE"
        echo "ALLOWED_HOSTS=172.28.1.148,localhost,127.0.0.1" >> "$ENV_FILE"
        print_success "Added ALLOWED_HOSTS"
    fi
    
    # Update or add CORS_ALLOWED_ORIGINS
    if grep -q "^CORS_ALLOWED_ORIGINS=" "$ENV_FILE"; then
        sed -i 's|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://localhost|g' "$ENV_FILE"
        print_success "Updated CORS_ALLOWED_ORIGINS"
    else
        echo "CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://localhost" >> "$ENV_FILE"
        print_success "Added CORS_ALLOWED_ORIGINS"
    fi
    
    # Ensure ports are set
    if ! grep -q "^BACKEND_PORT=" "$ENV_FILE"; then
        echo "BACKEND_PORT=8001" >> "$ENV_FILE"
        print_success "Added BACKEND_PORT"
    fi
    
    if ! grep -q "^FRONTEND_PORT=" "$ENV_FILE"; then
        echo "FRONTEND_PORT=3001" >> "$ENV_FILE"
        print_success "Added FRONTEND_PORT"
    fi
fi

print_success ".env file configured for HAProxy"

# Step 4: Check if Docker containers are running
print_header "Step 4: Checking Docker services"

if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    print_info "Docker containers are currently running"
    CONTAINERS_RUNNING=true
else
    print_info "Docker containers are not running"
    CONTAINERS_RUNNING=false
fi

# Step 5: Rebuild frontend container
print_header "Step 5: Rebuilding frontend container"

print_info "Building frontend with new REACT_APP_API_URL..."
if docker compose -f "$COMPOSE_FILE" build frontend; then
    print_success "Frontend container rebuilt successfully"
else
    print_error "Frontend build failed"
    print_info "Check the error messages above"
    exit 1
fi

# Step 6: Restart services
print_header "Step 6: Restarting services"

if [ "$CONTAINERS_RUNNING" = true ]; then
    print_info "Stopping existing containers..."
    docker compose -f "$COMPOSE_FILE" down
fi

print_info "Starting all services..."
if docker compose -f "$COMPOSE_FILE" up -d; then
    print_success "All services started"
else
    print_error "Failed to start services"
    print_info "Try running manually: docker compose -f $COMPOSE_FILE up -d"
    exit 1
fi

# Wait for services to be healthy
print_info "Waiting for services to become healthy (30 seconds)..."
sleep 30

# Step 7: Verify services
print_header "Step 7: Verifying services"

# Check backend
print_info "Checking backend health..."
if curl -sf http://localhost:8001/health > /dev/null; then
    print_success "Backend is healthy"
else
    print_warning "Backend health check failed (might still be starting)"
fi

# Check frontend
print_info "Checking frontend..."
if curl -sf http://localhost:3001/health > /dev/null; then
    print_success "Frontend is healthy"
else
    print_warning "Frontend health check failed (might still be starting)"
fi

# Check HAProxy
print_info "Checking HAProxy integration..."
if curl -sf http://localhost/haproxy-health > /dev/null; then
    print_success "HAProxy is routing correctly"
else
    print_warning "HAProxy routing check failed (ensure HAProxy is running)"
fi

# Step 8: Display status
print_header "Configuration Complete!"

echo ""
print_success "Docker containers updated for HAProxy integration"
echo ""
echo "Current configuration:"
echo "  • Frontend: Uses relative URL /api/v1"
echo "  • Backend Port: 8001 (internal)"
echo "  • Frontend Port: 3001 (internal)"
echo "  • HAProxy: Routes all traffic on port 80"
echo ""

# Display access URLs
print_header "Access URLs"
echo ""
echo "Main Application:"
echo "  🌐 http://$STAGING_IP"
echo ""
echo "HAProxy Stats:"
echo "  📊 http://$STAGING_IP:8404/stats"
echo "     Username: admin"
echo "     Password: admin_changeme"
echo ""
echo "API Endpoints (through HAProxy):"
echo "  🔧 API: http://$STAGING_IP/api/v1"
echo "  🔒 Admin: http://$STAGING_IP/admin"
echo ""

# Show logs command
print_header "Monitoring"
echo ""
echo "View container logs:"
echo "  docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "View HAProxy logs:"
echo "  sudo journalctl -u haproxy -f"
echo ""
echo "Check container status:"
echo "  docker compose -f $COMPOSE_FILE ps"
echo ""

# Final notes
print_header "Important Notes"
echo ""
echo "1. Test the login functionality at http://$STAGING_IP"
echo "2. Review .env file and update production secrets"
echo "3. Change HAProxy stats password in /etc/haproxy/haproxy.cfg"
echo "4. Consider setting up SSL certificates for HTTPS"
echo ""

print_success "Setup complete! Your EDMS is now running behind HAProxy."
