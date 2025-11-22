#!/usr/bin/env python
"""
Basic test to verify Viewflow installation and setup.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.workflow_dev')
sys.path.append('/home/jinkaiteo/Documents/QMS/QMS_04/backend')

django.setup()

def test_viewflow_basic():
    print("🧪 Testing Basic Viewflow Setup...")
    
    try:
        # Test 1: Import Viewflow core
        from viewflow import flow
        from viewflow.base import this, Flow
        print("✅ Viewflow core imports successful")
        
        # Test 2: Import workflow models
        from viewflow.workflow.models import Process, Task
        print("✅ Viewflow workflow models imported")
        
        # Test 3: Check our models
        from apps.workflows.viewflow_models import DocumentProcess, WorkflowTemplate
        print("✅ Custom workflow models imported")
        
        # Test 4: Check database tables exist
        process_count = Process.objects.count()
        print(f"✅ Viewflow Process table working - {process_count} processes")
        
        # Test 5: Test our custom process
        doc_process_count = DocumentProcess.objects.count()
        print(f"✅ DocumentProcess table working - {doc_process_count} document processes")
        
        print("\n🎉 Viewflow basic setup is working!")
        return True
        
    except Exception as e:
        print(f"❌ Viewflow setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_viewflow_basic()