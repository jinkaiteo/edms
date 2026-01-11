#!/bin/bash
#
# EDMS Backup Script - Hybrid Approach
# Creates full backup: database + media files
#
# Usage: ./backup.sh
# Output: /backups/backup_YYYYMMDD_HHMMSS.tar.gz
#

set -e  # Exit on error

# Configuration
BACKUP_BASE="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/tmp_$TIMESTAMP"
BACKUP_FILE="$BACKUP_BASE/backup_$TIMESTAMP.tar.gz"

# Database settings (from environment or docker-compose)
DB_HOST="${DB_HOST:-db}"
DB_USER="${DB_USER:-edms_user}"
DB_NAME="${DB_NAME:-edms_db}"
DB_PASSWORD="${DB_PASSWORD:-edms_password}"

# Storage location
STORAGE_PATH="${STORAGE_PATH:-/app/storage}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "============================================"
log "EDMS Hybrid Backup - Starting"
log "============================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"
log "Created backup directory: $BACKUP_DIR"

# Step 1: Database backup
log "Step 1/4: Backing up database..."
export PGPASSWORD="$DB_PASSWORD"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/database.dump" 2>&1 | grep -v "pg_dump: warning" || true

if [ -f "$BACKUP_DIR/database.dump" ] && [ -s "$BACKUP_DIR/database.dump" ]; then
    DB_SIZE=$(du -h "$BACKUP_DIR/database.dump" | cut -f1)
    log "✅ Database backup complete: $DB_SIZE"
else
    log "❌ ERROR: Database backup failed!"
    rm -rf "$BACKUP_DIR"
    exit 1
fi

# Step 2: Media files backup
log "Step 2/4: Backing up media files..."
if [ -d "$STORAGE_PATH" ]; then
    rsync -a "$STORAGE_PATH/" "$BACKUP_DIR/storage/" 2>&1 || true
    
    if [ -d "$BACKUP_DIR/storage" ]; then
        STORAGE_SIZE=$(du -sh "$BACKUP_DIR/storage" 2>/dev/null | cut -f1)
        FILE_COUNT=$(find "$BACKUP_DIR/storage" -type f 2>/dev/null | wc -l)
        log "✅ Media files backup complete: $STORAGE_SIZE ($FILE_COUNT files)"
    else
        log "⚠️  No media files found (directory empty or doesn't exist)"
        mkdir -p "$BACKUP_DIR/storage"
    fi
else
    log "⚠️  Storage path not found: $STORAGE_PATH"
    mkdir -p "$BACKUP_DIR/storage"
fi

# Step 3: Create manifest
log "Step 3/4: Creating manifest..."
GIT_VERSION=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
cat > "$BACKUP_DIR/manifest.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "database": "database.dump",
  "storage": "storage/",
  "version": "$GIT_VERSION",
  "backup_type": "full",
  "database_size": "$(du -b "$BACKUP_DIR/database.dump" 2>/dev/null | cut -f1)",
  "storage_file_count": $(find "$BACKUP_DIR/storage" -type f 2>/dev/null | wc -l),
  "created_by": "backup.sh"
}
EOF
log "✅ Manifest created"

# Step 4: Package everything
log "Step 4/4: Creating compressed archive..."
cd "$BACKUP_BASE"
tar -czf "$BACKUP_FILE" "tmp_$TIMESTAMP" 2>&1 || {
    log "❌ ERROR: Archive creation failed!"
    rm -rf "$BACKUP_DIR"
    exit 1
}

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Archive created: $(basename $BACKUP_FILE) ($BACKUP_SIZE)"
else
    log "❌ ERROR: Backup file not created!"
    rm -rf "$BACKUP_DIR"
    exit 1
fi

# Cleanup temporary directory
rm -rf "$BACKUP_DIR"
log "✅ Cleaned up temporary files"

# Summary
log "============================================"
log "Backup completed successfully!"
log "File: $BACKUP_FILE"
log "Size: $BACKUP_SIZE"
log "============================================"

exit 0
