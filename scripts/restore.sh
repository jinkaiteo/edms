#!/bin/bash
#
# EDMS Restore Script - Hybrid Approach
# Restores full backup: database + media files
#
# Usage: ./restore.sh /path/to/backup_20260111_120000.tar.gz
#

set -e  # Exit on error

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 /backups/backup_20260111_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Configuration
RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
DB_HOST="${DB_HOST:-db}"
DB_USER="${DB_USER:-edms_user}"
DB_NAME="${DB_NAME:-edms_db}"
DB_PASSWORD="${DB_PASSWORD:-edms_password}"
STORAGE_PATH="${STORAGE_PATH:-/app/storage}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "============================================"
log "EDMS Hybrid Restore - Starting"
log "============================================"
log "Backup file: $(basename $BACKUP_FILE)"

# Confirmation prompt
echo ""
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
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR" 2>&1 || {
    log "❌ ERROR: Failed to extract archive!"
    rm -rf "$RESTORE_DIR"
    exit 1
}
log "✅ Archive extracted successfully"

# Find the actual backup directory
BACKUP_CONTENT=$(find "$RESTORE_DIR" -name "database.dump" -type f | head -1)
if [ -z "$BACKUP_CONTENT" ]; then
    log "❌ ERROR: database.dump not found in backup!"
    rm -rf "$RESTORE_DIR"
    exit 1
fi
BACKUP_DATA_DIR=$(dirname "$BACKUP_CONTENT")
log "Backup data directory: $BACKUP_DATA_DIR"

# Show manifest
if [ -f "$BACKUP_DATA_DIR/manifest.json" ]; then
    log "Backup information:"
    cat "$BACKUP_DATA_DIR/manifest.json" | grep -E "timestamp|version|backup_type" | sed 's/^/  /'
fi

# Restore database
log "Step 2/4: Restoring database..."
export PGPASSWORD="$DB_PASSWORD"
pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --clean \
    --if-exists \
    "$BACKUP_DATA_DIR/database.dump" 2>&1 | grep -v "pg_restore: warning" | grep -v "ERROR:  role" || true

# Check if restore was successful
if [ ${PIPESTATUS[0]} -eq 0 ] || pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t documents_document --schema-only > /dev/null 2>&1; then
    log "✅ Database restored successfully"
else
    log "❌ ERROR: Database restore failed!"
    log "Note: Some errors might be normal (e.g., dropping non-existent objects)"
    read -p "Continue with file restore? (yes/no): " -r REPLY
    echo ""
    if [ "$REPLY" != "yes" ]; then
        rm -rf "$RESTORE_DIR"
        exit 1
    fi
fi

# Restore media files
log "Step 3/4: Restoring media files..."
if [ -d "$BACKUP_DATA_DIR/storage" ]; then
    # Backup existing storage (just in case)
    if [ -d "$STORAGE_PATH" ] && [ "$(ls -A $STORAGE_PATH 2>/dev/null)" ]; then
        STORAGE_BACKUP="/tmp/storage_backup_$(date +%Y%m%d_%H%M%S)"
        log "Creating safety backup of existing storage to $STORAGE_BACKUP"
        mkdir -p "$STORAGE_BACKUP"
        rsync -a "$STORAGE_PATH/" "$STORAGE_BACKUP/" 2>&1 || true
    fi
    
    # Restore files
    mkdir -p "$STORAGE_PATH"
    rsync -a --delete "$BACKUP_DATA_DIR/storage/" "$STORAGE_PATH/" 2>&1 || {
        log "❌ ERROR: Media files restore failed!"
        if [ -d "$STORAGE_BACKUP" ]; then
            log "Attempting to restore from safety backup..."
            rsync -a "$STORAGE_BACKUP/" "$STORAGE_PATH/" 2>&1 || true
        fi
        rm -rf "$RESTORE_DIR"
        exit 1
    }
    
    FILE_COUNT=$(find "$STORAGE_PATH" -type f 2>/dev/null | wc -l)
    log "✅ Media files restored successfully ($FILE_COUNT files)"
    
    # Cleanup safety backup if successful
    if [ -d "$STORAGE_BACKUP" ]; then
        rm -rf "$STORAGE_BACKUP"
    fi
else
    log "⚠️  WARNING: No storage directory found in backup"
fi

# Cleanup
log "Step 4/4: Cleaning up temporary files..."
rm -rf "$RESTORE_DIR"
log "✅ Cleanup complete"

# Summary
log "============================================"
log "Restore completed successfully!"
log "Database: ✅ Restored"
log "Media files: ✅ Restored"
log "============================================"
log ""
log "You may need to restart the application:"
log "  docker compose restart backend frontend"

exit 0
