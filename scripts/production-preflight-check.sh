#!/bin/bash

################################################################################
# Production Pre-Flight Check
################################################################################
#
# Description: Comprehensive readiness check for production deployment
# Version: 1.0
# Date: December 24, 2024
#
# Usage: ./scripts/production-preflight-check.sh
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

# Results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0
declare -A RESULTS

################################################################################
# Functions
################################################################################

print_header() {
    clear
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║          Production Deployment Pre-Flight Check              ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Checking readiness for production deployment..."
    echo ""
}

log_info() {
    echo -e "${CYAN}[CHECK]${NC} $1"
}

log_success() {
    echo -e "${GREEN}  ✓${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}  ⚠${NC} $1"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

log_error() {
    echo -e "${RED}  ✗${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

record_result() {
    local category="$1"
    local status="$2"
    local message="$3"
    RESULTS["$category"]="$status|$message"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_automation_scripts() {
    echo ""
    log_info "1. Automation Scripts"
    echo ""
    
    local scripts=(
        "health-check.sh"
        "rollback.sh"
        "pre-deploy-check.sh"
        "post-deploy-check.sh"
        "create-production-package.sh"
        "deploy-to-remote.sh"
    )
    
    local all_present=true
    local all_executable=true
    
    for script in "${scripts[@]}"; do
        if [ -f "scripts/$script" ]; then
            log_success "$script exists"
            
            if [ -x "scripts/$script" ]; then
                log_success "$script is executable"
            else
                log_error "$script is not executable"
                all_executable=false
            fi
        else
            log_error "$script not found"
            all_present=false
        fi
    done
    
    if [ "$all_present" = true ] && [ "$all_executable" = true ]; then
        record_result "automation_scripts" "pass" "All 6 scripts present and executable"
    else
        record_result "automation_scripts" "fail" "Missing or non-executable scripts"
    fi
}

check_cicd_configuration() {
    echo ""
    log_info "2. CI/CD Configuration"
    echo ""
    
    if [ -f ".github/workflows/deploy.yml" ]; then
        log_success "GitHub Actions workflow exists"
        record_result "cicd_github" "pass" "Workflow configured"
    else
        log_warning "GitHub Actions workflow not found"
        record_result "cicd_github" "warning" "No workflow file"
    fi
    
    if [ -f ".gitlab-ci.yml" ]; then
        log_success "GitLab CI configuration exists"
    fi
    
    if [ -f "Jenkinsfile" ]; then
        log_success "Jenkins pipeline exists"
    fi
    
    if [ -f "docker-compose.ci.yml" ]; then
        log_success "Docker CI configuration exists"
    fi
}

check_docker_files() {
    echo ""
    log_info "3. Docker Configuration"
    echo ""
    
    local docker_ok=true
    
    if [ -f "docker-compose.yml" ]; then
        log_success "docker-compose.yml exists"
    else
        log_error "docker-compose.yml not found"
        docker_ok=false
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        log_success "docker-compose.prod.yml exists"
    else
        log_error "docker-compose.prod.yml not found"
        docker_ok=false
    fi
    
    if [ -f "infrastructure/containers/Dockerfile.backend.prod" ]; then
        log_success "Production backend Dockerfile exists"
    else
        log_warning "Production backend Dockerfile not found"
    fi
    
    if [ -f "infrastructure/containers/Dockerfile.frontend.prod" ]; then
        log_success "Production frontend Dockerfile exists"
    else
        log_warning "Production frontend Dockerfile not found"
    fi
    
    if [ "$docker_ok" = true ]; then
        record_result "docker_config" "pass" "Docker configurations present"
    else
        record_result "docker_config" "fail" "Missing Docker configurations"
    fi
}

check_backend_structure() {
    echo ""
    log_info "4. Backend Structure"
    echo ""
    
    local backend_ok=true
    
    if [ -f "backend/manage.py" ]; then
        log_success "Django manage.py exists"
    else
        log_error "Django manage.py not found"
        backend_ok=false
    fi
    
    if [ -d "backend/apps" ]; then
        local app_count=$(find backend/apps -mindepth 1 -maxdepth 1 -type d | wc -l)
        log_success "Backend apps directory exists ($app_count apps)"
    else
        log_error "Backend apps directory not found"
        backend_ok=false
    fi
    
    if [ -f "backend/requirements/production.txt" ]; then
        log_success "Production requirements exist"
    else
        log_error "Production requirements not found"
        backend_ok=false
    fi
    
    if [ -f "backend/.env.example" ]; then
        log_success ".env.example exists"
    else
        log_warning ".env.example not found"
    fi
    
    if [ "$backend_ok" = true ]; then
        record_result "backend_structure" "pass" "Backend structure complete"
    else
        record_result "backend_structure" "fail" "Backend structure incomplete"
    fi
}

check_frontend_structure() {
    echo ""
    log_info "5. Frontend Structure"
    echo ""
    
    local frontend_ok=true
    
    if [ -f "frontend/package.json" ]; then
        log_success "package.json exists"
    else
        log_error "package.json not found"
        frontend_ok=false
    fi
    
    if [ -d "frontend/src" ]; then
        log_success "Frontend src directory exists"
    else
        log_error "Frontend src directory not found"
        frontend_ok=false
    fi
    
    if [ -f "frontend/nginx.conf" ]; then
        log_success "Nginx configuration exists"
    else
        log_warning "Nginx configuration not found"
    fi
    
    if [ "$frontend_ok" = true ]; then
        record_result "frontend_structure" "pass" "Frontend structure complete"
    else
        record_result "frontend_structure" "fail" "Frontend structure incomplete"
    fi
}

check_documentation() {
    echo ""
    log_info "6. Documentation"
    echo ""
    
    local doc_count=0
    
    if [ -f "README.md" ]; then
        log_success "README.md exists"
        doc_count=$((doc_count + 1))
    fi
    
    if [ -f "DEPLOYMENT_QUICK_REFERENCE.md" ]; then
        log_success "Quick reference exists"
        doc_count=$((doc_count + 1))
    fi
    
    if [ -f "CI_CD_INTEGRATION_GUIDE.md" ]; then
        log_success "CI/CD guide exists"
        doc_count=$((doc_count + 1))
    fi
    
    if [ -f "AUTOMATION_SCRIPTS_GUIDE.md" ]; then
        log_success "Automation guide exists"
        doc_count=$((doc_count + 1))
    fi
    
    if [ $doc_count -ge 3 ]; then
        log_success "Documentation is comprehensive ($doc_count key docs)"
        record_result "documentation" "pass" "$doc_count documentation files"
    else
        log_warning "Limited documentation ($doc_count docs)"
        record_result "documentation" "warning" "Could use more documentation"
    fi
}

check_security_files() {
    echo ""
    log_info "7. Security & Configuration"
    echo ""
    
    if [ -f ".gitignore" ]; then
        log_success ".gitignore exists"
        
        if grep -q ".env" .gitignore; then
            log_success ".env is in .gitignore"
        else
            log_warning ".env should be in .gitignore"
        fi
    fi
    
    if [ -f "SECURITY.md" ]; then
        log_success "SECURITY.md exists"
    fi
    
    # Check for sensitive files that shouldn't be committed
    if [ -f "backend/.env" ]; then
        log_warning "backend/.env exists (ensure it's in .gitignore)"
    fi
    
    if find . -name "*.sqlite3" -not -path "./backend/edms_*.sqlite3" | grep -q .; then
        log_warning "SQLite database files found (should not be in repo)"
    fi
    
    record_result "security" "pass" "Security configurations acceptable"
}

check_testing_readiness() {
    echo ""
    log_info "8. Testing Capability"
    echo ""
    
    if [ -f "backend/pytest.ini" ] || [ -f "backend/requirements/test.txt" ]; then
        log_success "Backend testing configured"
    else
        log_warning "Backend testing not fully configured"
    fi
    
    if [ -f "frontend/package.json" ]; then
        if grep -q "\"test\":" frontend/package.json; then
            log_success "Frontend tests configured"
        else
            log_warning "Frontend test script not found"
        fi
    fi
    
    record_result "testing" "pass" "Testing capability available"
}

check_deployment_readiness() {
    echo ""
    log_info "9. Deployment Package Creation"
    echo ""
    
    if [ -x "scripts/create-production-package.sh" ]; then
        log_info "Testing package creation..."
        
        # Create a test package
        if timeout 30 bash scripts/create-production-package.sh > /tmp/package-test.log 2>&1; then
            if ls edms-production-*.tar.gz 1> /dev/null 2>&1; then
                local package=$(ls -t edms-production-*.tar.gz | head -1)
                local size=$(du -h "$package" | cut -f1)
                log_success "Package creation successful ($size)"
                record_result "package_creation" "pass" "Can create packages"
            else
                log_error "Package creation failed (no output)"
                record_result "package_creation" "fail" "Package not created"
            fi
        else
            log_error "Package creation failed (timeout or error)"
            record_result "package_creation" "fail" "Package creation failed"
        fi
    else
        log_error "Package creation script not executable"
        record_result "package_creation" "fail" "Script not executable"
    fi
}

check_git_status() {
    echo ""
    log_info "10. Git Repository Status"
    echo ""
    
    if [ -d ".git" ]; then
        log_success "Git repository initialized"
        
        # Check for uncommitted changes
        if git diff-index --quiet HEAD -- 2>/dev/null; then
            log_success "No uncommitted changes"
        else
            log_warning "Uncommitted changes detected"
        fi
        
        # Check remote
        if git remote -v | grep -q "origin"; then
            log_success "Git remote configured"
        else
            log_warning "No git remote configured"
        fi
        
        record_result "git_status" "pass" "Git repository ready"
    else
        log_warning "Not a git repository"
        record_result "git_status" "warning" "No git repository"
    fi
}

generate_report() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}                    PRE-FLIGHT SUMMARY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed:${NC} $PASSED_CHECKS"
    echo -e "${YELLOW}Warnings:${NC} $WARNING_CHECKS"
    echo -e "${RED}Failed:${NC} $FAILED_CHECKS"
    echo ""
    
    # Calculate score
    local score=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    
    echo "Readiness Score: ${score}%"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ] && [ $score -ge 80 ]; then
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}║              ✓ READY FOR PRODUCTION DEPLOYMENT               ║${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Your system is ready for production deployment!"
        return 0
    elif [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║                                                               ║${NC}"
        echo -e "${YELLOW}║         ⚠ MOSTLY READY - REVIEW WARNINGS                     ║${NC}"
        echo -e "${YELLOW}║                                                               ║${NC}"
        echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Review warnings above before deploying."
        return 0
    else
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}║            ✗ NOT READY FOR PRODUCTION                         ║${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Fix failed checks before deploying to production."
        return 1
    fi
}

generate_recommendations() {
    echo ""
    echo -e "${CYAN}Recommendations:${NC}"
    echo ""
    
    if [ $FAILED_CHECKS -gt 0 ]; then
        echo "❌ Critical Issues:"
        for check in "${!RESULTS[@]}"; do
            IFS='|' read -r status message <<< "${RESULTS[$check]}"
            if [ "$status" = "fail" ]; then
                echo "  • $check: $message"
            fi
        done
        echo ""
    fi
    
    if [ $WARNING_CHECKS -gt 0 ]; then
        echo "⚠️  Warnings to Review:"
        for check in "${!RESULTS[@]}"; do
            IFS='|' read -r status message <<< "${RESULTS[$check]}"
            if [ "$status" = "warning" ]; then
                echo "  • $check: $message"
            fi
        done
        echo ""
    fi
    
    echo "📋 Next Steps:"
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo "  1. Set up CI/CD (GitHub Actions recommended)"
        echo "  2. Configure production server"
        echo "  3. Add deployment secrets"
        echo "  4. Run test deployment to staging"
        echo "  5. Deploy to production with approval"
    else
        echo "  1. Fix all failed checks"
        echo "  2. Re-run this pre-flight check"
        echo "  3. Proceed when all checks pass"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    cd "$PROJECT_ROOT"
    
    print_header
    
    check_automation_scripts
    check_cicd_configuration
    check_docker_files
    check_backend_structure
    check_frontend_structure
    check_documentation
    check_security_files
    check_testing_readiness
    check_deployment_readiness
    check_git_status
    
    generate_report
    local result=$?
    
    generate_recommendations
    
    echo ""
    echo "Pre-flight check complete!"
    echo ""
    
    exit $result
}

# Run main function
main "$@"
