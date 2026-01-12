#!/bin/bash
#
# EDMS Hybrid Restore - Production Ready
# Restores database and media files from backup
#

set -e

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
    # Extract and copy to container
    docker compose -f "$COMPOSE_FILE" exec -T backend bash -c "rm -rf /app/storage && mkdir -p /app/storage" 2>/dev/null
    cat "$BACKUP_DATA_DIR/storage.tar.gz" | docker compose -f "$COMPOSE_FILE" exec -T backend tar -xzf - -C /app
    log "✅ Media files restored"
else
    log "⚠️  No media files in backup"
fi

# Cleanup
log "Step 4/4: Cleaning up..."
rm -rf "$RESTORE_DIR"
log "✅ Cleanup complete"

# Summary
log "============================================"
log "Restore completed successfully!"
log "============================================"
log ""
log "Restarting services..."
docker compose -f "$COMPOSE_FILE" restart backend frontend

log "✅ Services restarted"
log ""
log "Restore complete! Please verify your application."

exit 0
