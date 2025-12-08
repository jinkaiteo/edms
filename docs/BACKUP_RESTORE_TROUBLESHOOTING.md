# EDMS Backup and Restore Troubleshooting Guide

## Quick Reference

### Common Issues and Solutions

| Issue | Symptoms | Quick Fix |
|-------|----------|-----------|
| **401 Authentication Error** | "Server returned 401" | Logout/login, check JWT token |
| **Package Validation Failed** | "Backup file corrupted" | Create new backup package |
| **No Data Restored** | Users missing after restore | Use NEW format backup (not old metadata) |
| **Login Fails After Restore** | Can't authenticate users | Verify password: admin/test123 |
| **Missing User Roles** | Users have no permissions | Create backup AFTER role assignment |

## Detailed Troubleshooting

### Authentication Issues

#### Problem: 401 Unauthorized Error
```
Error: Server returned 401
XHRPOST http://localhost:3000/api/v1/backup/system/create_export_package/
```

**Root Cause**: Expired JWT token or insufficient permissions

**Solutions**:
1. **Refresh Authentication**:
   - Logout from frontend
   - Login again as admin/test123
   - Try backup operation again

2. **Check User Privileges**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User
   admin = User.objects.get(username='admin')
   print(f'Is staff: {admin.is_staff}')
   print(f'Is active: {admin.is_active}')
   "
   ```

3. **Manual Token Generation**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from rest_framework_simplejwt.tokens import RefreshToken
   from apps.users.models import User
   user = User.objects.get(username='admin')
   token = str(RefreshToken.for_user(user).access_token)
   print(f'Fresh token: {token}')
   "
   ```

### Backup Creation Issues

#### Problem: Package Validation Failed
```
Error: Backup file is corrupted: File too small
```

**Root Cause**: Incomplete backup creation or network issues

**Solutions**:
1. **Verify Backup Size**:
   ```bash
   ls -lh /tmp/*migration*.tar.gz
   # Should be ~5MB, not a few KB
   ```

2. **Create Fresh Backup**:
   ```bash
   docker compose exec backend python manage.py create_backup \
     --type export \
     --output /tmp/fresh_backup.tar.gz \
     --include-users \
     --verify
   ```

3. **Check Package Contents**:
   ```bash
   tar -tf backup_package.tar.gz | head -20
   # Should show database/, configuration/, storage/ directories
   ```

### Restore Issues

#### Problem: No Data Restored
```
Loaddata completed but user count unchanged
```

**Root Cause**: Using old metadata-only backup or restoring to same database

**Solutions**:
1. **Check Backup Format**:
   ```bash
   python3 -c "
   import json, tarfile, tempfile
   with tempfile.TemporaryDirectory() as d:
       with tarfile.open('backup.tar.gz') as tar:
           tar.extractall(d)
       with open(f'{d}/database/database_backup.json') as f:
           data = json.load(f)
       if isinstance(data, list):
           print(f'✓ Valid Django fixture: {len(data)} records')
       else:
           print('❌ Old metadata format - will not restore data')
   "
   ```

2. **Create NEW Format Backup**:
   - Use backup created AFTER December 8, 2025
   - Verify contains 500+ records, not metadata

3. **Test Different Environment**:
   - Restore to different database/environment
   - Same data to same DB shows no change (expected)

#### Problem: User Login Fails After Restore
```
Authentication failed for restored users
```

**Root Cause**: Wrong password or corrupted password hashes

**Solutions**:
1. **Use Correct Passwords**:
   - admin: `test123`
   - author01: `test123`
   - All default users: `test123`

2. **Test Authentication**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from django.contrib.auth import authenticate
   users = ['admin', 'author01', 'reviewer01']
   for username in users:
       user = authenticate(username=username, password='test123')
       print(f'{username}: {'✓' if user else '❌'}')
   "
   ```

3. **Verify Password Hashes**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User
   from django.contrib.auth.hashers import check_password
   user = User.objects.get(username='admin')
   print(f'Hash length: {len(user.password)}')
   print(f'Password works: {check_password('test123', user.password)}')
   "
   ```

#### Problem: Missing User Roles
```
Users exist but have no roles assigned
```

**Root Cause**: Backup created before role assignments were fixed

**Solutions**:
1. **Check Current Role Assignments**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User, UserRole
   for user in User.objects.all():
       roles = [ur.role.name for ur in UserRole.objects.filter(user=user, is_active=True)]
       print(f'{user.username}: {roles}')
   "
   ```

2. **Assign Missing Roles**:
   ```bash
   docker compose exec backend python manage.py shell -c "
   from apps.users.models import User, Role, UserRole
   
   # Fix role assignments
   assignments = {
       'author01': 'Document Author',
       'reviewer01': 'Document Reviewer', 
       'approver01': 'Document Approver',
       'viewer01': 'Document Viewer'
   }
   
   admin = User.objects.filter(is_staff=True).first()
   for username, role_name in assignments.items():
       try:
           user = User.objects.get(username=username)
           role = Role.objects.get(name=role_name)
           UserRole.objects.get_or_create(
               user=user, role=role,
               defaults={'is_active': True, 'assigned_by': admin}
           )
           print(f'✓ {username} -> {role_name}')
       except Exception as e:
           print(f'❌ {username}: {e}')
   "
   ```

3. **Create New Backup After Role Fix**:
   ```bash
   docker compose exec backend python manage.py create_backup \
     --type export \
     --output /tmp/backup_with_roles.tar.gz \
     --include-users \
     --verify
   ```

### File System Issues

#### Problem: Package Upload Fails
```
Error uploading package: Network error or timeout
```

**Solutions**:
1. **Check File Size Limits**:
   - Nginx: `client_max_body_size 100M`
   - Django: `FILE_UPLOAD_MAX_MEMORY_SIZE`

2. **Verify Package Integrity**:
   ```bash
   file backup_package.tar.gz
   # Should show: gzip compressed data
   ```

3. **Use Smaller Packages**:
   - Create database-only backup if files are large
   - Transfer large files separately

#### Problem: Extraction Fails
```
Error: Invalid tar file or corrupt archive
```

**Solutions**:
1. **Test Archive Integrity**:
   ```bash
   gzip -t backup_package.tar.gz
   tar -tf backup_package.tar.gz > /dev/null
   echo "Exit code: $?"  # Should be 0
   ```

2. **Re-download Package**:
   - Package may be corrupted during transfer
   - Verify checksums if available

## Diagnostic Commands

### System Health Check
```bash
# Check all critical components
docker compose exec backend python manage.py shell -c "
print('=== SYSTEM HEALTH CHECK ===')

