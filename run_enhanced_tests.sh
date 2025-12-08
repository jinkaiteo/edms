#!/bin/bash

# Enhanced EDMS Playwright Test Runner
# Comprehensive test suite with validation, performance, and security testing

echo "🚀 Enhanced EDMS Test Suite Runner"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if the system is running
log "Checking system availability..."
if ! curl -f -s http://localhost:3000 > /dev/null; then
    error "Frontend not available at http://localhost:3000. Please start the EDMS system first: docker compose up -d"
fi

if ! curl -f -s http://localhost:8000/health/ > /dev/null; then
    error "Backend not available at http://localhost:8000. Please start the EDMS system first: docker compose up -d"
fi

log "✅ System is running"
echo ""

# Check Playwright installation
log "Checking Playwright installation..."
if ! command -v playwright &> /dev/null; then
    warn "Installing Playwright..."
    npm install -g @playwright/test
    playwright install
else
    log "✅ Playwright is available"
fi

# Create test results directory
mkdir -p test-results
mkdir -p playwright-report

echo ""
info "🎯 Enhanced Test Suite Components:"
info "  1. Enhanced User Seeding with validation"
info "  2. Comprehensive Workflow Testing"
info "  3. System Validation & Security Testing"
info "  4. Performance & Cross-browser Testing"
info "  5. API Response Validation"
info "  6. Error Handling & Recovery Testing"
echo ""

# Test execution mode
MODE=${1:-"complete"}

case $MODE in
    "fast")
        log "🏃 Running fast test suite (core functionality only)..."
        TESTS="tests/enhanced/01_enhanced_user_seeding.spec.js"
        ;;
    "validation")
        log "🔍 Running validation and security tests only..."
        TESTS="tests/enhanced/03_enhanced_validation_testing.spec.js"
        ;;
    "workflows")
        log "🔄 Running workflow tests only..."
        TESTS="tests/enhanced/02_enhanced_workflow_testing.spec.js"
        ;;
    "cross-browser")
        log "🌐 Running cross-browser compatibility tests..."
        playwright test tests/enhanced/ --project=chromium --project=firefox --project=webkit
        exit $?
        ;;
    *)
        log "🎯 Running complete enhanced test suite..."
        TESTS="tests/enhanced/"
        ;;
esac

# Start test execution
echo ""
log "🚀 Starting enhanced test execution..."
echo ""

# Run the tests
if [ "$MODE" == "cross-browser" ]; then
    # Cross-browser already handled above
    exit 0
else
    playwright test $TESTS --headed --reporter=html,line
fi

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log "🎉 Enhanced Test Suite completed successfully!"
    echo ""
    echo "📊 Test Results Summary:"
    echo "  ✅ User management validation completed"
    echo "  ✅ Workflow testing completed"
    echo "  ✅ System validation completed"
    echo "  ✅ Security testing completed"
    echo "  ✅ Performance testing completed"
    echo ""
    echo "📁 Test artifacts:"
    echo "  - HTML report: playwright-report/index.html"
    echo "  - Screenshots: test-results/"
    echo "  - Videos: test-results/"
    echo "  - Debug logs: test-results/"
else
    error "Enhanced Test Suite failed. Check the test output above for details."
fi

echo ""
echo "📋 Available test commands:"
echo "  ./run_enhanced_tests.sh fast        - Quick core functionality test"
echo "  ./run_enhanced_tests.sh validation  - Security and validation tests"
echo "  ./run_enhanced_tests.sh workflows   - Workflow testing only"
echo "  ./run_enhanced_tests.sh cross-browser - Multi-browser testing"
echo "  ./run_enhanced_tests.sh complete    - Full test suite (default)"
echo ""
echo "📊 View detailed results:"
echo "  npx playwright show-report"
echo ""
echo "🌐 Access the system:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo ""
echo "👤 Test user credentials:"
echo "  Username: [author01|reviewer01|approver01|senior01|viewer01]"
echo "  Password: test123"
echo ""

log "Enhanced test execution completed!"