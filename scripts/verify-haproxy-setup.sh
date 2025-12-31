#!/bin/bash
#
# HAProxy Setup Verification Script
# Purpose: Verify that HAProxy and EDMS services are working correctly
#
# Usage: bash scripts/verify-haproxy-setup.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
STAGING_IP="172.28.1.148"
TESTS_PASSED=0
TESTS_FAILED=0

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

test_endpoint() {
    local description=$1
    local url=$2
    local expected_status=${3:-200}
    
    print_info "Testing: $description"
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status_code" = "$expected_status" ]; then
        print_success "$description - Status: $status_code"
    else
        print_failure "$description - Expected: $expected_status, Got: $status_code"
    fi
}

print_header "EDMS HAProxy Setup Verification"
echo ""

# Test 1: HAProxy Service
print_header "1. HAProxy Service Status"
if systemctl is-active --quiet haproxy 2>/dev/null; then
    print_success "HAProxy service is running"
else
    print_failure "HAProxy service is not running"
    print_info "Start with: sudo systemctl start haproxy"
fi

# Test 2: HAProxy Listening Ports
print_header "2. HAProxy Port Bindings"

if netstat -tuln 2>/dev/null | grep -q ":80 " || ss -tuln 2>/dev/null | grep -q ":80 "; then
    print_success "HAProxy listening on port 80"
else
    print_failure "HAProxy not listening on port 80"
fi

if netstat -tuln 2>/dev/null | grep -q ":8404 " || ss -tuln 2>/dev/null | grep -q ":8404 "; then
    print_success "HAProxy stats available on port 8404"
else
    print_failure "HAProxy stats not available on port 8404"
fi

# Test 3: Docker Services
print_header "3. Docker Container Status"

if docker compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "Up"; then
    print_success "Docker containers are running"
    
    # Check individual services
    if docker compose -f docker-compose.prod.yml ps | grep backend | grep -q "Up"; then
        print_success "Backend container is up"
    else
        print_failure "Backend container is not running"
    fi
    
    if docker compose -f docker-compose.prod.yml ps | grep frontend | grep -q "Up"; then
        print_success "Frontend container is up"
    else
        print_failure "Frontend container is not running"
    fi
    
    if docker compose -f docker-compose.prod.yml ps | grep db | grep -q "Up"; then
        print_success "Database container is up"
    else
        print_failure "Database container is not running"
    fi
else
    print_failure "Docker containers are not running"
    print_info "Start with: docker compose -f docker-compose.prod.yml up -d"
fi

# Test 4: Direct Container Access
print_header "4. Direct Container Health Checks"

test_endpoint "Backend direct access" "http://localhost:8001/health"
test_endpoint "Frontend direct access" "http://localhost:3001/health"

# Test 5: HAProxy Routing
print_header "5. HAProxy Routing Tests"

test_endpoint "HAProxy health check" "http://localhost/haproxy-health"
test_endpoint "Frontend through HAProxy" "http://localhost/"
test_endpoint "Backend API through HAProxy" "http://localhost/api/v1/"
test_endpoint "Backend health through HAProxy" "http://localhost/health"

# Test 6: External Access
print_header "6. External Access Tests"

print_info "Testing external access (using $STAGING_IP)..."
test_endpoint "External frontend access" "http://$STAGING_IP/"
test_endpoint "External API access" "http://$STAGING_IP/api/v1/"
test_endpoint "External backend health" "http://$STAGING_IP/health"

# Test 7: Configuration Verification
print_header "7. Configuration Verification"

# Check REACT_APP_API_URL
print_info "Checking frontend configuration..."
if docker compose -f docker-compose.prod.yml exec -T frontend env 2>/dev/null | grep -q "REACT_APP_API_URL=/api/v1"; then
    print_success "Frontend using relative API URL"
elif docker compose -f docker-compose.prod.yml exec -T frontend env 2>/dev/null | grep "REACT_APP_API_URL" | grep -q "localhost"; then
    print_failure "Frontend still using localhost URL (needs rebuild)"
    print_info "Run: bash scripts/update-docker-for-haproxy.sh"
else
    print_info "Could not verify frontend configuration"
fi

# Check backend ALLOWED_HOSTS
print_info "Checking backend configuration..."
if grep -q "ALLOWED_HOSTS.*172.28.1.148" .env 2>/dev/null; then
    print_success "Backend ALLOWED_HOSTS includes staging IP"
else
    print_failure "Backend ALLOWED_HOSTS may need updating"
fi

# Test 8: API Authentication Endpoint
print_header "8. API Authentication Test"

print_info "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://localhost/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' 2>/dev/null || echo "000")

if [ "$LOGIN_RESPONSE" = "400" ] || [ "$LOGIN_RESPONSE" = "401" ]; then
    print_success "Login endpoint is accessible (returned $LOGIN_RESPONSE - expected for invalid credentials)"
elif [ "$LOGIN_RESPONSE" = "200" ]; then
    print_success "Login endpoint is accessible (returned 200)"
else
    print_failure "Login endpoint returned unexpected status: $LOGIN_RESPONSE"
fi

# Test 9: HAProxy Stats Page
print_header "9. HAProxy Statistics Page"

STATS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -u admin:admin_changeme \
    http://localhost:8404/stats 2>/dev/null || echo "000")

if [ "$STATS_STATUS" = "200" ]; then
    print_success "HAProxy stats page is accessible"
    print_info "Access at: http://$STAGING_IP:8404/stats (admin/admin_changeme)"
else
    print_failure "HAProxy stats page not accessible"
fi

# Test 10: Response Headers
print_header "10. Security Headers Check"

print_info "Checking security headers..."
HEADERS=$(curl -s -I http://localhost/ 2>/dev/null)

if echo "$HEADERS" | grep -qi "X-Frame-Options"; then
    print_success "X-Frame-Options header present"
else
    print_failure "X-Frame-Options header missing"
fi

if echo "$HEADERS" | grep -qi "X-Content-Type-Options"; then
    print_success "X-Content-Type-Options header present"
else
    print_failure "X-Content-Type-Options header missing"
fi

# Summary
print_header "Verification Summary"
echo ""
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "All tests passed! HAProxy setup is working correctly."
    echo ""
    echo "Access your application at:"
    echo "  🌐 Main App: http://$STAGING_IP"
    echo "  📊 Stats: http://$STAGING_IP:8404/stats (admin/admin_changeme)"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the output above for details.${NC}"
    echo ""
    echo "Common issues:"
    echo "  1. HAProxy not running: sudo systemctl start haproxy"
    echo "  2. Docker containers not running: docker compose -f docker-compose.prod.yml up -d"
    echo "  3. Frontend needs rebuild: bash scripts/update-docker-for-haproxy.sh"
    echo "  4. Firewall blocking ports: sudo ufw status"
    echo ""
    exit 1
fi
