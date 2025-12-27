#!/bin/bash

################################################################################
# EDMS Health Check Script
################################################################################
#
# Description: Comprehensive health monitoring for EDMS application
# Version: 1.0
# Date: December 24, 2024
#
# Features:
# - Checks all Docker containers status
# - Validates database connectivity
# - Tests API endpoints
# - Verifies file system health
# - Checks resource usage (CPU, memory, disk)
# - Monitors logs for errors
# - Generates detailed health report
#
# Usage: ./scripts/health-check.sh [options]
#
# Options:
#   --full          Run complete health check (default)
#   --quick         Quick health check (containers and API only)
#   --watch         Continuous monitoring mode
#   --report        Generate HTML report
#   --alert         Exit with error code if unhealthy
#   --verbose       Verbose output
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
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
HEALTH_ENDPOINT="${BACKEND_URL}/health/"
API_ENDPOINT="${BACKEND_URL}/api/v1/auth/profile/"

# Options
MODE="full"
WATCH_MODE=false
GENERATE_REPORT=false
ALERT_MODE=false
VERBOSE=false
WATCH_INTERVAL=30

# Health status
OVERALL_STATUS="healthy"
declare -A CHECKS
declare -A ISSUES

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║           EDMS Health Check & Monitoring v1.0                ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Mode: ${MODE}"
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

record_check() {
    local check_name="$1"
    local status="$2"
    local message="$3"
    
    CHECKS["$check_name"]="$status"
    
    if [ "$status" != "pass" ]; then
        ISSUES["$check_name"]="$message"
        OVERALL_STATUS="unhealthy"
    fi
}

check_docker_installed() {
    log_info "Checking Docker installation..."
    
    if command -v docker >/dev/null 2>&1; then
        local version=$(docker --version)
        log_success "Docker installed: $version"
        log_verbose "$(docker info 2>&1 | grep 'Server Version')"
        record_check "docker_installed" "pass" ""
        return 0
    else
        log_error "Docker not installed"
        record_check "docker_installed" "fail" "Docker is not installed"
        return 1
    fi
}

check_docker_compose() {
    log_info "Checking Docker Compose..."
    
    if command -v docker compose >/dev/null 2>&1; then
        local version=$(docker compose version)
        log_success "Docker Compose installed: $version"
        record_check "docker_compose" "pass" ""
        return 0
    elif command -v docker-compose >/dev/null 2>&1; then
        local version=$(docker-compose --version)
        log_success "Docker Compose installed: $version"
        record_check "docker_compose" "pass" ""
        return 0
    else
        log_error "Docker Compose not installed"
        record_check "docker_compose" "fail" "Docker Compose is not installed"
        return 1
    fi
}

check_containers() {
    log_info "Checking container status..."
    
    cd "${PROJECT_ROOT}"
    
    # Get expected containers
    local expected_containers=("backend" "frontend" "db" "redis")
    local all_healthy=true
    
    for container in "${expected_containers[@]}"; do
        log_verbose "Checking container: $container"
        
        # Check if container exists
        if docker compose ps -q "$container" >/dev/null 2>&1; then
            local status=$(docker compose ps "$container" --format json 2>/dev/null | jq -r '.State' 2>/dev/null || echo "unknown")
            
            if [ "$status" = "running" ]; then
                log_success "Container '$container' is running"
                
                # Check health status if available
                local health=$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose ps -q $container)" 2>/dev/null || echo "no-healthcheck")
                
                if [ "$health" != "no-healthcheck" ]; then
                    log_verbose "Health status: $health"
                    if [ "$health" != "healthy" ] && [ "$health" != "starting" ]; then
                        log_warning "Container '$container' health status: $health"
                        all_healthy=false
                    fi
                fi
            else
                log_error "Container '$container' is not running (status: $status)"
                all_healthy=false
            fi
        else
            log_warning "Container '$container' not found (may not be configured)"
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        record_check "containers" "pass" ""
        return 0
    else
        record_check "containers" "fail" "One or more containers are not running or healthy"
        return 1
    fi
}

