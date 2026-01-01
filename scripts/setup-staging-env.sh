#!/bin/bash
# Setup staging environment file
# Run this script on your staging server

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log "Setting up staging environment..."
echo

# Check if we're in the project root
if [[ ! -f "docker-compose.prod.yml" ]]; then
    error "docker-compose.prod.yml not found. Please run this from the project root directory."
fi

# Get server IP (or use provided value)
if [ -z "$1" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    warn "No IP provided, detected: $SERVER_IP"
    read -p "Is this correct? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your server IP: " SERVER_IP
    fi
else
    SERVER_IP=$1
fi

log "Using server IP: $SERVER_IP"

# Generate random secret key
SECRET_KEY=$(openssl rand -base64 32)

# Create .env.prod file
log "Creating .env.prod file..."

cat > .env.prod << ENVFILE
# Django Settings
DJANGO_SETTINGS_MODULE=edms.settings.production
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${SERVER_IP},localhost,127.0.0.1

# Database Configuration
DB_NAME=edms_prod_db
DB_USER=edms_prod_user
DB_PASSWORD=edms_prod_password_123
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://${SERVER_IP},http://${SERVER_IP}:3001,http://localhost:3000

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False

# Storage Configuration
MEDIA_ROOT=/app/storage/media
STATIC_ROOT=/app/staticfiles

# Security Settings
CSRF_TRUSTED_ORIGINS=http://${SERVER_IP},http://${SERVER_IP}:3001
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Application Environment
ENVIRONMENT=staging
ENVFILE

log "✓ .env.prod file created"
echo

log "Environment configuration:"
echo -e "  Server IP: ${BLUE}${SERVER_IP}${NC}"
echo -e "  Database: ${BLUE}edms_prod_db${NC}"
echo -e "  Environment: ${BLUE}staging${NC}"
echo

log "✅ Staging environment setup complete!"
echo
log "Next steps:"
echo "  1. Review .env.prod and update any settings if needed"
echo "  2. Run: bash scripts/deploy-production.sh"
echo
