#!/bin/bash
#
# Setup automated backup cron jobs for EDMS
# This script creates cron jobs on the host system
#

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
BACKUP_LOG="$LOG_DIR/backup.log"

echo "=========================================="
echo "EDMS Backup Cron Setup"
echo "=========================================="
echo "Project directory: $PROJECT_DIR"
echo "Log directory: $LOG_DIR"
echo ""

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create cron job entries
CRON_DAILY="0 2 * * * cd $PROJECT_DIR && ./scripts/backup-hybrid.sh >> $BACKUP_LOG 2>&1"
CRON_WEEKLY="0 3 * * 0 cd $PROJECT_DIR && ./scripts/backup-hybrid.sh >> $BACKUP_LOG 2>&1"
CRON_MONTHLY="0 4 1 * * cd $PROJECT_DIR && ./scripts/backup-hybrid.sh >> $BACKUP_LOG 2>&1"

echo "Proposed cron jobs:"
echo "-------------------------------------------"
echo "Daily (2 AM):   $CRON_DAILY"
echo "Weekly (3 AM):  $CRON_WEEKLY"
echo "Monthly (4 AM): $CRON_MONTHLY"
echo "-------------------------------------------"
echo ""

# Check if user wants to install
read -p "Do you want to install these cron jobs? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Installation cancelled."
    exit 0
fi

# Backup existing crontab
crontab -l > /tmp/crontab.backup 2>/dev/null || echo "# No existing crontab"

# Check if jobs already exist
if crontab -l 2>/dev/null | grep -q "backup-hybrid.sh"; then
    echo ""
    echo "⚠️  Warning: EDMS backup jobs already exist in crontab"
    read -p "Remove existing jobs and reinstall? (yes/no): " REINSTALL
    if [ "$REINSTALL" = "yes" ]; then
        # Remove existing EDMS backup jobs
        crontab -l 2>/dev/null | grep -v "backup-hybrid.sh" | crontab -
        echo "✅ Existing jobs removed"
    else
        echo "Installation cancelled."
        exit 0
    fi
fi

# Add new jobs
(crontab -l 2>/dev/null; echo ""; echo "# EDMS Automated Backups"; echo "$CRON_DAILY"; echo "$CRON_WEEKLY"; echo "$CRON_MONTHLY") | crontab -

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "Verify installation with: crontab -l"
echo "View logs with: tail -f $BACKUP_LOG"
echo ""
echo "Manual test: cd $PROJECT_DIR && ./scripts/backup-hybrid.sh"
echo ""

exit 0
