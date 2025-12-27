#!/bin/bash

################################################################################
# GitHub Actions Setup - Production Only (No Staging)
################################################################################
#
# Description: Simplified setup for production-only deployment
# Version: 1.0
# Date: December 24, 2024
#
# Usage: ./scripts/setup-github-production-only.sh
#
################################################################################

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

################################################################################
# Functions
################################################################################

print_header() {
    clear
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║      GitHub Actions Setup - Production Only                  ║${NC}"
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

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo ""
    echo -e "${YELLOW}▶${NC} $1"
    echo ""
}

press_enter() {
    echo ""
    read -p "Press Enter to continue..."
}

step_1_generate_key() {
    log_step "STEP 1: Generate SSH Deployment Key"
    
    echo "Generating SSH key for production deployment..."
    echo ""
    
    if [ -f ~/.ssh/github_production_key ]; then
        log_error "Key already exists: ~/.ssh/github_production_key"
        read -p "Overwrite? (y/n): " overwrite
        if [ "$overwrite" != "y" ]; then
            log_info "Using existing key"
            press_enter
            return
        fi
    fi
    
    ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""
    
    if [ $? -eq 0 ]; then
        log_success "Production key generated: ~/.ssh/github_production_key"
    else
        log_error "Failed to generate key"
    fi
    
    press_enter
}

step_2_add_to_server() {
    log_step "STEP 2: Add Public Key to Server"
    
    if [ ! -f ~/.ssh/github_production_key.pub ]; then
        log_error "Public key not found. Run step 1 first."
        press_enter
        return
    fi
    
    echo "Production Public Key:"
    echo "----------------------"
    cat ~/.ssh/github_production_key.pub
    echo ""
    
    read -p "Enter production server (user@host): " prod_server
    
    if [ -z "$prod_server" ]; then
        log_error "No server specified"
        press_enter
        return
    fi
    
    read -p "Copy key to server? (y/n): " copy_key
    if [ "$copy_key" = "y" ]; then
        ssh-copy-id -i ~/.ssh/github_production_key.pub "$prod_server"
        if [ $? -eq 0 ]; then
            log_success "Key copied to production server"
        else
            log_error "Failed to copy key"
        fi
    fi
    
    press_enter
}

step_3_test_connection() {
    log_step "STEP 3: Test SSH Connection"
    
    if [ ! -f ~/.ssh/github_production_key ]; then
        log_error "Private key not found. Run step 1 first."
        press_enter
        return
    fi
    
    read -p "Test connection to (user@host): " prod_server
    
    if [ -z "$prod_server" ]; then
        log_error "No server specified"
        press_enter
        return
    fi
    
    echo "Testing connection..."
    ssh -i ~/.ssh/github_production_key -o BatchMode=yes -o ConnectTimeout=5 "$prod_server" "echo 'Production connection OK'" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_success "SSH connection works!"
    else
        log_error "SSH connection failed"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Verify key was copied to server"
        echo "  2. Check server hostname/IP is correct"
        echo "  3. Ensure SSH service is running"
        echo "  4. Try manual connection: ssh -i ~/.ssh/github_production_key $prod_server"
    fi
    
    press_enter
}

step_4_display_secrets() {
    log_step "STEP 4: GitHub Secrets"
    
    echo "Add these 3 secrets to GitHub:"
    echo ""
    echo "Go to: Repository → Settings → Secrets and variables → Actions"
    echo ""
    
    if [ -f ~/.ssh/github_production_key ]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}SECRET 1: PRODUCTION_SSH_KEY${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        cat ~/.ssh/github_production_key
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    else
        log_error "Private key not found"
    fi
    
    press_enter
    
    read -p "Enter PRODUCTION_HOST (server hostname or IP): " prod_host
    if [ -n "$prod_host" ]; then
        echo ""
        echo -e "${CYAN}SECRET 2: PRODUCTION_HOST${NC}"
        echo "Value: ${prod_host}"
        echo ""
    fi
    
    read -p "Enter PRODUCTION_USER (SSH username): " prod_user
    if [ -n "$prod_user" ]; then
        echo ""
        echo -e "${CYAN}SECRET 3: PRODUCTION_USER${NC}"
        echo "Value: ${prod_user}"
        echo ""
    fi
    
    press_enter
}

