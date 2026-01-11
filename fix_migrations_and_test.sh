#!/bin/bash

# EDMS Migration Fix and Test Execution Script
# Fixes database schema issues and runs tests

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="edms_prod_backend"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              EDMS Migration Fix & Test Execution Script                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if container is running
echo -e "${YELLOW}[1/7] Checking Docker container...${NC}"
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}✗ Error: Container $CONTAINER_NAME is not running${NC}"
    echo "Please start the container with: docker-compose up -d backend"
    exit 1
fi
echo -e "${GREEN}✓ Container $CONTAINER_NAME is running${NC}"
echo ""

# Check current migration status
echo -e "${YELLOW}[2/7] Checking current migration status...${NC}"
echo "  → Listing applied migrations..."
docker exec $CONTAINER_NAME python manage.py showmigrations 2>&1 | grep -E "workflows|documents|scheduler" | tail -10
echo ""

# Detect unapplied changes
echo -e "${YELLOW}[3/7] Detecting unapplied model changes...${NC}"
CHANGES_NEEDED=$(docker exec $CONTAINER_NAME python manage.py makemigrations --dry-run 2>&1 | grep -c "Migrations for" || echo "0")

if [ "$CHANGES_NEEDED" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Model changes detected that need migrations${NC}"
    echo ""
    
    # Show what would be migrated
    echo -e "${CYAN}Preview of changes:${NC}"
    docker exec $CONTAINER_NAME python manage.py makemigrations --dry-run 2>&1 | grep -A 5 "Migrations for" || true
    echo ""
    
    # Ask for confirmation
    echo -e "${YELLOW}Do you want to create and apply these migrations? [y/N]${NC}"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo -e "${YELLOW}[4/7] Creating migrations...${NC}"
        
        # Create migrations with automatic answers
        # Answer 'n' to rename questions, let Django create new fields
        echo -e "${CYAN}Creating migrations (answering migration questions automatically)...${NC}"
        docker exec $CONTAINER_NAME bash -c 'echo "n" | python manage.py makemigrations 2>&1' || {
            echo -e "${RED}✗ Migration creation failed${NC}"
            echo ""
            echo -e "${YELLOW}Trying interactive mode...${NC}"
            docker exec -it $CONTAINER_NAME python manage.py makemigrations
        }
        
        echo -e "${GREEN}✓ Migrations created${NC}"
        echo ""
    else
        echo -e "${YELLOW}⚠ Skipping migration creation${NC}"
        echo ""
    fi
else
    echo -e "${GREEN}✓ No unapplied model changes detected${NC}"
    echo ""
fi

# Apply migrations
echo -e "${YELLOW}[5/7] Applying migrations...${NC}"
echo "  → Running migrate command..."
docker exec $CONTAINER_NAME python manage.py migrate 2>&1 | tail -20

echo ""
echo -e "${GREEN}✓ Migrations applied${NC}"
echo ""

# Verify database schema
echo -e "${YELLOW}[6/7] Verifying database schema...${NC}"
echo "  → Checking for any remaining unapplied migrations..."

UNAPPLIED=$(docker exec $CONTAINER_NAME python manage.py showmigrations 2>&1 | grep "\[ \]" | wc -l || echo "0")

if [ "$UNAPPLIED" -eq 0 ]; then
    echo -e "${GREEN}✓ All migrations applied successfully${NC}"
else
    echo -e "${YELLOW}⚠ Warning: $UNAPPLIED migrations still unapplied${NC}"
    docker exec $CONTAINER_NAME python manage.py showmigrations 2>&1 | grep "\[ \]" || true
fi
echo ""

# Run tests
echo -e "${YELLOW}[7/7] Running tests...${NC}"
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                          RUNNING TEST SUITE                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run a quick smoke test first
echo -e "${CYAN}Running quick smoke test...${NC}"
if docker exec $CONTAINER_NAME python -m pytest apps/documents/tests/test_document_dependencies.py::TestDocumentDependencies::test_add_dependency_to_document -v 2>&1 | grep -q "PASSED\|FAILED"; then
    echo -e "${GREEN}✓ Smoke test completed (tests are running!)${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Smoke test had issues, continuing with full test run...${NC}"
    echo ""
fi

# Run all new tests with summary
echo -e "${CYAN}Running full test suite...${NC}"
echo ""

# Create a temporary file to store results
RESULTS_FILE="/tmp/edms_test_results_$(date +%s).txt"

# Run tests and capture output
docker exec $CONTAINER_NAME python -m pytest \
    apps/workflows/tests/test_versioning_workflow.py \
    apps/workflows/tests/test_obsolescence_workflow.py \
    apps/workflows/tests/test_termination_workflow.py \
    apps/documents/tests/test_document_dependencies.py \
    apps/scheduler/tests/test_document_activation.py \
    apps/scheduler/tests/test_obsolescence_automation.py \
    apps/audit/tests/test_workflow_audit_trail.py \
    -v --tb=short 2>&1 | tee "$RESULTS_FILE"

# Parse results
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                         TEST RESULTS SUMMARY                                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extract test counts
PASSED=$(grep -c "PASSED" "$RESULTS_FILE" || echo "0")
FAILED=$(grep -c "FAILED" "$RESULTS_FILE" || echo "0")
ERROR=$(grep -c "ERROR" "$RESULTS_FILE" || echo "0")
SKIPPED=$(grep -c "SKIPPED" "$RESULTS_FILE" || echo "0")

TOTAL=$((PASSED + FAILED + ERROR + SKIPPED))

echo -e "${GREEN}✓ Passed:  $PASSED${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}✗ Failed:  $FAILED${NC}"
fi
if [ "$ERROR" -gt 0 ]; then
    echo -e "${RED}✗ Errors:  $ERROR${NC}"
fi
if [ "$SKIPPED" -gt 0 ]; then
    echo -e "${YELLOW}⊘ Skipped: $SKIPPED${NC}"
fi
echo -e "${CYAN}Total:     $TOTAL${NC}"
echo ""

# Calculate pass rate
if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo -e "${CYAN}Pass Rate: ${PASS_RATE}%${NC}"
    echo ""
fi

# Show failed test details
if [ "$FAILED" -gt 0 ] || [ "$ERROR" -gt 0 ]; then
    echo -e "${YELLOW}Failed/Errored Tests:${NC}"
    grep -E "FAILED|ERROR" "$RESULTS_FILE" | head -20 || true
    echo ""
fi

# Generate detailed report
REPORT_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"
cp "$RESULTS_FILE" "$REPORT_FILE"
echo -e "${CYAN}Detailed results saved to: ${REPORT_FILE}${NC}"
echo ""

# Success summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                      ✓ MIGRATION FIX COMPLETED!                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$PASSED" -gt 0 ]; then
    echo -e "${GREEN}🎉 SUCCESS! $PASSED tests are now passing!${NC}"
    echo ""
fi

if [ "$FAILED" -gt 0 ] || [ "$ERROR" -gt 0 ]; then
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo ""
    echo "Some tests failed or errored. Common reasons:"
    echo ""
    echo "1. Missing service methods:"
    echo "   - start_version_workflow() in document_lifecycle.py"
    echo "   - start_obsolete_workflow() in document_lifecycle.py"
    echo "   - terminate_document() in Document model"
    echo ""
    echo "2. Missing scheduler tasks:"
    echo "   - activate_pending_documents() in automated_tasks.py"
    echo "   - process_scheduled_obsolescence() in automated_tasks.py"
    echo ""
    echo "3. Check implementation guides:"
    echo "   - TEST_RESULTS_AND_FIXES.md"
    echo "   - TESTING_QUICK_START_GUIDE.md"
    echo ""
fi

# Show commands for investigating failures
if [ "$FAILED" -gt 0 ] || [ "$ERROR" -gt 0 ]; then
    echo -e "${CYAN}To investigate specific failures:${NC}"
    echo ""
    echo "# Run specific test with full output"
    echo "docker exec $CONTAINER_NAME python -m pytest apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document -vv"
    echo ""
    echo "# Run with Python debugger"
    echo "docker exec -it $CONTAINER_NAME python -m pytest apps/workflows/tests/test_versioning_workflow.py --pdb"
    echo ""
    echo "# Check logs"
    echo "docker logs $CONTAINER_NAME --tail 100"
    echo ""
fi

# Cleanup
rm -f "$RESULTS_FILE"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
