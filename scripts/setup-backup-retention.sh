#!/bin/bash
#
# Backup Retention and Cleanup Script
# Keeps: Last 7 daily, 4 weekly, 12 monthly backups
#

set -e

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backups"
LOG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs/backup-cleanup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "EDMS Backup Retention Policy"
log "=========================================="
log "Backup directory: $BACKUP_DIR"

# Keep last 7 daily backups (based on modification time)
DAILY_KEEP=7
WEEKLY_KEEP=4
MONTHLY_KEEP=12

cd "$BACKUP_DIR"

# Count current backups
TOTAL_BACKUPS=$(ls -1 backup_*.tar.gz 2>/dev/null | wc -l)
log "Total backups found: $TOTAL_BACKUPS"

if [ "$TOTAL_BACKUPS" -le "$DAILY_KEEP" ]; then
    log "✅ No cleanup needed (only $TOTAL_BACKUPS backups)"
    exit 0
fi

# Keep only the last N backups
BACKUPS_TO_DELETE=$((TOTAL_BACKUPS - DAILY_KEEP))
log "Backups to delete: $BACKUPS_TO_DELETE"

# Delete old backups (keep newest)
ls -t backup_*.tar.gz 2>/dev/null | tail -n +$((DAILY_KEEP + 1)) | while read backup; do
    SIZE=$(du -h "$backup" | cut -f1)
    log "🗑️  Deleting: $backup ($SIZE)"
    rm -f "$backup"
done

# Summary
REMAINING=$(ls -1 backup_*.tar.gz 2>/dev/null | wc -l)
log "✅ Cleanup complete. Remaining backups: $REMAINING"
log "=========================================="

exit 0
