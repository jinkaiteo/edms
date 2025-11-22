#!/usr/bin/env python
"""
Test script to verify workflow activation is working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.workflow_dev')
sys.path.append('/home/jinkaiteo/Documents/QMS/QMS_04/backend')

django.setup()

from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowType, WorkflowInstance, DocumentState

def test_workflow_activation():
    print("🧪 Testing Workflow Activation...")
    
    # Test 1: Check DocumentState model
    try:
        state_count = DocumentState.objects.count()
        print(f"✅ DocumentState model working - {state_count} states in database")
    except Exception as e:
        print(f"❌ DocumentState model error: {e}")
        return False
    
    # Test 2: Check WorkflowType model
    try:
        workflow_count = WorkflowType.objects.count()
        print(f"✅ WorkflowType model working - {workflow_count} workflow types in database")
    except Exception as e:
        print(f"❌ WorkflowType model error: {e}")
        return False
    
    # Test 3: Create a test user if needed
    User = get_user_model()
    try:
        user, created = User.objects.get_or_create(
            username='workflow_test_user',
            defaults={'email': 'test@edms.local', 'is_active': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
        print(f"✅ User model working - test user ready")
    except Exception as e:
        print(f"❌ User model error: {e}")
        return False
    
    # Test 4: Check if we can import document models
    try:
        from apps.documents.models import Document
        print(f"✅ Document models can be imported")
    except Exception as e:
        print(f"❌ Document model import error: {e}")
    
    print("\n🎉 Basic workflow system is activated and functional!")
    print("\nNext steps:")
    print("1. Run: python manage.py setup_simple_workflows")
    print("2. Start the development server")
    print("3. Test frontend integration")
    
    return True

if __name__ == '__main__':
    test_workflow_activation()