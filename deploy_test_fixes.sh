#!/bin/bash

# Deploy Test Fixes Script
# Copies updated test files and Celery tasks to Docker container

set -e

CONTAINER_NAME="edms_prod_backend"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              Deploying Test Fixes to Container                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/3] Copying updated test files..."

# Copy fixed test files
docker cp backend/apps/workflows/tests/test_versioning_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_versioning_workflow.py

docker cp backend/apps/workflows/tests/test_obsolescence_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_obsolescence_workflow.py

docker cp backend/apps/workflows/tests/test_termination_workflow.py \
  $CONTAINER_NAME:/app/apps/workflows/tests/test_termination_workflow.py

docker cp backend/apps/audit/tests/test_workflow_audit_trail.py \
  $CONTAINER_NAME:/app/apps/audit/tests/test_workflow_audit_trail.py

echo "✓ Test files copied"
echo ""

echo "[2/3] Verifying Celery tasks..."
docker exec $CONTAINER_NAME python -c "
from apps.scheduler.automated_tasks import activate_pending_documents, process_scheduled_obsolescence
print('✅ Celery tasks imported successfully')
" || echo "⚠️ Celery tasks already exist or need verification"

echo ""

echo "[3/3] Running tests with fixes..."
docker exec $CONTAINER_NAME python -m pytest \
  apps/workflows/tests/test_versioning_workflow.py \
  apps/workflows/tests/test_obsolescence_workflow.py \
  apps/workflows/tests/test_termination_workflow.py \
  apps/audit/tests/test_workflow_audit_trail.py \
  apps/scheduler/tests/ \
  apps/documents/tests/test_document_dependencies.py \
  --reuse-db -v --tb=line | tee test_results_with_fixes.txt

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                       Test Fixes Deployed!                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