# Database connectivity
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✓ Database: Connected')
except Exception as e:
    print(f'❌ Database: {e}')

# User system
from apps.users.models import User, UserRole
users_count = User.objects.count()
roles_count = UserRole.objects.filter(is_active=True).count()
print(f'✓ Users: {users_count} users, {roles_count} active roles')

# Authentication
from django.contrib.auth import authenticate
auth_test = authenticate(username='admin', password='test123')
print(f'✓ Authentication: {'Working' if auth_test else 'Failed'}')

# Backup system
from apps.backup.models import BackupJob
backup_count = BackupJob.objects.count()
print(f'✓ Backup system: {backup_count} backup jobs')
"
```

### Package Analysis
```bash
# Analyze any migration package
analyze_package() {
    PACKAGE="$1"
    echo "Analyzing: $PACKAGE"
    echo "Size: $(du -h "$PACKAGE" | cut -f1)"
    echo "Type: $(file "$PACKAGE")"
    
    # Extract and analyze
    mkdir -p /tmp/package_analysis
    cd /tmp/package_analysis
    tar -xf "$PACKAGE"
    
    echo "Contents:"
    find . -name "*.json" -exec echo "  {}" \; -exec wc -l {} \;
    
    # Check database format
    if [ -f database/database_backup.json ]; then
        python3 -c "
import json
with open('database/database_backup.json') as f:
    data = json.load(f)
if isinstance(data, list):
    print(f'✓ Django fixture: {len(data)} records')
    models = {}
    for item in data:
        model = item.get('model', 'unknown')
        models[model] = models.get(model, 0) + 1
    print('Top models:')
    for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {model}: {count}')
else:
    print('❌ Old metadata format')
        "
    fi
    
    cd - > /dev/null
    rm -rf /tmp/package_analysis
}

# Usage: analyze_package backup_package.tar.gz
```

## Performance Issues

### Slow Backup Creation
```bash
# Monitor backup creation
docker compose exec backend python manage.py shell -c "
import time
start_time = time.time()
# ... backup creation code ...
end_time = time.time()
print(f'Backup took: {end_time - start_time:.2f} seconds')
"
```

**Optimizations**:
- Reduce file count in storage
- Use compression (already enabled)
- Run during off-peak hours

### Slow Restore Process
```bash
# Monitor restore performance
docker compose logs backend --tail=50 | grep -E "(loaddata|restore|sequence)"
```

**Optimizations**:
- Ensure adequate disk space
- Monitor database connection pool
- Restart backend after large restores

## Environment-Specific Issues

### Development Environment
```bash
# Common development issues
docker compose ps  # Verify all services running
docker compose logs backend --tail=20  # Check for errors
docker compose restart backend  # Restart if needed
```

### Production Environment
- Verify SSL certificates for API calls
- Check firewall rules for backup uploads
- Monitor disk space for backup storage
- Verify backup schedule automation

## Emergency Recovery Procedures

### Complete System Recovery
1. **Prepare Clean Environment**:
   ```bash
   docker compose down
   docker volume rm edms_postgres_data  # ⚠️ Destroys data
   docker compose up -d
   ```

2. **Restore from Backup**:
   ```bash
   # Wait for services to start
   sleep 30
   
   # Upload backup through frontend or use CLI
   docker compose exec backend python manage.py restore_backup \
     --package /path/to/backup.tar.gz \
     --type full
   ```

3. **Verify Restoration**:
   ```bash
   # Test login
   # Check user roles
   # Verify document access
   # Test workflow operations
   ```

### Partial Recovery
```bash
# Database only
docker compose exec backend python manage.py loaddata backup.json

# Files only
tar -xf backup.tar.gz storage/
cp -r storage/* /app/storage/

# Configuration only
tar -xf backup.tar.gz configuration/
cp configuration/.env /app/.env
```

## Contact and Escalation

For issues not covered in this guide:

1. **Check system logs**: `docker compose logs backend`
2. **Review backup job status**: Check admin dashboard
3. **Test with minimal data**: Use fresh development environment
4. **Create support ticket**: Include error logs and system information

---

This troubleshooting guide covers the most common issues encountered with the EDMS backup and restore system. Keep this documentation updated as new issues are identified and resolved.