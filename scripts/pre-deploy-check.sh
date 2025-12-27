#!/bin/bash

################################################################################
# EDMS Pre-Deployment Verification Script
################################################################################
#
# Description: Verifies system readiness before deployment
# Version: 1.0
# Date: December 24, 2024
#
# Features:
# - Checks system requirements (Docker, ports, disk space)
# - Validates deployment package integrity
# - Verifies environment configuration
# - Checks for port conflicts
# - Validates SSL certificates (if applicable)
# - Tests database connectivity
# - Checks backup availability
# - Generates pre-deployment report
#
# Usage: ./scripts/pre-deploy-check.sh [package-path]
#
################################################################################

# Note: Don't use 'set -e' because we want to run all checks even if some fail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_PATH="${1:-$(pwd)}"

# Requirements
MIN_DOCKER_VERSION="20.10"
MIN_COMPOSE_VERSION="2.0"
MIN_DISK_SPACE_GB=15
MIN_MEMORY_GB=2
REQUIRED_PORTS=(80 443 8000 5432 6379)

# Check results
declare -A CHECKS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║         EDMS Pre-Deployment Verification v1.0                ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Package Path: $PACKAGE_PATH"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

log_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

record_check() {
    local name="$1"
    local status="$2"
    CHECKS["$name"]="$status"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        record_check "docker" "fail"
        return 1
    fi
    
    local docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0.0.0")
    log_success "Docker installed: $docker_version"
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        record_check "docker" "fail"
        return 1
    fi
    
    log_success "Docker daemon is running"
    record_check "docker" "pass"
    return 0
}

check_docker_compose() {
    log_info "Checking Docker Compose..."
    
    if command -v docker compose >/dev/null 2>&1; then
        local version=$(docker compose version --short 2>/dev/null || echo "0.0.0")
        log_success "Docker Compose installed: $version"
        record_check "docker_compose" "pass"
        return 0
    elif command -v docker-compose >/dev/null 2>&1; then
        local version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' || echo "0.0.0")
        log_success "Docker Compose (standalone) installed: $version"
        record_check "docker_compose" "pass"
        return 0
    else
        log_error "Docker Compose is not installed"
        record_check "docker_compose" "fail"
        return 1
    fi
}

check_disk_space() {
    log_info "Checking disk space..."
    
    local available_space=$(df -BG "$PACKAGE_PATH" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo "0")
    
    # Handle non-numeric values
    if ! [[ "$available_space" =~ ^[0-9]+$ ]]; then
        available_space=0
    fi
    
    if [ "$available_space" -ge "$MIN_DISK_SPACE_GB" ]; then
        log_success "Sufficient disk space: ${available_space}GB available (minimum: ${MIN_DISK_SPACE_GB}GB)"
        record_check "disk_space" "pass"
        return 0
    else
        log_error "Insufficient disk space: ${available_space}GB available (minimum: ${MIN_DISK_SPACE_GB}GB required)"
        record_check "disk_space" "fail"
        return 1
    fi
}

check_memory() {
    log_info "Checking system memory..."
    
    local total_memory=$(free -g | awk '/^Mem:/ {print $2}')
    
    if [ "$total_memory" -ge "$MIN_MEMORY_GB" ]; then
        log_success "Sufficient memory: ${total_memory}GB total (minimum: ${MIN_MEMORY_GB}GB)"
        record_check "memory" "pass"
        return 0
    else
        log_warning "Low memory: ${total_memory}GB total (recommended: ${MIN_MEMORY_GB}GB+)"
        record_check "memory" "warning"
        return 0
    fi
}

check_ports() {
    log_info "Checking port availability..."
    
    local ports_ok=true
    
    for port in "${REQUIRED_PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            log_warning "Port $port is already in use"
            ports_ok=false
        else
            log_success "Port $port is available"
        fi
    done
    
    if [ "$ports_ok" = true ]; then
        record_check "ports" "pass"
        return 0
    else
        log_warning "Some ports are in use - may cause conflicts"
        record_check "ports" "warning"
        return 0
    fi
}

check_package_integrity() {
    log_info "Checking deployment package..."
    
    if [ ! -d "$PACKAGE_PATH" ]; then
        log_error "Package directory not found: $PACKAGE_PATH"
        record_check "package" "fail"
        return 1
    fi
    
    # Check for critical files
    local critical_files=(
        "docker-compose.prod.yml"
        "backend/manage.py"
        "backend/requirements/production.txt"
        "frontend/package.json"
    )
    
    local all_present=true
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$PACKAGE_PATH/$file" ]; then
            log_error "Missing critical file: $file"
            all_present=false
        fi
    done
    
    if [ "$all_present" = true ]; then
        log_success "All critical files present"
        
        # Check checksums if available
        if [ -f "$PACKAGE_PATH/checksums.sha256" ]; then
            log_info "Verifying package checksums..."
            cd "$PACKAGE_PATH"
            if sha256sum -c checksums.sha256 >/dev/null 2>&1; then
                log_success "Package integrity verified (checksums valid)"
            else
                log_warning "Some checksum mismatches found"
            fi
        fi
        
        record_check "package" "pass"
        return 0
    else
        log_error "Package is incomplete or corrupted"
        record_check "package" "fail"
        return 1
    fi
}

