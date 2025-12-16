#!/bin/bash
# 
# End-to-End Workflow Restoration Test Script
# 
# This script tests the complete backup and restoration flow including workflow history.
# It creates test data, backs it up, clears the database, and restores to verify
# that all workflow information is correctly preserved.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/tmp/edms_test_backups"
TEST_BACKUP_FILE="$BACKUP_DIR/test_workflow_restoration_$(date +%Y%m%d_%H%M%S).tar.gz"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   EDMS Workflow Restoration Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Step 1: Create test data
echo -e "${YELLOW}Step 1: Creating test data...${NC}"
docker compose exec backend python manage.py shell << 'EOF'
import sys
from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentType, DocumentSource
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition, DocumentState

User = get_user_model()

# Get or create test infrastructure
doc_type, _ = DocumentType.objects.get_or_create(
    code='TEST',
    defaults={'name': 'Test Document Type'}
)
doc_source, _ = DocumentSource.objects.get_or_create(
    code='TEST',
    defaults={'name': 'Test Source'}
)

# Get test user
author = User.objects.filter(username='author01').first()
if not author:
    print("❌ Error: author01 user not found. Run seed_test_users first.")
    sys.exit(1)

# Create test document
doc, created = Document.objects.get_or_create(
    document_number='TEST-RESTORE-2025-v01.00',
    defaults={
        'title': 'Workflow Restoration Test Document',
        'document_type': doc_type,
        'document_source': doc_source,
        'author': author,
        'status': 'DRAFT',
        'version_major': 1,
        'version_minor': 0,
        'content': 'Test content for workflow restoration'
    }
)

if created:
    # Create workflow
    draft_state = DocumentState.objects.filter(code='DRAFT').first()
    review_state = DocumentState.objects.filter(code='PENDING_REVIEW').first()
    approved_state = DocumentState.objects.filter(code='APPROVED').first()
    
    workflow = DocumentWorkflow.objects.create(
        document=doc,
        workflow_type='REVIEW',
        current_state=draft_state,
        initiated_by=author,
        is_terminated=False
    )
    
    # Create transitions
    DocumentTransition.objects.create(
        workflow=workflow,
        from_state=draft_state,
        to_state=review_state,
        transitioned_by=author,
        comment='Submitted for review',
        transition_data={'action': 'submit', 'timestamp': '2025-01-01T10:00:00Z'}
    )
    
    DocumentTransition.objects.create(
        workflow=workflow,
        from_state=review_state,
        to_state=approved_state,
        transitioned_by=author,
        comment='Approved by reviewer',
        transition_data={'action': 'approve', 'timestamp': '2025-01-02T14:30:00Z'}
    )
    
    # Update workflow state
    workflow.current_state = approved_state
    workflow.save()
    
    print(f"✅ Created test document: {doc.document_number}")
    print(f"✅ Created workflow with 2 transitions")
else:
    print(f"ℹ️  Test document already exists: {doc.document_number}")

# Print current state
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition
doc_count = Document.objects.count()
wf_count = DocumentWorkflow.objects.count()
tr_count = DocumentTransition.objects.count()

print(f"\n📊 Current database state:")
print(f"   Documents: {doc_count}")
print(f"   Workflows: {wf_count}")
print(f"   Transitions: {tr_count}")
EOF

echo -e "${GREEN}✅ Test data created${NC}"
echo ""

# Step 2: Create backup
echo -e "${YELLOW}Step 2: Creating backup package...${NC}"
docker compose exec backend python manage.py create_backup \
    --type export \
    --output "$TEST_BACKUP_FILE" \
    --description "Workflow restoration test backup"

if [ -f "$TEST_BACKUP_FILE" ]; then
    BACKUP_SIZE=$(stat -f%z "$TEST_BACKUP_FILE" 2>/dev/null || stat -c%s "$TEST_BACKUP_FILE" 2>/dev/null)
    echo -e "${GREEN}✅ Backup created: $TEST_BACKUP_FILE ($BACKUP_SIZE bytes)${NC}"
else
    echo -e "${RED}❌ Backup file not found!${NC}"
    exit 1
fi
echo ""

# Step 3: Capture pre-reinit state
echo -e "${YELLOW}Step 3: Capturing pre-reinit state...${NC}"
docker compose exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition

# Store counts
import os
os.environ['PRE_DOC_COUNT'] = str(Document.objects.count())
os.environ['PRE_WF_COUNT'] = str(DocumentWorkflow.objects.count())
os.environ['PRE_TR_COUNT'] = str(DocumentTransition.objects.count())

