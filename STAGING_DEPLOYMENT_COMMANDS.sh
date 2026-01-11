#!/bin/bash
#
# EDMS Staging Deployment - Method #2 Backup System
# Server: 172.28.1.148
# User: lims
#

echo "═══════════════════════════════════════════════════════════"
echo "EDMS STAGING DEPLOYMENT - METHOD #2 BACKUP SYSTEM"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. SSH to staging server
echo "Step 1: Connecting to staging server..."
echo "Command: ssh lims@172.28.1.148"
echo ""

# Commands to run on staging server:
cat << 'STAGING_COMMANDS'

# ═══════════════════════════════════════════════════════════
# RUN THESE COMMANDS ON STAGING SERVER
# ═══════════════════════════════════════════════════════════

# 1. Navigate to deployment directory
cd ~/edms-staging
pwd  # Should show: /home/lims/edms-staging

# 2. Check current status
git status
git log --oneline -3

# 3. Pull latest changes
git pull origin develop

# 4. Check what changed
git log --oneline -10

# 5. Restart services (backend only - where changes are)
docker-compose restart backend

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# 6. Check backend health
curl -s http://localhost:8000/health/ | python3 -m json.tool

# 7. Test backup system (IMPORTANT!)
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TESTING METHOD #2 BACKUP SYSTEM"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Set environment variables for staging
export POSTGRES_CONTAINER="edms-staging_db_1"  # Or check: docker ps | grep postgres
export POSTGRES_USER="edms_user"
export POSTGRES_DB="edms_db"

# Check PostgreSQL container name
echo "PostgreSQL container:"
docker ps | grep postgres

# Create test backup
./scripts/backup-edms.sh staging_test_$(date +%Y%m%d_%H%M%S)

# Verify the backup
LATEST_BACKUP=$(ls -t ~/edms-backups/ | head -1)
echo ""
echo "Verifying backup: $LATEST_BACKUP"
./scripts/verify-backup.sh $LATEST_BACKUP

# List backups
echo ""
echo "Available backups:"
ls -lth ~/edms-backups/ | head -5

# Check backup contents
echo ""
echo "Backup contents:"
du -sh ~/edms-backups/$LATEST_BACKUP/*

# Setup automated backups (optional)
echo ""
echo "To setup automated backups:"
echo "  ./scripts/setup-backup-cron.sh"
echo ""
echo "Choose: Daily at 2 AM, Keep 14 days"

STAGING_COMMANDS

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "DEPLOYMENT COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next: SSH to staging and run the commands above"
echo "  ssh lims@172.28.1.148"
echo ""