step_5_workflow_setup() {
    log_step "STEP 5: Configure Workflow"
    
    echo "Choose your workflow configuration:"
    echo ""
    echo "1. Production Only (Recommended)"
    echo "   - Simpler setup"
    echo "   - Deploy directly to production"
    echo "   - Manual approval required"
    echo ""
    echo "2. Keep Original (Test with PRs)"
    echo "   - Use pull requests for testing"
    echo "   - Deploy to production from main"
    echo ""
    
    read -p "Choose option (1 or 2): " option
    
    if [ "$option" = "1" ]; then
        cd "$PROJECT_ROOT"
        
        if [ -f ".github/workflows/deploy-production-only.yml" ]; then
            # Backup original if exists
            if [ -f ".github/workflows/deploy.yml" ]; then
                mv .github/workflows/deploy.yml .github/workflows/deploy-with-staging.yml.disabled
                log_info "Original workflow backed up to: deploy-with-staging.yml.disabled"
            fi
            
            # Use production-only workflow
            mv .github/workflows/deploy-production-only.yml .github/workflows/deploy.yml
            log_success "Production-only workflow activated"
        else
            log_error "Production-only workflow file not found"
        fi
    else
        log_info "Keeping original workflow"
        log_info "You can test with pull requests before deploying"
    fi
    
    echo ""
    log_info "Next: Configure environment in GitHub"
    echo "  1. Go to Settings → Environments"
    echo "  2. Create 'production' environment"
    echo "  3. Add required reviewers"
    
    press_enter
}

step_6_test_deployment() {
    log_step "STEP 6: Test Deployment"
    
    echo "To test your deployment:"
    echo ""
    echo "1. Commit and push to main:"
    echo "   git add ."
    echo "   git commit -m 'Setup GitHub Actions'"
    echo "   git push origin main"
    echo ""
    echo "2. Go to Actions tab in GitHub"
    echo ""
    echo "3. Click on running workflow"
    echo ""
    echo "4. When it reaches 'Deploy to Production', click 'Review deployments'"
    echo ""
    echo "5. Select 'production' and click 'Approve and deploy'"
    echo ""
    echo "6. Monitor the deployment progress"
    echo ""
    
    press_enter
}

generate_summary() {
    clear
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║         GitHub Actions Setup Complete!                       ║${NC}"
    echo -e "${GREEN}║         (Production Only - No Staging)                       ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo "Summary:"
    echo "--------"
    
    if [ -f ~/.ssh/github_production_key ]; then
        log_success "SSH key generated"
    else
        log_error "SSH key not found"
    fi
    
    if [ -f ".github/workflows/deploy.yml" ]; then
        log_success "Workflow file configured"
    else
        log_error "Workflow file not found"
    fi
    
    echo ""
    echo "Secrets to add to GitHub (3):"
    echo "  1. PRODUCTION_SSH_KEY"
    echo "  2. PRODUCTION_HOST"
    echo "  3. PRODUCTION_USER"
    echo ""
    
    echo "Environment to create:"
    echo "  - production (with required reviewers)"
    echo ""
    
    echo "Documentation:"
    echo "  - GITHUB_SETUP_PRODUCTION_ONLY.md"
    echo "  - .github/SETUP_INSTRUCTIONS.md"
    echo ""
    
    echo "Ready to deploy!"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    cd "$PROJECT_ROOT"
    
    print_header
    
    echo "This wizard will set up GitHub Actions for production-only deployment."
    echo ""
    echo "You will:"
    echo "  1. Generate SSH key"
    echo "  2. Add key to server"
    echo "  3. Test connection"
    echo "  4. Get secrets for GitHub"
    echo "  5. Configure workflow"
    echo "  6. Learn how to test"
    echo ""
    
    read -p "Continue? (y/n): " continue_setup
    if [ "$continue_setup" != "y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    step_1_generate_key
    step_2_add_to_server
    step_3_test_connection
    step_4_display_secrets
    step_5_workflow_setup
    step_6_test_deployment
    
    generate_summary
}

# Run main function
main "$@"
