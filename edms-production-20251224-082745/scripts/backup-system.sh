#!/bin/bash
#
# EDMS Comprehensive Backup System
#
# This script provides complete backup and restore functionality
# for Docker-based EDMS installations.
#
# Usage:
#   ./backup-system.sh create full [output_path]
#   ./backup-system.sh create export /path/to/export.tar.gz
#   ./backup-system.sh restore /path/to/backup.tar.gz
#   ./backup-system.sh schedule setup
#   ./backup-system.sh verify /path/to/backup.tar.gz

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-$PROJECT_ROOT/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"
CONTAINER_PREFIX="${CONTAINER_PREFIX:-edms}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running in project root
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        log_error "Please run this script from the EDMS project root directory"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if containers are running
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_error "EDMS containers are not running"
        log_error "Start the system with: docker-compose up -d"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create backup directory structure
setup_backup_structure() {
    mkdir -p "$BACKUP_ROOT"/{daily,weekly,monthly,export,temp}
    mkdir -p "$BACKUP_ROOT"/temp/{database,storage,config}
    log_info "Backup directory structure created"
}

# Database backup
backup_database() {
    local output_path="$1"
    local container_name="${CONTAINER_PREFIX}_db"
    
    log_info "Creating database backup..."
    
    # Get database credentials from Docker Compose environment
    local db_name=$(docker-compose -f "$COMPOSE_FILE" exec -T backend printenv DB_NAME | tr -d '\r')
    local db_user=$(docker-compose -f "$COMPOSE_FILE" exec -T backend printenv DB_USER | tr -d '\r')
    
    # Create database dump
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "$db_user" \
        -d "$db_name" \
        --verbose \
        --no-password \
        --clean \
        --if-exists \
        | gzip > "$output_path"
    
    if [[ $? -eq 0 ]]; then
        log_success "Database backup completed: $(basename "$output_path")"
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Storage backup
backup_storage() {
    local output_path="$1"
    local temp_dir="$2"
    
    log_info "Creating storage backup..."
    
    # Copy storage from host
    if [[ -d "$PROJECT_ROOT/storage" ]]; then
        cp -r "$PROJECT_ROOT/storage" "$temp_dir/"
        log_success "Storage files copied"
    else
        log_warning "Storage directory not found: $PROJECT_ROOT/storage"
        mkdir -p "$temp_dir/storage"
    fi
    
    # Create storage archive
    tar -czf "$output_path" -C "$temp_dir" storage/
    log_success "Storage backup completed: $(basename "$output_path")"
}

# Configuration backup
backup_configuration() {
    local output_path="$1"
    local temp_dir="$2"
    
    log_info "Creating configuration backup..."
    
    # Copy important configuration files
    local config_files=(
        "docker-compose.yml"
        "docker-compose.prod.yml" 
        "backend/.env"
        "frontend/package.json"
    )
    
    mkdir -p "$temp_dir/config"
    
    for config_file in "${config_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$config_file" ]]; then
            cp "$PROJECT_ROOT/$config_file" "$temp_dir/config/"
            log_info "Copied: $config_file"
        fi
    done
    
    # Export Django settings (non-sensitive)
    docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py dumpdata \
        --format json \
        --indent 2 \
        auth.group auth.permission \
        > "$temp_dir/config/permissions.json"
    
    # Create configuration archive
    tar -czf "$output_path" -C "$temp_dir" config/
    log_success "Configuration backup completed: $(basename "$output_path")"
}

