#!/bin/bash
# Initialize workflow defaults (DocumentStates and WorkflowTypes)

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

header "🔧 Initializing Workflow Defaults"

log "This script will create:"
echo "  • DocumentStates (12 states: DRAFT, PENDING_REVIEW, etc.)"
echo "  • WorkflowTypes (3 types: REVIEW, APPROVAL, REVISION)"
echo ""

# Step 1: Run migrations
header "📊 Step 1: Running Migrations"
log "Ensuring database schema is up to date..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# Step 2: Initialize DocumentStates and WorkflowTypes
header "🏗️  Step 2: Creating DocumentStates and WorkflowTypes"
log "Initializing workflow defaults..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.workflows.models import DocumentState, WorkflowType

print("\n" + "="*60)
print("Creating DocumentStates...")
print("="*60)

# Create DocumentStates
states = [
    ('DRAFT', 'Draft'),
    ('PENDING_REVIEW', 'Pending Review'),
    ('UNDER_REVIEW', 'Under Review'),
    ('REVIEWED', 'Reviewed'),
    ('PENDING_APPROVAL', 'Pending Approval'),
    ('UNDER_APPROVAL', 'Under Approval'),
    ('APPROVED_PENDING_EFFECTIVE', 'Approved - Pending Effective'),
    ('APPROVED_AND_EFFECTIVE', 'Approved and Effective'),
    ('SUPERSEDED', 'Superseded'),
    ('PENDING_OBSOLETE', 'Pending Obsolete'),
    ('OBSOLETE', 'Obsolete'),
    ('TERMINATED', 'Terminated'),
]

created_count = 0
existing_count = 0

for code, name in states:
    obj, created = DocumentState.objects.get_or_create(
        code=code,
        defaults={'name': name}
    )
    if created:
        print(f"✓ Created DocumentState: {code} - {name}")
        created_count += 1
    else:
        print(f"  Already exists: {code}")
        existing_count += 1

print(f"\nDocumentStates Summary:")
print(f"  • Created: {created_count}")
print(f"  • Already existed: {existing_count}")
print(f"  • Total in database: {DocumentState.objects.count()}")

print("\n" + "="*60)
print("Creating WorkflowTypes...")
print("="*60)

# Create WorkflowTypes
workflow_types = [
    ('REVIEW', 'Document Review', 'Standard document review process', True),
    ('APPROVAL', 'Document Approval', 'Standard document approval process', True),
    ('UP_VERSION', 'Document Up-versioning', 'Document up-versioning process', True),
    ('OBSOLETE', 'Document Obsolescence', 'Document obsolescence process', True),
]

wf_created_count = 0
wf_existing_count = 0

for wf_type, name, desc, active in workflow_types:
    obj, created = WorkflowType.objects.get_or_create(
        workflow_type=wf_type,
        defaults={
            'name': name,
            'description': desc,
            'is_active': active,
            'requires_approval': True,
            'allows_parallel': False,
            'auto_transition': False
        }
    )
    if created:
        print(f"✓ Created WorkflowType: {wf_type} - {name}")
        wf_created_count += 1
    else:
        print(f"  Already exists: {wf_type}")
        wf_existing_count += 1

print(f"\nWorkflowTypes Summary:")
print(f"  • Created: {wf_created_count}")
print(f"  • Already existed: {wf_existing_count}")
print(f"  • Total in database: {WorkflowType.objects.count()}")

print("\n" + "="*60)
print("✅ Initialization Complete!")
print("="*60)
PYTHON

# Step 3: Restart backend
header "🔄 Step 3: Restarting Backend"
log "Restarting backend to ensure changes are loaded..."
docker compose -f docker-compose.prod.yml restart backend

log "Waiting for backend to be ready (30 seconds)..."
sleep 30

# Step 4: Verify
header "✅ Step 4: Verification"
log "Verifying initialization..."

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.workflows.models import DocumentState, WorkflowType

state_count = DocumentState.objects.count()
wf_count = WorkflowType.objects.count()

print(f"\n✓ DocumentStates: {state_count}")
print(f"✓ WorkflowTypes: {wf_count}")

if state_count >= 12 and wf_count >= 3:
    print("\n✅ SUCCESS! Workflow defaults are properly initialized.")
    print("\nYou can now:")
    print("  1. Submit documents for review")
    print("  2. Process review workflows")
    print("  3. Complete approval workflows")
else:
    print("\n⚠️  WARNING: Some defaults may be missing")
    print(f"   Expected: 12 DocumentStates, got {state_count}")
    print(f"   Expected: 3 WorkflowTypes, got {wf_count}")
PYTHON

echo ""
header "🎉 Initialization Complete!"
echo ""
log "Next steps:"
echo "  1. Test document submission from the frontend"
echo "  2. Or run the debug script to verify everything:"
echo "     ${BLUE}bash scripts/debug-review-workflow.sh${NC}"
echo ""