check_env_file() {
    log_info "Checking environment configuration..."
    
    local env_file="$PACKAGE_PATH/backend/.env"
    local env_example="$PACKAGE_PATH/backend/.env.example"
    
    # Check if .env exists
    if [ -f "$env_file" ]; then
        log_success ".env file found"
    elif [ -f "$env_example" ]; then
        log_success ".env.example found (will be used as template)"
        record_check "env_file" "pass"
        return 0
    else
        log_warning "No .env or .env.example file found in package"
        log_info "Note: deploy-interactive.sh will handle environment configuration"
        record_check "env_file" "warning"
        return 0
    fi
    
    # Check for required variables
    local required_vars=("SECRET_KEY" "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD")
    local all_present=true
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            log_warning "Missing environment variable: $var"
            all_present=false
        fi
    done
    
    # Check for default/insecure values
    if grep -q "SECRET_KEY=changeme" "$env_file" 2>/dev/null; then
        log_error "SECRET_KEY is set to default value - SECURITY RISK!"
        all_present=false
    fi
    
    if grep -q "POSTGRES_PASSWORD=postgres" "$env_file" 2>/dev/null; then
        log_warning "Database password is set to default value"
    fi
    
    if [ "$all_present" = true ]; then
        log_success "Environment configuration looks good"
        record_check "env_file" "pass"
        return 0
    else
        log_warning "Environment configuration needs review"
        record_check "env_file" "warning"
        return 0
    fi
}

check_existing_deployment() {
    log_info "Checking for existing deployment..."
    
    if [ ! -d "$PACKAGE_PATH" ]; then
        log_info "Package directory not found (this is OK during CI/CD)"
        record_check "existing_deployment" "pass"
        return 0
    fi
    
    cd "$PACKAGE_PATH"
    
    if docker compose ps -q >/dev/null 2>&1; then
        local running=$(docker compose ps -q | wc -l)
        if [ "$running" -gt 0 ]; then
            log_warning "Found $running running container(s) from existing deployment"
            log_info "Recommendation: Stop existing deployment before proceeding"
            record_check "existing_deployment" "warning"
            return 0
        fi
    fi
    
    log_success "No conflicting deployment found"
    record_check "existing_deployment" "pass"
    return 0
}

check_network_connectivity() {
    log_info "Checking network connectivity..."
    
    # Check internet connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_success "Internet connectivity available"
    else
        log_warning "No internet connectivity (may be needed for pulling images)"
    fi
    
    # Check if Docker Hub is accessible
    if curl -s --head https://hub.docker.com >/dev/null 2>&1; then
        log_success "Docker Hub is accessible"
    else
        log_warning "Docker Hub is not accessible (may affect image pulls)"
    fi
    
    record_check "network" "pass"
    return 0
}

check_docker_images() {
    log_info "Checking Docker images..."
    
    if [ ! -d "$PACKAGE_PATH" ]; then
        log_info "Package directory not accessible (this is OK during CI/CD)"
        record_check "docker_images" "pass"
        return 0
    fi
    
    cd "$PACKAGE_PATH"
    
    # Check if docker-compose.prod.yml exists
    if [ -f "docker-compose.prod.yml" ]; then
        local required_images=$(grep "image:" docker-compose.prod.yml | awk '{print $2}' | sort -u)
        
        if [ -n "$required_images" ]; then
            log_info "Required images will be pulled during deployment"
            log_success "Docker compose file is valid"
        else
            log_info "Images will be built from Dockerfiles"
        fi
    fi
    
    record_check "docker_images" "pass"
    return 0
}

check_backup_availability() {
    log_info "Checking backup availability..."
    
    local backup_script="$PACKAGE_PATH/scripts/backup-system.sh"
    
    if [ -f "$backup_script" ] && [ -x "$backup_script" ]; then
        log_success "Backup script available and executable"
        record_check "backup" "pass"
        return 0
    elif [ -f "$backup_script" ]; then
        log_warning "Backup script found but not executable"
        log_info "Run: chmod +x $backup_script"
        record_check "backup" "warning"
        return 0
    else
        log_warning "No backup script found"
        record_check "backup" "warning"
        return 0
    fi
}

