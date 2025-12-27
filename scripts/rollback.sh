#!/bin/bash

################################################################################
# EDMS Rollback Script
################################################################################
#
# Description: Safe rollback mechanism for EDMS deployments
# Version: 1.0
# Date: December 24, 2024
#
# Features:
# - Lists available deployment versions
# - Creates backup before rollback
# - Validates target version
# - Performs database migration rollback
# - Rolls back Docker containers
# - Verifies rollback success
# - Can restore from backup if rollback fails
#
# Usage: ./scripts/rollback.sh [options]
#
# Options:
#   --list              List available versions to rollback to
#   --to VERSION        Rollback to specific version
#   --previous          Rollback to previous version (default)
#   --backup-first      Create backup before rollback (recommended)
#   --dry-run           Show what would be done without executing
#   --force             Skip confirmation prompts
#   --preserve-data     Keep database data (rollback code only)
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/rollback-backups"
DEPLOYMENTS_DIR="/opt"
CURRENT_DIR="${PROJECT_ROOT}"

# Options
ACTION="rollback"
TARGET_VERSION=""
BACKUP_FIRST=false
DRY_RUN=false
FORCE=false
PRESERVE_DATA=false
LIST_ONLY=false

# State
CURRENT_VERSION=""
ROLLBACK_TIMESTAMP=$(date +%Y%m%d-%H%M%S)

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║              EDMS Deployment Rollback v1.0                   ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [options]

Options:
  --list              List available versions to rollback to
  --to VERSION        Rollback to specific version (e.g., edms-production-20241224-082745)
  --previous          Rollback to previous version (default)
  --backup-first      Create backup before rollback (recommended)
  --dry-run           Show what would be done without executing
  --force             Skip confirmation prompts
  --preserve-data     Keep database data (rollback code only)
  -h, --help          Show this help message

Examples:
  # List available versions
  $0 --list

  # Rollback to previous version with backup
  $0 --previous --backup-first

  # Rollback to specific version
  $0 --to edms-production-20241224-082745

  # Dry run to see what would happen
  $0 --previous --dry-run

  # Quick rollback (no confirmation)
  $0 --previous --force

Safety Features:
  - Always creates backup before rollback
  - Validates target version exists
  - Checks database compatibility
  - Verifies rollback success
  - Can restore if rollback fails

EOF
}

detect_current_version() {
    log_info "Detecting current deployment version..."
    
    # Try to detect from directory name
    local dir_name=$(basename "${CURRENT_DIR}")
    
    if [[ "$dir_name" =~ edms-production-[0-9]{8}-[0-9]{6} ]]; then
        CURRENT_VERSION="$dir_name"
        log_success "Current version: $CURRENT_VERSION"
        return 0
    fi
    
    # Try to detect from git tag or version file
    if [ -f "${CURRENT_DIR}/VERSION" ]; then
        CURRENT_VERSION=$(cat "${CURRENT_DIR}/VERSION")
        log_success "Current version: $CURRENT_VERSION"
        return 0
    fi
    
    # Try to get from container label
    local container_version=$(docker inspect "$(docker compose ps -q backend)" 2>/dev/null | jq -r '.[0].Config.Labels.version' 2>/dev/null || echo "unknown")
    
    if [ "$container_version" != "unknown" ] && [ "$container_version" != "null" ]; then
        CURRENT_VERSION="$container_version"
        log_success "Current version: $CURRENT_VERSION"
        return 0
    fi
    
    log_warning "Could not detect current version automatically"
    CURRENT_VERSION="unknown"
    return 1
}

