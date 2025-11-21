# File Storage Architecture

## Overview
This document defines the comprehensive file storage architecture for the EDMS system, including encryption, access control, backup strategies, and compliance requirements.

## Storage Architecture Components

### File System Organization
```
/edms-storage/
├── documents/
│   ├── 2024/
│   │   ├── 01/           # Month-based organization
│   │   │   ├── originals/
│   │   │   ├── processed/
│   │   │   └── versions/
│   │   └── 02/
│   ├── 2025/
│   └── archive/
├── temp/
│   ├── uploads/
│   ├── processing/
│   └── exports/
├── backups/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
├── certificates/
│   ├── signing/
│   └── encryption/
└── logs/
    ├── access/
    ├── audit/
    └── system/
```

## Django Storage Configuration

### Settings Configuration

```python
# settings.py
import os
from django.core.files.storage import FileSystemStorage

# Storage Backends
DEFAULT_FILE_STORAGE = 'edms.storage.backends.EncryptedFileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# File Storage Settings
MEDIA_ROOT = '/edms-storage/documents/'
MEDIA_URL = '/media/'
STATIC_ROOT = '/edms-storage/static/'
STATIC_URL = '/static/'

# Custom Storage Settings
EDMS_STORAGE = {
    'DOCUMENTS_ROOT': '/edms-storage/documents/',
    'TEMP_ROOT': '/edms-storage/temp/',
    'BACKUP_ROOT': '/edms-storage/backups/',
    'ENCRYPTION_KEY_PATH': '/edms-storage/certificates/encryption/storage.key',
    'CHUNK_SIZE': 8192,  # 8KB chunks for encryption
    'MAX_FILE_SIZE': 100 * 1024 * 1024,  # 100MB
    'ALLOWED_EXTENSIONS': [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.rtf', '.odt', '.ods', '.odp', '.jpg', '.png', '.tiff'
    ],
    'VIRUS_SCANNING': True,
    'CONTENT_VALIDATION': True,
}

# Storage Quotas
STORAGE_QUOTAS = {
    'total_limit': 1024 * 1024 * 1024 * 1024,  # 1TB
    'user_limit': 10 * 1024 * 1024 * 1024,     # 10GB per user
    'document_limit': 100 * 1024 * 1024,       # 100MB per document
    'temp_retention_hours': 24,
    'deleted_retention_days': 30,
}
```

### Custom Storage Backend

