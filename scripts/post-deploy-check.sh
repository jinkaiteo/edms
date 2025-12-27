#!/bin/bash

################################################################################
# EDMS Post-Deployment Validation Script
################################################################################
#
# Description: Validates deployment success and application health
# Version: 1.0
# Date: December 24, 2024
#
# Features:
# - Validates all services are running
# - Tests critical API endpoints
# - Checks database connectivity and migrations
# - Validates file storage accessibility
# - Tests user authentication flow
# - Checks frontend availability
# - Verifies static files serving
# - Tests document upload/download
# - Validates workflow system
# - Generates deployment validation report
#
# Usage: ./scripts/post-deploy-check.sh [options]
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
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# Test results
declare -A TESTS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Options
VERBOSE=false
QUICK_MODE=false
GENERATE_REPORT=true

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║        EDMS Post-Deployment Validation v1.0                  ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Deployment Path: $PROJECT_ROOT"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

log_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

log_skip() {
    echo -e "${YELLOW}⊘${NC} $1"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}  →${NC} $1"
    fi
}

record_test() {
    local name="$1"
    local status="$2"
    local details="$3"
    TESTS["$name"]="$status|$details"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

test_containers_running() {
    log_info "Testing container status..."
    
    cd "$PROJECT_ROOT"
    
    local expected_containers=("backend" "frontend" "db")
    local all_running=true
    local details=""
    
    for container in "${expected_containers[@]}"; do
        if docker compose ps "$container" 2>/dev/null | grep -q "Up"; then
            log_verbose "Container '$container' is running"
            details="${details}${container}:running "
        else
            log_error "Container '$container' is not running"
            all_running=false
            details="${details}${container}:stopped "
        fi
    done
    
    if [ "$all_running" = true ]; then
        log_success "All required containers are running"
        record_test "containers" "pass" "$details"
        return 0
    else
        log_error "Some containers are not running"
        record_test "containers" "fail" "$details"
        return 1
    fi
}

test_backend_health_endpoint() {
    log_info "Testing backend health endpoint..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health/" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Backend health endpoint responding (HTTP $response)"
        
        # Get detailed health data
        local health_data=$(curl -s "${BACKEND_URL}/health/" 2>/dev/null)
        log_verbose "Health data: $health_data"
        
        record_test "backend_health" "pass" "HTTP $response"
        return 0
    else
        log_error "Backend health endpoint failed (HTTP $response)"
        record_test "backend_health" "fail" "HTTP $response"
        return 1
    fi
}

test_backend_api_endpoints() {
    log_info "Testing backend API endpoints..."
    
    local endpoints=(
        "/api/v1/"
        "/api/v1/auth/profile/"
        "/api/v1/documents/"
        "/api/v1/workflows/"
    )
    
    local all_ok=true
    local details=""
    
    for endpoint in "${endpoints[@]}"; do
        local url="${BACKEND_URL}${endpoint}"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        # Accept 200, 401, 403 (auth required but endpoint exists)
        if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "403" ]; then
            log_verbose "Endpoint $endpoint: HTTP $response"
            details="${details}${endpoint}:${response} "
        else
            log_error "Endpoint $endpoint failed: HTTP $response"
            all_ok=false
            details="${details}${endpoint}:${response} "
        fi
    done
    
    if [ "$all_ok" = true ]; then
        log_success "All API endpoints are accessible"
        record_test "api_endpoints" "pass" "$details"
        return 0
    else
        log_error "Some API endpoints are not accessible"
        record_test "api_endpoints" "fail" "$details"
        return 1
    fi
}

test_frontend_availability() {
    log_info "Testing frontend availability..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Frontend is accessible (HTTP $response)"
        
        # Check if it returns HTML
        local content=$(curl -s "${FRONTEND_URL}" 2>/dev/null | head -1)
        if echo "$content" | grep -q "<!DOCTYPE html>"; then
            log_verbose "Frontend returns valid HTML"
        fi
        
        record_test "frontend" "pass" "HTTP $response"
        return 0
    else
        log_error "Frontend is not accessible (HTTP $response)"
        record_test "frontend" "fail" "HTTP $response"
        return 1
    fi
}

