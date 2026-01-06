#!/bin/bash
#
# EDMS Backup Script - Method #2 (PostgreSQL pg_dump)
#
# This script creates a complete backup of:
# 1. PostgreSQL database (using pg_dump)
# 2. Document storage (Docker volumes)
# 3. Configuration files
#
# Usage: ./backup-edms.sh [backup_name]
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$HOME/edms-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-backup_${TIMESTAMP}}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Docker configuration
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-edms_db}"
POSTGRES_USER="${POSTGRES_USER:-edms}"
POSTGRES_DB="${POSTGRES_DB:-edms}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Create backup directory
log_info "Creating backup directory: ${BACKUP_PATH}"
mkdir -p "${BACKUP_PATH}"

# Check if PostgreSQL container is running
if ! docker ps | grep -q "${POSTGRES_CONTAINER}"; then
    log_error "PostgreSQL container '${POSTGRES_CONTAINER}' is not running"
    exit 1
fi

log_info "Starting EDMS backup: ${BACKUP_NAME}"
echo "========================================"

# 1. Backup PostgreSQL database
log_info "Step 1/4: Backing up PostgreSQL database..."
docker exec "${POSTGRES_CONTAINER}" pg_dump \
    -U "${POSTGRES_USER}" \
    -Fc \
    "${POSTGRES_DB}" > "${BACKUP_PATH}/database.dump"

# Check if backup was successful
if [ -f "${BACKUP_PATH}/database.dump" ] && [ -s "${BACKUP_PATH}/database.dump" ]; then
    DB_SIZE=$(du -h "${BACKUP_PATH}/database.dump" | cut -f1)
    log_info "✓ Database backup complete (${DB_SIZE})"
else
    log_error "Database backup failed"
    exit 1
fi

# 2. Backup document storage (Docker volumes)
log_info "Step 2/4: Backing up document storage..."

# Get volume names (adjust based on your docker-compose setup)
STORAGE_VOLUMES=(
    "edms-staging_media_files"
    "edms-staging_static_files"
    "edms-staging_documents"
)

# Check which volumes exist
EXISTING_VOLUMES=()
for volume in "${STORAGE_VOLUMES[@]}"; do
    if docker volume ls | grep -q "${volume}"; then
        EXISTING_VOLUMES+=("${volume}")
    fi
done

if [ ${#EXISTING_VOLUMES[@]} -eq 0 ]; then
    log_warn "No storage volumes found. Creating empty storage backup..."
    touch "${BACKUP_PATH}/storage.tar.gz"
else
    # Create temporary container to access volumes
    log_info "Found ${#EXISTING_VOLUMES[@]} storage volume(s)"
    
    # Build docker run command with all volumes
    VOLUME_MOUNTS=""
    for volume in "${EXISTING_VOLUMES[@]}"; do
        VOLUME_MOUNTS="${VOLUME_MOUNTS} -v ${volume}:/backup-source/${volume}:ro"
    done
    
    docker run --rm \
        ${VOLUME_MOUNTS} \
        -v "${BACKUP_PATH}:/backup-dest" \
        alpine:latest \
        tar -czf /backup-dest/storage.tar.gz -C /backup-source .
    
    STORAGE_SIZE=$(du -h "${BACKUP_PATH}/storage.tar.gz" | cut -f1)
    log_info "✓ Storage backup complete (${STORAGE_SIZE})"
fi

# 3. Backup configuration files
log_info "Step 3/4: Backing up configuration files..."

# Configuration files to backup
CONFIG_FILES=(
    ".env"
    "docker-compose.yml"
    "docker-compose.prod.yml"
)

mkdir -p "${BACKUP_PATH}/config"
CONFIG_COUNT=0

for config in "${CONFIG_FILES[@]}"; do
    if [ -f "${config}" ]; then
        cp "${config}" "${BACKUP_PATH}/config/"
        CONFIG_COUNT=$((CONFIG_COUNT + 1))
    fi
done

if [ ${CONFIG_COUNT} -gt 0 ]; then
    log_info "✓ Backed up ${CONFIG_COUNT} configuration file(s)"
else
    log_warn "No configuration files found"
fi

# 4. Create metadata file
log_info "Step 4/4: Creating backup metadata..."

cat > "${BACKUP_PATH}/backup_metadata.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "created_at": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "postgres_container": "${POSTGRES_CONTAINER}",
    "postgres_user": "${POSTGRES_USER}",
    "postgres_db": "${POSTGRES_DB}",
    "database_size": "$(stat -f%z "${BACKUP_PATH}/database.dump" 2>/dev/null || stat -c%s "${BACKUP_PATH}/database.dump")",
    "storage_volumes": $(printf '%s\n' "${EXISTING_VOLUMES[@]}" | jq -R . | jq -s .),
    "method": "postgresql_pg_dump",
    "version": "2.0"
}
EOF

log_info "✓ Metadata created"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)

echo "========================================"
log_info "Backup completed successfully!"
echo ""
echo "Backup location: ${BACKUP_PATH}"
echo "Total size: ${TOTAL_SIZE}"
echo ""
echo "Backup contains:"
echo "  - database.dump (PostgreSQL backup)"
echo "  - storage.tar.gz (Docker volumes)"
echo "  - config/ (Configuration files)"
echo "  - backup_metadata.json (Backup info)"
echo ""
log_info "To restore this backup, run:"
echo "  ./restore-edms.sh ${BACKUP_NAME}"
echo ""