# Create full system backup
create_full_backup() {
    local backup_type="$1"
    local output_path="$2"
    
    check_prerequisites
    setup_backup_structure
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local temp_dir="$BACKUP_ROOT/temp/backup_$timestamp"
    
    mkdir -p "$temp_dir"
    
    if [[ "$backup_type" == "export" ]]; then
        # Create migration package using Django management command
        log_info "Creating migration package..."
        
        if [[ -z "$output_path" ]]; then
            output_path="$BACKUP_ROOT/export/edms_migration_package_$timestamp.tar.gz"
        fi
        
        # Use Django management command for comprehensive export
        docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py create_backup \
            --type export \
            --output "/tmp/migration_package.tar.gz" \
            --include-users \
            --compress \
            --verify
        
        # Copy from container to host
        docker cp "${CONTAINER_PREFIX}_backend:/tmp/migration_package.tar.gz" "$output_path"
        
        # Cleanup temp file in container
        docker-compose -f "$COMPOSE_FILE" exec -T backend rm -f /tmp/migration_package.tar.gz
        
    else
        # Create standard backup
        log_info "Creating full system backup..."
        
        if [[ -z "$output_path" ]]; then
            output_path="$BACKUP_ROOT/daily/edms_full_backup_$timestamp.tar.gz"
        fi
        
        local db_backup="$temp_dir/database_$timestamp.sql.gz"
        local storage_backup="$temp_dir/storage_$timestamp.tar.gz"
        local config_backup="$temp_dir/config_$timestamp.tar.gz"
        
        # Create component backups
        backup_database "$db_backup"
        backup_storage "$storage_backup" "$temp_dir"
        backup_configuration "$config_backup" "$temp_dir"
        
        # Create metadata
        cat > "$temp_dir/metadata.json" << EOF
{
    "backup_type": "full_system",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "edms_version": "1.0.0",
    "components": {
        "database": "database_$timestamp.sql.gz",
        "storage": "storage_$timestamp.tar.gz",
        "configuration": "config_$timestamp.tar.gz"
    },
    "creator": "backup-system.sh",
    "hostname": "$(hostname)"
}
EOF
        
        # Create final archive
        tar -czf "$output_path" -C "$temp_dir" .
    fi
    
    # Cleanup temporary directory
    rm -rf "$temp_dir"
    
    # Verify backup
    if [[ -f "$output_path" ]]; then
        local backup_size=$(stat -f%z "$output_path" 2>/dev/null || stat -c%s "$output_path")
        log_success "Backup completed successfully!"
        log_info "Backup file: $output_path"
        log_info "Backup size: $(numfmt --to=iec-i --suffix=B "$backup_size")"
        
        # Calculate checksum
        local checksum=$(sha256sum "$output_path" | cut -d' ' -f1)
        echo "$checksum  $(basename "$output_path")" > "$output_path.sha256"
        log_info "Checksum: $checksum"
    else
        log_error "Backup file was not created"
        return 1
    fi
}

# Restore from backup
restore_backup() {
    local backup_path="$1"
    local restore_options="${2:-}"
    
    if [[ ! -f "$backup_path" ]]; then
        log_error "Backup file not found: $backup_path"
        return 1
    fi
    
    check_prerequisites
    
    log_warning "WARNING: This will overwrite the current system!"
    log_warning "Current database and files will be replaced."
    
    if [[ "$restore_options" != "--force" ]]; then
        read -p "Do you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "Restore cancelled"
            return 0
        fi
    fi
    
    log_info "Starting restore from: $(basename "$backup_path")"
    
    # Check if this is a migration package (use Django management command)
    if [[ "$backup_path" == *"migration_package"* ]]; then
        # Copy to container for restoration
        docker cp "$backup_path" "${CONTAINER_PREFIX}_backend:/tmp/restore_package.tar.gz"
        
        # Use Django management command
        docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py restore_backup \
            --package /tmp/restore_package.tar.gz \
            --verify \
            --force
        
        # Cleanup
        docker-compose -f "$COMPOSE_FILE" exec -T backend rm -f /tmp/restore_package.tar.gz
        
    else
        # Handle standard backup restore
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local temp_dir="$BACKUP_ROOT/temp/restore_$timestamp"
        
        mkdir -p "$temp_dir"
        
        # Extract backup
        log_info "Extracting backup..."
        tar -xzf "$backup_path" -C "$temp_dir"
        
        # Restore database
        if [[ -f "$temp_dir"/database_*.sql.gz ]]; then
            log_info "Restoring database..."
            
            local db_name=$(docker-compose -f "$COMPOSE_FILE" exec -T backend printenv DB_NAME | tr -d '\r')
            local db_user=$(docker-compose -f "$COMPOSE_FILE" exec -T backend printenv DB_USER | tr -d '\r')
            
            # Drop and recreate database
            docker-compose -f "$COMPOSE_FILE" exec -T db dropdb -U "$db_user" "$db_name" --if-exists
            docker-compose -f "$COMPOSE_FILE" exec -T db createdb -U "$db_user" "$db_name"
            
            # Restore data
            gunzip -c "$temp_dir"/database_*.sql.gz | \
            docker-compose -f "$COMPOSE_FILE" exec -T db psql -U "$db_user" -d "$db_name"
            
            log_success "Database restored"
        fi
        
        # Restore storage
        if [[ -f "$temp_dir"/storage_*.tar.gz ]]; then
            log_info "Restoring storage files..."
            
            # Backup existing storage
            if [[ -d "$PROJECT_ROOT/storage" ]]; then
                mv "$PROJECT_ROOT/storage" "$PROJECT_ROOT/storage.backup.$timestamp"
                log_info "Existing storage backed up to storage.backup.$timestamp"
            fi
            
            # Extract storage
            tar -xzf "$temp_dir"/storage_*.tar.gz -C "$PROJECT_ROOT/"
            log_success "Storage files restored"
        fi
        
        # Cleanup
        rm -rf "$temp_dir"
    fi
    
    # Restart services to apply changes
    log_info "Restarting services..."
    docker-compose -f "$COMPOSE_FILE" restart backend frontend
    
    log_success "Restore completed successfully!"
    log_info "Please verify the system functionality"
}

