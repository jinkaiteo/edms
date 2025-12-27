#!/bin/bash

################################################################################
# EDMS Automated Remote Deployment Transfer Script
################################################################################
#
# Description: Automates the transfer and deployment of EDMS to remote servers
# Version: 1.0
# Date: December 24, 2024
#
# Features:
# - Automatically creates deployment package
# - Transfers to remote server via SCP
# - Optionally extracts and deploys on remote server
# - Verifies transfer integrity
# - Supports SSH key authentication
#
# Usage: ./scripts/deploy-to-remote.sh [user@]host[:path] [options]
#
# Examples:
#   ./scripts/deploy-to-remote.sh root@192.168.1.100:/opt/
#   ./scripts/deploy-to-remote.sh user@server.com --auto-deploy
#   ./scripts/deploy-to-remote.sh server.com --path /var/www --key ~/.ssh/id_rsa
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

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PATH="/opt"
SSH_KEY=""
SSH_PORT="22"
AUTO_DEPLOY=false
VERIFY_CHECKSUM=true
KEEP_LOCAL=false
VERBOSE=false

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║     EDMS Automated Remote Deployment Transfer                ║${NC}"
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

log_verbose() {
    if [ "${VERBOSE}" = true ]; then
        echo -e "${CYAN}  →${NC} $1"
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [user@]host[:path] [options]

Arguments:
  [user@]host[:path]    Remote server (e.g., user@server.com:/opt/)
                        If user is omitted, current user is used
                        If path is omitted, /opt/ is used

Options:
  -p, --path PATH       Remote deployment path (default: /opt)
  -k, --key KEY         SSH private key file
  -P, --port PORT       SSH port (default: 22)
  -a, --auto-deploy     Automatically deploy after transfer
  -n, --no-verify       Skip checksum verification
  -K, --keep            Keep local package after transfer
  -v, --verbose         Verbose output
  -h, --help            Show this help message

Examples:
  # Basic transfer
  $0 root@192.168.1.100

  # Transfer to specific path
  $0 user@server.com:/var/www/edms

  # Transfer and auto-deploy
  $0 user@server.com --auto-deploy

  # Use specific SSH key
  $0 user@server.com --key ~/.ssh/production_key

  # Custom SSH port
  $0 user@server.com --port 2222

  # Keep local package
  $0 user@server.com --keep

Notes:
  - Requires SSH access to remote server
  - Requires Docker and Docker Compose on remote server
  - Remote user needs sudo privileges for deployment
  - Package is created automatically before transfer

EOF
}

parse_arguments() {
    # Check for help flag first
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    # Parse remote destination
    local destination="$1"
    shift
    
    # Parse user@host:path
    if [[ "$destination" =~ ^([^@]+@)?([^:]+)(:(.+))?$ ]]; then
        local user_part="${BASH_REMATCH[1]}"
        REMOTE_HOST="${BASH_REMATCH[2]}"
        local path_part="${BASH_REMATCH[4]}"
        
        # Extract user if provided
        if [ -n "$user_part" ]; then
            REMOTE_USER="${user_part%@}"
        else
            REMOTE_USER="$USER"
        fi
        
        # Extract path if provided
        if [ -n "$path_part" ]; then
            REMOTE_PATH="$path_part"
        fi
    else
        log_error "Invalid destination format: $destination"
        show_usage
        exit 1
    fi
    
    # Parse options
    while [ $# -gt 0 ]; do
        case "$1" in
            -p|--path)
                REMOTE_PATH="$2"
                shift 2
                ;;
            -k|--key)
                SSH_KEY="$2"
                shift 2
                ;;
            -P|--port)
                SSH_PORT="$2"
                shift 2
                ;;
            -a|--auto-deploy)
                AUTO_DEPLOY=true
                shift
                ;;
            -n|--no-verify)
                VERIFY_CHECKSUM=false
                shift
                ;;
            -K|--keep)
                KEEP_LOCAL=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
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
}

validate_remote_connection() {
    log_info "Validating remote connection..."
    
    local ssh_opts="-p ${SSH_PORT} -o ConnectTimeout=10 -o BatchMode=yes"
    
    if [ -n "$SSH_KEY" ]; then
        if [ ! -f "$SSH_KEY" ]; then
            log_error "SSH key not found: $SSH_KEY"
            exit 1
        fi
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    log_verbose "Testing SSH connection to ${REMOTE_USER}@${REMOTE_HOST}:${SSH_PORT}"
    
    if ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "echo 'Connection successful'" >/dev/null 2>&1; then
        log_success "Remote connection validated"
        return 0
    else
        log_error "Cannot connect to ${REMOTE_USER}@${REMOTE_HOST}"
        log_error "Please check:"
        echo "  - SSH service is running on remote host"
        echo "  - Port ${SSH_PORT} is accessible"
        echo "  - SSH key authentication is configured"
        echo "  - Username is correct"
        exit 1
    fi
}

