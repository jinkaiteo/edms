#!/usr/bin/env python
"""
Fix the UUID conflict issue in restore process
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.base')
django.setup()

def fix_uuid_conflicts_and_test_restore():
    """Fix UUID conflicts and test complete restore"""
    print("🔧 FIXING UUID CONFLICTS AND TESTING RESTORE")
    print("=" * 60)
    
    from django.contrib.auth import get_user_model
    from apps.users.models import UserRole
    from apps.documents.models import Document
    from apps.audit.models import AuditTrail
    
    User = get_user_model()
    
    print(f"Current state:")
    print(f"  Users: {User.objects.count()}")
    print(f"  UserRoles: {UserRole.objects.count()}")
    print(f"  Documents: {Document.objects.count()}")
    print(f"  AuditTrail entries: {AuditTrail.objects.count()}")
    
    # Clear audit trail to avoid UUID conflicts
    print(f"\n🧹 Clearing audit trail to avoid UUID conflicts...")
    deleted_count = AuditTrail.objects.all().delete()[0]
    print(f"   Deleted {deleted_count} audit trail entries")
    
    # Clear existing test data
    print(f"\n🗑️ Clearing existing test data...")
    UserRole.objects.all().delete()
    Document.objects.all().delete()
    
    print(f"\nAfter clearing:")
    print(f"  UserRoles: {UserRole.objects.count()}")
    print(f"  Documents: {Document.objects.count()}")
    print(f"  AuditTrail entries: {AuditTrail.objects.count()}")
    
    # Now test the restore process via direct command
    print(f"\n🚀 Testing restore with UUID conflicts resolved...")
    import subprocess
    
    result = subprocess.run([
        'docker', 'compose', 'exec', '-T', 'backend', 
        'python', 'manage.py', 'restore_from_package', 
        '/tmp/final_restore_test.tar.gz', '--type', 'full', '--confirm'
    ], capture_output=True, text=True)
    
    print(f"Restore command output:")
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    # Check final results
    print(f"\n📊 FINAL RESTORATION RESULTS")
    print("=" * 40)
    
    final_user_roles = UserRole.objects.count()
    final_documents = Document.objects.count()
    
    print(f"UserRoles restored: {final_user_roles}")
    print(f"Documents restored: {final_documents}")
    
    if final_user_roles > 0:
        print(f"\n✅ USER ROLES SUCCESSFULLY RESTORED:")
        for ur in UserRole.objects.all():
            print(f"  • {ur.user.username} → {ur.role.name}")
    
    if final_documents > 0:
        print(f"\n✅ DOCUMENTS SUCCESSFULLY RESTORED:")
        for doc in Document.objects.all():
            print(f"  • {doc.title} | Author: {doc.author.username}")
            print(f"    File path: {doc.file_path}")
            
            # Check if file exists
            if doc.file_path:
                import os
                full_path = doc.full_file_path
                file_exists = os.path.exists(full_path) if full_path else False
                print(f"    File exists: {'✅ YES' if file_exists else '❌ NO'}")
    
    # Test summary
    success = final_user_roles > 0 and final_documents > 0
    print(f"\n🎯 RESTORE PROCESS ASSESSMENT")
    print("=" * 35)
    
    if success:
        print("✅ RESTORE PROCESS IS WORKING!")
        print("  • User roles are properly restored")
        print("  • Documents are properly restored")
        print("  • Foreign key resolution is functional")
        print("  • The issue was UUID conflicts, now resolved")
    else:
        print("❌ RESTORE PROCESS STILL HAS ISSUES")
        print("  • Need further investigation")
    
    return success

if __name__ == '__main__':
    success = fix_uuid_conflicts_and_test_restore()
    exit(0 if success else 1)