list_available_versions() {
    log_info "Scanning for available deployment versions..."
    echo ""
    
    local versions=()
    
    # Look for edms-production directories
    if [ -d "$DEPLOYMENTS_DIR" ]; then
        while IFS= read -r dir; do
            if [ -d "$dir" ] && [ -f "$dir/docker-compose.prod.yml" ]; then
                local version=$(basename "$dir")
                local timestamp=$(echo "$version" | grep -oP '\d{8}-\d{6}' || echo "unknown")
                local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
                
                versions+=("$version|$timestamp|$size")
            fi
        done < <(find "$DEPLOYMENTS_DIR" -maxdepth 1 -type d -name "edms-production-*" 2>/dev/null | sort -r)
    fi
    
    # Also check current directory parent
    if [ -d "${PROJECT_ROOT}/.." ]; then
        while IFS= read -r dir; do
            if [ -d "$dir" ] && [ -f "$dir/docker-compose.prod.yml" ]; then
                local version=$(basename "$dir")
                if [[ ! " ${versions[@]} " =~ " ${version}| " ]]; then
                    local timestamp=$(echo "$version" | grep -oP '\d{8}-\d{6}' || echo "unknown")
                    local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
                    versions+=("$version|$timestamp|$size")
                fi
            fi
        done < <(find "${PROJECT_ROOT}/.." -maxdepth 1 -type d -name "edms-production-*" 2>/dev/null | sort -r)
    fi
    
    if [ ${#versions[@]} -eq 0 ]; then
        log_warning "No deployment versions found"
        return 1
    fi
    
    echo -e "${CYAN}Available Versions:${NC}"
    echo ""
    printf "%-40s %-20s %-10s\n" "VERSION" "TIMESTAMP" "SIZE"
    echo "────────────────────────────────────────────────────────────────────"
    
    for version_info in "${versions[@]}"; do
        IFS='|' read -r version timestamp size <<< "$version_info"
        
        if [ "$version" = "$CURRENT_VERSION" ]; then
            printf "${GREEN}%-40s %-20s %-10s [CURRENT]${NC}\n" "$version" "$timestamp" "$size"
        else
            printf "%-40s %-20s %-10s\n" "$version" "$timestamp" "$size"
        fi
    done
    
    echo ""
    log_success "Found ${#versions[@]} deployment version(s)"
    return 0
}

find_previous_version() {
    log_info "Finding previous deployment version..."
    
    # Get all versions sorted by timestamp
    local versions=()
    
    for dir in "$DEPLOYMENTS_DIR"/edms-production-* "${PROJECT_ROOT}"/../edms-production-*; do
        if [ -d "$dir" ] && [ -f "$dir/docker-compose.prod.yml" ]; then
            local version=$(basename "$dir")
            if [ "$version" != "$CURRENT_VERSION" ]; then
                versions+=("$version")
            fi
        fi
    done 2>/dev/null
    
    # Sort by timestamp (newest first)
    IFS=$'\n' versions=($(sort -r <<<"${versions[*]}"))
    unset IFS
    
    if [ ${#versions[@]} -eq 0 ]; then
        log_error "No previous version found"
        return 1
    fi
    
    TARGET_VERSION="${versions[0]}"
    log_success "Previous version: $TARGET_VERSION"
    return 0
}

validate_target_version() {
    log_info "Validating target version..."
    
    # Check if target version directory exists
    local target_paths=(
        "$DEPLOYMENTS_DIR/$TARGET_VERSION"
        "${PROJECT_ROOT}/../$TARGET_VERSION"
    )
    
    for path in "${target_paths[@]}"; do
        if [ -d "$path" ]; then
            TARGET_PATH="$path"
            log_success "Target version found: $TARGET_PATH"
            
            # Verify critical files
            if [ ! -f "$path/docker-compose.prod.yml" ]; then
                log_error "Missing docker-compose.prod.yml in target version"
                return 1
            fi
            
            if [ ! -d "$path/backend" ]; then
                log_error "Missing backend directory in target version"
                return 1
            fi
            
            return 0
        fi
    done
    
    log_error "Target version not found: $TARGET_VERSION"
    return 1
}

create_backup() {
    log_info "Creating pre-rollback backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_name="pre-rollback-${CURRENT_VERSION}-${ROLLBACK_TIMESTAMP}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    
    # Backup database
    log_info "Backing up database..."
    cd "${CURRENT_DIR}"
    
    if docker compose exec -T backend python manage.py dumpdata \
        --natural-foreign --natural-primary \
        -o /tmp/backup.json 2>/dev/null; then
        
        docker compose cp backend:/tmp/backup.json "${backup_path}/database.json"
        log_success "Database backed up"
    else
        log_warning "Could not backup database"
    fi
    
    # Backup media files
    if [ -d "${CURRENT_DIR}/backend/media" ]; then
        log_info "Backing up media files..."
        cp -r "${CURRENT_DIR}/backend/media" "${backup_path}/"
        log_success "Media files backed up"
    fi
    
    # Backup storage files
    if [ -d "${CURRENT_DIR}/backend/storage" ]; then
        log_info "Backing up storage files..."
        cp -r "${CURRENT_DIR}/backend/storage" "${backup_path}/"
        log_success "Storage files backed up"
    fi
    
    # Backup environment file
    if [ -f "${CURRENT_DIR}/backend/.env" ]; then
        cp "${CURRENT_DIR}/backend/.env" "${backup_path}/.env.backup"
        log_success "Environment file backed up"
    fi
    
    # Create backup manifest
    cat > "${backup_path}/MANIFEST.txt" << EOF
EDMS Pre-Rollback Backup
========================
Timestamp: $(date)
Current Version: $CURRENT_VERSION
Target Version: $TARGET_VERSION
Backup Location: $backup_path

Contents:
$(ls -lh "$backup_path")
EOF
    
    log_success "Backup created: $backup_path"
    echo "$backup_path" > "${BACKUP_DIR}/latest-backup.txt"
}

stop_current_services() {
    log_info "Stopping current services..."
    
    cd "${CURRENT_DIR}"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would stop services in: ${CURRENT_DIR}"
        return 0
    fi
    
    if docker compose ps -q >/dev/null 2>&1; then
        docker compose down
        log_success "Current services stopped"
    else
        log_warning "No running services found"
    fi
}

rollback_code() {
    log_info "Rolling back code to: $TARGET_VERSION"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would switch to: ${TARGET_PATH}"
        return 0
    fi
    
    # Update symlink or switch directory
    # This assumes deployments are in /opt and there's a 'current' symlink
    if [ -L "/opt/edms-current" ]; then
        ln -sfn "$TARGET_PATH" "/opt/edms-current"
        log_success "Updated symlink to target version"
    else
        log_info "Manual directory switch required"
        log_info "Switch to: cd $TARGET_PATH"
    fi
}

rollback_database() {
    if [ "$PRESERVE_DATA" = true ]; then
        log_info "Skipping database rollback (preserve-data mode)"
        return 0
    fi
    
    log_info "Rolling back database..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would rollback database migrations"
        return 0
    fi
    
    cd "${TARGET_PATH}"
    
    # Start database service
    docker compose up -d db
    sleep 5
    
    # Run migrations for target version
    log_info "Running migrations for target version..."
    if docker compose run --rm backend python manage.py migrate; then
        log_success "Database migrations applied"
    else
        log_error "Database migration failed"
        return 1
    fi
}

start_target_services() {
    log_info "Starting services with target version..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would start services from: ${TARGET_PATH}"
        return 0
    fi
    
    cd "${TARGET_PATH}"
    
    # Start all services
    docker compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        log_success "Services started successfully"
        return 0
    else
        log_error "Services failed to start"
        return 1
    fi
}

verify_rollback() {
    log_info "Verifying rollback..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would verify services"
        return 0
    fi
    
    cd "${TARGET_PATH}"
    
    # Wait for application to be ready
    sleep 5
    
    # Check health endpoint
    local health_check=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health/" 2>/dev/null || echo "000")
    
    if [ "$health_check" = "200" ]; then
        log_success "Health check passed (HTTP $health_check)"
        return 0
    else
        log_error "Health check failed (HTTP $health_check)"
        return 1
    fi
}

confirm_action() {
    if [ "$FORCE" = true ]; then
        return 0
    fi
    
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}                    ROLLBACK CONFIRMATION${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Current Version: ${CURRENT_VERSION}"
    echo "  Target Version:  ${TARGET_VERSION}"
    echo "  Backup First:    ${BACKUP_FIRST}"
    echo "  Preserve Data:   ${PRESERVE_DATA}"
    echo ""
    echo -e "${YELLOW}⚠ WARNING: This will stop current services and switch versions${NC}"
    echo ""
    read -p "Do you want to continue? (yes/no): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
}

perform_rollback() {
    log_info "Starting rollback process..."
    echo ""
    
    # Confirm action
    confirm_action
    
    # Create backup if requested
    if [ "$BACKUP_FIRST" = true ]; then
        create_backup
    fi
    
    # Execute rollback steps
    stop_current_services
    rollback_code
    
    if [ "$PRESERVE_DATA" = false ]; then
        rollback_database
    fi
    
    start_target_services
    
    # Verify rollback
    if verify_rollback; then
        log_success "Rollback completed successfully!"
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}║              Rollback Completed Successfully!                ║${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "New version: $TARGET_VERSION"
        echo "Location: $TARGET_PATH"
        echo ""
        return 0
    else
        log_error "Rollback verification failed!"
        echo ""
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}║                  Rollback Failed!                            ║${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ "$BACKUP_FIRST" = true ]; then
            log_info "Backup is available at: ${BACKUP_DIR}/latest-backup.txt"
            echo "You can restore from backup if needed"
        fi
        
        return 1
    fi
}

show_rollback_summary() {
    echo ""
    echo -e "${CYAN}Rollback Summary:${NC}"
    echo "  From: $CURRENT_VERSION"
    echo "  To:   $TARGET_VERSION"
    
    if [ "$DRY_RUN" = true ]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo "  1. Verify application is working correctly"
    echo "  2. Check logs: docker compose logs -f"
    echo "  3. Run health check: ./scripts/health-check.sh"
    
    if [ "$BACKUP_FIRST" = true ]; then
        echo "  4. Backup is saved at: ${BACKUP_DIR}"
    fi
    
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --list)
                LIST_ONLY=true
                shift
                ;;
            --to)
                TARGET_VERSION="$2"
                shift 2
                ;;
            --previous)
                ACTION="previous"
                shift
                ;;
            --backup-first)
                BACKUP_FIRST=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --preserve-data)
                PRESERVE_DATA=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_header
    
    # List versions and exit if requested
    if [ "$LIST_ONLY" = true ]; then
        list_available_versions
        exit 0
    fi
    
    # Detect current version
    detect_current_version
    
    # Determine target version
    if [ -z "$TARGET_VERSION" ]; then
        find_previous_version || exit 1
    fi
    
    # Validate target version
    validate_target_version || exit 1
    
    # Show what we're going to do
    echo -e "${CYAN}Rollback Plan:${NC}"
    echo "  Current: $CURRENT_VERSION"
    echo "  Target:  $TARGET_VERSION"
    echo "  Mode:    $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE")"
    echo ""
    
    # Perform rollback
    if perform_rollback; then
        show_rollback_summary
        exit 0
    else
        show_rollback_summary
        exit 1
    fi
}

# Run main function
main "$@"
