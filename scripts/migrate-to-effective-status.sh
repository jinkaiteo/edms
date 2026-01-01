#!/bin/bash
# Migrate APPROVED_AND_EFFECTIVE status to EFFECTIVE

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

header "🔄 Migrating APPROVED_AND_EFFECTIVE to EFFECTIVE"

log "This script will:"
echo "  1. Update all documents with status APPROVED_AND_EFFECTIVE to EFFECTIVE"
echo "  2. Update DocumentState records if needed"
echo "  3. Update DocumentWorkflow current_state references"
echo "  4. Verify the migration"
echo ""

# Step 1: Check current state
header "📊 Step 1: Checking Current State"
log "Checking for APPROVED_AND_EFFECTIVE documents..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.models import Document
from apps.workflows.models import DocumentState, DocumentWorkflow

print("\n🔍 Documents with APPROVED_AND_EFFECTIVE status:")
approved_and_effective = Document.objects.filter(status='APPROVED_AND_EFFECTIVE')
print(f"  Count: {approved_and_effective.count()}")
for doc in approved_and_effective:
    print(f"    - {doc.document_number}: {doc.title}")

print("\n🔍 DocumentStates:")
try:
    effective = DocumentState.objects.filter(code='EFFECTIVE')
    print(f"  EFFECTIVE state exists: {effective.exists()}")
except:
    print("  EFFECTIVE state: Not found")

try:
    approved_and_eff = DocumentState.objects.filter(code='APPROVED_AND_EFFECTIVE')
    print(f"  APPROVED_AND_EFFECTIVE state exists: {approved_and_eff.exists()}")
except:
    print("  APPROVED_AND_EFFECTIVE state: Not found")

print("\n🔍 Workflows with APPROVED_AND_EFFECTIVE state:")
workflows = DocumentWorkflow.objects.filter(current_state__code='APPROVED_AND_EFFECTIVE')
print(f"  Count: {workflows.count()}")
PYTHON

# Step 2: Perform migration
header "🔄 Step 2: Performing Migration"
log "Migrating documents and workflows..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.models import Document
from apps.workflows.models import DocumentState, DocumentWorkflow
from django.db import transaction

print("\n🔄 Starting migration...")

with transaction.atomic():
    # 1. Ensure EFFECTIVE state exists
    effective_state, created = DocumentState.objects.get_or_create(
        code='EFFECTIVE',
        defaults={'name': 'Effective'}
    )
    if created:
        print("✓ Created EFFECTIVE DocumentState")
    else:
        print("✓ EFFECTIVE DocumentState already exists")
    
    # 2. Migrate Document status
    docs_updated = Document.objects.filter(status='APPROVED_AND_EFFECTIVE').update(status='EFFECTIVE')
    print(f"✓ Updated {docs_updated} documents from APPROVED_AND_EFFECTIVE to EFFECTIVE")
    
    # 3. Migrate DocumentWorkflow current_state
    try:
        old_state = DocumentState.objects.get(code='APPROVED_AND_EFFECTIVE')
        workflows_updated = DocumentWorkflow.objects.filter(current_state=old_state).update(current_state=effective_state)
        print(f"✓ Updated {workflows_updated} workflows to EFFECTIVE state")
    except DocumentState.DoesNotExist:
        print("  No APPROVED_AND_EFFECTIVE state found in workflows")
    
    print("\n✅ Migration completed successfully!")
PYTHON

# Step 3: Verify migration
header "✅ Step 3: Verifying Migration"
log "Verifying all changes..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.models import Document
from apps.workflows.models import DocumentState, DocumentWorkflow

print("\n🔍 Verification:")

# Check for any remaining APPROVED_AND_EFFECTIVE
remaining_docs = Document.objects.filter(status='APPROVED_AND_EFFECTIVE').count()
print(f"  Documents with APPROVED_AND_EFFECTIVE: {remaining_docs}")

# Check EFFECTIVE documents
effective_docs = Document.objects.filter(status='EFFECTIVE').count()
print(f"  Documents with EFFECTIVE: {effective_docs}")

# Check workflows
effective_workflows = DocumentWorkflow.objects.filter(current_state__code='EFFECTIVE').count()
print(f"  Workflows in EFFECTIVE state: {effective_workflows}")

if remaining_docs == 0:
    print("\n✅ SUCCESS! All documents migrated to EFFECTIVE")
else:
    print(f"\n⚠️  WARNING: {remaining_docs} documents still have APPROVED_AND_EFFECTIVE status")
PYTHON

# Step 4: Clean up old state (optional)
header "🧹 Step 4: Cleanup (Optional)"
info "The APPROVED_AND_EFFECTIVE DocumentState can be removed if no longer needed"
echo "Run this manually if desired:"
echo "  docker compose -f docker-compose.prod.yml exec backend python manage.py shell"
echo "  >>> from apps.workflows.models import DocumentState"
echo "  >>> DocumentState.objects.filter(code='APPROVED_AND_EFFECTIVE').delete()"
echo ""

header "✅ Migration Complete!"
echo ""
log "Summary:"
echo "  • Documents migrated to EFFECTIVE status"
echo "  • Workflows updated to EFFECTIVE state"
echo "  • System now using standardized EFFECTIVE status"
echo ""
log "Next steps:"
echo "  1. Restart backend: docker compose -f docker-compose.prod.yml restart backend"
echo "  2. Rebuild frontend: docker compose -f docker-compose.prod.yml up -d --build frontend"
echo "  3. Test document approval workflow"
echo ""
