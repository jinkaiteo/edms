#!/usr/bin/env python
"""
Simple backup test using Django ORM instead of pg_dump.
"""

import os
import django
from pathlib import Path
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.base')
django.setup()

def test_django_backup():
    """Test backup using Django's built-in functionality."""
    print("🔍 Testing Django-based backup...")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Test database dump using Django
        backup_dir = Path('/tmp/edms_backup_test')
        backup_dir.mkdir(exist_ok=True)
        
        # Create database dump using Django's dumpdata
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_file = backup_dir / f"django_data_{timestamp}.json"
        
        with open(data_file, 'w') as f:
            call_command('dumpdata', 
                        '--indent', '2',
                        '--natural-foreign',
                        '--natural-primary',
                        stdout=f)
        
        if data_file.exists():
            file_size = data_file.stat().st_size
            print(f"✅ Django backup successful: {data_file.name}")
            print(f"   File size: {file_size:,} bytes")
            return True
        
    except Exception as e:
        print(f"❌ Django backup failed: {str(e)}")
        return False

def test_system_stats():
    """Test system statistics gathering."""
    print("\n🔍 Testing system statistics...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get basic stats
        user_count = User.objects.count()
        print(f"✅ Users: {user_count}")
        
        # Try to get document count
        try:
            from apps.documents.models import Document
            doc_count = Document.objects.count()
            print(f"✅ Documents: {doc_count}")
        except Exception:
            print("⚠️  Documents model not accessible")
        
        # Try to get workflow count
        try:
            from apps.workflows.models import DocumentWorkflow
            workflow_count = DocumentWorkflow.objects.count()
            print(f"✅ Workflows: {workflow_count}")
        except Exception:
            print("⚠️  Workflows model not accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ System stats error: {str(e)}")
        return False

def test_backup_models():
    """Test if our backup models work."""
    print("\n🔍 Testing backup models...")
    
    try:
        from apps.backup.models import BackupConfiguration, BackupJob
        
        # Test creating a backup configuration
        config = BackupConfiguration(
            name='test_config',
            description='Test backup configuration',
            backup_type='FULL',
            frequency='ON_DEMAND',
            storage_path='/tmp/test_backups',
            is_enabled=False  # Don't enable for testing
        )
        config.save()
        
        print(f"✅ Created backup configuration: {config.name}")
        
        # Clean up
        config.delete()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup models test failed: {str(e)}")
        return False

def main():
    """Run simplified backup tests."""
    print("🚀 EDMS Simplified Backup Test")
    print("=" * 50)
    
    results = []
    
    # Test Django backup
    results.append(test_django_backup())
    
    # Test system stats
    results.append(test_system_stats())
    
    # Test backup models
    results.append(test_backup_models())
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())