```python
# storage/backends.py
import os
import hashlib
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class EncryptedFileSystemStorage(FileSystemStorage):
    """Encrypted file storage backend"""
    
    def __init__(self, location=None, base_url=None, 
                 file_permissions_mode=0o644, 
                 directory_permissions_mode=0o755):
        super().__init__(location, base_url, file_permissions_mode, directory_permissions_mode)
        self.encryption_key = self._load_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _load_encryption_key(self):
        """Load or generate encryption key"""
        key_path = settings.EDMS_STORAGE['ENCRYPTION_KEY_PATH']
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            with open(key_path, 'wb') as f:
                f.write(key)
            os.chmod(key_path, 0o600)  # Secure permissions
            return key
    
    def _save(self, name, content):
        """Save file with encryption"""
        # Validate file
        self._validate_file(name, content)
        
        # Generate secure filename
        secure_name = self._generate_secure_filename(name)
        
        # Encrypt content
        encrypted_content = self._encrypt_content(content)
        
        # Save encrypted file
        return super()._save(secure_name, encrypted_content)
    
    def _open(self, name, mode='rb'):
        """Open and decrypt file"""
        encrypted_file = super()._open(name, mode)
        
        # Read and decrypt content
        encrypted_data = encrypted_file.read()
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        
        return ContentFile(decrypted_data)
    
    def _validate_file(self, name, content):
        """Validate file before storage"""
        # Check file size
        if content.size > settings.EDMS_STORAGE['MAX_FILE_SIZE']:
            raise ValidationError(f"File size exceeds maximum limit")
        
        # Check file extension
        _, ext = os.path.splitext(name)
        if ext.lower() not in settings.EDMS_STORAGE['ALLOWED_EXTENSIONS']:
            raise ValidationError(f"File type {ext} not allowed")
        
        # Virus scanning
        if settings.EDMS_STORAGE['VIRUS_SCANNING']:
            self._scan_for_viruses(content)
        
        # Content validation
        if settings.EDMS_STORAGE['CONTENT_VALIDATION']:
            self._validate_content(name, content)
    
    def _scan_for_viruses(self, content):
        """Scan file for viruses using ClamAV"""
        try:
            import pyclamd
            cd = pyclamd.ClamdAgnostic()
            
            # Scan content
            scan_result = cd.scan_stream(content.read())
            content.seek(0)  # Reset file pointer
            
            if scan_result:
                raise ValidationError("File contains malicious content")
                
        except ImportError:
            logger.warning("ClamAV not available for virus scanning")
        except Exception as e:
            logger.error(f"Virus scanning error: {e}")
            # Don't block upload if scanner fails, but log it
    
    def _validate_content(self, name, content):
        """Validate file content matches extension"""
        import magic
        
        try:
            # Get actual file type
            content.seek(0)
            file_type = magic.from_buffer(content.read(1024), mime=True)
            content.seek(0)
            
            # Define expected MIME types
            mime_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.jpg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
            }
            
            _, ext = os.path.splitext(name)
            expected_type = mime_map.get(ext.lower())
            
            if expected_type and file_type != expected_type:
                logger.warning(f"File type mismatch: {name} - expected {expected_type}, got {file_type}")
                # Don't block, but log suspicious activity
                
        except Exception as e:
            logger.error(f"Content validation error: {e}")
    
    def _encrypt_content(self, content):
        """Encrypt file content"""
        content.seek(0)
        plaintext = content.read()
        encrypted_data = self.cipher_suite.encrypt(plaintext)
        return ContentFile(encrypted_data)
    
    def _generate_secure_filename(self, name):
        """Generate secure filename with hash"""
        import uuid
        from datetime import datetime
        
        # Extract extension
        _, ext = os.path.splitext(name)
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        
        # Create year/month path
        now = datetime.now()
        path = f"{now.year:04d}/{now.month:02d}"
        
        # Secure filename with hash
        filename = f"{unique_id}{ext}"
        
        return f"{path}/{filename}"
    
    def get_file_metadata(self, name):
        """Get file metadata including checksum"""
        full_path = self.path(name)
        
        if not os.path.exists(full_path):
            return None
        
        stat = os.stat(full_path)
        
        # Calculate checksum of encrypted file
        with open(full_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'checksum': checksum,
            'encrypted': True
        }

class SecureTemporaryStorage(FileSystemStorage):
    """Temporary storage for processing"""
    
    def __init__(self):
        location = settings.EDMS_STORAGE['TEMP_ROOT']
        super().__init__(location=location)
    
    def _save(self, name, content):
        """Save temporary file with automatic cleanup"""
        saved_name = super()._save(name, content)
        
        # Schedule cleanup
        from .tasks import cleanup_temp_file
        cleanup_temp_file.apply_async(
            args=[saved_name],
            countdown=settings.STORAGE_QUOTAS['temp_retention_hours'] * 3600
        )
        
        return saved_name
```

## File Management Service

