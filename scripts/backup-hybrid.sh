#!/bin/bash
#
# EDMS Hybrid Backup - Production Ready
# Runs pg_dump from DB container, packages with storage files
#

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Configuration
BACKUP_DIR="$(pwd)/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_DIR="$BACKUP_DIR/tmp_$TIMESTAMP"

# Use environment variables with fallbacks to defaults
DB_USER="${DB_USER:-edms_user}"
DB_NAME="${DB_NAME:-edms_db}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

log "============================================"
log "EDMS Hybrid Backup - Starting"
log "============================================"
log "Database: $DB_NAME (User: $DB_USER)"
log "Compose file: $COMPOSE_FILE"

mkdir -p "$TEMP_DIR"

# Step 1: Database backup (from db container)
log "Step 1/4: Backing up database..."
docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    > "$TEMP_DIR/database.dump"

if [ -f "$TEMP_DIR/database.dump" ] && [ -s "$TEMP_DIR/database.dump" ]; then
    DB_SIZE=$(du -h "$TEMP_DIR/database.dump" | cut -f1)
    log "✅ Database backup complete: $DB_SIZE"
else
    log "❌ ERROR: Database backup failed!"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Step 2: Media files backup (from backend container)
log "Step 2/4: Backing up media files..."
docker compose -f "$COMPOSE_FILE" exec -T backend tar -czf - -C /app storage 2>/dev/null > "$TEMP_DIR/storage.tar.gz"

if [ -f "$TEMP_DIR/storage.tar.gz" ] && [ -s "$TEMP_DIR/storage.tar.gz" ]; then
    STORAGE_SIZE=$(du -h "$TEMP_DIR/storage.tar.gz" | cut -f1)
    log "✅ Media files backup complete: $STORAGE_SIZE"
else
    log "⚠️  No media files or empty storage"
    touch "$TEMP_DIR/storage.tar.gz"
fi

# Step 3: Create manifest
log "Step 3/4: Creating manifest..."
GIT_VERSION=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
cat > "$TEMP_DIR/manifest.json" << MANEOF
{
  "timestamp": "$(date -Iseconds)",
  "database": "database.dump",
  "storage": "storage.tar.gz",
  "version": "$GIT_VERSION",
  "backup_type": "full",
  "created_by": "backup-hybrid.sh"
}
MANEOF
log "✅ Manifest created"

# Step 4: Package everything
log "Step 4/4: Creating final archive..."
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" "tmp_$TIMESTAMP"

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Archive created: backup_$TIMESTAMP.tar.gz ($BACKUP_SIZE)"
else
    log "❌ ERROR: Failed to create archive!"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"
log "✅ Cleaned up temporary files"

# Summary
log "============================================"
log "Backup completed successfully!"
log "File: $BACKUP_FILE"
log "Size: $BACKUP_SIZE"
log "============================================"

exit 0
