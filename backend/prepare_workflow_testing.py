#!/usr/bin/env python
"""
Preparation script for complete workflow testing.
Sets up test users, permissions, and sample data for workflow testing.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.workflow_dev')
sys.path.append('/home/jinkaiteo/Documents/QMS/QMS_04/backend')

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from apps.workflows.models import DocumentState, WorkflowType
from apps.documents.models import Document, DocumentType

User = get_user_model()

def setup_test_environment():
    print("🚀 PREPARING COMPLETE WORKFLOW TESTING ENVIRONMENT")
    print("=" * 60)
    
    # Step 1: Create user groups and permissions
    setup_user_groups()
    
    # Step 2: Create test users with proper roles
    create_test_users()
    
    # Step 3: Setup document types
    setup_document_types()
    
    # Step 4: Create sample documents
    create_sample_documents()
    
    # Step 5: Verify workflow states and types
    verify_workflow_system()
    
    # Step 6: Create workflow testing scenarios
    create_testing_scenarios()
    
    print("\n🎯 TESTING ENVIRONMENT READY!")

def setup_user_groups():
    print("\n👥 Setting up user groups and permissions...")
    
    # Document content type for permissions
    document_ct = ContentType.objects.get_for_model(Document)
    
    # Create groups
    groups_data = [
        ('Document_Authors', 'Users who can create and edit documents'),
        ('Document_Reviewers', 'Users who can review documents'),
        ('Technical_Reviewers', 'Users who can review technical documents'),
        ('SOP_Reviewers', 'Users who can review SOPs'),
        ('Policy_Reviewers', 'Users who can review policies'),
        ('Document_Approvers', 'Users who can approve documents'),
        ('Senior_Approvers', 'Senior managers who can approve high-criticality documents'),
        ('Quality_Managers', 'Quality department managers'),
        ('Department_Managers', 'Department managers with approval authority'),
    ]
    
    created_groups = {}
    for group_name, description in groups_data:
        group, created = Group.objects.get_or_create(
            name=group_name,
            defaults={'id': None}
        )
        created_groups[group_name] = group
        status = "✅ Created" if created else "📝 Exists"
        print(f"   {status}: {group_name}")
    
    # Create custom permissions if they don't exist
    permissions_data = [
        ('can_review_document', 'Can review documents'),
        ('can_approve_document', 'Can approve documents'),
        ('can_make_effective', 'Can make documents effective'),
        ('can_obsolete_document', 'Can mark documents as obsolete'),
        ('can_assign_reviewers', 'Can assign reviewers to documents'),
        ('can_assign_approvers', 'Can assign approvers to documents'),
    ]
    
    for codename, name in permissions_data:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=document_ct,
            defaults={'name': name}
        )
        if created:
            print(f"   ✅ Created permission: {name}")
    
    # Assign permissions to groups
    print("\n🔐 Assigning permissions to groups...")
    
    # Document Reviewers permissions
    review_permissions = Permission.objects.filter(
        codename__in=['can_review_document', 'view_document', 'change_document']
    )
    created_groups['Document_Reviewers'].permissions.set(review_permissions)
    created_groups['Technical_Reviewers'].permissions.set(review_permissions)
    created_groups['SOP_Reviewers'].permissions.set(review_permissions)
    created_groups['Policy_Reviewers'].permissions.set(review_permissions)
    
    # Document Approvers permissions
    approve_permissions = Permission.objects.filter(
        codename__in=['can_approve_document', 'can_make_effective', 'view_document']
    )
    created_groups['Document_Approvers'].permissions.set(approve_permissions)
    created_groups['Senior_Approvers'].permissions.set(approve_permissions)
    created_groups['Quality_Managers'].permissions.set(approve_permissions)
    created_groups['Department_Managers'].permissions.set(approve_permissions)
    
    print("   ✅ Permissions assigned to groups")

def create_test_users():
    print("\n👤 Creating test users with roles...")
    
    users_data = [
        # Authors
        ('john_author', 'John', 'Author', 'john.author@edms.local', ['Document_Authors']),
        ('sarah_author', 'Sarah', 'Writer', 'sarah.writer@edms.local', ['Document_Authors']),
        
        # Technical Reviewers
        ('mike_reviewer', 'Mike', 'Johnson', 'mike.johnson@edms.local', ['Document_Reviewers', 'Technical_Reviewers']),
        ('lisa_reviewer', 'Lisa', 'Chen', 'lisa.chen@edms.local', ['Document_Reviewers', 'Technical_Reviewers']),
        
        # SOP/Policy Reviewers
        ('alex_sop', 'Alex', 'Rodriguez', 'alex.rodriguez@edms.local', ['Document_Reviewers', 'SOP_Reviewers']),
        ('emma_policy', 'Emma', 'Wilson', 'emma.wilson@edms.local', ['Document_Reviewers', 'Policy_Reviewers']),
        
        # Approvers
        ('david_approver', 'David', 'Manager', 'david.manager@edms.local', ['Document_Approvers', 'Department_Managers']),
        ('jennifer_qa', 'Jennifer', 'Brown', 'jennifer.brown@edms.local', ['Document_Approvers', 'Quality_Managers']),
        
        # Senior Approvers
        ('robert_senior', 'Robert', 'Director', 'robert.director@edms.local', ['Senior_Approvers', 'Quality_Managers']),
        ('karen_vp', 'Karen', 'Smith', 'karen.smith@edms.local', ['Senior_Approvers']),
    ]
    
    created_users = {}
    for username, first_name, last_name, email, group_names in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'is_active': True,
                'is_staff': True
            }
        )
        
        # Set password for testing
        if created:
            user.set_password('testing123')
            user.save()
        
        # Add to groups
        for group_name in group_names:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        
        created_users[username] = user
        status = "✅ Created" if created else "📝 Updated"
        print(f"   {status}: {username} ({first_name} {last_name}) - {', '.join(group_names)}")
    
    return created_users

def setup_document_types():
    print("\n📁 Setting up document types...")
    
    # Create admin user for document types
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            'admin', 'admin@edms.local', 'admin123'
        )
        print("   ✅ Created admin user for document types")
    
    doc_types_data = [
        ('POLICY', 'Policy Document', 'Company policies and procedures'),
        ('SOP', 'Standard Operating Procedure', 'Step-by-step operational procedures'),
        ('MANUAL', 'Manual/Handbook', 'Comprehensive operational manuals'),
        ('FORM', 'Form Template', 'Standard forms and templates'),
        ('RECORD', 'Record Template', 'Record keeping templates'),
        ('PROCEDURE', 'General Procedure', 'General procedural documents'),
        ('INSTRUCTION', 'Work Instruction', 'Detailed work instructions'),
    ]
    
    for code, name, description in doc_types_data:
        doc_type, created = DocumentType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'is_active': True,
                'created_by': admin_user
            }
        )
        status = "✅ Created" if created else "📝 Exists"
        print(f"   {status}: {code} - {name}")

def create_sample_documents():
    print("\n📄 Creating sample documents for testing...")
    
    # Get test users
    john = User.objects.get(username='john_author')
    sarah = User.objects.get(username='sarah_author')
    
    # Get document types
    sop_type = DocumentType.objects.get(code='SOP')
    policy_type = DocumentType.objects.get(code='POLICY')
    manual_type = DocumentType.objects.get(code='MANUAL')
    
    documents_data = [
        ('SOP-001', 'Document Review Process', sop_type, john, 'Standard operating procedure for document review and approval workflow.'),
        ('SOP-002', 'Quality Control Testing', sop_type, sarah, 'Procedures for quality control testing of manufactured products.'),
        ('POL-001', 'Information Security Policy', policy_type, john, 'Company policy for information security and data protection.'),
        ('POL-002', 'Employee Code of Conduct', policy_type, sarah, 'Guidelines for employee behavior and professional conduct.'),
        ('MAN-001', 'Quality Management Manual', manual_type, john, 'Comprehensive manual for quality management system implementation.'),
    ]
    
    created_docs = {}
    for doc_number, title, doc_type, author, description in documents_data:
        document, created = Document.objects.get_or_create(
            title=title,
            defaults={
                'document_type': doc_type,
                'author': author,
                'description': description,
            }
        )
        created_docs[doc_number] = document
        status = "✅ Created" if created else "📝 Exists"
        print(f"   {status}: {doc_number} - {title} (by {author.username})")
    
    return created_docs

def verify_workflow_system():
    print("\n🔄 Verifying workflow system...")
    
    # Check workflow states
    states_count = DocumentState.objects.count()
    print(f"   📊 Document States: {states_count}")
    
    if states_count == 11:
        print("   ✅ All 11 workflow states are available")
    else:
        print("   ⚠️ Expected 11 states, found {states_count}")
    
    # Check workflow types
    workflow_types_count = WorkflowType.objects.count()
    print(f"   ⚙️ Workflow Types: {workflow_types_count}")
    
    if workflow_types_count >= 4:
        print("   ✅ Workflow types are configured")
    else:
        print("   ⚠️ Expected at least 4 workflow types")

def create_testing_scenarios():
    print("\n🧪 Creating testing scenarios...")
    
    scenarios = [
        {
            'name': 'Complete Review Workflow',
            'description': 'Test complete document lifecycle from DRAFT to EFFECTIVE',
            'document': 'SOP-001',
            'reviewer': 'mike_reviewer',
            'approver': 'david_approver',
            'timeline': '5 days review, 3 days approval'
        },
        {
            'name': 'High-Criticality Policy Approval',
            'description': 'Test high-criticality document requiring senior approval',
            'document': 'POL-001',
            'reviewer': 'emma_policy',
            'approver': 'robert_senior',
            'timeline': '3 days review, 2 days approval'
        },
        {
            'name': 'Workload Balancing Test',
            'description': 'Test user selection based on workload indicators',
            'document': 'SOP-002',
            'reviewer': 'Choose between mike_reviewer and lisa_reviewer',
            'approver': 'Choose based on workload',
            'timeline': 'Standard 5+3 days'
        },
        {
            'name': 'Reassignment Test',
            'description': 'Test mid-workflow reassignment capabilities',
            'document': 'MAN-001',
            'reviewer': 'alex_sop (then reassign to lisa_reviewer)',
            'approver': 'jennifer_qa',
            'timeline': 'Test reassignment during review phase'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n   🎯 Scenario {i}: {scenario['name']}")
        print(f"      Description: {scenario['description']}")
        print(f"      Document: {scenario['document']}")
        print(f"      Reviewer: {scenario['reviewer']}")
        print(f"      Approver: {scenario['approver']}")
        print(f"      Timeline: {scenario['timeline']}")

def print_testing_instructions():
    print("\n" + "=" * 60)
    print("🎯 COMPLETE WORKFLOW TESTING INSTRUCTIONS")
    print("=" * 60)
    
    print("""
