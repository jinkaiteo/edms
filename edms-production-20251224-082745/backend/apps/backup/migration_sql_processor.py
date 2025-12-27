"""
Migration SQL Processor for EDMS Critical Business Data

This processor uses direct SQL operations to ensure UserRoles and Documents
are restored completely, bypassing all Django ORM and natural key issues.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from django.db import connection, transaction
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationSQLProcessor:
    """
    SQL-based processor that directly inserts critical business data
    using raw SQL to bypass all Django ORM issues.
    """
    
    def __init__(self):
        self.restoration_stats = {
            'user_roles_created': 0,
            'documents_created': 0,
            'sql_operations': 0,
            'errors': []
        }
        
    def restore_critical_data_via_sql(self, backup_file_path: str) -> Dict[str, Any]:
        """
        Restore UserRoles and Documents using direct SQL operations.
        """
        logger.info("🔧 Starting SQL-based critical data restoration")
        
        try:
            # Load backup data
            with open(backup_file_path, 'r') as f:
                backup_data = json.load(f)
            
            with transaction.atomic():
                # Process UserRoles via SQL
                self._restore_user_roles_via_sql(backup_data)
                
                # Process Documents via SQL
                self._restore_documents_via_sql(backup_data)
            
            return self._generate_sql_report()
            
        except Exception as e:
            logger.error(f"SQL restoration failed: {str(e)}")
            self.restoration_stats['errors'].append(str(e))
            raise
    
    def _restore_user_roles_via_sql(self, backup_data: List[Dict]):
        """Restore UserRoles using direct SQL."""
        logger.info("👥 Restoring UserRoles via SQL...")
        
        userrole_records = [r for r in backup_data if r.get('model') == 'users.userrole']
        
        for record in userrole_records:
            try:
                self._create_user_role_via_sql(record)
                self.restoration_stats['user_roles_created'] += 1
                self.restoration_stats['sql_operations'] += 1
            except Exception as e:
                logger.warning(f"SQL UserRole creation failed: {str(e)}")
                self.restoration_stats['errors'].append(f"UserRole: {str(e)}")
    
    def _create_user_role_via_sql(self, record: Dict):
        """Create UserRole via direct SQL."""
        fields = record.get('fields', {})
        
        # Resolve natural keys to IDs
        user_natural_key = fields.get('user', [])  # ['author01']
        role_natural_key = fields.get('role', [])  # ['Document Author']
        assigned_by_natural_key = fields.get('assigned_by', [])  # ['admin']
        
        if not user_natural_key or not role_natural_key:
            raise ValueError(f"Missing user or role natural key: user={user_natural_key}, role={role_natural_key}")
        
        # Get IDs via SQL
        user_id = self._get_user_id_by_username(user_natural_key[0])
        role_id = self._get_role_id_by_name(role_natural_key[0])
        assigned_by_id = None
        
        if assigned_by_natural_key:
            assigned_by_id = self._get_user_id_by_username(assigned_by_natural_key[0])
        
        if not user_id or not role_id:
            raise ValueError(f"Could not resolve IDs: user_id={user_id}, role_id={role_id}")
        
        # Check if UserRole already exists
        if self._user_role_exists(user_id, role_id):
            logger.debug(f"UserRole already exists: {user_natural_key[0]} -> {role_natural_key[0]}")
            return
        
        # Insert UserRole via SQL
        uuid_val = str(uuid.uuid4())
        assigned_at = datetime.now()
        
        sql = """
            INSERT INTO users_userrole 
            (uuid, user_id, role_id, assigned_by_id, is_active, assigned_at, assignment_reason) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            uuid_val,
            user_id,
            role_id,
            assigned_by_id,
            fields.get('is_active', True),
            assigned_at,
            fields.get('assignment_reason', 'Restored from migration package')
        ]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        
        logger.info(f"✅ SQL Created UserRole: {user_natural_key[0]} -> {role_natural_key[0]}")
    
    def _restore_documents_via_sql(self, backup_data: List[Dict]):
        """Restore Documents using direct SQL."""
        logger.info("📄 Restoring Documents via SQL...")
        
        document_records = [r for r in backup_data if r.get('model') == 'documents.document']
        
        for record in document_records:
            try:
                self._create_document_via_sql(record)
                self.restoration_stats['documents_created'] += 1
                self.restoration_stats['sql_operations'] += 1
            except Exception as e:
                logger.warning(f"SQL Document creation failed: {str(e)}")
                self.restoration_stats['errors'].append(f"Document: {str(e)}")
    
    def _create_document_via_sql(self, record: Dict):
        """Create Document via direct SQL."""
        fields = record.get('fields', {})
        
        # Resolve natural keys to IDs
        author_natural_key = fields.get('author', [])  # ['author01']
        doc_type_natural_key = fields.get('document_type', [])  # ['POL']
        doc_source_natural_key = fields.get('document_source', [])  # ['Original Digital Draft']
        
        if not author_natural_key or not doc_type_natural_key or not doc_source_natural_key:
            raise ValueError(f"Missing document natural keys")
        
        # Get IDs via SQL
        author_id = self._get_user_id_by_username(author_natural_key[0])
        doc_type_id = self._get_document_type_id_by_code(doc_type_natural_key[0])
        doc_source_id = self._get_document_source_id_by_name(doc_source_natural_key[0])
        
        if not author_id or not doc_type_id or not doc_source_id:
            raise ValueError(f"Could not resolve document IDs: author_id={author_id}, doc_type_id={doc_type_id}, doc_source_id={doc_source_id}")
        
        # Check if Document already exists
        document_number = fields.get('document_number', f'DOC-{uuid.uuid4().hex[:8].upper()}')
        if self._document_exists(document_number):
            logger.debug(f"Document already exists: {document_number}")
            return
        
        # Insert Document via SQL
        uuid_val = str(uuid.uuid4())
        created_at = datetime.now()
        
        sql = """
            INSERT INTO documents_document 
            (uuid, document_number, title, description, version_major, version_minor, 
             document_type_id, document_source_id, status, priority, author_id, 
             file_name, file_path, file_size, file_checksum, mime_type, 
             is_active, is_controlled, requires_training, keywords, 
             reason_for_change, change_summary, obsolescence_reason, 
             created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            uuid_val,
            document_number,
            fields.get('title', 'Restored Document'),
            fields.get('description', ''),
            fields.get('version_major', 1),
            fields.get('version_minor', 0),
            doc_type_id,
            doc_source_id,
            fields.get('status', 'DRAFT'),
            fields.get('priority', 'normal'),
            author_id,
            fields.get('file_name', ''),
            fields.get('file_path', ''),
            fields.get('file_size', 0),
            fields.get('file_checksum', ''),
            fields.get('mime_type', ''),
            fields.get('is_active', True),
            fields.get('is_controlled', True),
            fields.get('requires_training', False),
            fields.get('keywords', ''),
            fields.get('reason_for_change', ''),
            fields.get('change_summary', ''),
            fields.get('obsolescence_reason', ''),
            created_at,
            created_at
        ]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        
        logger.info(f"✅ SQL Created Document: \"{fields.get('title')}\" by {author_natural_key[0]}")
    
    def _get_user_id_by_username(self, username: str) -> Optional[int]:
        """Get User ID by username."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users_user WHERE username = %s", [username])
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _get_role_id_by_name(self, name: str) -> Optional[int]:
        """Get Role ID by name."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users_role WHERE name = %s", [name])
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _get_document_type_id_by_code(self, code: str) -> Optional[int]:
        """Get DocumentType ID by code."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM documents_documenttype WHERE code = %s", [code])
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _get_document_source_id_by_name(self, name: str) -> Optional[int]:
        """Get DocumentSource ID by name."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM documents_documentsource WHERE name = %s", [name])
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _user_role_exists(self, user_id: int, role_id: int) -> bool:
        """Check if UserRole already exists."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM users_userrole WHERE user_id = %s AND role_id = %s", 
                [user_id, role_id]
            )
            return cursor.fetchone() is not None
    
    def _document_exists(self, document_number: str) -> bool:
        """Check if Document already exists."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM documents_document WHERE document_number = %s", 
                [document_number]
            )
            return cursor.fetchone() is not None
    
    def _generate_sql_report(self) -> Dict[str, Any]:
        """Generate SQL restoration report."""
        stats = self.restoration_stats
        
        report = {
            'status': 'completed',
            'user_roles_created': stats['user_roles_created'],
            'documents_created': stats['documents_created'],
            'sql_operations': stats['sql_operations'],
            'errors': stats['errors'],
            'success': stats['user_roles_created'] > 0 or stats['documents_created'] > 0
        }
        
        logger.info(f"🔧 SQL Restoration Complete:")
        logger.info(f"   UserRoles Created: {stats['user_roles_created']}")
        logger.info(f"   Documents Created: {stats['documents_created']}")
        logger.info(f"   SQL Operations: {stats['sql_operations']}")
        logger.info(f"   Errors: {len(stats['errors'])}")
        
        return report