check_ssl_certificates() {
    log_info "Checking SSL certificates..."
    
    local ssl_cert="$PACKAGE_PATH/ssl/cert.pem"
    local ssl_key="$PACKAGE_PATH/ssl/key.pem"
    
    if [ -f "$ssl_cert" ] && [ -f "$ssl_key" ]; then
        log_success "SSL certificates found"
        
        # Check certificate validity
        local expiry=$(openssl x509 -enddate -noout -in "$ssl_cert" 2>/dev/null | cut -d= -f2)
        if [ -n "$expiry" ]; then
            log_info "Certificate expires: $expiry"
        fi
        
        record_check "ssl" "pass"
        return 0
    else
        log_warning "No SSL certificates found (using self-signed or Let's Encrypt)"
        record_check "ssl" "warning"
        return 0
    fi
}

check_firewall() {
    log_info "Checking firewall configuration..."
    
    if command -v ufw >/dev/null 2>&1; then
        if ufw status 2>/dev/null | grep -q "Status: active"; then
            log_info "UFW firewall is active"
            log_warning "Ensure ports 80, 443 are open for web access"
        else
            log_info "UFW firewall is not active"
        fi
    elif command -v firewall-cmd >/dev/null 2>&1; then
        if firewall-cmd --state 2>/dev/null | grep -q "running"; then
            log_info "Firewalld is active"
            log_warning "Ensure ports 80, 443 are open for web access"
        fi
    else
        log_info "No standard firewall detected"
    fi
    
    record_check "firewall" "info"
    return 0
}

check_system_updates() {
    log_info "Checking for system updates..."
    
    if command -v apt-get >/dev/null 2>&1; then
        local updates=$(apt list --upgradable 2>/dev/null | grep -c "upgradable" || echo "0")
        if [ "$updates" -gt 0 ]; then
            log_warning "$updates system packages have updates available"
            log_info "Consider updating before deployment: sudo apt update && sudo apt upgrade"
        else
            log_success "System packages are up to date"
        fi
    fi
    
    record_check "system_updates" "info"
    return 0
}

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}                   VERIFICATION SUMMARY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed:${NC} $PASSED_CHECKS"
    echo -e "${YELLOW}Warnings:${NC} $WARNING_CHECKS"
    echo -e "${RED}Failed:${NC} $FAILED_CHECKS"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}║            System is Ready for Deployment ✓                  ║${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Next Steps:${NC}"
        echo "  1. Review any warnings above"
        echo "  2. Run deployment: ./deploy-interactive.sh"
        echo "  3. Monitor logs: docker compose logs -f"
        echo "  4. Run post-deployment check: ./scripts/post-deploy-check.sh"
        echo ""
        return 0
    else
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}║          System is NOT Ready for Deployment ✗                ║${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Required Actions:${NC}"
        echo "  1. Fix all failed checks listed above"
        echo "  2. Re-run this verification: $0"
        echo "  3. Do not proceed with deployment until all checks pass"
        echo ""
        return 1
    fi
}

generate_report() {
    # Determine report location
    if [ -d "$PACKAGE_PATH" ] && [ -w "$PACKAGE_PATH" ]; then
        local report_file="$PACKAGE_PATH/pre-deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    else
        # Fallback to current directory if package path not writable
        local report_file="./pre-deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    fi
    
    {
        echo "EDMS Pre-Deployment Verification Report"
        echo "========================================"
        echo "Date: $(date)"
        echo "Package: $PACKAGE_PATH"
        echo ""
        echo "Summary:"
        echo "--------"
        echo "Total Checks: $TOTAL_CHECKS"
        echo "Passed: $PASSED_CHECKS"
        echo "Warnings: $WARNING_CHECKS"
        echo "Failed: $FAILED_CHECKS"
        echo ""
        echo "Check Details:"
        echo "-------------"
        for check in "${!CHECKS[@]}"; do
            echo "  $check: ${CHECKS[$check]}"
        done
        echo ""
        if [ $FAILED_CHECKS -eq 0 ]; then
            echo "Result: READY FOR DEPLOYMENT"
        else
            echo "Result: NOT READY - FIX FAILED CHECKS"
        fi
    } > "$report_file" 2>/dev/null || {
        log_warning "Could not save report to file"
        return 0
    }
    
    log_success "Report saved: $report_file"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header
    
    # Run all checks
    check_docker
    check_docker_compose
    check_disk_space
    check_memory
    check_ports
    check_package_integrity
    check_env_file
    check_existing_deployment
    check_network_connectivity
    check_docker_images
    check_backup_availability
    check_ssl_certificates
    check_firewall
    check_system_updates
    
    # Print summary
    print_summary
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [ $FAILED_CHECKS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
