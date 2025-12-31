#!/bin/bash
#
# HAProxy Installation and Configuration Script for EDMS Staging Server
# Purpose: Set up HAProxy as reverse proxy for single port 80 entry point
# Server: 172.28.1.148 (staging)
#
# Usage: sudo bash scripts/setup-haproxy-staging.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HAPROXY_CONFIG_SOURCE="infrastructure/haproxy/haproxy.cfg"
HAPROXY_CONFIG_DEST="/etc/haproxy/haproxy.cfg"
HAPROXY_CONFIG_BACKUP="/etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d_%H%M%S)"
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_header "EDMS HAProxy Setup for Staging Server"
echo ""
echo "This script will:"
echo "  1. Install HAProxy"
echo "  2. Configure HAProxy for EDMS"
echo "  3. Update firewall rules"
echo "  4. Update Docker configuration"
echo "  5. Start and enable HAProxy"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Installation cancelled"
    exit 0
fi

# Step 1: Install HAProxy
print_header "Step 1: Installing HAProxy"

if command -v haproxy &> /dev/null; then
    CURRENT_VERSION=$(haproxy -v | head -n1)
    print_info "HAProxy already installed: $CURRENT_VERSION"
    read -p "Reinstall/upgrade? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt update
        apt install -y --only-upgrade haproxy
        print_success "HAProxy upgraded"
    else
        print_info "Skipping HAProxy installation"
    fi
else
    print_info "Installing HAProxy..."
    apt update
    apt install -y haproxy
    print_success "HAProxy installed successfully"
fi

# Verify installation
HAPROXY_VERSION=$(haproxy -v | head -n1)
print_success "HAProxy version: $HAPROXY_VERSION"

# Step 2: Backup existing configuration
print_header "Step 2: Backing up existing configuration"

if [ -f "$HAPROXY_CONFIG_DEST" ]; then
    cp "$HAPROXY_CONFIG_DEST" "$HAPROXY_CONFIG_BACKUP"
    print_success "Backup created: $HAPROXY_CONFIG_BACKUP"
else
    print_info "No existing configuration to backup"
fi

# Step 3: Install new configuration
print_header "Step 3: Installing HAProxy configuration"

if [ ! -f "$HAPROXY_CONFIG_SOURCE" ]; then
    print_error "Configuration file not found: $HAPROXY_CONFIG_SOURCE"
    print_info "Current directory: $(pwd)"
    print_info "Please run this script from the repository root"
    exit 1
fi

# Copy configuration
cp "$HAPROXY_CONFIG_SOURCE" "$HAPROXY_CONFIG_DEST"
print_success "Configuration installed"

# Validate configuration
print_info "Validating HAProxy configuration..."
if haproxy -c -f "$HAPROXY_CONFIG_DEST"; then
    print_success "Configuration is valid"
else
    print_error "Configuration validation failed"
    if [ -f "$HAPROXY_CONFIG_BACKUP" ]; then
        print_warning "Restoring backup..."
        cp "$HAPROXY_CONFIG_BACKUP" "$HAPROXY_CONFIG_DEST"
    fi
    exit 1
fi

# Step 4: Configure firewall
print_header "Step 4: Configuring firewall"

# Check if UFW is installed and active
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | head -n1 | awk '{print $2}')
    if [ "$UFW_STATUS" = "active" ]; then
        print_info "Configuring UFW firewall..."
        
        # Allow HTTP
        ufw allow 80/tcp comment 'HAProxy HTTP'
        print_success "Allowed port 80 (HTTP)"
        
        # Allow HTTPS (for future use)
        ufw allow 443/tcp comment 'HAProxy HTTPS'
        print_success "Allowed port 443 (HTTPS)"
        
        # Allow HAProxy stats page
        ufw allow 8404/tcp comment 'HAProxy Stats'
        print_success "Allowed port 8404 (HAProxy Stats)"
        
        # Reload UFW
        ufw reload
        print_success "Firewall rules updated"
    else
        print_warning "UFW is installed but not active"
    fi
else
    print_warning "UFW not found, skipping firewall configuration"
    print_info "You may need to configure your firewall manually:"
    print_info "  - Allow port 80 (HTTP)"
    print_info "  - Allow port 443 (HTTPS)"
    print_info "  - Allow port 8404 (HAProxy Stats)"
fi

# Step 5: Enable and start HAProxy
print_header "Step 5: Starting HAProxy"

# Enable HAProxy to start on boot
systemctl enable haproxy
print_success "HAProxy enabled to start on boot"

# Start HAProxy
print_info "Starting HAProxy service..."
systemctl restart haproxy
sleep 2

# Check status
if systemctl is-active --quiet haproxy; then
    print_success "HAProxy is running"
else
    print_error "HAProxy failed to start"
    print_info "Checking logs..."
    journalctl -u haproxy -n 20 --no-pager
    exit 1
fi

# Step 6: Verify HAProxy is listening
print_header "Step 6: Verifying HAProxy"

print_info "Checking listening ports..."
if netstat -tuln | grep -q ":80 "; then
    print_success "HAProxy listening on port 80"
else
    print_warning "HAProxy not listening on port 80"
fi

if netstat -tuln | grep -q ":8404 "; then
    print_success "HAProxy stats page available on port 8404"
else
    print_warning "HAProxy stats not listening on port 8404"
fi

# Test HAProxy health endpoint
print_info "Testing HAProxy health endpoint..."
if curl -s http://localhost/haproxy-health | grep -q "Healthy"; then
    print_success "HAProxy health check passed"
else
    print_warning "HAProxy health check failed (this is OK if Docker services aren't running yet)"
fi

# Step 7: Instructions for Docker update
print_header "Step 7: Next Steps - Update Docker Configuration"

echo ""
print_info "HAProxy installation complete! Now you need to update Docker configuration."
echo ""
echo "Run the following command:"
echo ""
echo "  ${GREEN}bash scripts/update-docker-for-haproxy.sh${NC}"
echo ""
echo "This will:"
echo "  - Update docker-compose.prod.yml with correct REACT_APP_API_URL"
echo "  - Update backend ALLOWED_HOSTS and CORS settings"
echo "  - Rebuild and restart containers"
echo ""

# Display access information
print_header "Access Information"
echo ""
echo "After Docker is updated and running:"
echo ""
echo "  📱 Application:    http://$STAGING_IP"
echo "  📊 HAProxy Stats:  http://$STAGING_IP:8404/stats"
echo "     Username: admin"
echo "     Password: admin_changeme (CHANGE THIS!)"
echo ""
echo "  🔧 Backend API:    http://$STAGING_IP/api/v1"
echo "  🔒 Django Admin:   http://$STAGING_IP/admin"
echo ""

# Display useful commands
print_header "Useful Commands"
echo ""
echo "Check HAProxy status:"
echo "  sudo systemctl status haproxy"
echo ""
echo "View HAProxy logs:"
echo "  sudo journalctl -u haproxy -f"
echo ""
echo "Test configuration:"
echo "  sudo haproxy -c -f /etc/haproxy/haproxy.cfg"
echo ""
echo "Restart HAProxy:"
echo "  sudo systemctl restart haproxy"
echo ""

print_success "HAProxy setup completed successfully!"
