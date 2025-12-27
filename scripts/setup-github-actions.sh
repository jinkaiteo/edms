#!/bin/bash

################################################################################
# GitHub Actions Setup Assistant
################################################################################
#
# Description: Interactive setup wizard for GitHub Actions CI/CD
# Version: 1.0
# Date: December 24, 2024
#
# Usage: ./scripts/setup-github-actions.sh
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
    echo -e "${BLUE}║        GitHub Actions CI/CD Setup Assistant                  ║${NC}"
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

step_1_generate_keys() {
    log_step "STEP 1: Generate SSH Deployment Keys"
    
    echo "This will generate SSH keys for GitHub Actions deployments."
    echo ""
    
    read -p "Generate staging SSH key? (y/n): " gen_staging
    if [ "$gen_staging" = "y" ]; then
        if [ -f ~/.ssh/github_staging_key ]; then
            log_error "Key already exists: ~/.ssh/github_staging_key"
            read -p "Overwrite? (y/n): " overwrite
            if [ "$overwrite" != "y" ]; then
                log_info "Skipping staging key generation"
            else
                ssh-keygen -t ed25519 -C "github-staging-deploy" -f ~/.ssh/github_staging_key -N ""
                log_success "Staging key generated"
            fi
        else
            ssh-keygen -t ed25519 -C "github-staging-deploy" -f ~/.ssh/github_staging_key -N ""
            log_success "Staging key generated: ~/.ssh/github_staging_key"
        fi
    fi
    
    read -p "Generate production SSH key? (y/n): " gen_prod
    if [ "$gen_prod" = "y" ]; then
        if [ -f ~/.ssh/github_production_key ]; then
            log_error "Key already exists: ~/.ssh/github_production_key"
            read -p "Overwrite? (y/n): " overwrite
            if [ "$overwrite" != "y" ]; then
                log_info "Skipping production key generation"
            else
                ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""
                log_success "Production key generated"
            fi
        else
            ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""
            log_success "Production key generated: ~/.ssh/github_production_key"
        fi
    fi
    
    press_enter
}

step_2_add_public_keys() {
    log_step "STEP 2: Add Public Keys to Servers"
    
    echo "You need to add the public keys to your servers."
    echo ""
    
    if [ -f ~/.ssh/github_staging_key.pub ]; then
        echo "Staging Public Key:"
        echo "-------------------"
        cat ~/.ssh/github_staging_key.pub
        echo ""
        
        read -p "Enter staging server (user@host): " staging_server
        if [ -n "$staging_server" ]; then
            read -p "Copy key to staging server? (y/n): " copy_staging
            if [ "$copy_staging" = "y" ]; then
                ssh-copy-id -i ~/.ssh/github_staging_key.pub "$staging_server"
                if [ $? -eq 0 ]; then
                    log_success "Key copied to staging server"
                else
                    log_error "Failed to copy key to staging server"
                fi
            fi
        fi
    fi
    
    echo ""
    
    if [ -f ~/.ssh/github_production_key.pub ]; then
        echo "Production Public Key:"
        echo "----------------------"
        cat ~/.ssh/github_production_key.pub
        echo ""
        
        read -p "Enter production server (user@host): " prod_server
        if [ -n "$prod_server" ]; then
            read -p "Copy key to production server? (y/n): " copy_prod
            if [ "$copy_prod" = "y" ]; then
                ssh-copy-id -i ~/.ssh/github_production_key.pub "$prod_server"
                if [ $? -eq 0 ]; then
                    log_success "Key copied to production server"
                else
                    log_error "Failed to copy key to production server"
                fi
            fi
        fi
    fi
    
    press_enter
}

step_3_test_connections() {
    log_step "STEP 3: Test SSH Connections"
    
    echo "Testing SSH connections with the new keys..."
    echo ""
    
    if [ -f ~/.ssh/github_staging_key ]; then
        read -p "Test staging connection (user@host): " staging_server
        if [ -n "$staging_server" ]; then
            ssh -i ~/.ssh/github_staging_key -o BatchMode=yes -o ConnectTimeout=5 "$staging_server" "echo 'Staging connection OK'" 2>/dev/null
            if [ $? -eq 0 ]; then
                log_success "Staging SSH connection works"
            else
                log_error "Staging SSH connection failed"
            fi
        fi
    fi
    
    echo ""
    
    if [ -f ~/.ssh/github_production_key ]; then
        read -p "Test production connection (user@host): " prod_server
        if [ -n "$prod_server" ]; then
            ssh -i ~/.ssh/github_production_key -o BatchMode=yes -o ConnectTimeout=5 "$prod_server" "echo 'Production connection OK'" 2>/dev/null
            if [ $? -eq 0 ]; then
                log_success "Production SSH connection works"
            else
                log_error "Production SSH connection failed"
            fi
        fi
    fi
    
    press_enter
}

