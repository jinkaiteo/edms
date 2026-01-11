#!/bin/bash
#
# EDMS Backup Cron Setup Script
#
# This script helps set up automated backups using cron
#
# Usage: ./setup-backup-cron.sh
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "========================================"
echo "EDMS Backup Cron Setup"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-edms.sh"

# Check if backup script exists
if [ ! -f "${BACKUP_SCRIPT}" ]; then
    echo "Error: backup-edms.sh not found at ${BACKUP_SCRIPT}"
    exit 1
fi

log_info "Current backup script: ${BACKUP_SCRIPT}"
echo ""

# Cron schedule options
log_step "Select backup schedule:"
echo ""
echo "1) Daily at 2:00 AM"
echo "2) Daily at 3:00 AM" 
echo "3) Every 12 hours (2 AM and 2 PM)"
echo "4) Every 6 hours"
echo "5) Weekly on Sunday at 2:00 AM"
echo "6) Custom schedule"
echo ""
read -p "Enter choice [1-6]: " -r SCHEDULE_CHOICE
echo ""

case ${SCHEDULE_CHOICE} in
    1)
        CRON_SCHEDULE="0 2 * * *"
        SCHEDULE_DESC="Daily at 2:00 AM"
        ;;
    2)
        CRON_SCHEDULE="0 3 * * *"
        SCHEDULE_DESC="Daily at 3:00 AM"
        ;;
    3)
        CRON_SCHEDULE="0 2,14 * * *"
        SCHEDULE_DESC="Every 12 hours (2 AM and 2 PM)"
        ;;
    4)
        CRON_SCHEDULE="0 */6 * * *"
        SCHEDULE_DESC="Every 6 hours"
        ;;
    5)
        CRON_SCHEDULE="0 2 * * 0"
        SCHEDULE_DESC="Weekly on Sunday at 2:00 AM"
        ;;
    6)
        echo "Enter cron schedule (e.g., '0 2 * * *' for daily at 2 AM):"
        read -p "Schedule: " -r CRON_SCHEDULE
        SCHEDULE_DESC="Custom: ${CRON_SCHEDULE}"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Retention policy
log_step "Select backup retention policy:"
echo ""
echo "1) Keep last 7 backups"
echo "2) Keep last 14 backups"
echo "3) Keep last 30 backups"
echo "4) Keep all backups (no cleanup)"
echo ""
read -p "Enter choice [1-4]: " -r RETENTION_CHOICE
echo ""

case ${RETENTION_CHOICE} in
    1)
        RETENTION_DAYS=7
        ;;
    2)
        RETENTION_DAYS=14
        ;;
    3)
        RETENTION_DAYS=30
        ;;
    4)
        RETENTION_DAYS=0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Build cron command
CRON_COMMAND="${BACKUP_SCRIPT}"

# Add cleanup if retention policy set
if [ ${RETENTION_DAYS} -gt 0 ]; then
    CLEANUP_COMMAND="find \$HOME/edms-backups -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;"
    CRON_COMMAND="${CRON_COMMAND} && ${CLEANUP_COMMAND}"
fi

# Add log redirection
LOG_FILE="\$HOME/edms-backups/backup.log"
CRON_COMMAND="${CRON_COMMAND} >> ${LOG_FILE} 2>&1"

# Complete cron entry
CRON_ENTRY="${CRON_SCHEDULE} ${CRON_COMMAND}"

# Display summary
echo "========================================"
log_info "Backup Schedule Summary"
echo "========================================"
echo ""
echo "Schedule: ${SCHEDULE_DESC}"
echo "Cron: ${CRON_SCHEDULE}"
if [ ${RETENTION_DAYS} -gt 0 ]; then
    echo "Retention: Keep last ${RETENTION_DAYS} days"
else
    echo "Retention: Keep all backups"
fi
echo "Log file: ~/edms-backups/backup.log"
echo ""
echo "Cron entry:"
echo "${CRON_ENTRY}"
echo ""

# Confirm installation
read -p "Install this cron job? (y/n): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Installation cancelled"
    echo ""
    echo "To install manually, add this line to your crontab:"
    echo "${CRON_ENTRY}"
    exit 0
fi

# Install cron job
log_info "Installing cron job..."

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -F "${BACKUP_SCRIPT}" > /dev/null; then
    log_info "Removing existing backup cron job..."
    crontab -l 2>/dev/null | grep -v "${BACKUP_SCRIPT}" | crontab - || true
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "${CRON_ENTRY}") | crontab -

log_info "✓ Cron job installed successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep "${BACKUP_SCRIPT}"
echo ""
log_info "Next steps:"
echo "  1. Backups will run automatically according to schedule"
echo "  2. Check logs: tail -f ~/edms-backups/backup.log"
echo "  3. List backups: ls -lt ~/edms-backups/"
echo "  4. Verify backup: ./verify-backup.sh <backup_name>"
echo ""
