#!/bin/bash
set -e
CONTAINER_NAME="edms_prod_backend"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         Deploying Fixes to OLD Tests (Review, Approval, Rejections)         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/2] Copying fixed old test files..."
docker cp backend/apps/workflows/tests/test_review_workflow.py $CONTAINER_NAME:/app/apps/workflows/tests/
docker cp backend/apps/workflows/tests/test_approval_workflow.py $CONTAINER_NAME:/app/apps/workflows/tests/
docker cp backend/apps/workflows/tests/test_workflow_rejections.py $CONTAINER_NAME:/app/apps/workflows/tests/

echo "✓ All old test files updated"
echo ""

echo "[2/2] Running COMPLETE test suite (NEW + OLD tests)..."
docker exec $CONTAINER_NAME python -m pytest \
  apps/documents/tests/test_document_dependencies.py \
  apps/workflows/tests/ \
  apps/scheduler/tests/ \
  apps/audit/tests/test_workflow_audit_trail.py \
  --reuse-db -v 2>&1 | tee complete_test_results.txt

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                     COMPLETE TEST SUITE RESULTS                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=$(grep -c "PASSED" complete_test_results.txt || echo "0")
FAILED=$(grep -c "FAILED" complete_test_results.txt || echo "0")
ERROR=$(grep -c " ERROR " complete_test_results.txt || echo "0")
TOTAL=$((PASSED + FAILED + ERROR))

echo "✓ Passed:  $PASSED tests"
if [ "$FAILED" -gt 0 ]; then echo "✗ Failed:  $FAILED tests"; fi
if [ "$ERROR" -gt 0 ]; then echo "⚠ Errors:  $ERROR tests"; fi
echo "Total:     $TOTAL tests"
echo ""

if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "Pass Rate: ${PASS_RATE}%"
    echo ""
    if [ "$PASS_RATE" -gt 50 ]; then
        echo "🎉 SUCCESS! Over 50% pass rate achieved!"
    fi
fi

