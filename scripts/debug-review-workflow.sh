#!/bin/bash
# Debug review workflow issues on staging server

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

log "🔍 Debugging Review Workflow Issues"
echo ""

# 1. Check backend logs for recent errors
info "1. Checking backend container logs (last 100 lines)..."
echo "=========================================="
docker compose -f docker-compose.prod.yml logs --tail=100 backend | grep -i "error\|exception\|traceback" || echo "No errors found in recent logs"
echo ""

# 2. Check if document exists
info "2. Checking if document ea462429-29b2-4723-9eb5-fe0e84cabf2e exists..."
echo "=========================================="
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.models import Document

try:
    doc = Document.objects.get(uuid='ea462429-29b2-4723-9eb5-fe0e84cabf2e')
    print(f"✓ Document found: {doc.document_number}")
    print(f"  - Title: {doc.title}")
    print(f"  - Status: {doc.status}")
    print(f"  - Author: {doc.author.username if doc.author else 'None'}")
    print(f"  - Reviewer: {doc.reviewer.username if doc.reviewer else 'None'}")
    print(f"  - Approver: {doc.approver.username if doc.approver else 'None'}")
except Document.DoesNotExist:
    print("✗ Document not found!")
except Exception as e:
    print(f"✗ Error: {e}")
PYTHON
echo ""

# 3. Check if reviewer user exists
info "3. Checking if reviewer user ID=3 exists..."
echo "=========================================="
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.users.models import User, UserRole

try:
    user = User.objects.get(id=3)
    print(f"✓ User found: {user.username} ({user.get_full_name()})")
    print(f"  - Email: {user.email}")
    print(f"  - Is active: {user.is_active}")
    
    # Check roles
    roles = UserRole.objects.filter(user=user, is_active=True)
    if roles.exists():
        print(f"  - Roles:")
        for ur in roles:
            print(f"    * {ur.role.name} (Module: {ur.role.module}, Level: {ur.role.permission_level})")
    else:
        print("  ⚠️  No active roles!")
        
    # Check if user can review
    can_review = roles.filter(
        role__module='O1',
        role__permission_level__in=['review', 'approve', 'admin']
    ).exists()
    print(f"  - Can review documents: {can_review}")
    
except User.DoesNotExist:
    print("✗ User with ID=3 not found!")
except Exception as e:
    print(f"✗ Error: {e}")
PYTHON
echo ""

# 4. Check DocumentState and WorkflowType setup
info "4. Checking DocumentState and WorkflowType configuration..."
echo "=========================================="
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.workflows.models import DocumentState, WorkflowType

print("DocumentStates:")
states = DocumentState.objects.all()
if states.exists():
    for state in states:
        print(f"  - {state.code}: {state.name}")
else:
    print("  ✗ No DocumentStates found! Run migrations or initialize defaults.")

print("\nWorkflowTypes:")
workflow_types = WorkflowType.objects.all()
if workflow_types.exists():
    for wt in workflow_types:
        print(f"  - {wt.workflow_type}: {wt.name} (Active: {wt.is_active})")
else:
    print("  ✗ No WorkflowTypes found! Run migrations or initialize defaults.")
PYTHON
echo ""

# 5. Test submit_for_review directly
info "5. Testing submit_for_review function directly..."
echo "=========================================="
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.models import Document
from apps.users.models import User
from apps.workflows.document_lifecycle import get_document_lifecycle_service

try:
    # Get document
    doc = Document.objects.get(uuid='ea462429-29b2-4723-9eb5-fe0e84cabf2e')
    print(f"✓ Document: {doc.document_number} (Status: {doc.status})")
    
    # Get author
    author = doc.author
    print(f"✓ Author: {author.username}")
    
    # Get reviewer
    if not doc.reviewer:
        print("✗ No reviewer assigned!")
    else:
        print(f"✓ Reviewer: {doc.reviewer.username}")
        
        # Try to submit
        print("\nAttempting to submit for review...")
        lifecycle_service = get_document_lifecycle_service()
        
        try:
            result = lifecycle_service.submit_for_review(doc, author, "Test submission from debug script")
            print(f"✓ Submit result: {result}")
            
            # Check final status
            doc.refresh_from_db()
            print(f"✓ Document status after submit: {doc.status}")
            
        except Exception as submit_error:
            print(f"✗ Submit failed: {submit_error}")
            import traceback
            traceback.print_exc()
        
except Document.DoesNotExist:
    print("✗ Document not found!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON
echo ""

log "✅ Debug complete!"
echo ""
echo "If you see errors above, the issue is likely:"
echo "  1. Missing DocumentStates or WorkflowTypes (run initialize defaults)"
echo "  2. Reviewer user has no roles or wrong roles (run fix-reviewer-approver-roles.sh)"
echo "  3. Document is in wrong state (not DRAFT)"
echo "  4. Database migration issues"
