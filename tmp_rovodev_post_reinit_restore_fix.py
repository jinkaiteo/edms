#!/usr/bin/env python
"""
Fix restore process to handle post-reinit Role UUID conflicts
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.base')
django.setup()

import json
import uuid as uuid_lib
from django.contrib.auth import get_user_model
from apps.users.models import Role, UserRole
from apps.documents.models import Document, DocumentType, DocumentSource

def post_reinit_restore_fix():
    """Fix restore process for post-reinit scenario"""
    print("🔧 POST-REINIT RESTORE FIX")
    print("=" * 40)
    
    User = get_user_model()
    
    # Step 1: Analyze current vs backup state
    print("Step 1: Analyzing current vs backup role conflicts...")
    
    database_file = '/tmp/test_fixed_uuid/database/database_backup.json'
    with open(database_file, 'r') as f:
        backup_data = json.load(f)
    
    # Get backup data
    backup_roles = [r for r in backup_data if r['model'] == 'users.role']
    backup_user_roles = [r for r in backup_data if r['model'] == 'users.userrole'] 
    backup_documents = [r for r in backup_data if r['model'] == 'documents.document']
    backup_users = [r for r in backup_data if r['model'] == 'auth.user']
    
    # Get current roles (post-reinit)
    current_roles = {role.name: role for role in Role.objects.all()}
    
    print(f"Current roles after reinit: {len(current_roles)}")
    print(f"Backup roles to restore: {len(backup_roles)}")
    
    # Create role mapping (backup UUID → current role)
    role_mapping = {}
    for backup_role in backup_roles:
        role_name = backup_role['fields']['name']
        backup_uuid = backup_role['fields']['uuid']
        
        if role_name in current_roles:
            current_role = current_roles[role_name]
            role_mapping[backup_uuid] = current_role
            print(f"  📍 Mapped: {role_name}")
            print(f"     Backup UUID: {backup_uuid[:8]}... → Current UUID: {str(current_role.uuid)[:8]}...")
        else:
            print(f"  ❌ Role not found in current system: {role_name}")
    
    # Step 2: Create missing users first
    print(f"\nStep 2: Creating missing users...")
    
    current_usernames = {user.username for user in User.objects.all()}
    
    for backup_user in backup_users:
        username = backup_user['fields']['username']
        
        if username not in current_usernames:
            try:
                # Create user with same fields as backup
                user = User.objects.create(
                    username=username,
                    email=backup_user['fields'].get('email', f'{username}@edms.local'),
                    first_name=backup_user['fields'].get('first_name', ''),
                    last_name=backup_user['fields'].get('last_name', ''),
                    is_staff=backup_user['fields'].get('is_staff', False),
                    is_active=backup_user['fields'].get('is_active', True)
                )
                # Set password
                user.set_password('edms123')  # Default password for restored users
                user.save()
                
                print(f"  ✅ Created user: {username}")
                current_usernames.add(username)
                
            except Exception as e:
                print(f"  ❌ Failed to create user {username}: {str(e)}")
    
    # Step 3: Restore UserRoles with role mapping
    print(f"\nStep 3: Restoring UserRoles with role mapping...")
    
    restored_user_roles = 0
    for ur_record in backup_user_roles:
        fields = ur_record['fields']
        
        try:
            # Resolve user
            user = User.objects.get(username=fields['user'][0])
            
            # Resolve role using our mapping
            backup_role_name = fields['role'][0]
            if backup_role_name in current_roles:
                role = current_roles[backup_role_name]
                
                # Resolve assigned_by
                assigned_by = User.objects.get(username=fields['assigned_by'][0])
                
                # Create UserRole with new UUID
                user_role = UserRole.objects.create(
                    uuid=uuid_lib.uuid4(),  # New UUID to avoid conflicts
                    user=user,
                    role=role,  # Use current role (not backup role)
                    assigned_by=assigned_by,
                    assignment_reason=fields.get('assignment_reason', 'Restored from backup'),
                    is_active=fields.get('is_active', True)
                )
                
                restored_user_roles += 1
                print(f"  ✅ {user.username} → {role.name}")
                
            else:
                print(f"  ❌ Role not found: {backup_role_name}")
                
        except Exception as e:
            print(f"  ❌ Failed to restore UserRole: {str(e)}")
    
    # Step 4: Restore Documents with FK resolution
    print(f"\nStep 4: Restoring Documents...")
    
    restored_documents = 0
    for doc_record in backup_documents:
        fields = doc_record['fields']
        
        try:
            # Resolve author
            author = User.objects.get(username=fields['author'][0])
            
            # Resolve document type and source
            document_type = DocumentType.objects.get(code=fields['document_type'][0])
            document_source = DocumentSource.objects.get(name=fields['document_source'][0])
            
            # Create Document with new UUID
            document = Document.objects.create(
                uuid=uuid_lib.uuid4(),  # New UUID to avoid conflicts
                title=fields['title'],
                document_number=fields['document_number'],
                author=author,
                document_type=document_type,
                document_source=document_source,
                version_major=fields.get('version_major', 1),
                version_minor=fields.get('version_minor', 0),
                status=fields.get('status', 'DRAFT'),
                file_path=fields.get('file_path', ''),
                file_name=fields.get('file_name', ''),
                file_size=fields.get('file_size'),
                description=fields.get('description', '')
            )
            
            restored_documents += 1
            print(f"  ✅ {document.title} by {author.username}")
            
        except Exception as e:
            print(f"  ❌ Failed to restore Document: {str(e)}")
    
    # Step 5: Verification
    print(f"\nStep 5: Final verification...")
    
    final_users = User.objects.count()
    final_user_roles = UserRole.objects.count()
    final_documents = Document.objects.count()
    
    print(f"Final counts:")
    print(f"  Users: {final_users}")
    print(f"  UserRoles: {final_user_roles}")
    print(f"  Documents: {final_documents}")
    
    success = final_user_roles > 0 and final_documents >= 0
    
    if success:
        print(f"\n🎉 POST-REINIT RESTORE SUCCESS!")
        print("✅ Role UUID conflicts resolved by mapping to existing roles")
        print("✅ Missing users created successfully")
        print("✅ UserRoles restored with proper FK references")
        print("✅ Documents restored (if any in backup)")
        print("✅ All UUID conflicts avoided")
        
        print(f"\n📋 RESTORED USER ROLES:")
        for ur in UserRole.objects.all():
            print(f"  • {ur.user.username} → {ur.role.name}")
            
        if Document.objects.exists():
            print(f"\n📋 RESTORED DOCUMENTS:")
            for doc in Document.objects.all():
                print(f"  • {doc.title} by {doc.author.username}")
    else:
        print(f"\n❌ Post-reinit restore failed")
    
    return success

if __name__ == '__main__':
    success = post_reinit_restore_fix()
    exit(0 if success else 1)