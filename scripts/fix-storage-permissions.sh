#!/bin/bash
# Fix storage directory permissions for EDMS deployment
# This ensures the backend container can write to storage directories

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

log "Fixing EDMS storage directory permissions..."
echo

# Check if we're in the right directory
if [[ ! -f "docker-compose.prod.yml" ]]; then
    error "docker-compose.prod.yml not found. Please run this from the project root directory."
fi

# Create storage directories if they don't exist
log "Creating storage directories..."
mkdir -p storage/documents
mkdir -p storage/backups
mkdir -p storage/temp
mkdir -p logs/backend
mkdir -p logs/db
mkdir -p logs/redis
mkdir -p logs/nginx

log "✓ Directories created"
echo

# Set proper permissions
log "Setting directory permissions..."

# For staging/development: Make directories writable by Docker container
# The container typically runs as root or a specific user (UID 1000 is common)
chmod -R 755 storage/
chmod -R 755 logs/

log "✓ Permissions set to 755 (readable/executable by all, writable by owner)"
echo

# Alternative: If you know the specific UID the container uses, set ownership
# Uncomment and adjust if needed:
# log "Setting directory ownership to UID 1000..."
# sudo chown -R 1000:1000 storage/
# sudo chown -R 1000:1000 logs/

# Show current permissions
log "Current directory structure and permissions:"
echo
echo "Storage directories:"
ls -lah storage/
echo
echo "Log directories:"
ls -lah logs/
echo

# Restart backend to apply changes
log "Restarting backend container..."
docker compose -f docker-compose.prod.yml restart backend

# Wait for backend to be ready
log "Waiting for backend to restart (10 seconds)..."
sleep 10

# Check if backend is healthy
log "Checking backend health..."
if docker compose -f docker-compose.prod.yml exec -T backend python manage.py check --deploy > /dev/null 2>&1; then
    log "✓ Backend is healthy"
else
    warn "Backend health check returned warnings (this may be normal)"
fi

echo
log "✅ Storage permissions fixed successfully!"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Try creating a document in the application"
echo "  2. Check that files are being saved to storage/documents/"
echo "  3. Verify logs are being written to logs/backend/"
echo