check_remote_requirements() {
    log_info "Checking remote server requirements..."
    
    local ssh_opts="-p ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    # Check Docker
    log_verbose "Checking Docker installation..."
    if ! ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "command -v docker >/dev/null 2>&1"; then
        log_warning "Docker not found on remote server"
        log_warning "Deployment will require Docker to be installed"
    else
        local docker_version=$(ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "docker --version 2>/dev/null")
        log_success "Docker found: $docker_version"
    fi
    
    # Check Docker Compose
    log_verbose "Checking Docker Compose installation..."
    if ! ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1"; then
        log_warning "Docker Compose not found on remote server"
        log_warning "Deployment will require Docker Compose to be installed"
    else
        local compose_version=$(ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "docker compose version 2>/dev/null || docker-compose version 2>/dev/null")
        log_success "Docker Compose found: $compose_version"
    fi
    
    # Check remote path
    log_verbose "Checking remote path accessibility..."
    if ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" "test -d ${REMOTE_PATH} || sudo mkdir -p ${REMOTE_PATH}"; then
        log_success "Remote path accessible: ${REMOTE_PATH}"
    else
        log_error "Cannot access or create remote path: ${REMOTE_PATH}"
        exit 1
    fi
}

create_deployment_package() {
    log_info "Creating deployment package..."
    
    cd "${REPO_ROOT}"
    
    if [ ! -f "scripts/create-production-package.sh" ]; then
        log_error "Package creator script not found: scripts/create-production-package.sh"
        exit 1
    fi
    
    chmod +x scripts/create-production-package.sh
    
    log_verbose "Running package creator..."
    if bash scripts/create-production-package.sh; then
        # Find the created package
        PACKAGE_FILE=$(ls -t edms-production-*.tar.gz 2>/dev/null | head -1)
        
        if [ -z "$PACKAGE_FILE" ]; then
            log_error "Package file not found after creation"
            exit 1
        fi
        
        PACKAGE_NAME="${PACKAGE_FILE%.tar.gz}"
        log_success "Package created: $PACKAGE_FILE"
        
        # Get package size
        local package_size=$(du -sh "$PACKAGE_FILE" | cut -f1)
        log_info "Package size: $package_size"
        
        return 0
    else
        log_error "Failed to create deployment package"
        exit 1
    fi
}

transfer_package() {
    log_info "Transferring package to remote server..."
    
    local ssh_opts="-P ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    log_verbose "Transferring ${PACKAGE_FILE} to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
    
    # Show progress
    if [ "${VERBOSE}" = true ]; then
        scp $ssh_opts "$PACKAGE_FILE" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
    else
        scp $ssh_opts "$PACKAGE_FILE" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/" >/dev/null 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Package transferred successfully"
    else
        log_error "Failed to transfer package"
        exit 1
    fi
}

