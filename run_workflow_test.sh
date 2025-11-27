#!/bin/bash
# EDMS Workflow E2E Test Runner
# This script sets up and runs the Playwright test for Submit for Review workflow

set -e

echo "🎯 EDMS Submit for Review - E2E Test Runner"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check prerequisites
log "Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    error "Node.js is not installed. Please install Node.js 16+ to run Playwright tests."
fi

log "Node.js version: $(node --version)"

# Check if EDMS services are running
log "Checking EDMS services..."

# Check frontend
if curl -s -f http://localhost:3000 > /dev/null; then
    log "✓ Frontend running on http://localhost:3000"
else
    error "Frontend is not running on http://localhost:3000. Please start the EDMS frontend."
fi

# Check backend
if curl -s -f http://localhost:8000/health/ > /dev/null; then
    log "✓ Backend running on http://localhost:8000"
else
    error "Backend is not running on http://localhost:8000. Please start the EDMS backend."
fi

# Check if test users exist
log "Verifying test user credentials..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
    -H "Content-Type: application/json" \
    -d '{"username": "author", "password": "test123"}')

if echo "$AUTH_RESPONSE" | grep -q "access"; then
    log "✓ Test user 'author' authentication working"
else
    error "Test user 'author' with password 'test123' not working. Please check user setup."
fi

# Install Playwright if not installed
if [ ! -d "node_modules" ]; then
    log "Installing Playwright dependencies..."
    npm install
fi

if [ ! -d "node_modules/@playwright" ]; then
    log "Installing Playwright browsers..."
    npx playwright install
fi

# Run the test
log "Starting E2E workflow test..."
echo ""

case "${1:-headed}" in
    "headless"|"ci")
        log "Running test in headless mode..."
        npx playwright test
        ;;
    "debug")
        log "Running test in debug mode..."
        npx playwright test --debug
        ;;
    "ui")
        log "Running test in interactive UI mode..."
        npx playwright test --ui
        ;;
    *)
        log "Running test in headed mode (with browser visible)..."
        npx playwright test --headed
        ;;
esac

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log "🎉 E2E Test completed successfully!"
    echo ""
    echo "📋 Test verified:"
    echo "   ✅ Author login"
    echo "   ✅ Document creation (DRAFT)"
    echo "   ✅ Submit for Review workflow"
    echo "   ✅ Reviewer assignment"
    echo "   ✅ Document state transition"
    echo ""
    echo "🎯 EDMS Submit for Review workflow is working correctly!"
else
    error "E2E Test failed. Check the test output above for details."
fi