check_backend_health() {
    log_info "Checking backend health endpoint..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Backend health endpoint responding (HTTP $response)"
        log_verbose "Endpoint: ${HEALTH_ENDPOINT}"
        
        # Get detailed health info
        local health_data=$(curl -s --max-time 5 "${HEALTH_ENDPOINT}" 2>/dev/null)
        if [ -n "$health_data" ]; then
            log_verbose "Health data: $health_data"
        fi
        
        record_check "backend_health" "pass" ""
        return 0
    else
        log_error "Backend health endpoint not responding (HTTP $response)"
        record_check "backend_health" "fail" "Backend health endpoint returned HTTP $response"
        return 1
    fi
}

check_backend_api() {
    log_info "Checking backend API..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${BACKEND_URL}/api/v1/" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "403" ]; then
        log_success "Backend API responding (HTTP $response)"
        log_verbose "API base: ${BACKEND_URL}/api/v1/"
        record_check "backend_api" "pass" ""
        return 0
    else
        log_error "Backend API not responding properly (HTTP $response)"
        record_check "backend_api" "fail" "Backend API returned HTTP $response"
        return 1
    fi
}

check_frontend() {
    log_info "Checking frontend..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${FRONTEND_URL}" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Frontend responding (HTTP $response)"
        log_verbose "URL: ${FRONTEND_URL}"
        record_check "frontend" "pass" ""
        return 0
    else
        log_error "Frontend not responding (HTTP $response)"
        record_check "frontend" "fail" "Frontend returned HTTP $response"
        return 1
    fi
}

check_database() {
    log_info "Checking database connectivity..."
    
    cd "${PROJECT_ROOT}"
    
    # Try to connect to database via Django shell
    local db_check=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("DB_CONNECTED")
except Exception as e:
    print(f"DB_ERROR: {e}")
EOF
)
    
    if echo "$db_check" | grep -q "DB_CONNECTED"; then
        log_success "Database connection successful"
        
        # Get database stats
        local db_stats=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1
from django.contrib.auth import get_user_model
from apps.documents.models import Document
User = get_user_model()
print(f"Users: {User.objects.count()}")
print(f"Documents: {Document.objects.count()}")
EOF
)
        log_verbose "$db_stats"
        
        record_check "database" "pass" ""
        return 0
    else
        log_error "Database connection failed"
        log_verbose "$db_check"
        record_check "database" "fail" "Cannot connect to database"
        return 1
    fi
}

check_redis() {
    log_info "Checking Redis connectivity..."
    
    cd "${PROJECT_ROOT}"
    
    if docker compose ps -q redis >/dev/null 2>&1; then
        local redis_check=$(docker compose exec -T redis redis-cli ping 2>/dev/null || echo "FAILED")
        
        if [ "$redis_check" = "PONG" ]; then
            log_success "Redis connection successful"
            
            # Get Redis info
            local redis_info=$(docker compose exec -T redis redis-cli INFO stats 2>/dev/null | grep -E "total_connections_received|total_commands_processed" || echo "")
            log_verbose "$redis_info"
            
            record_check "redis" "pass" ""
            return 0
        else
            log_error "Redis not responding"
            record_check "redis" "fail" "Redis connection failed"
            return 1
        fi
    else
        log_warning "Redis container not found (may not be configured)"
        record_check "redis" "warning" "Redis not configured"
        return 0
    fi
}

