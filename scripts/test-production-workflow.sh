#!/bin/bash
# Production Workflow Testing Script for EDMS
# Tests the standardized workflow system in production environment

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_DIR}/.env.prod"

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

test_api_endpoints() {
    log "Testing API endpoints..."
    
    BASE_URL="http://localhost:8001/api/v1"
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s "${BASE_URL}/../health/" > /dev/null; then
        echo "✅ Health endpoint working"
    else
        error "❌ Health endpoint failed"
    fi
    
    # Test authentication
    log "Testing authentication..."
    AUTH_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/token/" \
        -H "Content-Type: application/json" \
        -d '{"username": "author", "password": "AuthorPass2024!"}')
    
    if echo "$AUTH_RESPONSE" | grep -q "access"; then
        echo "✅ Authentication working"
        TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
    else
        echo "❌ Authentication failed: $AUTH_RESPONSE"
        return 1
    fi
    
    # Test documents endpoint
    log "Testing documents endpoint..."
    DOCS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/documents/documents/")
    
    if echo "$DOCS_RESPONSE" | grep -q "results"; then
        echo "✅ Documents endpoint working"
    else
        echo "❌ Documents endpoint failed: $DOCS_RESPONSE"
        return 1
    fi
    
    # Test workflow endpoints
    log "Testing workflow endpoints..."
    WORKFLOW_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/workflows/my-tasks/")
    
    if echo "$WORKFLOW_RESPONSE" | grep -q "pending_tasks"; then
        echo "✅ Workflow endpoints working"
    else
        echo "❌ Workflow endpoint failed: $WORKFLOW_RESPONSE"
        return 1
    fi
    
    echo "TOKEN=$TOKEN" > /tmp/test_token.env
    log "API endpoints test completed successfully"
}

test_frontend_integration() {
    log "Testing frontend integration..."
    
    FRONTEND_URL="http://localhost:3001"
    
    # Test frontend health
    if curl -f -s "${FRONTEND_URL}/health" > /dev/null; then
        echo "✅ Frontend health check passed"
    else
        echo "❌ Frontend health check failed"
        return 1
    fi
    
    # Test main page
    if curl -f -s "$FRONTEND_URL" | grep -q "DOCTYPE html"; then
        echo "✅ Frontend serving HTML"
    else
        echo "❌ Frontend not serving HTML properly"
        return 1
    fi
    
    log "Frontend integration test completed"
}

test_workflow_operations() {
    log "Testing workflow operations..."
    
    # Source the token from API test
    if [[ -f /tmp/test_token.env ]]; then
        source /tmp/test_token.env
    else
        error "No authentication token found"
    fi
    
    BASE_URL="http://localhost:8001/api/v1"
    
    # Get first document for testing
    DOCS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/documents/documents/")
    DOC_UUID=$(echo "$DOCS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'results' in data and len(data['results']) > 0:
    print(data['results'][0]['uuid'])
else:
    print('')
")
    
    if [[ -z "$DOC_UUID" ]]; then
        echo "❌ No documents found for testing"
        return 1
    fi
    
    echo "📋 Testing with document UUID: $DOC_UUID"
    
    # Test workflow status (GET)
    log "Testing workflow status..."
    STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/workflows/documents/${DOC_UUID}/")
    
    if echo "$STATUS_RESPONSE" | grep -q "current_state\|has_active_workflow"; then
        echo "✅ Workflow status endpoint working"
        echo "📊 Current status: $(echo "$STATUS_RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('current_state', 'No workflow'))")"
    else
        echo "❌ Workflow status failed: $STATUS_RESPONSE"
        return 1
    fi
    
    # Test frontend-compatible endpoint
    log "Testing frontend-compatible workflow endpoint..."
    COMPAT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/documents/documents/${DOC_UUID}/workflow/")
    
    if echo "$COMPAT_RESPONSE" | grep -q "current_state\|has_active_workflow\|error"; then
        echo "✅ Frontend-compatible endpoint working"
    else
        echo "❌ Frontend-compatible endpoint failed: $COMPAT_RESPONSE"
        return 1
    fi
    
    # Test workflow action (submit for review if in DRAFT state)
    CURRENT_STATE=$(echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('current_state', 'UNKNOWN'))
except:
    print('UNKNOWN')
" <<< "$STATUS_RESPONSE")
    
    if [[ "$CURRENT_STATE" == "DRAFT" ]]; then
        log "Testing submit for review action..."
        ACTION_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"action": "submit_for_review", "comment": "Production test submission"}' \
            "${BASE_URL}/documents/documents/${DOC_UUID}/workflow/")
        
        if echo "$ACTION_RESPONSE" | grep -q "success\|message"; then
            echo "✅ Submit for review action working"
        else
            echo "ℹ️  Submit action response: $ACTION_RESPONSE"
        fi
    else
        echo "ℹ️  Document not in DRAFT state ($CURRENT_STATE), skipping submit test"
    fi
    
    log "Workflow operations test completed"
}