print(f"📊 Pre-reinit state:")
print(f"   Documents: {Document.objects.count()}")
print(f"   Workflows: {DocumentWorkflow.objects.count()}")
print(f"   Transitions: {DocumentTransition.objects.count()}")

# Verify test document exists
test_doc = Document.objects.filter(document_number='TEST-RESTORE-2025-v01.00').first()
if test_doc:
    print(f"   ✅ Test document exists: {test_doc.document_number}")
    workflow = DocumentWorkflow.objects.filter(document=test_doc).first()
    if workflow:
        transitions = DocumentTransition.objects.filter(workflow=workflow).count()
        print(f"   ✅ Workflow exists with {transitions} transitions")
    else:
        print(f"   ❌ No workflow found for test document!")
else:
    print(f"   ❌ Test document not found!")
EOF
echo ""

# Step 4: System reinit
echo -e "${YELLOW}Step 4: Running system_reinit...${NC}"
echo -e "${YELLOW}   (This will clear all business data but preserve infrastructure)${NC}"
docker compose exec backend python manage.py system_reinit --confirm --preserve-backups

echo -e "${GREEN}✅ System reinitialized${NC}"
echo ""

# Step 5: Verify data cleared
echo -e "${YELLOW}Step 5: Verifying data cleared...${NC}"
docker compose exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition

doc_count = Document.objects.count()
wf_count = DocumentWorkflow.objects.count()
tr_count = DocumentTransition.objects.count()

print(f"📊 Post-reinit state:")
print(f"   Documents: {doc_count}")
print(f"   Workflows: {wf_count}")
print(f"   Transitions: {tr_count}")

if doc_count == 0 and wf_count == 0 and tr_count == 0:
    print("✅ All business data cleared successfully")
else:
    print("❌ Warning: Some data not cleared!")
    import sys
    sys.exit(1)
EOF
echo ""

# Step 6: Restore from backup
echo -e "${YELLOW}Step 6: Restoring from backup...${NC}"
docker compose exec backend python manage.py restore_from_package \
    "$TEST_BACKUP_FILE" \
    --type full \
    --confirm

echo -e "${GREEN}✅ Restore completed${NC}"
echo ""

# Step 7: Verify restoration
echo -e "${YELLOW}Step 7: Verifying restoration...${NC}"
docker compose exec backend python manage.py shell << 'EOF'
import sys
from apps.documents.models import Document
from apps.workflows.models_simple import DocumentWorkflow, DocumentTransition

print(f"\n📊 Post-restore state:")
doc_count = Document.objects.count()
wf_count = DocumentWorkflow.objects.count()
tr_count = DocumentTransition.objects.count()

print(f"   Documents: {doc_count}")
print(f"   Workflows: {wf_count}")
print(f"   Transitions: {tr_count}")

# Verify test document
test_doc = Document.objects.filter(document_number='TEST-RESTORE-2025-v01.00').first()

if not test_doc:
    print("❌ FAILED: Test document not restored!")
    sys.exit(1)

print(f"\n✅ Test document restored: {test_doc.document_number}")
print(f"   Title: {test_doc.title}")
print(f"   Status: {test_doc.status}")

# Verify workflow
workflow = DocumentWorkflow.objects.filter(document=test_doc).first()

if not workflow:
    print("❌ FAILED: Workflow not restored!")
    sys.exit(1)

print(f"\n✅ Workflow restored:")
print(f"   Type: {workflow.workflow_type}")
print(f"   Current state: {workflow.current_state.code}")
print(f"   Initiated by: {workflow.initiated_by.username}")

# Verify transitions
transitions = DocumentTransition.objects.filter(workflow=workflow).order_by('id')
transition_count = transitions.count()

if transition_count != 2:
    print(f"❌ FAILED: Expected 2 transitions, found {transition_count}")
    sys.exit(1)

print(f"\n✅ Transitions restored: {transition_count}")
for i, trans in enumerate(transitions, 1):
    print(f"   {i}. {trans.from_state.code} → {trans.to_state.code}")
    print(f"      Comment: {trans.comment}")
    print(f"      By: {trans.transitioned_by.username}")

# Final verification
if doc_count > 0 and wf_count > 0 and tr_count >= 2:
    print(f"\n{'='*60}")
    print(f"🎉 SUCCESS! All workflow data restored correctly!")
    print(f"{'='*60}")
else:
    print(f"\n❌ FAILED: Incomplete restoration")
    sys.exit(1)
EOF

RESTORE_STATUS=$?

echo ""
if [ $RESTORE_STATUS -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "Backup file saved at: ${BLUE}$TEST_BACKUP_FILE${NC}"
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}   ❌ TESTS FAILED!${NC}"
    echo -e "${RED}================================================${NC}"
    exit 1
fi