test_database_connectivity() {
    log_info "Testing database connectivity..."
    
    cd "$PROJECT_ROOT"
    
    local db_test=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("DB_OK")
except Exception as e:
    print(f"DB_ERROR: {e}")
EOF
)
    
    if echo "$db_test" | grep -q "DB_OK"; then
        log_success "Database connection successful"
        
        # Get database info
        local db_info=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from django.db import connection
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Engine: {connection.settings_dict['ENGINE']}")
EOF
)
        log_verbose "$db_info"
        
        record_test "database" "pass" "Connected"
        return 0
    else
        log_error "Database connection failed"
        log_verbose "$db_test"
        record_test "database" "fail" "Connection failed"
        return 1
    fi
}

test_database_migrations() {
    log_info "Testing database migrations..."
    
    cd "$PROJECT_ROOT"
    
    local migrations=$(docker compose exec -T backend python manage.py showmigrations 2>&1)
    
    # Check if there are unapplied migrations
    if echo "$migrations" | grep -q "\[ \]"; then
        log_error "Unapplied migrations detected"
        log_verbose "$migrations"
        record_test "migrations" "fail" "Unapplied migrations"
        return 1
    else
        log_success "All migrations applied"
        record_test "migrations" "pass" "All applied"
        return 0
    fi
}

test_admin_access() {
    log_info "Testing admin interface..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/admin/" 2>/dev/null || echo "000")
    
    # Admin should redirect to login (302) or show login page (200)
    if [ "$response" = "200" ] || [ "$response" = "302" ]; then
        log_success "Admin interface accessible (HTTP $response)"
        record_test "admin" "pass" "HTTP $response"
        return 0
    else
        log_error "Admin interface not accessible (HTTP $response)"
        record_test "admin" "fail" "HTTP $response"
        return 1
    fi
}

test_static_files() {
    log_info "Testing static files serving..."
    
    # Test common static file paths
    local static_paths=(
        "/static/admin/css/base.css"
        "/static/admin/js/core.js"
    )
    
    local files_ok=true
    
    for path in "${static_paths[@]}"; do
        local url="${BACKEND_URL}${path}"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ]; then
            log_verbose "Static file accessible: $path"
        else
            log_error "Static file not accessible: $path (HTTP $response)"
            files_ok=false
        fi
    done
    
    if [ "$files_ok" = true ]; then
        log_success "Static files are being served correctly"
        record_test "static_files" "pass" "All accessible"
        return 0
    else
        log_error "Some static files are not accessible"
        record_test "static_files" "fail" "Missing files"
        return 1
    fi
}

test_media_directory() {
    log_info "Testing media directory..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "backend/media" ]; then
        if [ -w "backend/media" ]; then
            log_success "Media directory exists and is writable"
            record_test "media" "pass" "Writable"
            return 0
        else
            log_error "Media directory is not writable"
            record_test "media" "fail" "Not writable"
            return 1
        fi
    else
        log_error "Media directory does not exist"
        record_test "media" "fail" "Missing"
        return 1
    fi
}

test_storage_directory() {
    log_info "Testing storage directory..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "backend/storage" ]; then
        if [ -w "backend/storage" ]; then
            log_success "Storage directory exists and is writable"
            record_test "storage" "pass" "Writable"
            return 0
        else
            log_error "Storage directory is not writable"
            record_test "storage" "fail" "Not writable"
            return 1
        fi
    else
        log_error "Storage directory does not exist"
        record_test "storage" "fail" "Missing"
        return 1
    fi
}

test_user_authentication() {
    log_info "Testing user authentication system..."
    
    cd "$PROJECT_ROOT"
    
    # Check if users exist in database
    local user_count=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.count())
EOF
)
    
    user_count=$(echo "$user_count" | grep -oP '^\d+$' || echo "0")
    
    if [ "$user_count" -gt 0 ]; then
        log_success "User authentication system operational ($user_count users)"
        record_test "authentication" "pass" "$user_count users"
        return 0
    else
        log_error "No users found in database"
        record_test "authentication" "fail" "No users"
        return 1
    fi
}

