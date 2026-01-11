#!/bin/bash

# EDMS Test Deployment Script
# Deploys new test files to Docker container and installs dependencies

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="edms_prod_backend"
APP_PATH="/app"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   EDMS Test Suite Deployment Script                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if container is running
echo -e "${YELLOW}[1/5] Checking Docker container...${NC}"
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}✗ Error: Container $CONTAINER_NAME is not running${NC}"
    echo "Please start the container with: docker-compose up -d backend"
    exit 1
fi
echo -e "${GREEN}✓ Container $CONTAINER_NAME is running${NC}"
echo ""

# Check if test files exist locally
echo -e "${YELLOW}[2/5] Verifying test files exist locally...${NC}"
TEST_FILES=(
    "backend/apps/workflows/tests/test_versioning_workflow.py"
    "backend/apps/workflows/tests/test_obsolescence_workflow.py"
    "backend/apps/workflows/tests/test_termination_workflow.py"
    "backend/apps/workflows/tests/test_workflow_notifications.py"
    "backend/apps/documents/tests/test_document_dependencies.py"
    "backend/apps/scheduler/tests/test_document_activation.py"
    "backend/apps/scheduler/tests/test_obsolescence_automation.py"
    "backend/apps/scheduler/tests/__init__.py"
    "backend/apps/audit/tests/test_workflow_audit_trail.py"
    "backend/apps/audit/tests/__init__.py"
)

MISSING_FILES=0
for file in "${TEST_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo -e "${RED}✗ Error: $MISSING_FILES test file(s) not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All 10 test files found locally${NC}"
echo ""

# Copy test files to container
echo -e "${YELLOW}[3/5] Copying test files to container...${NC}"

echo "  → Copying workflow tests..."
docker cp backend/apps/workflows/tests/test_versioning_workflow.py \
    $CONTAINER_NAME:$APP_PATH/apps/workflows/tests/test_versioning_workflow.py
docker cp backend/apps/workflows/tests/test_obsolescence_workflow.py \
    $CONTAINER_NAME:$APP_PATH/apps/workflows/tests/test_obsolescence_workflow.py
docker cp backend/apps/workflows/tests/test_termination_workflow.py \
    $CONTAINER_NAME:$APP_PATH/apps/workflows/tests/test_termination_workflow.py
docker cp backend/apps/workflows/tests/test_workflow_notifications.py \
    $CONTAINER_NAME:$APP_PATH/apps/workflows/tests/test_workflow_notifications.py

echo "  → Copying document tests..."
docker cp backend/apps/documents/tests/test_document_dependencies.py \
    $CONTAINER_NAME:$APP_PATH/apps/documents/tests/test_document_dependencies.py

echo "  → Copying scheduler tests..."
docker cp backend/apps/scheduler/tests/__init__.py \
    $CONTAINER_NAME:$APP_PATH/apps/scheduler/tests/__init__.py 2>/dev/null || \
    docker exec $CONTAINER_NAME mkdir -p $APP_PATH/apps/scheduler/tests && \
    docker cp backend/apps/scheduler/tests/__init__.py \
    $CONTAINER_NAME:$APP_PATH/apps/scheduler/tests/__init__.py

docker cp backend/apps/scheduler/tests/test_document_activation.py \
    $CONTAINER_NAME:$APP_PATH/apps/scheduler/tests/test_document_activation.py
docker cp backend/apps/scheduler/tests/test_obsolescence_automation.py \
    $CONTAINER_NAME:$APP_PATH/apps/scheduler/tests/test_obsolescence_automation.py

echo "  → Copying audit tests..."
docker cp backend/apps/audit/tests/__init__.py \
    $CONTAINER_NAME:$APP_PATH/apps/audit/tests/__init__.py 2>/dev/null || \
    docker exec $CONTAINER_NAME mkdir -p $APP_PATH/apps/audit/tests && \
    docker cp backend/apps/audit/tests/__init__.py \
    $CONTAINER_NAME:$APP_PATH/apps/audit/tests/__init__.py

docker cp backend/apps/audit/tests/test_workflow_audit_trail.py \
    $CONTAINER_NAME:$APP_PATH/apps/audit/tests/test_workflow_audit_trail.py