check_filesystem() {
    log_info "Checking filesystem health..."
    
    cd "${PROJECT_ROOT}"
    
    local all_ok=true
    
    # Check critical directories
    local dirs=("backend/storage" "backend/media" "backend/logs")
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            if [ -w "$dir" ]; then
                log_verbose "Directory '$dir' is writable"
            else
                log_error "Directory '$dir' is not writable"
                all_ok=false
            fi
        else
            log_warning "Directory '$dir' does not exist"
        fi
    done
    
    # Check disk space
    local disk_usage=$(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $5}' | sed 's/%//')
    log_verbose "Disk usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Disk usage critical: ${disk_usage}%"
        all_ok=false
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Disk usage high: ${disk_usage}%"
    fi
    
    if [ "$all_ok" = true ]; then
        record_check "filesystem" "pass" ""
        return 0
    else
        record_check "filesystem" "fail" "Filesystem issues detected"
        return 1
    fi
}

check_resources() {
    log_info "Checking resource usage..."
    
    cd "${PROJECT_ROOT}"
    
    # Get container stats
    local stats=$(docker compose ps -q 2>/dev/null | xargs docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "")
    
    if [ -n "$stats" ]; then
        log_success "Container resource usage:"
        echo "$stats" | while read line; do
            log_verbose "$line"
        done
        record_check "resources" "pass" ""
        return 0
    else
        log_warning "Could not retrieve resource usage"
        record_check "resources" "warning" "Resource stats unavailable"
        return 0
    fi
}

check_logs_for_errors() {
    log_info "Checking logs for recent errors..."
    
    cd "${PROJECT_ROOT}"
    
    local error_count=0
    
    # Check backend logs for errors in last 100 lines
    local backend_errors=$(docker compose logs --tail=100 backend 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    
    if [ "$backend_errors" -gt 0 ]; then
        log_warning "Found $backend_errors error entries in backend logs (last 100 lines)"
        log_verbose "Run 'docker compose logs backend | grep -i error' for details"
        error_count=$((error_count + backend_errors))
    else
        log_success "No errors found in recent backend logs"
    fi
    
    # Check frontend logs
    local frontend_errors=$(docker compose logs --tail=100 frontend 2>/dev/null | grep -i "error" | wc -l)
    
    if [ "$frontend_errors" -gt 0 ]; then
        log_warning "Found $frontend_errors error entries in frontend logs (last 100 lines)"
        error_count=$((error_count + frontend_errors))
    else
        log_success "No errors found in recent frontend logs"
    fi
    
    if [ "$error_count" -gt 10 ]; then
        record_check "logs" "fail" "High number of errors in logs ($error_count)"
        return 1
    elif [ "$error_count" -gt 0 ]; then
        record_check "logs" "warning" "Some errors found in logs ($error_count)"
        return 0
    else
        record_check "logs" "pass" ""
        return 0
    fi
}

run_quick_check() {
    echo -e "${CYAN}Running Quick Health Check...${NC}"
    echo ""
    
    check_containers
    check_backend_health
    check_backend_api
    check_frontend
}

run_full_check() {
    echo -e "${CYAN}Running Full Health Check...${NC}"
    echo ""
    
    check_docker_installed
    check_docker_compose
    check_containers
    check_backend_health
    check_backend_api
    check_frontend
    check_database
    check_redis
    check_filesystem
    check_resources
    check_logs_for_errors
}

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}                    HEALTH CHECK SUMMARY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local pass_count=0
    local fail_count=0
    local warning_count=0
    
    for check in "${!CHECKS[@]}"; do
        local status="${CHECKS[$check]}"
        case "$status" in
            pass)
                pass_count=$((pass_count + 1))
                echo -e "  ${GREEN}✓${NC} $check"
                ;;
            fail)
                fail_count=$((fail_count + 1))
                echo -e "  ${RED}✗${NC} $check: ${ISSUES[$check]}"
                ;;
            warning)
                warning_count=$((warning_count + 1))
                echo -e "  ${YELLOW}⚠${NC} $check: ${ISSUES[$check]}"
                ;;
        esac
    done
    
    echo ""
    echo "Results: $pass_count passed, $fail_count failed, $warning_count warnings"
    echo ""
    
    if [ "$OVERALL_STATUS" = "healthy" ]; then
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}║                  System Status: HEALTHY ✓                    ║${NC}"
        echo -e "${GREEN}║                                                               ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    else
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}║                 System Status: UNHEALTHY ✗                   ║${NC}"
        echo -e "${RED}║                                                               ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Issues detected:"
        for check in "${!ISSUES[@]}"; do
            echo "  - $check: ${ISSUES[$check]}"
        done
    fi
    echo ""
}