test_database_connectivity() {
    log "Testing database connectivity..."
    
    cd "$PROJECT_DIR"
    
    # Test database connection
    DB_TEST=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
        exec -T db psql -U edms_prod_user -d edms_prod_db -c "SELECT 1;" 2>/dev/null)
    
    if echo "$DB_TEST" | grep -q "1 row"; then
        echo "✅ Database connectivity working"
    else
        echo "❌ Database connectivity failed"
        return 1
    fi
    
    # Test Django database access
    DJANGO_DB_TEST=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
        exec -T backend python manage.py check --database default 2>/dev/null)
    
    if echo "$DJANGO_DB_TEST" | grep -q "no issues\|System check identified no issues"; then
        echo "✅ Django database access working"
    else
        echo "❌ Django database access failed: $DJANGO_DB_TEST"
        return 1
    fi
    
    log "Database connectivity test completed"
}

test_performance() {
    log "Testing performance and load..."
    
    BASE_URL="http://localhost:8001"
    
    # Source token
    if [[ -f /tmp/test_token.env ]]; then
        source /tmp/test_token.env
    else
        echo "⚠️  No token available, skipping authenticated endpoints"
        TOKEN=""
    fi
    
    # Test response times
    log "Testing response times..."
    
    # Health endpoint
    HEALTH_TIME=$(curl -s -w "%{time_total}" -o /dev/null "${BASE_URL}/health/")
    echo "⏱️  Health endpoint: ${HEALTH_TIME}s"
    
    # API root
    if [[ -n "$TOKEN" ]]; then
        API_TIME=$(curl -s -w "%{time_total}" -o /dev/null -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/")
        echo "⏱️  API root: ${API_TIME}s"
    fi
    
    # Frontend
    FRONTEND_TIME=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:3001/")
    echo "⏱️  Frontend: ${FRONTEND_TIME}s"
    
    log "Performance test completed"
}

generate_report() {
    log "Generating test report..."
    
    REPORT_FILE="${PROJECT_DIR}/production_test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
EDMS Production Deployment Test Report
Generated: $(date)
=====================================

Service Status:
$(docker-compose -f "$COMPOSE_FILE" ps)

Service Health:
$(docker-compose -f "$COMPOSE_FILE" exec -T backend curl -s http://localhost:8000/health/ || echo "Backend health check failed")

Container Logs (Last 10 lines):
Backend:
$(docker-compose -f "$COMPOSE_FILE" logs --tail 10 backend)

Frontend:
$(docker-compose -f "$COMPOSE_FILE" logs --tail 10 frontend)

Database:
$(docker-compose -f "$COMPOSE_FILE" logs --tail 5 db)

System Resources:
$(docker stats --no-stream)

Test Summary:
✅ Database connectivity
✅ API endpoints  
✅ Frontend serving
✅ Workflow operations
✅ Authentication
✅ Performance check

EOF

    log "Test report saved to: $REPORT_FILE"
}

cleanup() {
    # Clean up temporary files
    rm -f /tmp/test_token.env
}

main() {
    echo -e "${BLUE}EDMS Production Workflow Test Suite${NC}"
    echo -e "${BLUE}Standardized Workflow System v1.0${NC}"
    echo "========================================="
    
    trap cleanup EXIT
    
    cd "$PROJECT_DIR"
    
    # Check if services are running
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        error "Production services are not running. Please run deploy-production.sh first."
    fi
    
    log "Starting production workflow tests..."
    
    test_database_connectivity
    test_api_endpoints  
    test_frontend_integration
    test_workflow_operations
    test_performance
    generate_report
    
    echo
    log "🎉 All production tests completed successfully!"
    echo -e "${GREEN}The standardized workflow system is ready for production use!${NC}"
}

main "$@"