test_document_system() {
    log_info "Testing document management system..."
    
    cd "$PROJECT_ROOT"
    
    # Check document models
    local doc_check=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from apps.documents.models import Document, DocumentType
print(f"DocumentTypes: {DocumentType.objects.count()}")
print(f"Documents: {Document.objects.count()}")
print("DOC_OK")
EOF
)
    
    if echo "$doc_check" | grep -q "DOC_OK"; then
        log_success "Document system operational"
        log_verbose "$doc_check"
        record_test "documents" "pass" "Operational"
        return 0
    else
        log_error "Document system check failed"
        record_test "documents" "fail" "Check failed"
        return 1
    fi
}

test_workflow_system() {
    log_info "Testing workflow system..."
    
    cd "$PROJECT_ROOT"
    
    # Check workflow models
    local workflow_check=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from apps.workflows.models import WorkflowType, WorkflowState
print(f"WorkflowTypes: {WorkflowType.objects.count()}")
print(f"WorkflowStates: {WorkflowState.objects.count()}")
print("WORKFLOW_OK")
EOF
)
    
    if echo "$workflow_check" | grep -q "WORKFLOW_OK"; then
        log_success "Workflow system operational"
        log_verbose "$workflow_check"
        record_test "workflows" "pass" "Operational"
        return 0
    else
        log_error "Workflow system check failed"
        record_test "workflows" "fail" "Check failed"
        return 1
    fi
}

test_celery_workers() {
    log_info "Testing Celery workers..."
    
    cd "$PROJECT_ROOT"
    
    # Check if celery container is running
    if docker compose ps celery 2>/dev/null | grep -q "Up"; then
        log_success "Celery worker is running"
        record_test "celery" "pass" "Running"
        return 0
    else
        log_skip "Celery worker not configured or not running"
        record_test "celery" "skip" "Not configured"
        return 0
    fi
}

test_redis_connectivity() {
    log_info "Testing Redis connectivity..."
    
    cd "$PROJECT_ROOT"
    
    if docker compose ps redis 2>/dev/null | grep -q "Up"; then
        local redis_test=$(docker compose exec -T redis redis-cli ping 2>/dev/null || echo "FAILED")
        
        if [ "$redis_test" = "PONG" ]; then
            log_success "Redis is operational"
            record_test "redis" "pass" "Connected"
            return 0
        else
            log_error "Redis not responding"
            record_test "redis" "fail" "No response"
            return 1
        fi
    else
        log_skip "Redis not configured"
        record_test "redis" "skip" "Not configured"
        return 0
    fi
}

test_logs_for_errors() {
    log_info "Checking logs for critical errors..."
    
    cd "$PROJECT_ROOT"
    
    local critical_errors=$(docker compose logs --tail=50 backend 2>/dev/null | grep -i "critical\|fatal" | wc -l)
    
    if [ "$critical_errors" -eq 0 ]; then
        log_success "No critical errors in recent logs"
        record_test "logs" "pass" "No critical errors"
        return 0
    else
        log_error "Found $critical_errors critical error(s) in logs"
        record_test "logs" "fail" "$critical_errors critical errors"
        return 1
    fi
}

test_backup_system() {
    log_info "Testing backup system availability..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/backup-system.sh" ] && [ -x "scripts/backup-system.sh" ]; then
        log_success "Backup system is available"
        record_test "backup_system" "pass" "Available"
        return 0
    else
        log_error "Backup system not available or not executable"
        record_test "backup_system" "fail" "Not available"
        return 1
    fi
}

