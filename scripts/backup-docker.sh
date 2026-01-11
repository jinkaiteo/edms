#!/bin/bash
# Wrapper to run backup from Docker container

docker compose exec -T \
  -e DB_HOST=db \
  -e DB_USER=edms_user \
  -e DB_NAME=edms_db \
  -e STORAGE_PATH=/app/storage \
  backend bash << 'INNEREOF'
#!/bin/bash
set -e

# Configuration
BACKUP_BASE="/tmp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/tmp_$TIMESTAMP"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

log "============================================"
log "EDMS Hybrid Backup - Starting"
log "============================================"

mkdir -p "$BACKUP_DIR"

# Database backup
log "Step 1/4: Backing up database..."
export PGPASSWORD="${DB_PASSWORD:-edms_password}"
pg_dump -h "${DB_HOST:-db}" -U "${DB_USER:-edms_user}" -d "${DB_NAME:-edms_db}" \
    --format=custom --compress=9 \
    --file="$BACKUP_DIR/database.dump" 2>&1 | grep -v "pg_dump: warning" || true

if [ -f "$BACKUP_DIR/database.dump" ] && [ -s "$BACKUP_DIR/database.dump" ]; then
    DB_SIZE=$(du -h "$BACKUP_DIR/database.dump" | cut -f1)
    log "✅ Database backup complete: $DB_SIZE"
else
    log "❌ ERROR: Database backup failed!"
    exit 1
fi

# Media files backup
log "Step 2/4: Backing up media files..."
STORAGE_PATH="${STORAGE_PATH:-/app/storage}"
if [ -d "$STORAGE_PATH" ]; then
    rsync -a "$STORAGE_PATH/" "$BACKUP_DIR/storage/" 2>&1 || true
    FILE_COUNT=$(find "$BACKUP_DIR/storage" -type f 2>/dev/null | wc -l)
    STORAGE_SIZE=$(du -sh "$BACKUP_DIR/storage" 2>/dev/null | cut -f1)
    log "✅ Media files backup complete: $STORAGE_SIZE ($FILE_COUNT files)"
else
    mkdir -p "$BACKUP_DIR/storage"
    log "⚠️  No storage directory found"
fi

# Create manifest
log "Step 3/4: Creating manifest..."
cat > "$BACKUP_DIR/manifest.json" << MANEOF
{
  "timestamp": "$(date -Iseconds)",
  "database": "database.dump",
  "storage": "storage/",
  "backup_type": "full",
  "created_by": "backup-docker.sh"
}
MANEOF

# Package
log "Step 4/4: Creating archive..."
cd "$BACKUP_BASE"
tar -czf "backup_$TIMESTAMP.tar.gz" "tmp_$TIMESTAMP"
BACKUP_SIZE=$(du -h "backup_$TIMESTAMP.tar.gz" | cut -f1)
log "✅ Archive created: $BACKUP_SIZE"

# Output for host to copy
echo "BACKUP_FILE=/tmp/backups/backup_$TIMESTAMP.tar.gz"

rm -rf "$BACKUP_DIR"
log "============================================"
log "Backup complete!"
log "============================================"
INNEREOF
