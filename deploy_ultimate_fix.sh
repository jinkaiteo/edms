#!/bin/bash
set -e
CONTAINER_NAME="edms_prod_backend"

echo "Deploying ultimate fix (removing workflow_type parameter)..."

docker cp backend/apps/workflows/tests/test_versioning_workflow.py $CONTAINER_NAME:/app/apps/workflows/tests/
docker cp backend/apps/workflows/tests/test_obsolescence_workflow.py $CONTAINER_NAME:/app/apps/workflows/tests/
docker cp backend/apps/workflows/tests/test_termination_workflow.py $CONTAINER_NAME:/app/apps/workflows/tests/
docker cp backend/apps/audit/tests/test_workflow_audit_trail.py $CONTAINER_NAME:/app/apps/audit/tests/

echo "Running complete test suite..."
docker exec $CONTAINER_NAME python -m pytest \
  apps/documents/tests/test_document_dependencies.py \
  apps/workflows/tests/ \
  apps/scheduler/tests/ \
  apps/audit/tests/test_workflow_audit_trail.py \
  --reuse-db -v 2>&1 | tee ultimate_test_results.txt

echo ""
echo "========== FINAL RESULTS =========="
echo "✓ Passed:  $(grep -c "PASSED" ultimate_test_results.txt || echo 0)"
echo "✗ Failed:  $(grep -c "FAILED" ultimate_test_results.txt || echo 0)"  
echo "⚠ Errors:  $(grep -c " ERROR " ultimate_test_results.txt || echo 0)"