generate_html_report() {
    local report_file="${PROJECT_ROOT}/health-report-$(date +%Y%m%d-%H%M%S).html"
    
    log_info "Generating HTML report..."
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>EDMS Health Check Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        .status-healthy { color: #27ae60; font-weight: bold; }
        .status-unhealthy { color: #e74c3c; font-weight: bold; }
        .check-pass { color: #27ae60; }
        .check-fail { color: #e74c3c; }
        .check-warning { color: #f39c12; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        .timestamp { color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>EDMS Health Check Report</h1>
        <p class="timestamp">Generated: $(date '+%Y-%m-%d %H:%M:%S')</p>
        <p>Overall Status: <span class="status-${OVERALL_STATUS}">${OVERALL_STATUS^^}</span></p>
        
        <h2>Check Results</h2>
        <table>
            <tr>
                <th>Check</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
EOF
    
    for check in "${!CHECKS[@]}"; do
        local status="${CHECKS[$check]}"
        local message="${ISSUES[$check]:-OK}"
        echo "            <tr>" >> "$report_file"
        echo "                <td>$check</td>" >> "$report_file"
        echo "                <td class='check-$status'>$status</td>" >> "$report_file"
        echo "                <td>$message</td>" >> "$report_file"
        echo "            </tr>" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF
        </table>
    </div>
</body>
</html>
EOF
    
    log_success "HTML report generated: $report_file"
}

watch_mode() {
    log_info "Starting continuous monitoring (interval: ${WATCH_INTERVAL}s)"
    log_info "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        clear
        print_header
        
        if [ "$MODE" = "quick" ]; then
            run_quick_check
        else
            run_full_check
        fi
        
        print_summary
        
        echo "Next check in ${WATCH_INTERVAL} seconds..."
        sleep "$WATCH_INTERVAL"
    done
}

show_usage() {
    cat << EOF
Usage: $0 [options]

Options:
  --full          Run complete health check (default)
  --quick         Quick health check (containers and API only)
  --watch         Continuous monitoring mode
  --interval SEC  Watch mode interval in seconds (default: 30)
  --report        Generate HTML report
  --alert         Exit with error code if unhealthy
  --verbose       Verbose output
  -h, --help      Show this help message

Examples:
  # Full health check
  $0

  # Quick health check
  $0 --quick

  # Continuous monitoring
  $0 --watch

  # Generate report
  $0 --report

  # Alert mode (for CI/CD)
  $0 --alert

EOF
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --full)
                MODE="full"
                shift
                ;;
            --quick)
                MODE="quick"
                shift
                ;;
            --watch)
                WATCH_MODE=true
                shift
                ;;
            --interval)
                WATCH_INTERVAL="$2"
                shift 2
                ;;
            --report)
                GENERATE_REPORT=true
                shift
                ;;
            --alert)
                ALERT_MODE=true
                shift
                ;;
            --verbose)
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
    
    # Run health checks
    if [ "$WATCH_MODE" = true ]; then
        watch_mode
    else
        print_header
        
        if [ "$MODE" = "quick" ]; then
            run_quick_check
        else
            run_full_check
        fi
        
        print_summary
        
        if [ "$GENERATE_REPORT" = true ]; then
            generate_html_report
        fi
        
        # Exit with error code if unhealthy and alert mode
        if [ "$ALERT_MODE" = true ] && [ "$OVERALL_STATUS" != "healthy" ]; then
            exit 1
        fi
    fi
}

# Run main function
main "$@"