📋 TESTING CHECKLIST:

1. 🚀 START DEVELOPMENT SERVER:
   cd backend
   source venv/bin/activate
   export DJANGO_SETTINGS_MODULE=edms.settings.workflow_dev
   python manage.py runserver 8002

2. 🎯 TEST BASIC USER SELECTION:
   • Use WorkflowInitiator component
   • Select document ID: 1, 2, 3, 4, or 5
   • Choose document type: SOP, POLICY, or MANUAL
   • Set criticality: normal or high
   • Select reviewer from dropdown (shows workload)
   • Select approver from dropdown (shows workload)
   • Set custom due dates
   • Create workflow with assignments

3. 👥 TEST USER ACCOUNTS:
   Login Credentials (all password: testing123):
   
   📝 AUTHORS:
   • john_author (John Author)
   • sarah_author (Sarah Writer)
   
   👀 REVIEWERS:
   • mike_reviewer (Mike Johnson - Technical)
   • lisa_reviewer (Lisa Chen - Technical)  
   • alex_sop (Alex Rodriguez - SOP Specialist)
   • emma_policy (Emma Wilson - Policy Specialist)
   
   ✅ APPROVERS:
   • david_approver (David Manager - Department)
   • jennifer_qa (Jennifer Brown - Quality Manager)
   • robert_senior (Robert Director - Senior)
   • karen_vp (Karen Smith - VP Level)