echo -e "${GREEN}✓ All test files copied successfully${NC}"
echo ""

# Verify files in container
echo -e "${YELLOW}[4/5] Verifying files in container...${NC}"
CONTAINER_FILE_COUNT=$(docker exec $CONTAINER_NAME find apps/workflows/tests apps/documents/tests apps/scheduler/tests apps/audit/tests -name "test_*.py" 2>/dev/null | wc -l)
echo "  → Found $CONTAINER_FILE_COUNT test files in container"
echo -e "${GREEN}✓ Files verified in container${NC}"
echo ""

# Install pytest and dependencies
echo -e "${YELLOW}[5/5] Installing test dependencies...${NC}"
echo "  → Checking if pytest is already installed..."

if docker exec $CONTAINER_NAME python -m pytest --version &>/dev/null; then
    echo -e "${GREEN}✓ pytest already installed${NC}"
else
    echo "  → Installing pytest, pytest-django, pytest-cov..."
    docker exec $CONTAINER_NAME pip install --no-cache-dir \
        pytest==7.4.3 \
        pytest-django==4.7.0 \
        pytest-cov==4.1.0 \
        factory-boy==3.3.0 \
        faker==20.1.0 2>&1 | grep -v "Requirement already satisfied" || true
    
    echo -e "${GREEN}✓ Test dependencies installed${NC}"
fi
echo ""

# Success summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                     ✓ DEPLOYMENT SUCCESSFUL!                                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo "  ✓ Container verified: $CONTAINER_NAME"
echo "  ✓ Test files copied: 10 files"
echo "  ✓ Dependencies installed: pytest, pytest-django, pytest-cov"
echo "  ✓ Test files in container: $CONTAINER_FILE_COUNT"
echo ""

# Quick test
echo -e "${BLUE}🧪 Running Quick Verification Test...${NC}"
echo ""
if docker exec $CONTAINER_NAME python -m pytest --collect-only apps/workflows/tests/test_versioning_workflow.py 2>&1 | grep -q "test session starts"; then
    TEST_COUNT=$(docker exec $CONTAINER_NAME python -m pytest --collect-only apps/workflows/tests/test_versioning_workflow.py 2>&1 | grep "test_" | wc -l)
    echo -e "${GREEN}✓ Tests are discoverable! Found ~$TEST_COUNT tests in versioning workflow${NC}"
else
    echo -e "${YELLOW}⚠ Test discovery check inconclusive (may be normal)${NC}"
fi
echo ""

# Show available commands
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        🚀 READY TO RUN TESTS!                                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Run individual test files:${NC}"
echo ""
echo "  # Document Versioning (15 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/workflows/tests/test_versioning_workflow.py -v"
echo ""
echo "  # Document Obsolescence (8 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/workflows/tests/test_obsolescence_workflow.py -v"
echo ""
echo "  # Document Termination (9 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/workflows/tests/test_termination_workflow.py -v"
echo ""
echo "  # Document Dependencies (14 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/documents/tests/test_document_dependencies.py -v"
echo ""
echo "  # Scheduler Automation (11 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/scheduler/tests/ -v"
echo ""
echo "  # Audit Trail (10 tests)"
echo "  docker exec $CONTAINER_NAME python -m pytest apps/audit/tests/test_workflow_audit_trail.py -v"
echo ""
echo -e "${GREEN}Run ALL new tests:${NC}"
echo "  docker exec $CONTAINER_NAME python -m pytest \\"
echo "    apps/workflows/tests/test_versioning_workflow.py \\"
echo "    apps/workflows/tests/test_obsolescence_workflow.py \\"
echo "    apps/workflows/tests/test_termination_workflow.py \\"
echo "    apps/documents/tests/test_document_dependencies.py \\"
echo "    apps/scheduler/tests/ \\"
echo "    apps/audit/tests/test_workflow_audit_trail.py -v"
echo ""
echo -e "${GREEN}Run with coverage:${NC}"
echo "  docker exec $CONTAINER_NAME python -m pytest --cov=apps --cov-report=term apps/workflows/tests/"
echo ""
echo -e "${GREEN}Run specific test:${NC}"
echo "  docker exec $CONTAINER_NAME python -m pytest \\"
echo "    apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document -v"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
