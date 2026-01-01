#!/bin/bash
# Configure docker-compose.prod.yml to work with HAProxy
# HAProxy handles port 80, containers use internal ports only

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

log "Configuring docker-compose.prod.yml for HAProxy..."

# Check if file exists
if [ ! -f "docker-compose.prod.yml" ]; then
    error "docker-compose.prod.yml not found"
fi

# Backup original
cp docker-compose.prod.yml docker-compose.prod.yml.backup
log "Backed up docker-compose.prod.yml"

# Comment out nginx port 80 binding
log "Removing nginx port 80 binding (HAProxy will handle it)..."

# Use sed to comment out the port 80:80 line in nginx section
sed -i.tmp '/nginx:/,/healthcheck:/{
    s/^\(\s*\)- "80:80"$/\1# - "80:80"  # Commented out - HAProxy handles port 80/
    s/^\(\s*\)- "443:443"$/\1# - "443:443"  # Commented out - HAProxy handles HTTPS/
}' docker-compose.prod.yml

# Remove temp file
rm -f docker-compose.prod.yml.tmp

log "✓ Configuration updated"
log ""
log "Architecture:"
echo "  Internet (port 80) → HAProxy (host)"
echo "                         ↓"
echo "                         ├─ Frontend: localhost:3001"
echo "                         └─ Backend:  localhost:8001"
log ""
log "Next steps:"
echo "  1. Setup HAProxy: sudo bash scripts/setup-haproxy-staging.sh"
echo "  2. Deploy containers: bash deploy-staging-complete.sh"
log ""
log "Note: Nginx container will still run but won't bind to port 80"