4. 🔄 TEST WORKFLOW SCENARIOS:
   
   A) BASIC WORKFLOW:
   • Login as john_author
   • Create workflow for SOP-001
   • Select mike_reviewer as reviewer
   • Select david_approver as approver
   • Set 5-day review, 8-day approval timeline
   
   B) HIGH-CRITICALITY WORKFLOW:
   • Login as sarah_author
   • Create workflow for POL-001 (Information Security)
   • Set criticality to HIGH
   • Select emma_policy as reviewer
   • Select robert_senior as approver (senior required)
   • Set 3-day review, 5-day approval timeline
   
   C) WORKLOAD TESTING:
   • Create multiple workflows
   • Observe workload indicators change
   • Test user selection based on availability
   
   D) REASSIGNMENT TESTING:
   • Start workflow with one reviewer
   • Use reassignment API to change mid-workflow
   • Verify audit trail tracking

5. 🔍 VERIFY FEATURES:
   ✅ User search and filtering in dropdowns
   ✅ Workload indicators (low/normal/high)
   ✅ Assignment validation (different users)
   ✅ Timeline validation (approval after review)
   ✅ Document type filtering for users
   ✅ Criticality-based approver filtering
   ✅ Custom due date setting
   ✅ Assignment comments and reasoning
   ✅ Complete audit trail creation
   ✅ Error handling and user feedback

6. 📊 API ENDPOINTS TO TEST:
   GET  /api/v1/workflows/users/reviewers/
   GET  /api/v1/workflows/users/approvers/
   POST /api/v1/workflows/create_with_assignments/
   POST /api/v1/workflows/{id}/reassign/
   GET  /api/v1/workflows/my_tasks/
   GET  /api/v1/workflows/users/user_workload/

7. 🎨 FRONTEND TESTING:
   • UserSelector component functionality
   • WorkflowInitiator form validation
   • Real-time search performance
   • Mobile responsiveness
   • Error state handling
   • Loading state indicators

8. 📋 COMPLIANCE VERIFICATION:
   • Check audit trail completeness
   • Verify all assignments tracked
   • Test permission validation
   • Confirm 21 CFR Part 11 compliance features

🎯 SUCCESS CRITERIA:
✅ Can select specific reviewers and approvers
✅ Workload indicators show current user load
✅ Search functionality works across all user fields
✅ Validation prevents invalid assignments
✅ Workflows create successfully with manual assignments
✅ Audit trail tracks all assignment decisions
✅ Performance is responsive (< 200ms API calls)
✅ Error handling provides clear feedback
    """)

if __name__ == '__main__':
    setup_test_environment()
    print_testing_instructions()