# EDMS Comprehensive Backup and Restore System

## Overview

The EDMS backup system provides enterprise-grade backup, restore, and migration functionality for Docker-based deployments. This system supports multiple backup types, automated scheduling, and complete system migration between environments.

## Architecture Components

### 1. Backend Services
- **Backup Service** (`apps.backup.services.backup_service`)
- **Restore Service** (`apps.backup.services.restore_service`) 
- **Health Check Service** (`apps.backup.health_service`)
- **Management Commands** (Django CLI tools)
- **REST API** (Web interface integration)

### 2. Data Components Backed Up
- **PostgreSQL Database** - All application data, user accounts, workflows
- **Document Storage** - Original files, processed documents, annotations
- **Media Files** - Uploaded files, certificates, generated PDFs
- **System Configuration** - Settings, permissions, workflow configurations

### 3. Backup Types

#### Full System Backup
- Complete database dump with schema and data
- All storage files (documents, media, certificates)
- System configuration and user permissions
- Compressed archive with integrity checksums

#### Migration Export Package
- Portable system snapshot for environment migration
- Includes database, files, configuration, and restore scripts
- Self-contained with automated restoration capability
- Cross-platform compatibility

#### Incremental Backups
- Changes since last backup (files only)
- Space-efficient for frequent backups
- Requires base backup for full restoration

#### Database-Only Backups
- PostgreSQL dump with compression
- Fast backup for data protection
- Suitable for frequent automated runs

## Quick Start Guide

### 1. Create Migration Package (Recommended)

**Via Script:**
```bash
# Create complete migration package
./scripts/backup-system.sh create export /path/to/migration.tar.gz

# Create standard full backup
./scripts/backup-system.sh create full
```

**Via Django Management:**
```bash
# Create migration package with all options
docker-compose exec backend python manage.py create_backup \
    --type export \
    --output /tmp/migration_package.tar.gz \
    --include-users \
    --compress \
    --verify

# Create scheduled backup
docker-compose exec backend python manage.py create_backup \
    --type full \
    --schedule
```

### 2. Setup Automated Backups

```bash
# Setup backup schedule (daily, weekly, monthly)
./scripts/backup-system.sh schedule setup

# Create backup configurations
docker-compose exec backend python manage.py backup_scheduler --create-config

# List active configurations
docker-compose exec backend python manage.py backup_scheduler --list-configs
```

### 3. Restore System

**From Migration Package:**
```bash
# Restore complete system
./scripts/backup-system.sh restore /path/to/migration_package.tar.gz

# Force restore without confirmation
./scripts/backup-system.sh restore /path/to/backup.tar.gz --force
```

**Via Management Command:**
```bash
# Restore from migration package
docker-compose exec backend python manage.py restore_backup \
    --package /path/to/migration_package.tar.gz \
    --verify

# Restore specific components
docker-compose exec backend python manage.py restore_backup \
    --from-file /path/to/backup.tar.gz \
    --type database \
    --skip-users
```

## Detailed Usage Instructions

### Management Commands

#### create_backup
```bash
# Full system backup
python manage.py create_backup --type full

# Migration export with options
python manage.py create_backup \
    --type export \
    --output /path/to/export.tar.gz \
    --include-users \
    --compress \
    --encrypt \
    --verify

# Database only backup
python manage.py create_backup --type database --compress

# Use existing configuration
python manage.py create_backup --schedule --config-name daily_backup
```

#### restore_backup
```bash
# Restore from migration package
python manage.py restore_backup \
    --package /path/to/package.tar.gz \
    --verify \
    --force

# Restore from backup job
python manage.py restore_backup \
    --backup-job 12345-abc-def \
    --type full

# Selective restore
python manage.py restore_backup \
    --from-file /path/to/backup.tar.gz \
    --type files \
    --target /restore/location \
    --skip-database
```

#### backup_scheduler
```bash
# Create default configurations
python manage.py backup_scheduler --create-config

# Enable/disable configurations
python manage.py backup_scheduler --enable daily_full_backup
python manage.py backup_scheduler --disable hourly_incremental

# Run scheduled backups
python manage.py backup_scheduler --run-scheduled
```

### Docker Script Usage

#### backup-system.sh
```bash
# Environment variables
export BACKUP_ROOT="/custom/backup/path"
export COMPOSE_FILE="docker-compose.prod.yml"
export CONTAINER_PREFIX="edms_prod"

# Create backups
./scripts/backup-system.sh create full [output_path]
./scripts/backup-system.sh create export [output_path]

# Restore operations
./scripts/backup-system.sh restore /path/to/backup.tar.gz
./scripts/backup-system.sh restore /path/to/backup.tar.gz --force

# Verify integrity
./scripts/backup-system.sh verify /path/to/backup.tar.gz

# Setup automation
./scripts/backup-system.sh schedule setup
```

## Migration Between Environments

### Export from Source Environment

1. **Create Migration Package:**
   ```bash
   ./scripts/backup-system.sh create export /tmp/migration.tar.gz
   ```

2. **Verify Package:**
   ```bash
   ./scripts/backup-system.sh verify /tmp/migration.tar.gz
   ```

3. **Transfer Package:**
   ```bash
   scp /tmp/migration.tar.gz user@target-server:/tmp/
   ```

### Import to Target Environment

1. **Prepare Target System:**
   ```bash
   # Ensure Docker and EDMS are installed
   docker-compose up -d
   ```

