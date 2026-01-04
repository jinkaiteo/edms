#!/bin/bash
#
# EDMS Restore Script - Method #2 (PostgreSQL pg_restore)
#
# This script restores a complete EDMS backup:
# 1. PostgreSQL database (using pg_restore)
# 2. Document storage (Docker volumes)
# 3. Configuration files (optional)
#
# Usage: ./restore-edms.sh <backup_name>
#
# WARNING: This will OVERWRITE existing data!
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$HOME/edms-backups}"
BACKUP_NAME="${1}"

# Docker configuration
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-edms_db}"
POSTGRES_USER="${POSTGRES_USER:-edms}"
POSTGRES_DB="${POSTGRES_DB:-edms}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if backup name provided
if [ -z "${BACKUP_NAME}" ]; then
    log_error "Backup name required"
    echo ""
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    if [ -d "${BACKUP_DIR}" ]; then
        ls -1 "${BACKUP_DIR}" | head -10
    else
        echo "  (no backups found in ${BACKUP_DIR})"
    fi
    exit 1
fi

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Check if backup exists
if [ ! -d "${BACKUP_PATH}" ]; then
    log_error "Backup not found: ${BACKUP_PATH}"
    echo ""
    echo "Available backups:"
    ls -1 "${BACKUP_DIR}" 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

# Check backup contents
if [ ! -f "${BACKUP_PATH}/database.dump" ]; then
    log_error "Invalid backup: database.dump not found"
    exit 1
fi

# Display backup info
if [ -f "${BACKUP_PATH}/backup_metadata.json" ]; then
    log_info "Backup Information:"
    cat "${BACKUP_PATH}/backup_metadata.json" | jq '.' 2>/dev/null || cat "${BACKUP_PATH}/backup_metadata.json"
    echo ""
fi

# Confirmation prompt
log_warn "⚠️  WARNING: This will OVERWRITE existing data!"
echo ""
echo "This will restore:"
echo "  - Database: ${POSTGRES_DB}"
echo "  - Storage: Docker volumes"
echo "  - From: ${BACKUP_PATH}"
echo ""
read -p "Are you sure you want to continue? (type 'YES' to confirm): " -r
echo ""

if [ "$REPLY" != "YES" ]; then
    log_info "Restore cancelled"
    exit 0
fi

log_info "Starting EDMS restore: ${BACKUP_NAME}"
echo "========================================"

# Check if PostgreSQL container is running
if ! docker ps | grep -q "${POSTGRES_CONTAINER}"; then
    log_error "PostgreSQL container '${POSTGRES_CONTAINER}' is not running"
    echo "Start the container first: docker-compose up -d"
    exit 1
fi

# 1. Restore PostgreSQL database
log_step "Step 1/3: Restoring PostgreSQL database..."

# Drop existing database and recreate (clean restore)
log_info "Dropping existing database..."
docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" postgres

log_info "Creating fresh database..."
docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};" postgres

log_info "Restoring database from backup..."
docker exec -i "${POSTGRES_CONTAINER}" pg_restore \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --no-owner \
    --no-acl \
    --if-exists \
    --clean < "${BACKUP_PATH}/database.dump" 2>&1 | grep -v "already exists\|does not exist" || true

log_info "✓ Database restored"

# 2. Restore storage volumes
log_step "Step 2/3: Restoring document storage..."

if [ -f "${BACKUP_PATH}/storage.tar.gz" ] && [ -s "${BACKUP_PATH}/storage.tar.gz" ]; then
    # Get volume names
    STORAGE_VOLUMES=(
        "edms-staging_media_files"
        "edms-staging_static_files"
        "edms-staging_documents"
    )
    
    # Build docker run command with all volumes
    VOLUME_MOUNTS=""
    for volume in "${STORAGE_VOLUMES[@]}"; do
        # Create volume if it doesn't exist
        docker volume create "${volume}" 2>/dev/null || true
        VOLUME_MOUNTS="${VOLUME_MOUNTS} -v ${volume}:/restore-dest/${volume}"
    done
    
    log_info "Extracting storage data to volumes..."
    docker run --rm \
        ${VOLUME_MOUNTS} \
        -v "${BACKUP_PATH}:/backup-source:ro" \
        alpine:latest \
        sh -c "cd /restore-dest && tar -xzf /backup-source/storage.tar.gz"
    
    log_info "✓ Storage restored"
else
    log_warn "No storage backup found or empty, skipping"
fi

# 3. Restore configuration files (optional)
log_step "Step 3/3: Configuration files..."

if [ -d "${BACKUP_PATH}/config" ]; then
    log_info "Configuration files available in: ${BACKUP_PATH}/config"
    echo ""
    ls -1 "${BACKUP_PATH}/config"
    echo ""
    log_warn "Configuration files NOT automatically restored (manual review recommended)"
    echo "To restore configs manually:"
    echo "  cp ${BACKUP_PATH}/config/.env ."
    echo "  cp ${BACKUP_PATH}/config/docker-compose.yml ."
else
    log_info "No configuration backup found"
fi

echo "========================================"
log_info "Restore completed successfully!"
echo ""
log_info "Next steps:"
echo "  1. Restart services: docker-compose restart"
echo "  2. Run migrations (if needed): docker-compose exec backend python manage.py migrate"
echo "  3. Verify data: Check documents and users"
echo ""
log_warn "Note: You may need to:"
echo "  - Clear browser cache"
echo "  - Re-login to the system"
echo "  - Verify file permissions"
echo ""
