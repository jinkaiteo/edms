"""
Direct Restore Processor for EDMS Migration Packages

This processor bypasses Django ORM field processing issues by directly
creating objects with resolved natural keys, specifically targeting
critical business data like UserRoles and Documents.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.apps import apps
import uuid
from datetime import datetime

User = get_user_model()
logger = logging.getLogger(__name__)


class DirectRestoreProcessor:
    """
    Direct restore processor that manually creates critical business objects
    without relying on Django's natural key deserialization.
    """
    
    def __init__(self):
        self.restoration_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'user_roles_created': 0,
            'documents_created': 0
        }
        
    def process_critical_business_data(self, backup_file_path: str) -> Dict[str, Any]:
        """
        Process only the critical business data that must be restored:
        UserRoles and Documents.
        """
        logger.info("🎯 Starting Direct Restore for Critical Business Data")
        
        try:
            # Load backup data
            with open(backup_file_path, 'r') as f:
                backup_data = json.load(f)
            
            with transaction.atomic():
                # Process UserRoles first (dependencies for documents)
                self._process_user_roles(backup_data)
                
                # Process Documents
                self._process_documents(backup_data)
            
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Direct restore failed: {str(e)}")
            raise
    
    def _process_user_roles(self, backup_data: List[Dict]):
        """Directly process UserRole records."""
        logger.info("👥 Processing UserRole assignments...")
        
        userrole_records = [r for r in backup_data if r.get('model') == 'users.userrole']
        logger.info(f"Found {len(userrole_records)} UserRole records")
        
        for record in userrole_records:
            try:
                self._create_user_role_directly(record)
                self.restoration_stats['successful'] += 1
                self.restoration_stats['user_roles_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to create UserRole: {str(e)}")
                self.restoration_stats['failed'] += 1
            
            self.restoration_stats['processed'] += 1
    
    def _create_user_role_directly(self, record: Dict):
        """Create UserRole object directly without Django deserialization."""
        from apps.users.models import UserRole, Role
        
        fields = record.get('fields', {})
        
        # Manually resolve natural keys
        user_natural_key = fields.get('user')  # ['author01']
        role_natural_key = fields.get('role')  # ['Document Author']
        assigned_by_natural_key = fields.get('assigned_by')  # ['admin']
        
        # Resolve User
        if not user_natural_key or not isinstance(user_natural_key, list):
            raise ValueError(f"Invalid user natural key: {user_natural_key}")
        
        try:
            user = User.objects.get(username=user_natural_key[0])
        except User.DoesNotExist:
            raise ValueError(f"User not found: {user_natural_key[0]}")
        
        # Resolve Role
        if not role_natural_key or not isinstance(role_natural_key, list):
            raise ValueError(f"Invalid role natural key: {role_natural_key}")
        
        try:
            role = Role.objects.get(name=role_natural_key[0])
        except Role.DoesNotExist:
            raise ValueError(f"Role not found: {role_natural_key[0]}")
        
        # Resolve assigned_by User
        assigned_by = None
        if assigned_by_natural_key and isinstance(assigned_by_natural_key, list):
            try:
                assigned_by = User.objects.get(username=assigned_by_natural_key[0])
            except User.DoesNotExist:
                logger.debug(f"Assigned by user not found: {assigned_by_natural_key[0]}")
        
        # Check if UserRole already exists
        if UserRole.objects.filter(user=user, role=role).exists():
            logger.debug(f"UserRole already exists: {user.username} -> {role.name}")
            return
        
        # Create UserRole directly
        user_role = UserRole(
            uuid=uuid.uuid4(),
            user=user,
            role=role,
            assigned_by=assigned_by,
            is_active=fields.get('is_active', True),
            assignment_reason=fields.get('assignment_reason', 'Restored from migration package')
        )
        
        # Handle datetime fields safely
        if 'assigned_at' in fields and fields['assigned_at']:
            try:
                from django.utils.dateparse import parse_datetime
                user_role.assigned_at = parse_datetime(fields['assigned_at'])
            except:
                pass  # Use default
        
        user_role.save()
        logger.info(f"✅ Created UserRole: {user.username} → {role.name}")
    
    def _process_documents(self, backup_data: List[Dict]):
        """Directly process Document records."""
        logger.info("📄 Processing Documents...")
        
        document_records = [r for r in backup_data if r.get('model') == 'documents.document']
        logger.info(f"Found {len(document_records)} Document records")
        
        for record in document_records:
            try:
                self._create_document_directly(record)
                self.restoration_stats['successful'] += 1
                self.restoration_stats['documents_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to create Document: {str(e)}")
                self.restoration_stats['failed'] += 1
            
            self.restoration_stats['processed'] += 1
    
    def _create_document_directly(self, record: Dict):
        """Create Document object directly without Django deserialization."""
        from apps.documents.models import Document, DocumentType, DocumentSource
        
        fields = record.get('fields', {})
        
        # Manually resolve natural keys
        author_natural_key = fields.get('author')  # ['author01']
        document_type_natural_key = fields.get('document_type')  # ['POL']
        document_source_natural_key = fields.get('document_source')  # ['Original Digital Draft']
        
        # Resolve Author
        if not author_natural_key or not isinstance(author_natural_key, list):
            raise ValueError(f"Invalid author natural key: {author_natural_key}")
        
        try:
            author = User.objects.get(username=author_natural_key[0])
        except User.DoesNotExist:
            raise ValueError(f"Author not found: {author_natural_key[0]}")
        
        # Resolve DocumentType
        if not document_type_natural_key or not isinstance(document_type_natural_key, list):
            raise ValueError(f"Invalid document type natural key: {document_type_natural_key}")
        
        try:
            document_type = DocumentType.objects.get(code=document_type_natural_key[0])
        except DocumentType.DoesNotExist:
            raise ValueError(f"Document type not found: {document_type_natural_key[0]}")
        
        # Resolve DocumentSource
        if not document_source_natural_key or not isinstance(document_source_natural_key, list):
            raise ValueError(f"Invalid document source natural key: {document_source_natural_key}")
        
        try:
            document_source = DocumentSource.objects.get(name=document_source_natural_key[0])
        except DocumentSource.DoesNotExist:
            raise ValueError(f"Document source not found: {document_source_natural_key[0]}")
        
        # Check if Document already exists
        document_number = fields.get('document_number')
        if document_number and Document.objects.filter(document_number=document_number).exists():
            logger.debug(f"Document already exists: {document_number}")
            return
        
        # Create Document directly
        document = Document(
            uuid=uuid.uuid4(),
            document_number=fields.get('document_number', f'DOC-{uuid.uuid4().hex[:8].upper()}'),
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
        
        # Handle datetime fields safely
        datetime_fields = ['created_at', 'updated_at']
        for field_name in datetime_fields:
            if field_name in fields and fields[field_name]:
                try:
                    from django.utils.dateparse import parse_datetime
                    setattr(document, field_name, parse_datetime(fields[field_name]))
                except:
                    pass  # Use defaults
        
        document.save()
        logger.info(f"✅ Created Document: \"{document.title}\" by {document.author.username}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate restoration report."""
        stats = self.restoration_stats
        
        success_rate = (stats['successful'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
        
        report = {
            'status': 'completed',
            'success_rate': round(success_rate, 2),
            'processed': stats['processed'],
            'successful': stats['successful'],
            'failed': stats['failed'],
            'user_roles_created': stats['user_roles_created'],
            'documents_created': stats['documents_created'],
            'critical_data_restored': stats['user_roles_created'] > 0 or stats['documents_created'] > 0
        }
        
        logger.info(f"🎯 Direct Restoration Complete:")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   UserRoles Created: {stats['user_roles_created']}")
        logger.info(f"   Documents Created: {stats['documents_created']}")
        
        return report