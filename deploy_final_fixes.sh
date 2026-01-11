#!/bin/bash

# Deploy Final Fixes Script
# Copies all updated test files with DocumentState fixtures

set -e

CONTAINER_NAME="edms_prod_backend"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              Deploying Final Test Fixes (DocumentState)                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/2] Copying all updated test files with DocumentState fixtures..."

docker cp backend/apps/workflows/tests/test_versioning_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_versioning_workflow.py

docker cp backend/apps/workflows/tests/test_obsolescence_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_obsolescence_workflow.py

docker cp backend/apps/workflows/tests/test_termination_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_termination_workflow.py

docker cp backend/apps/audit/tests/test_workflow_audit_trail.py \
  $CONTAINER_NAME:/app/apps/audit/tests/test_workflow_audit_trail.py

echo "✓ All test files copied with DocumentState fixtures"
echo ""

echo "[2/2] Running complete test suite..."
echo ""

docker exec $CONTAINER_NAME python -m pytest \
  apps/documents/tests/test_document_dependencies.py \
  apps/workflows/tests/test_versioning_workflow.py \
  apps/workflows/tests/test_obsolescence_workflow.py \
  apps/workflows/tests/test_termination_workflow.py \
  apps/scheduler/tests/ \
  apps/audit/tests/test_workflow_audit_trail.py \
  --reuse-db -v --tb=line 2>&1 | tee final_test_results.txt

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                   Final Test Results Summary                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Count results
PASSED=$(grep -c "PASSED" final_test_results.txt || echo "0")
FAILED=$(grep -c "FAILED" final_test_results.txt || echo "0")
ERROR=$(grep -c "ERROR" final_test_results.txt || echo "0")
TOTAL=$((PASSED + FAILED + ERROR))

echo "✓ Passed:  $PASSED tests"
if [ "$FAILED" -gt 0 ]; then
    echo "✗ Failed:  $FAILED tests"
fi
if [ "$ERROR" -gt 0 ]; then
    echo "⚠ Errors:  $ERROR tests"
fi
echo "Total:     $TOTAL tests"
echo ""

if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "Pass Rate: ${PASS_RATE}%"
fi

echo ""
echo "Full results saved to: final_test_results.txt"