# Verify backup integrity
verify_backup() {
    local backup_path="$1"
    
    if [[ ! -f "$backup_path" ]]; then
        log_error "Backup file not found: $backup_path"
        return 1
    fi
    
    log_info "Verifying backup: $(basename "$backup_path")"
    
    # Check file integrity
    if tar -tzf "$backup_path" >/dev/null 2>&1; then
        log_success "Archive integrity: OK"
    else
        log_error "Archive integrity: FAILED"
        return 1
    fi
    
    # Verify checksum if available
    if [[ -f "$backup_path.sha256" ]]; then
        if sha256sum -c "$backup_path.sha256" >/dev/null 2>&1; then
            log_success "Checksum verification: OK"
        else
            log_error "Checksum verification: FAILED"
            return 1
        fi
    else
        log_warning "No checksum file found"
    fi
    
    # Check backup contents
    log_info "Backup contents:"
    tar -tzf "$backup_path" | head -20
    
    log_success "Backup verification completed"
}

# Setup automated backup schedule
setup_schedule() {
    log_info "Setting up automated backup schedule..."
    
    # Create backup configurations using Django management command
    docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py backup_scheduler --create-config
    
    # Create systemd timer (if systemd is available)
    if command -v systemctl >/dev/null 2>&1; then
        create_systemd_backup_service
    else
        create_cron_backup_job
    fi
    
    log_success "Backup schedule setup completed"
}

# Create systemd backup service
create_systemd_backup_service() {
    log_info "Creating systemd backup service..."
    
    # Create service file
    sudo tee /etc/systemd/system/edms-backup.service > /dev/null << EOF
[Unit]
Description=EDMS System Backup
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_ROOT
ExecStart=$SCRIPT_DIR/backup-system.sh create full
User=$(whoami)
Group=$(id -gn)

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file
    sudo tee /etc/systemd/system/edms-backup.timer > /dev/null << EOF
[Unit]
Description=Run EDMS backup daily
Requires=edms-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable edms-backup.timer
    sudo systemctl start edms-backup.timer
    
    log_success "Systemd backup timer created and started"
}

# Create cron backup job
create_cron_backup_job() {
    log_info "Creating cron backup job..."
    
    # Create backup script wrapper
    local wrapper_script="$SCRIPT_DIR/backup-cron.sh"
    cat > "$wrapper_script" << EOF
#!/bin/bash
cd "$PROJECT_ROOT"
"$SCRIPT_DIR/backup-system.sh" create full >> "$BACKUP_ROOT/backup.log" 2>&1
EOF
    chmod +x "$wrapper_script"
    
    # Add to crontab
    (crontab -l 2>/dev/null || echo "") | grep -v "edms-backup" > /tmp/crontab-backup
    echo "0 2 * * * $wrapper_script # edms-backup" >> /tmp/crontab-backup
    crontab /tmp/crontab-backup
    rm /tmp/crontab-backup
    
    log_success "Cron backup job created (daily at 2 AM)"
}

# Show usage
show_usage() {
    echo "EDMS Comprehensive Backup System"
    echo "================================"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create full [output_path]           Create full system backup"
    echo "  create export [output_path]         Create migration export package"
    echo "  restore <backup_path> [--force]     Restore from backup"
    echo "  verify <backup_path>                Verify backup integrity"
    echo "  schedule setup                      Setup automated backup schedule"
    echo ""
    echo "Examples:"
    echo "  $0 create full"
    echo "  $0 create export /tmp/migration.tar.gz"
    echo "  $0 restore /path/to/backup.tar.gz"
    echo "  $0 verify /path/to/backup.tar.gz"
    echo "  $0 schedule setup"
    echo ""
    echo "Environment Variables:"
    echo "  BACKUP_ROOT      Backup storage directory (default: ./backups)"
    echo "  COMPOSE_FILE     Docker Compose file path (default: ./docker-compose.yml)"
    echo "  CONTAINER_PREFIX Container name prefix (default: edms)"
    echo ""
}

# Main execution
main() {
    case "${1:-}" in
        "create")
            case "${2:-}" in
                "full")
                    create_full_backup "full" "$3"
                    ;;
                "export")
                    create_full_backup "export" "$3"
                    ;;
                *)
                    log_error "Unknown backup type. Use 'full' or 'export'"
                    show_usage
                    exit 1
                    ;;
            esac
            ;;
        "restore")
            if [[ -n "${2:-}" ]]; then
                restore_backup "$2" "$3"
            else
                log_error "Backup path required for restore"
                show_usage
                exit 1
            fi
            ;;
        "verify")
            if [[ -n "${2:-}" ]]; then
                verify_backup "$2"
            else
                log_error "Backup path required for verification"
                show_usage
                exit 1
            fi
            ;;
        "schedule")
            case "${2:-}" in
                "setup")
                    setup_schedule
                    ;;
                *)
                    log_error "Unknown schedule command. Use 'setup'"
                    show_usage
                    exit 1
                    ;;
            esac
            ;;
        *)
            show_usage
            ;;
    esac
}

# Execute main function with all arguments
main "$@"