verify_transfer() {
    if [ "${VERIFY_CHECKSUM}" = false ]; then
        log_info "Skipping checksum verification"
        return 0
    fi
    
    log_info "Verifying transfer integrity..."
    
    local ssh_opts="-p ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    # Get local checksum
    local local_checksum=$(sha256sum "$PACKAGE_FILE" | cut -d' ' -f1)
    log_verbose "Local checksum: $local_checksum"
    
    # Get remote checksum
    local remote_checksum=$(ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" \
        "sha256sum ${REMOTE_PATH}/$(basename $PACKAGE_FILE) 2>/dev/null | cut -d' ' -f1")
    log_verbose "Remote checksum: $remote_checksum"
    
    if [ "$local_checksum" = "$remote_checksum" ]; then
        log_success "Checksum verification passed"
        return 0
    else
        log_error "Checksum mismatch! Transfer may be corrupted"
        log_error "Local:  $local_checksum"
        log_error "Remote: $remote_checksum"
        exit 1
    fi
}

extract_on_remote() {
    log_info "Extracting package on remote server..."
    
    local ssh_opts="-p ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    local package_file=$(basename "$PACKAGE_FILE")
    
    ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" << EOF
cd ${REMOTE_PATH}
tar -xzf ${package_file}
if [ \$? -eq 0 ]; then
    echo "Package extracted successfully"
    rm -f ${package_file}
    echo "Archive removed"
else
    echo "Error: Failed to extract package"
    exit 1
fi
EOF
    
    if [ $? -eq 0 ]; then
        log_success "Package extracted on remote server"
    else
        log_error "Failed to extract package"
        exit 1
    fi
}

deploy_on_remote() {
    log_info "Deploying application on remote server..."
    
    local ssh_opts="-p ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi
    
    log_verbose "Running deployment script..."
    
    ssh $ssh_opts "${REMOTE_USER}@${REMOTE_HOST}" << EOF
cd ${REMOTE_PATH}/${PACKAGE_NAME}

# Check if deploy-interactive.sh exists
if [ ! -f "./deploy-interactive.sh" ]; then
    echo "Error: deploy-interactive.sh not found"
    exit 1
fi

# Make executable
chmod +x deploy-interactive.sh
chmod +x quick-deploy.sh 2>/dev/null || true

echo "Deployment package ready at: ${REMOTE_PATH}/${PACKAGE_NAME}"
echo ""
echo "To complete deployment, SSH to the server and run:"
echo "  cd ${REMOTE_PATH}/${PACKAGE_NAME}"
echo "  ./deploy-interactive.sh"
echo ""
EOF
    
    if [ $? -eq 0 ]; then
        log_success "Deployment package prepared on remote server"
    else
        log_error "Failed to prepare deployment"
        exit 1
    fi
}

cleanup_local() {
    if [ "${KEEP_LOCAL}" = true ]; then
        log_info "Keeping local package: $PACKAGE_FILE"
        return 0
    fi
    
    log_info "Cleaning up local files..."
    
    if [ -f "$PACKAGE_FILE" ]; then
        rm -f "$PACKAGE_FILE"
        log_verbose "Removed $PACKAGE_FILE"
    fi
    
    if [ -d "$PACKAGE_NAME" ]; then
        rm -rf "$PACKAGE_NAME"
        log_verbose "Removed $PACKAGE_NAME/"
    fi
    
    log_success "Local cleanup completed"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║     Transfer Completed Successfully                           ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}Transfer Details:${NC}"
    echo "  Package:        $PACKAGE_NAME"
    echo "  Remote Host:    ${REMOTE_USER}@${REMOTE_HOST}"
    echo "  Remote Path:    ${REMOTE_PATH}/${PACKAGE_NAME}"
    echo "  SSH Port:       ${SSH_PORT}"
    if [ -n "$SSH_KEY" ]; then
        echo "  SSH Key:        $SSH_KEY"
    fi
    echo ""
    
    echo -e "${CYAN}Next Steps:${NC}"
    echo ""
    echo "1. SSH to the remote server:"
    echo "   ${YELLOW}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
    echo ""
    echo "2. Navigate to deployment directory:"
    echo "   ${YELLOW}cd ${REMOTE_PATH}/${PACKAGE_NAME}${NC}"
    echo ""
    echo "3. Run interactive deployment:"
    echo "   ${YELLOW}./deploy-interactive.sh${NC}"
    echo ""
    echo "   Or quick deploy:"
    echo "   ${YELLOW}./quick-deploy.sh${NC}"
    echo ""
    echo -e "${CYAN}Remote Command:${NC}"
    echo "   ${YELLOW}ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH}/${PACKAGE_NAME} && ./deploy-interactive.sh'${NC}"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    parse_arguments "$@"
    
    print_header
    
    echo -e "${CYAN}Configuration:${NC}"
    echo "  Remote Host:    ${REMOTE_USER}@${REMOTE_HOST}"
    echo "  Remote Path:    ${REMOTE_PATH}"
    echo "  SSH Port:       ${SSH_PORT}"
    echo "  Auto Deploy:    ${AUTO_DEPLOY}"
    echo "  Verify Checksum: ${VERIFY_CHECKSUM}"
    echo "  Keep Local:     ${KEEP_LOCAL}"
    echo ""
    
    # Validate and check
    validate_remote_connection
    check_remote_requirements
    
    # Create and transfer
    create_deployment_package
    transfer_package
    verify_transfer
    extract_on_remote
    
    # Deploy if requested
    if [ "${AUTO_DEPLOY}" = true ]; then
        deploy_on_remote
    fi
    
    # Cleanup
    cleanup_local
    
    # Summary
    print_summary
}

# Run main function
main "$@"