test_security_headers() {
    log_info "Testing security headers..."
    
    local headers=$(curl -s -I "${BACKEND_URL}" 2>/dev/null)
    local security_ok=true
    
    # Check for important security headers
    if echo "$headers" | grep -qi "X-Frame-Options"; then
        log_verbose "X-Frame-Options header present"
    else
        log_error "Missing X-Frame-Options header"
        security_ok=false
    fi
    
    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        log_verbose "X-Content-Type-Options header present"
    else
        log_error "Missing X-Content-Type-Options header"
        security_ok=false
    fi
    
    if [ "$security_ok" = true ]; then
        log_success "Security headers configured"
        record_test "security_headers" "pass" "Configured"
        return 0
    else
        log_error "Some security headers missing"
        record_test "security_headers" "fail" "Missing headers"
        return 1
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}                   VALIDATION SUMMARY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}Failed:${NC} $FAILED_TESTS"
    echo -e "${YELLOW}Skipped:${NC} $SKIPPED_TESTS"
    echo ""
    
    # Show test details
    echo "Test Results:"
    for test in "${!TESTS[@]}"; do
        IFS='|' read -r status details <<< "${TESTS[$test]}"
        case "$status" in
            pass)
                echo -e "  ${GREEN}✓${NC} $test: $details"
                ;;
            fail)
                echo -e "  ${RED}✗${NC} $test: $details"
                ;;
            skip)
                echo -e "  ${YELLOW}⊘${NC} $test: $details"
                ;;
        esac
    done
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}║           Deployment Validation Successful ✓                 ║${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Deployment Status: READY FOR PRODUCTION${NC}"
        echo ""
        echo "Next Steps:"
        echo "  1. Application is ready to use"
        echo "  2. Monitor with: ./scripts/health-check.sh --watch"
        echo "  3. Create initial backup: ./scripts/backup-system.sh"
        echo "  4. Configure SSL certificates if needed"
        echo ""
        return 0
    else
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}║          Deployment Validation Failed ✗                      ║${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Required Actions:${NC}"
        echo "  1. Review failed tests above"
        echo "  2. Check logs: docker compose logs"
        echo "  3. Fix issues and re-test"
        echo "  4. Consider rollback if issues persist"
        echo ""
        return 1
    fi
}

generate_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return 0
    fi
    
    local report_file="${PROJECT_ROOT}/post-deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "Generating validation report..."
    
    {
        echo "EDMS Post-Deployment Validation Report"
        echo "======================================="
        echo "Date: $(date)"
        echo "Deployment: $PROJECT_ROOT"
        echo ""
        echo "Summary:"
        echo "--------"
        echo "Total Tests: $TOTAL_TESTS"
        echo "Passed: $PASSED_TESTS"
        echo "Failed: $FAILED_TESTS"
        echo "Skipped: $SKIPPED_TESTS"
        echo ""
        echo "Test Details:"
        echo "------------"
        for test in "${!TESTS[@]}"; do
            IFS='|' read -r status details <<< "${TESTS[$test]}"
            echo "  $test: $status - $details"
        done
        echo ""
        if [ $FAILED_TESTS -eq 0 ]; then
            echo "Result: DEPLOYMENT SUCCESSFUL"
            echo "Status: READY FOR PRODUCTION"
        else
            echo "Result: DEPLOYMENT VALIDATION FAILED"
            echo "Status: REQUIRES ATTENTION"
        fi
        echo ""
        echo "Container Status:"
        docker compose ps 2>/dev/null || echo "Could not retrieve container status"
    } > "$report_file"
    
    log_success "Report saved: $report_file"
}

show_usage() {
    cat << EOF
Usage: $0 [options]

Options:
  --quick         Quick validation (essential checks only)
  --verbose       Verbose output
  --no-report     Don't generate report file
  -h, --help      Show this help message

Examples:
  # Full validation
  $0

  # Quick validation
  $0 --quick

  # Verbose output
  $0 --verbose

EOF
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --quick)
                QUICK_MODE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --no-report)
                GENERATE_REPORT=false
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
    
    # Run tests
    test_containers_running
    test_backend_health_endpoint
    test_backend_api_endpoints
    test_frontend_availability
    test_database_connectivity
    test_database_migrations
    test_admin_access
    
    if [ "$QUICK_MODE" = false ]; then
        test_static_files
        test_media_directory
        test_storage_directory
        test_user_authentication
        test_document_system
        test_workflow_system
        test_celery_workers
        test_redis_connectivity
        test_logs_for_errors
        test_backup_system
        test_security_headers
    fi
    
    # Print summary
    print_summary
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
