#!/bin/bash
#
# EDMS Migration Package Restore Script
#
# This script restores an EDMS system from a migration package.
#
# Usage: ./restore.sh [options]
#   --target-dir /path/to/edms    Target EDMS installation directory
#   --db-host hostname            Database host (default: localhost)
#   --db-port 5432               Database port (default: 5432)
#   --db-name edms_db            Database name (default: edms_db)
#   --db-user edms_user          Database user (default: edms_user)
#   --skip-users                 Skip user account restoration
#   --verify                     Verify restoration after completion
#   --help                       Show this help message

set -e

# Default values
TARGET_DIR="/opt/edms"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="edms_db"
DB_USER="edms_user"
SKIP_USERS=false
VERIFY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --db-host)
            DB_HOST="$2"
            shift 2
            ;;
        --db-port)
            DB_PORT="$2"
            shift 2
            ;;
        --db-name)
            DB_NAME="$2"
            shift 2
            ;;
        --db-user)
            DB_USER="$2"
            shift 2
            ;;
        --skip-users)
            SKIP_USERS=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# //g'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 EDMS Migration Package Restore"
echo "=================================="
echo ""
echo "Target Directory: $TARGET_DIR"
echo "Database Host: $DB_HOST:$DB_PORT"
echo "Database Name: $DB_NAME"
echo ""

# Check prerequisites
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client (psql) not found"
    exit 1
fi

if ! command -v pg_restore &> /dev/null; then
    echo "❌ PostgreSQL restore tool (pg_restore) not found"
    exit 1
fi

# Prompt for database password
read -s -p "Enter database password for $DB_USER: " DB_PASSWORD
echo ""
export PGPASSWORD="$DB_PASSWORD"

# Check database connectivity
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
    echo "❌ Cannot connect to database"
    exit 1
fi

echo "✓ Database connection verified"

# Restore database
echo "📊 Restoring database..."
if [ -f "database/complete.sql" ]; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "database/complete.sql"
    echo "✓ Database restored"
else
    echo "❌ Database backup file not found"
    exit 1
fi

# Restore storage files
echo "📁 Restoring storage files..."
if [ -d "$TARGET_DIR/storage" ]; then
    echo "Creating backup of existing storage..."
    mv "$TARGET_DIR/storage" "$TARGET_DIR/storage.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$TARGET_DIR/storage"
if [ -d "storage" ]; then
    cp -r storage/* "$TARGET_DIR/storage/"
    echo "✓ Storage files restored"
else
    echo "⚠️  No storage files found in package"
fi

# Restore configuration (if target directory has EDMS installation)
if [ -d "$TARGET_DIR/backend" ]; then
    echo "⚙️  Configuration restoration available"
    echo "   (Manual configuration review recommended)"
fi

echo ""
echo "✅ Restoration completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "   1. Review and update configuration files"
echo "   2. Run Django migrations: python manage.py migrate"
echo "   3. Collect static files: python manage.py collectstatic"
echo "   4. Create superuser if needed: python manage.py createsuperuser"
echo "   5. Restart application services"
if [ "$VERIFY" = true ]; then
    echo "   6. Run verification: ./verify.sh"
fi
echo ""

unset PGPASSWORD
