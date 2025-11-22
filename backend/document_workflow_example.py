#!/usr/bin/env python
"""
Example demonstrating the EDMS workflow engine in action.
Shows how documents flow through the complete lifecycle.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.workflow_dev')
sys.path.append('/home/jinkaiteo/Documents/QMS/QMS_04/backend')

django.setup()

from django.contrib.auth import get_user_model
from apps.workflows.models import DocumentState, DocumentWorkflow, WorkflowType
from apps.documents.models import Document, DocumentType

User = get_user_model()

def demonstrate_workflow():
    print("📋 EDMS Enhanced Simple Workflow Engine Demo")
    print("=" * 50)
    
    # Show available states
    print("\n🔄 DOCUMENT WORKFLOW STATES:")
    states = DocumentState.objects.all().order_by('name')
    for state in states:
        if state.is_initial:
            print(f"   🟢 {state.code}: {state.name} (START)")
        elif state.is_final:
            print(f"   🔴 {state.code}: {state.name} (END)")
        else:
            print(f"   🔵 {state.code}: {state.name}")
    
    # Show workflow types
    print(f"\n⚙️ CONFIGURED WORKFLOW TYPES:")
    workflows = WorkflowType.objects.all()
    for wf in workflows:
        print(f"   📊 {wf.name}")
        print(f"      Type: {wf.get_workflow_type_display()}")
        print(f"      Timeline: {wf.timeout_days} days")
        print(f"      Requires Approval: {'Yes' if wf.requires_approval else 'No'}")
    
    print(f"\n✅ Total States: {states.count()}")
    print(f"✅ Total Workflow Types: {workflows.count()}")
    print(f"✅ System Status: OPERATIONAL")

def show_workflow_example():
    print("\n" + "=" * 50)
    print("📖 EXAMPLE: Document Lifecycle Flow")
    print("=" * 50)
    
    print("""
    STANDARD DOCUMENT REVIEW WORKFLOW:
    
    1. 📝 DRAFT
       ↓ (Author completes document)
       
    2. 🔄 PENDING_REVIEW
       ↓ (Assigned to reviewer)
       
    3. 👀 UNDER_REVIEW
       ↓ (Reviewer evaluates)
       
    4. ✅ REVIEW_COMPLETED
       ↓ (Approved for next step)
       
    5. ⏳ PENDING_APPROVAL
       ↓ (Assigned to approver)
       
    6. 🎯 UNDER_APPROVAL
       ↓ (Approver evaluates)
       
    7. ✅ APPROVED
       ↓ (Final approval granted)
       
    8. 🟢 EFFECTIVE
       ↓ (Document is live and in use)
       
    9. 🔄 SUPERSEDED (when replaced)
       OR
    9. 🔴 OBSOLETE (when retired)
    
    KEY FEATURES:
    • 🔐 Role-based permissions at each step
    • 📊 Complete audit trail for compliance
    • ⏰ Timeout and reminder notifications
    • 🔄 Revision loops (back to DRAFT if changes needed)
    • 🔀 Multiple workflow types (Review, Up-version, Obsolete)
    • 📋 Task assignment and tracking
    """)

if __name__ == '__main__':
    demonstrate_workflow()
    show_workflow_example()