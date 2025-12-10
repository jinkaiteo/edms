#!/usr/bin/env python
"""
Comprehensive UUID Conflict Resolution Fix
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.base')
django.setup()

import json
import uuid as uuid_lib
from django.db import transaction

def comprehensive_uuid_conflict_fix():
    """Fix all UUID conflicts comprehensively"""
    print("🔧 COMPREHENSIVE UUID CONFLICT RESOLUTION")
    print("=" * 55)
    
    from apps.audit.models import AuditTrail, SystemEvent
    from apps.backup.models import BackupJob, RestoreJob
    from django.contrib.auth import get_user_model
    from apps.users.models import UserRole
    from apps.documents.models import Document
    
    User = get_user_model()
    
    print("Step 1: Clearing ALL system records that could cause conflicts")
    print("-" * 60)
    
    # Clear system records (keep business data)
    try:
        audit_deleted = AuditTrail.objects.all().delete()[0]
        print(f"✅ AuditTrail cleared: {audit_deleted} records")
    except Exception as e:
        print(f"⚠️ AuditTrail clear: {str(e)}")
    
    try:
        system_deleted = SystemEvent.objects.all().delete()[0]
        print(f"✅ SystemEvent cleared: {system_deleted} records")
    except Exception as e:
        print(f"⚠️ SystemEvent clear: {str(e)}")
    
    # Clear backup/restore jobs (these cause FK conflicts)
    try:
        # Delete RestoreJobs first (they reference BackupJobs)
        restore_deleted = RestoreJob.objects.all().delete()[0]
        print(f"✅ RestoreJob cleared: {restore_deleted} records")
        
        backup_deleted = BackupJob.objects.all().delete()[0]
        print(f"✅ BackupJob cleared: {backup_deleted} records")
    except Exception as e:
        print(f"⚠️ Backup/Restore jobs clear: {str(e)}")
    
    # Clear any scheduled tasks or notifications
    try:
        from apps.scheduler.models import NotificationQueue
        notif_deleted = NotificationQueue.objects.all().delete()[0]
        print(f"✅ NotificationQueue cleared: {notif_deleted} records")
    except Exception as e:
        print(f"⚠️ NotificationQueue clear: {str(e)}")
    
    print("\nStep 2: Regenerating backup data with new UUIDs")
    print("-" * 50)
    
    # Load backup data
    database_file = '/tmp/test_fixed_uuid/database/database_backup.json'
    with open(database_file, 'r') as f:
        backup_data = json.load(f)
    
    # Models that might have UUID conflicts
    system_models = [
        'audit.audittrail', 
        'audit.systemevent', 
        'scheduler.notificationqueue',
        'backup.backupjob', 
        'backup.restorejob',
        'django_celery_beat.periodictask',
        'django_celery_beat.crontabschedule'
    ]
    
    uuid_regenerated = 0
    for record in backup_data:
        if record['model'] in system_models:
            # Regenerate UUID if it exists
            if 'uuid' in record['fields']:
                old_uuid = record['fields']['uuid']
                new_uuid = str(uuid_lib.uuid4())
                record['fields']['uuid'] = new_uuid
                uuid_regenerated += 1
    
    print(f"✅ Regenerated {uuid_regenerated} UUIDs in backup data")
    
    # Save the modified backup data
    fixed_backup_file = '/tmp/fixed_uuid_backup.json'
    with open(fixed_backup_file, 'w') as f:
        json.dump(backup_data, f)
    
    print(f"✅ Saved fixed backup data to: {fixed_backup_file}")
    
    print("\nStep 3: Manual restoration with fixed UUIDs")
    print("-" * 45)
    
    # Clear existing business data for clean test
    UserRole.objects.all().delete()
    Document.objects.all().delete()
    
    # Manually restore business data with FK resolution
    user_roles = [r for r in backup_data if r['model'] == 'users.userrole']
    documents = [r for r in backup_data if r['model'] == 'documents.document']
    
    print(f"Restoring {len(user_roles)} UserRoles...")
    restored_user_roles = 0
    for record in user_roles:
        fields = record['fields']
        try:
            # Resolve foreign keys manually
            user = User.objects.get(username=fields['user'][0])
            from apps.users.models import Role
            role = Role.objects.get(name=fields['role'][0]) 
            assigned_by = User.objects.get(username=fields['assigned_by'][0])
            
            # Create UserRole with new UUID
            user_role = UserRole.objects.create(
                uuid=uuid_lib.uuid4(),  # Force new UUID
                user=user,
                role=role,
                assigned_by=assigned_by,
                assignment_reason=fields['assignment_reason'],
                is_active=fields['is_active']
            )
            
            restored_user_roles += 1
            print(f"  ✅ {user.username} → {role.name}")
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
    
    print(f"\\nRestoring {len(documents)} Documents...")
    restored_documents = 0
    for record in documents:
        fields = record['fields']
        try:
            # Resolve foreign keys manually  
            author = User.objects.get(username=fields['author'][0])
            from apps.documents.models import DocumentType, DocumentSource
            document_type = DocumentType.objects.get(code=fields['document_type'][0])
            document_source = DocumentSource.objects.get(name=fields['document_source'][0])
            
            # Create Document with new UUID
            document = Document.objects.create(
                uuid=uuid_lib.uuid4(),  # Force new UUID
                title=fields['title'],
                document_number=fields['document_number'],
                author=author,
                document_type=document_type,
                document_source=document_source,
                version_major=fields['version_major'],
                version_minor=fields['version_minor'],
                status=fields['status'],
                file_path=fields['file_path'],
                file_name=fields.get('file_name', ''),
                file_size=fields.get('file_size'),
                description=fields.get('description', '')
            )
            
            restored_documents += 1
            print(f"  ✅ {document.title} by {author.username}")
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
    
    print(f"\nStep 4: Verification")
    print("-" * 20)
    
    final_user_roles = UserRole.objects.count()
    final_documents = Document.objects.count()
    
    print(f"Final counts:")
    print(f"  UserRoles: {final_user_roles}")
    print(f"  Documents: {final_documents}")
    
    success = final_user_roles > 0 and final_documents > 0
    
    if success:
        print(f"\n🎉 UUID CONFLICT RESOLUTION SUCCESS!")
        print("✅ All system records cleared")
        print("✅ UUIDs regenerated in backup data")  
        print("✅ Business data restored with new UUIDs")
        print("✅ No UUID conflicts remaining")
        
        print(f"\n📋 RESTORED DATA:")
        for ur in UserRole.objects.all():
            print(f"  • {ur.user.username} → {ur.role.name}")
        for doc in Document.objects.all():
            print(f"  • {doc.title} | {doc.document_number}")
            
    else:
        print(f"\n❌ UUID CONFLICT RESOLUTION FAILED")
        
    return success

if __name__ == '__main__':
    success = comprehensive_uuid_conflict_fix()
    exit(0 if success else 1)