2. **Restore from Package:**
   ```bash
   ./scripts/backup-system.sh restore /tmp/migration.tar.gz
   ```

3. **Verify Restoration:**
   ```bash
   # Check system health
   docker-compose exec backend python manage.py check
   
   # Verify data integrity
   docker-compose exec backend python manage.py shell -c "
   from django.contrib.auth.models import User
   from apps.documents.models import Document
   print(f'Users: {User.objects.count()}')
   print(f'Documents: {Document.objects.count()}')
   "
   ```

4. **Post-Migration Tasks:**
   ```bash
   # Update configuration if needed
   # Reset user passwords
   # Test critical workflows
   # Setup new backup schedule
   ./scripts/backup-system.sh schedule setup
   ```

## REST API Endpoints

### Backup Management
- `GET /api/v1/backup/configurations/` - List backup configurations
- `POST /api/v1/backup/configurations/` - Create backup configuration
- `POST /api/v1/backup/configurations/{id}/execute/` - Run backup
- `GET /api/v1/backup/jobs/` - List backup jobs
- `GET /api/v1/backup/jobs/{id}/download/` - Download backup file

### System Operations
- `POST /api/v1/backup/system/create_export_package/` - Create migration package
- `GET /api/v1/backup/system/system_status/` - Get backup system status
- `POST /api/v1/backup/system/run_health_check/` - Run health check

### Restore Operations
- `POST /api/v1/backup/restores/restore_from_file/` - Restore from uploaded file
- `POST /api/v1/backup/restores/restore_from_backup/` - Restore from backup job
- `GET /api/v1/backup/restores/` - List restore jobs

## Configuration Options

### Backup Configuration Model
```python
{
    "name": "daily_full_backup",
    "backup_type": "FULL",  # FULL, DATABASE, FILES, INCREMENTAL
    "frequency": "DAILY",   # HOURLY, DAILY, WEEKLY, MONTHLY, ON_DEMAND
    "schedule_time": "02:00:00",
    "retention_days": 30,
    "max_backups": 10,
    "storage_path": "/var/backups/edms",
    "compression_enabled": true,
    "encryption_enabled": false
}
```

### Environment Variables
```bash
# Backup system configuration
BACKUP_ROOT=/var/backups/edms
BACKUP_RETENTION_DAYS=30

# Database settings (auto-detected from Django settings)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=edms_db
DB_USER=edms_user

# Container settings (for Docker script)
COMPOSE_FILE=docker-compose.yml
CONTAINER_PREFIX=edms
```

## Monitoring and Health Checks

### Health Check Types
- **DATABASE** - Connection, performance, size monitoring
- **STORAGE** - Disk usage, write permissions, file integrity  
- **APPLICATION** - CPU, memory, cache connectivity
- **BACKUP_SYSTEM** - Backup success rates, schedule compliance
- **SECURITY** - Configuration validation, access controls

### System Metrics
- Backup success rate tracking
- Storage utilization monitoring
- Database performance metrics
- System resource usage

### Automated Monitoring
```bash
# Run comprehensive health check
docker-compose exec backend python manage.py backup_scheduler --run-scheduled

# Check specific component
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/backup/health/latest_status/
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors:**
   ```bash
   # Fix storage permissions
   sudo chown -R $USER:$USER /opt/edms/storage
   sudo chmod -R 755 /opt/edms/storage
   ```

2. **Database Connection Failures:**
   ```bash
   # Check database connectivity
   docker-compose exec backend python manage.py dbshell
   
   # Verify environment variables
   docker-compose exec backend printenv | grep DB_
   ```

3. **Large Backup Files:**
   ```bash
   # Enable compression
   python manage.py create_backup --type full --compress
   
   # Use incremental backups
   python manage.py create_backup --type incremental
   ```

4. **Restore Failures:**
   ```bash
   # Verify backup integrity first
   ./scripts/backup-system.sh verify /path/to/backup.tar.gz
   
   # Check available disk space
   df -h /opt/edms
   
   # Use force option if necessary
   python manage.py restore_backup --package backup.tar.gz --force
   ```

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=True
export DJANGO_LOG_LEVEL=DEBUG

# Run with detailed output
python manage.py create_backup --type export --output debug.tar.gz --verbosity 2
```

## Security Considerations

1. **Access Control:** Backup operations require admin privileges
2. **Encryption:** Optional backup encryption for sensitive data
3. **Audit Logging:** All backup/restore operations are logged
4. **File Permissions:** Backup files are created with restricted permissions
5. **Password Handling:** User passwords are never exported in migration packages

## Performance Optimization

1. **Compression:** Always enable compression for space efficiency
2. **Incremental Backups:** Use for frequent automated backups
3. **Parallel Processing:** Multiple backup jobs can run simultaneously
4. **Storage Location:** Use fast storage for backup operations
5. **Database Optimization:** Run VACUUM before major backups

## Best Practices

1. **Regular Testing:** Test restore procedures monthly
2. **Multiple Retention:** Keep daily, weekly, and monthly backups
3. **Off-site Storage:** Copy migration packages to external storage
4. **Documentation:** Maintain disaster recovery procedures
5. **Monitoring:** Set up alerts for backup failures
6. **Validation:** Always verify backup integrity after creation

This backup system provides enterprise-grade data protection with minimal operational overhead while supporting both routine operations and disaster recovery scenarios.