step_4_display_secrets() {
    log_step "STEP 4: GitHub Secrets Configuration"
    
    echo "Add these secrets to your GitHub repository:"
    echo "Go to: Settings → Secrets and variables → Actions → New repository secret"
    echo ""
    
    if [ -f ~/.ssh/github_staging_key ]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}SECRET: STAGING_SSH_KEY${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        cat ~/.ssh/github_staging_key
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    read -p "Enter STAGING_HOST (server hostname or IP): " staging_host
    if [ -n "$staging_host" ]; then
        echo ""
        echo -e "${CYAN}SECRET: STAGING_HOST${NC}"
        echo "Value: ${staging_host}"
        echo ""
    fi
    
    read -p "Enter STAGING_USER (SSH username): " staging_user
    if [ -n "$staging_user" ]; then
        echo ""
        echo -e "${CYAN}SECRET: STAGING_USER${NC}"
        echo "Value: ${staging_user}"
        echo ""
    fi
    
    press_enter
    
    if [ -f ~/.ssh/github_production_key ]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}SECRET: PRODUCTION_SSH_KEY${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        cat ~/.ssh/github_production_key
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    read -p "Enter PRODUCTION_HOST (server hostname or IP): " prod_host
    if [ -n "$prod_host" ]; then
        echo ""
        echo -e "${CYAN}SECRET: PRODUCTION_HOST${NC}"
        echo "Value: ${prod_host}"
        echo ""
    fi
    
    read -p "Enter PRODUCTION_USER (SSH username): " prod_user
    if [ -n "$prod_user" ]; then
        echo ""
        echo -e "${CYAN}SECRET: PRODUCTION_USER${NC}"
        echo "Value: ${prod_user}"
        echo ""
    fi
    
    press_enter
}

step_5_verify_workflow() {
    log_step "STEP 5: Verify Workflow File"
    
    if [ -f ".github/workflows/deploy.yml" ]; then
        log_success "Workflow file exists: .github/workflows/deploy.yml"
        echo ""
        echo "File size: $(du -h .github/workflows/deploy.yml | cut -f1)"
        echo "Lines: $(wc -l < .github/workflows/deploy.yml)"
        echo ""
        
        read -p "View workflow summary? (y/n): " view_workflow
        if [ "$view_workflow" = "y" ]; then
            echo ""
            echo "Workflow triggers:"
            grep -A 10 "^on:" .github/workflows/deploy.yml
            echo ""
        fi
    else
        log_error "Workflow file not found!"
        echo "Expected: .github/workflows/deploy.yml"
    fi
    
    press_enter
}

step_6_next_steps() {
    log_step "STEP 6: Next Steps"
    
    echo "To complete setup:"
    echo ""
    echo "1. Add all secrets to GitHub:"
    echo "   Repository → Settings → Secrets and variables → Actions"
    echo ""
    echo "2. Create environments:"
    echo "   Repository → Settings → Environments"
    echo "   - Create 'staging' environment"
    echo "   - Create 'production' environment (add reviewers)"
    echo ""
    echo "3. Enable GitHub Actions:"
    echo "   Repository → Actions → Enable workflows"
    echo ""
    echo "4. Test deployment:"
    echo "   git checkout -b develop"
    echo "   git push origin develop"
    echo ""
    echo "5. Monitor workflow:"
    echo "   Repository → Actions → View running workflow"
    echo ""
    
    press_enter
}

generate_summary() {
    clear
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║            GitHub Actions Setup Complete!                    ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo "Summary:"
    echo "--------"
    
    if [ -f ~/.ssh/github_staging_key ]; then
        log_success "Staging SSH key generated"
    else
        log_error "Staging SSH key not found"
    fi
    
    if [ -f ~/.ssh/github_production_key ]; then
        log_success "Production SSH key generated"
    else
        log_error "Production SSH key not found"
    fi
    
    if [ -f ".github/workflows/deploy.yml" ]; then
        log_success "Workflow file exists"
    else
        log_error "Workflow file not found"
    fi
    
    echo ""
    echo "Documentation:"
    echo "--------------"
    echo "  - GITHUB_ACTIONS_SETUP.md (detailed guide)"
    echo "  - CI_CD_INTEGRATION_GUIDE.md (complete CI/CD guide)"
    echo ""
    
    echo "Quick commands:"
    echo "---------------"
    echo "  # Deploy to staging"
    echo "  git push origin develop"
    echo ""
    echo "  # Deploy to production"
    echo "  git push origin main"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    cd "$PROJECT_ROOT"
    
    print_header
    
    echo "This wizard will help you set up GitHub Actions CI/CD."
    echo ""
    echo "What it does:"
    echo "  1. Generate SSH keys for deployment"
    echo "  2. Add public keys to servers"
    echo "  3. Test SSH connections"
    echo "  4. Display secrets for GitHub"
    echo "  5. Verify workflow configuration"
    echo "  6. Show next steps"
    echo ""
    
    read -p "Continue? (y/n): " continue_setup
    if [ "$continue_setup" != "y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    step_1_generate_keys
    step_2_add_public_keys
    step_3_test_connections
    step_4_display_secrets
    step_5_verify_workflow
    step_6_next_steps
    
    generate_summary
}

# Run main function
main "$@"
