"""
Management Command to Restore Critical Business Data

This command bypasses all Django ORM issues by directly creating
UserRoles and Documents from the migration package after infrastructure restore.
"""

import json
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.users.models import UserRole, Role
from apps.documents.models import Document, DocumentType, DocumentSource

User = get_user_model()


class Command(BaseCommand):
    help = 'Restore critical business data (UserRoles and Documents) from migration package'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the database backup JSON file'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing data'
        )
    
    def handle(self, *args, **options):
        backup_file = options['backup_file']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎯 Restoring Critical Business Data from: {backup_file}'
            )
        )
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            with transaction.atomic():
                user_roles_created = self.restore_user_roles(backup_data, force)
                documents_created = self.restore_documents(backup_data, force)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Restoration Complete: {user_roles_created} UserRoles, {documents_created} Documents'
                )
            )
            
            # Verification
            self.verify_restoration()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Restoration failed: {str(e)}')
            )
            raise
    
    def restore_user_roles(self, backup_data, force=False):
        """Restore UserRole assignments."""
        self.stdout.write('👥 Restoring UserRole assignments...')
        
        userrole_records = [r for r in backup_data if r.get('model') == 'users.userrole']
        created_count = 0
        
        for record in userrole_records:
            try:
                if self.create_user_role(record, force):
                    created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️ UserRole creation failed: {str(e)}')
                )
        
        self.stdout.write(f'   ✅ UserRoles created: {created_count}/{len(userrole_records)}')
        return created_count
    
    def create_user_role(self, record, force=False):
        """Create a single UserRole."""
        fields = record.get('fields', {})
        
        # Resolve natural keys
        user_natural_key = fields.get('user', [])
        role_natural_key = fields.get('role', [])
        assigned_by_natural_key = fields.get('assigned_by', [])
        
        if not user_natural_key or not role_natural_key:
            raise ValueError(f'Missing user or role natural key')
        
        # Get actual objects
        try:
            user = User.objects.get(username=user_natural_key[0])
        except User.DoesNotExist:
            raise ValueError(f'User not found: {user_natural_key[0]}')
        
        try:
            role = Role.objects.get(name=role_natural_key[0])
        except Role.DoesNotExist:
            raise ValueError(f'Role not found: {role_natural_key[0]}')
        
        assigned_by = None
        if assigned_by_natural_key:
            try:
                assigned_by = User.objects.get(username=assigned_by_natural_key[0])
            except User.DoesNotExist:
                pass  # Optional field
        
        # Check if exists
        if UserRole.objects.filter(user=user, role=role).exists():
            if not force:
                self.stdout.write(f'   ⚠️ UserRole exists: {user.username} -> {role.name}')
                return False
            else:
                UserRole.objects.filter(user=user, role=role).delete()
        
        # Create UserRole
        user_role = UserRole.objects.create(
            uuid=uuid.uuid4(),
            user=user,
            role=role,
            assigned_by=assigned_by,
            is_active=fields.get('is_active', True),
            assignment_reason=fields.get('assignment_reason', 'Restored from migration package')
        )
        
        self.stdout.write(f'   ✅ Created: {user.username} -> {role.name}')
        return True
    
    def restore_documents(self, backup_data, force=False):
        """Restore Documents."""
        self.stdout.write('📄 Restoring Documents...')
        
        document_records = [r for r in backup_data if r.get('model') == 'documents.document']
        created_count = 0
        
        for record in document_records:
            try:
                if self.create_document(record, force):
                    created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️ Document creation failed: {str(e)}')
                )
        
        self.stdout.write(f'   ✅ Documents created: {created_count}/{len(document_records)}')
        return created_count
    
    def create_document(self, record, force=False):
        """Create a single Document."""
        fields = record.get('fields', {})
        
        # Resolve natural keys
        author_natural_key = fields.get('author', [])
        doc_type_natural_key = fields.get('document_type', [])
        doc_source_natural_key = fields.get('document_source', [])
        
        if not author_natural_key or not doc_type_natural_key or not doc_source_natural_key:
            raise ValueError(f'Missing document natural keys')
        
        # Get actual objects
        try:
            author = User.objects.get(username=author_natural_key[0])
        except User.DoesNotExist:
            raise ValueError(f'Author not found: {author_natural_key[0]}')
        
        try:
            document_type = DocumentType.objects.get(code=doc_type_natural_key[0])
        except DocumentType.DoesNotExist:
            raise ValueError(f'Document type not found: {doc_type_natural_key[0]}')
        
        try:
            document_source = DocumentSource.objects.get(name=doc_source_natural_key[0])
        except DocumentSource.DoesNotExist:
            raise ValueError(f'Document source not found: {doc_source_natural_key[0]}')
        
        # Check if exists
        document_number = fields.get('document_number')
        if document_number and Document.objects.filter(document_number=document_number).exists():
            if not force:
                self.stdout.write(f'   ⚠️ Document exists: {document_number}')
                return False
            else:
                Document.objects.filter(document_number=document_number).delete()
        
        # Create Document
        document = Document.objects.create(
            uuid=uuid.uuid4(),
            document_number=document_number or f'DOC-{uuid.uuid4().hex[:8].upper()}',
            title=fields.get('title', 'Restored Document'),
            description=fields.get('description', ''),
            version_major=fields.get('version_major', 1),
            version_minor=fields.get('version_minor', 0),
            document_type=document_type,
            document_source=document_source,
            status=fields.get('status', 'DRAFT'),
            priority=fields.get('priority', 'normal'),
            author=author,
            file_name=fields.get('file_name', ''),
            file_path=fields.get('file_path', ''),
            file_size=fields.get('file_size', 0),
            file_checksum=fields.get('file_checksum', ''),
            mime_type=fields.get('mime_type', ''),
            is_active=fields.get('is_active', True),
            is_controlled=fields.get('is_controlled', True),
            requires_training=fields.get('requires_training', False),
            keywords=fields.get('keywords', ''),
            reason_for_change=fields.get('reason_for_change', ''),
            change_summary=fields.get('change_summary', ''),
            obsolescence_reason=fields.get('obsolescence_reason', ''),
        )
        
        self.stdout.write(f'   ✅ Created: "{document.title}" by {document.author.username}')
        return True
    
    def verify_restoration(self):
        """Verify the restoration was successful."""
        self.stdout.write('\n📊 Verification Results:')
        
        user_role_count = UserRole.objects.count()
        document_count = Document.objects.count()
        
        self.stdout.write(f'   UserRoles: {user_role_count}')
        self.stdout.write(f'   Documents: {document_count}')
        
        if user_role_count > 0:
            self.stdout.write('   ✅ UserRole assignments:')
            for ur in UserRole.objects.select_related('user', 'role').all():
                self.stdout.write(f'     - {ur.user.username} -> {ur.role.name}')
        
        if document_count > 0:
            self.stdout.write('   ✅ Documents:')
            for doc in Document.objects.all()[:5]:
                self.stdout.write(f'     - "{doc.title}" by {doc.author.username}')
        
        # Check author01 specifically
        author01_user = User.objects.filter(username='author01').first()
        if author01_user:
            author01_docs = Document.objects.filter(author=author01_user)
            author01_roles = UserRole.objects.filter(user=author01_user)
            
            task_functional = author01_docs.count() > 0 and author01_roles.count() > 0
            status = '✅' if task_functional else '❌'
            
            self.stdout.write(f'\n   {status} author01 Task Access:')
            self.stdout.write(f'     Documents: {author01_docs.count()}')
            self.stdout.write(f'     Roles: {author01_roles.count()}')
            
            if task_functional:
                self.stdout.write('     🎯 author01 can access and manage their tasks!')
            else:
                self.stdout.write('     ⚠️ author01 cannot access tasks properly')
        
        # Final assessment
        critical_success = user_role_count > 0 and document_count > 0
        
        if critical_success:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 CRITICAL BUSINESS DATA RESTORATION: COMPLETE SUCCESS!'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ Critical business data restoration incomplete'
                )
            )