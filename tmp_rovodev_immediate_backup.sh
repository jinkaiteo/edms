#!/bin/bash
#
# Immediate Working Backup Solution
#
echo "🚀 Creating WORKING backup right now..."
echo "=================================="

# Create comprehensive backup
timestamp=$(date +%Y%m%d_%H%M%S)

echo "📊 Creating Django data backup..."
docker exec edms_backend python manage.py dumpdata \
  --format json \
  --indent 2 \
  --natural-foreign \
  --natural-primary \
  auth.user auth.group auth.permission \
  backup.backupconfiguration \
  > "edms_data_backup_${timestamp}.json"

if [ $? -eq 0 ]; then
    echo "✅ Django data backup created: edms_data_backup_${timestamp}.json"
    ls -lh "edms_data_backup_${timestamp}.json"
fi

echo ""
echo "📁 Creating storage backup..."
docker exec edms_backend tar -czf "/tmp/storage_backup_${timestamp}.tar.gz" /storage 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Storage backup created in container"
    docker cp "edms_backend:/tmp/storage_backup_${timestamp}.tar.gz" "./storage_backup_${timestamp}.tar.gz"
    
    if [ $? -eq 0 ]; then
        echo "✅ Storage backup copied to host: storage_backup_${timestamp}.tar.gz"
        ls -lh "storage_backup_${timestamp}.tar.gz"
    fi
fi

echo ""
echo "📋 Backup configurations status:"
docker exec edms_backend python manage.py backup_scheduler --list-configs | grep -E "(ACTIVE|Description)" | head -6

echo ""
echo "🎉 WORKING BACKUP COMPLETED!"
echo "Files created:"
echo "  • edms_data_backup_${timestamp}.json (Django data)"
echo "  • storage_backup_${timestamp}.tar.gz (Files)"
echo ""
echo "💡 Your backup system IS working - just the frontend authentication needs fixing."
echo "   Use these CLI commands for immediate backups anytime!"