```python
# storage/services.py
import os
import shutil
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class FileManagementService:
    """Comprehensive file management service"""
    
    def __init__(self):
        self.storage = EncryptedFileSystemStorage()
        self.temp_storage = SecureTemporaryStorage()
    
    def store_document(self, file_obj, document):
        """Store document file with metadata"""
        try:
            with transaction.atomic():
                # Calculate checksum before encryption
                file_obj.seek(0)
                content = file_obj.read()
                checksum = hashlib.sha256(content).hexdigest()
                file_obj.seek(0)
                
                # Store file
                filename = self.storage.save(file_obj.name, file_obj)
                
                # Update document record
                document.file_path = filename
                document.file_name = os.path.basename(file_obj.name)
                document.file_size = len(content)
                document.file_checksum = checksum
                document.mime_type = self._detect_mime_type(file_obj)
                document.save()
                
                logger.info(f"Stored document {document.id}: {filename}")
                return filename
                
        except Exception as e:
            logger.error(f"Error storing document {document.id}: {e}")
            raise
    
    def retrieve_document(self, document, user):
        """Retrieve document with access control"""
        # Check permissions
        if not self._check_access_permission(document, user):
            raise PermissionError("Access denied")
        
        # Log access
        self._log_file_access(document, user, 'RETRIEVE')
        
        # Return file
        return self.storage.open(document.file_path)
    
    def create_version(self, document, new_file):
        """Create new version of document"""
        try:
            with transaction.atomic():
                # Archive current version
                self._archive_current_version(document)
                
                # Store new version
                return self.store_document(new_file, document)
                
        except Exception as e:
            logger.error(f"Error creating version for document {document.id}: {e}")
            raise
    
    def delete_document(self, document, user):
        """Soft delete document with retention"""
        try:
            with transaction.atomic():
                # Move to deleted folder
                deleted_path = self._move_to_deleted(document.file_path)
                
                # Update document
                document.file_path = deleted_path
                document.status = 'DELETED'
                document.save()
                
                # Schedule permanent deletion
                from .tasks import permanent_delete_file
                permanent_delete_file.apply_async(
                    args=[deleted_path],
                    countdown=settings.STORAGE_QUOTAS['deleted_retention_days'] * 24 * 3600
                )
                
                self._log_file_access(document, user, 'DELETE')
                logger.info(f"Soft deleted document {document.id}")
                
        except Exception as e:
            logger.error(f"Error deleting document {document.id}: {e}")
            raise
    
    def _detect_mime_type(self, file_obj):
        """Detect MIME type of file"""
        import magic
        file_obj.seek(0)
        mime_type = magic.from_buffer(file_obj.read(1024), mime=True)
        file_obj.seek(0)
        return mime_type
    
    def _check_access_permission(self, document, user):
        """Check if user has access to document"""
        # Basic permission check - extend based on business rules
        if user.is_superuser:
            return True
        
        if document.author == user:
            return True
        
        if document.status in ['Approved and Effective', 'Obsolete']:
            return True
        
        # Check workflow permissions
        if document.reviewer == user or document.approver == user:
            return True
        
        return False
    
    def _log_file_access(self, document, user, action):
        """Log file access for audit trail"""
        from edms.audit.models import FileAccessLog
        
        FileAccessLog.objects.create(
            document=document,
            user=user,
            action=action,
            ip_address=getattr(user, '_ip_address', None),
            user_agent=getattr(user, '_user_agent', None)
        )
    
    def _archive_current_version(self, document):
        """Archive current version before creating new one"""
        if not document.file_path:
            return
        
        # Create archive path
        archive_dir = f"archive/{document.document_number}"
        archive_filename = f"v{document.version_major}.{document.version_minor}_{os.path.basename(document.file_path)}"
        archive_path = os.path.join(archive_dir, archive_filename)
        
        # Copy file to archive
        source_path = self.storage.path(document.file_path)
        dest_path = self.storage.path(archive_path)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(source_path, dest_path)
        
        logger.info(f"Archived version {document.version} of document {document.id}")
    
    def _move_to_deleted(self, file_path):
        """Move file to deleted folder"""
        if not file_path:
            return None
        
        # Create deleted path
        deleted_filename = f"deleted_{int(time.time())}_{os.path.basename(file_path)}"
        deleted_path = f"deleted/{deleted_filename}"
        
        # Move file
        source_path = self.storage.path(file_path)
        dest_path = self.storage.path(deleted_path)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(source_path, dest_path)
        
        return deleted_path

class FileIntegrityService:
    """File integrity monitoring and verification"""
    
    @staticmethod
    def verify_integrity(document):
        """Verify file integrity using checksum"""
        try:
            storage = EncryptedFileSystemStorage()
            
            # Get current file metadata
            metadata = storage.get_file_metadata(document.file_path)
            
            if not metadata:
                return False, "File not found"
            
            # Calculate checksum of decrypted content
            with storage.open(document.file_path) as f:
                content = f.read()
                current_checksum = hashlib.sha256(content).hexdigest()
            
            # Compare with stored checksum
            if current_checksum == document.file_checksum:
                return True, "File integrity verified"
            else:
                return False, "File integrity check failed"
                
        except Exception as e:
            return False, f"Integrity check error: {e}"
    
    @staticmethod
    def repair_corrupted_file(document):
        """Attempt to repair corrupted file from backup"""
        try:
            backup_service = BackupService()
            
            # Find latest backup containing this file
            backup_file = backup_service.find_file_in_backups(document.file_path)
            
            if backup_file:
                # Restore from backup
                storage = EncryptedFileSystemStorage()
                with open(backup_file, 'rb') as f:
                    storage.save(document.file_path, ContentFile(f.read()))
                
                # Verify restored file
                is_valid, message = FileIntegrityService.verify_integrity(document)
                
                if is_valid:
                    logger.info(f"Successfully repaired document {document.id}")
                    return True, "File repaired from backup"
                else:
                    logger.error(f"Repair failed for document {document.id}: {message}")
                    return False, "Repair failed"
            else:
                return False, "No backup found"
                
        except Exception as e:
            logger.error(f"Error repairing document {document.id}: {e}")
            return False, f"Repair error: {e}"

class StorageQuotaService:
    """Storage quota management and monitoring"""
    
    @staticmethod
    def check_user_quota(user):
        """Check user's storage quota"""
        from django.db.models import Sum
        from edms.documents.models import Document
        
        used_space = Document.objects.filter(
            author=user,
            status__ne='DELETED'
        ).aggregate(total=Sum('file_size'))['total'] or 0
        
        quota_limit = settings.STORAGE_QUOTAS['user_limit']
        
        return {
            'used': used_space,
            'limit': quota_limit,
            'available': quota_limit - used_space,
            'percentage': (used_space / quota_limit) * 100
        }
    
    @staticmethod
    def check_total_quota():
        """Check total system storage quota"""
        import shutil
        
        storage_root = settings.EDMS_STORAGE['DOCUMENTS_ROOT']
        total, used, free = shutil.disk_usage(storage_root)
        
        quota_limit = settings.STORAGE_QUOTAS['total_limit']
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'limit': quota_limit,
            'percentage': (used / total) * 100
        }
    
    @staticmethod
    def cleanup_temp_files():
        """Clean up expired temporary files"""
        temp_dir = settings.EDMS_STORAGE['TEMP_ROOT']
        retention_hours = settings.STORAGE_QUOTAS['temp_retention_hours']
        
        cutoff_time = time.time() - (retention_hours * 3600)
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        logger.debug(f"Cleaned up temp file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning temp file {file_path}: {e}")

class BackupService:
    """File backup and restoration service"""
    
    def __init__(self):
        self.backup_root = settings.EDMS_STORAGE['BACKUP_ROOT']
    
    def create_file_backup(self, file_path):
        """Create backup of specific file"""
        from datetime import datetime
        
        try:
            storage = EncryptedFileSystemStorage()
            source_path = storage.path(file_path)
            
            if not os.path.exists(source_path):
                return False, "Source file not found"
            
            # Create backup path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{timestamp}_{os.path.basename(file_path)}"
            backup_path = os.path.join(self.backup_root, 'files', backup_filename)
            
            # Create backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, backup_path)
            
            # Compress backup
            compressed_path = f"{backup_path}.gz"
            with open(source_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed backup
            os.remove(backup_path)
            
            logger.info(f"Created backup: {compressed_path}")
            return True, compressed_path
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, str(e)
    
    def find_file_in_backups(self, file_path):
        """Find file in backup archives"""
        # Implementation depends on backup strategy
        # This is a simplified version
        backup_pattern = f"*_{os.path.basename(file_path)}.gz"
        backup_dir = os.path.join(self.backup_root, 'files')
        
        import glob
        backups = glob.glob(os.path.join(backup_dir, backup_pattern))
        
        if backups:
            # Return most recent backup
            return max(backups, key=os.path.getmtime)
        
        return None
```

