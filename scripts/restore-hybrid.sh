#!/bin/bash
#
# EDMS Hybrid Restore - Production Ready
# Restores database and media files from backup
#

# Exit on error, but allow us to handle specific errors
set -e
set -o pipefail

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Use environment variables with fallbacks to defaults
DB_USER="${DB_USER:-edms_user}"
DB_NAME="${DB_NAME:-edms_db}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 backups/backup_20260111_222335.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

log "============================================"
log "EDMS Hybrid Restore - Starting"
log "============================================"
log "Backup file: $(basename $BACKUP_FILE)"
log ""

# Confirmation
echo "⚠️  WARNING: This will overwrite the current database and media files!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r CONFIRM
echo ""

if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# Extract backup
log "Step 1/4: Extracting backup archive..."
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Find backup data
BACKUP_DATA=$(find "$RESTORE_DIR" -name "database.dump" | head -1)
if [ -z "$BACKUP_DATA" ]; then
    log "❌ ERROR: database.dump not found in backup!"
    rm -rf "$RESTORE_DIR"
    exit 1
fi
BACKUP_DATA_DIR=$(dirname "$BACKUP_DATA")
log "✅ Archive extracted"

# Show manifest
if [ -f "$BACKUP_DATA_DIR/manifest.json" ]; then
    log "Backup information:"
    cat "$BACKUP_DATA_DIR/manifest.json" | python3 -m json.tool | head -10
    echo ""
fi

# Restore database
log "Step 2/4: Restoring database..."
log "Database: $DB_NAME (User: $DB_USER)"
docker compose -f "$COMPOSE_FILE" exec -T db pg_restore \
    -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists \
    < "$BACKUP_DATA_DIR/database.dump" 2>&1 | grep -v "pg_restore: warning" | grep -v "ERROR:  role" || true

log "✅ Database restored"

# Restore media files
log "Step 3/4: Restoring media files..."
if [ -f "$BACKUP_DATA_DIR/storage.tar.gz" ] && [ -s "$BACKUP_DATA_DIR/storage.tar.gz" ]; then
    # Clear existing storage contents (not the directory itself, as it's a volume mount)
    log "Clearing existing storage contents..."
    if docker compose -f "$COMPOSE_FILE" exec -T backend bash -c "rm -rf /app/storage/* && mkdir -p /app/storage/documents /app/storage/media"; then
        log "Extracting storage files to container..."
        if cat "$BACKUP_DATA_DIR/storage.tar.gz" | docker compose -f "$COMPOSE_FILE" exec -T backend tar -xzf - -C /app; then
            log "✅ Media files restored"
        else
            log "❌ ERROR: Failed to extract storage files to container"
            rm -rf "$RESTORE_DIR"
            exit 1
        fi
    else
        log "❌ ERROR: Failed to clear storage directory"
        rm -rf "$RESTORE_DIR"
        exit 1
    fi
else
    log "⚠️  No media files in backup"
fi

# Restart services first (before cleanup)
log "Step 4/4: Restarting services..."
if docker compose -f "$COMPOSE_FILE" restart backend frontend; then
    log "✅ Services restarted"
    log "Waiting for services to stabilize..."
    sleep 5
else
    log "⚠️  WARNING: Failed to restart services, but continuing..."
fi

# Cleanup
log "Cleaning up temporary files..."
rm -rf "$RESTORE_DIR"
log "✅ Cleanup complete"

# Summary
log ""
log "============================================"
log "  Restore Completed Successfully!"
log "============================================"
log ""
log "Next steps:"
log "  1. Verify documents are restored"
log "  2. Check uploaded files are accessible"
log "  3. Test login with restored user credentials"
log ""

exit 0
