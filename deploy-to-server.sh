#!/bin/bash

################################################################################
# EDMS Automated Deployment Transfer Script
################################################################################
#
# Description: Automates package transfer and deployment to production server
# Version: 1.0
# Date: December 24, 2024
#
# This script:
# 1. Creates deployment package
# 2. Transfers to production server
# 3. Optionally starts remote deployment
#
# Usage: ./deploy-to-server.sh [server] [user] [path]
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_step() {
    echo -e "${CYAN}▶${NC} $1"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$(echo -e "${CYAN}?${NC} $prompt")" yn
        yn=${yn:-$default}
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [ -n "$default" ]; then
        read -p "$(echo -e "${CYAN}?${NC} $prompt [$default]: ")" input
        echo "${input:-$default}"
    else
        read -p "$(echo -e "${CYAN}?${NC} $prompt: ")" input
        while [ -z "$input" ]; do
            echo "This field is required."
            read -p "$(echo -e "${CYAN}?${NC} $prompt: ")" input
        done
        echo "$input"
    fi
}

################################################################################
# Main Script
################################################################################

main() {
    clear
    
    # Banner
    echo -e "${BOLD}${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║     EDMS Automated Deployment Transfer                       ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # Check if running from correct directory
    if [ ! -f "./create-deployment-package.sh" ]; then
        print_error "This script must be run from the EDMS root directory"
        exit 1
    fi
    
    # Get server details
    print_header "Server Configuration"
    
    echo "Enter details for your production server:"
    echo ""
    
    SERVER_USER=$(prompt_input "Server username" "root")
    SERVER_HOST=$(prompt_input "Server hostname or IP")
    SERVER_PATH=$(prompt_input "Deployment path on server" "/opt")
    
    # Optional SSH key
    echo ""
    if prompt_yes_no "Use specific SSH key?" "n"; then
        SSH_KEY=$(prompt_input "Path to SSH key" "~/.ssh/id_rsa")
        SSH_OPTS="-i ${SSH_KEY}"
    else
        SSH_OPTS=""
    fi
    
    # Summary
    print_header "Deployment Summary"
    
    echo "Target Server:"
    echo "  User:         $SERVER_USER"
    echo "  Host:         $SERVER_HOST"
    echo "  Path:         $SERVER_PATH"
    echo "  SSH Key:      ${SSH_KEY:-Default}"
    echo ""
    
    if ! prompt_yes_no "Proceed with deployment?" "y"; then
        print_info "Deployment cancelled."
        exit 0
    fi
    
    # Step 1: Create deployment package
    print_header "Step 1: Creating Deployment Package"
    
    print_step "Running package creator..."
    echo ""
    
    if ! ./create-deployment-package.sh; then
        print_error "Failed to create deployment package"
        exit 1
    fi
    
    # Find the created package
    PACKAGE_FILE=$(ls -t edms-deployment-*.tar.gz 2>/dev/null | head -1)
    PACKAGE_DIR=$(basename "$PACKAGE_FILE" .tar.gz)
    
    if [ -z "$PACKAGE_FILE" ]; then
        print_error "No deployment package found"
        exit 1
    fi
    
    print_success "Package created: $PACKAGE_FILE"
    
    # Step 2: Test SSH connection
    print_header "Step 2: Testing SSH Connection"
    
    print_step "Testing connection to $SERVER_USER@$SERVER_HOST..."
    
    if ssh $SSH_OPTS -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_HOST" "echo 'Connection successful'" 2>/dev/null; then
        print_success "SSH connection successful"
    else
        print_warning "SSH connection test failed"
        print_info "Will attempt transfer anyway (may prompt for password)"
    fi
    
    # Step 3: Transfer package
    print_header "Step 3: Transferring Package"
    
    print_step "Copying package to $SERVER_HOST:$SERVER_PATH/$PACKAGE_FILE"
    print_info "This may take a few minutes depending on network speed..."
    echo ""
    
    if scp $SSH_OPTS "$PACKAGE_FILE" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"; then
        print_success "Package transferred successfully"
    else
        print_error "Failed to transfer package"
        exit 1
    fi
    
    # Step 4: Extract on server
    print_header "Step 4: Extracting Package on Server"
    
    print_step "Extracting package on remote server..."
    
    EXTRACT_CMD="cd $SERVER_PATH && tar -xzf $PACKAGE_FILE && echo 'Extraction complete'"
    
    if ssh $SSH_OPTS "$SERVER_USER@$SERVER_HOST" "$EXTRACT_CMD"; then
        print_success "Package extracted successfully"
    else
        print_error "Failed to extract package"
        exit 1
    fi
    
    # Step 5: Verify extraction
    print_header "Step 5: Verifying Package Contents"
    
    VERIFY_CMD="cd $SERVER_PATH/$PACKAGE_DIR && ls -la deploy-interactive.sh && wc -l deploy-interactive.sh"
    
    if ssh $SSH_OPTS "$SERVER_USER@$SERVER_HOST" "$VERIFY_CMD" >/dev/null 2>&1; then
        print_success "Package contents verified"
    else
        print_warning "Could not verify package contents (may still be OK)"
    fi
    
    # Step 6: Remote deployment option
    print_header "Step 6: Remote Deployment"
    
    echo ""
    if prompt_yes_no "Start deployment on remote server now?" "y"; then
        print_step "Starting remote deployment..."
        print_info "You will be connected to the remote server"
        print_info "The interactive deployment script will run"
        echo ""
        
        sleep 2
        
        # Connect and run deployment
        DEPLOY_CMD="cd $SERVER_PATH/$PACKAGE_DIR && chmod +x deploy-interactive.sh && ./deploy-interactive.sh"
        
        ssh $SSH_OPTS -t "$SERVER_USER@$SERVER_HOST" "$DEPLOY_CMD"
        
    else
        print_info "Skipping remote deployment"
        echo ""
        print_info "To deploy manually, SSH to the server and run:"
        echo ""
        echo "  ssh $SERVER_USER@$SERVER_HOST"
        echo "  cd $SERVER_PATH/$PACKAGE_DIR"
        echo "  ./deploy-interactive.sh"
        echo ""
    fi
    
    # Final Summary
    print_header "Transfer Complete!"
    
    echo -e "${GREEN}Deployment package has been transferred successfully!${NC}"
    echo ""
    echo "Package Location on Server:"
    echo "  Path:         $SERVER_PATH/$PACKAGE_DIR/"
    echo "  Archive:      $SERVER_PATH/$PACKAGE_FILE"
    echo ""
    echo "To deploy (if not done already):"
    echo "  ssh $SERVER_USER@$SERVER_HOST"
    echo "  cd $SERVER_PATH/$PACKAGE_DIR"
    echo "  ./deploy-interactive.sh"
    echo ""
    echo "To connect to server:"
    echo "  ssh $SSH_OPTS $SERVER_USER@$SERVER_HOST"
    echo ""
    
    # Cleanup local package option
    echo ""
    if prompt_yes_no "Clean up local package files?" "n"; then
        print_step "Cleaning up local files..."
        rm -rf "$PACKAGE_DIR" "$PACKAGE_FILE"
        print_success "Local package files removed"
    else
        print_info "Local package files kept in current directory"
    fi
    
    echo ""
    print_success "Deployment transfer completed successfully!"
    echo ""
}

# Run main function
main "$@"