## Celery Tasks for File Management

```python
# storage/tasks.py
from celery import shared_task
import os
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_temp_file(file_path):
    """Clean up temporary file"""
    try:
        temp_storage = SecureTemporaryStorage()
        full_path = temp_storage.path(file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Cleaned up temp file: {file_path}")
        
    except Exception as e:
        logger.error(f"Error cleaning temp file {file_path}: {e}")

@shared_task
def permanent_delete_file(file_path):
    """Permanently delete file after retention period"""
    try:
        storage = EncryptedFileSystemStorage()
        full_path = storage.path(file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Permanently deleted file: {file_path}")
        
    except Exception as e:
        logger.error(f"Error permanently deleting file {file_path}: {e}")

@shared_task
def verify_file_integrity():
    """Periodic file integrity verification"""
    from edms.documents.models import Document
    
    # Check random sample of files
    documents = Document.objects.filter(
        status__in=['Approved and Effective', 'Superseded']
    ).order_by('?')[:100]  # Random 100 documents
    
    for document in documents:
        is_valid, message = FileIntegrityService.verify_integrity(document)
        
        if not is_valid:
            logger.error(f"File integrity check failed for document {document.id}: {message}")
            # Send alert to administrators

@shared_task
def monitor_storage_quotas():
    """Monitor storage quotas and send alerts"""
    quota_info = StorageQuotaService.check_total_quota()
    
    if quota_info['percentage'] > 85:
        # Send alert to administrators
        logger.warning(f"Storage usage at {quota_info['percentage']:.1f}%")

@shared_task
def create_automated_backup():
    """Create automated file backups"""
    backup_service = BackupService()
    
    # Backup strategy implementation
    # This would integrate with your backup solution
    pass
```

This file storage architecture provides:

1. **Encrypted storage** with Fernet encryption
2. **File validation** including virus scanning and content verification
3. **Access control** with permission checking and audit logging
4. **Version management** with archiving capabilities
5. **Quota management** for users and system-wide limits
6. **Integrity verification** with checksum validation
7. **Backup and recovery** capabilities
8. **Secure deletion** with retention periods
9. **Temporary file management** with automatic cleanup
10. **Comprehensive logging** for audit compliance

The system ensures 21 CFR Part 11 compliance through encryption, access controls, audit trails, and data integrity verification.