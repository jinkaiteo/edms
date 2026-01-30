"""
Document Management Models (O1)

This module contains the core document management models for the EDMS system,
including documents, versions, dependencies, and file storage with 21 CFR Part 11 compliance.
"""

import uuid
import os
import hashlib
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError


User = get_user_model()


class DocumentType(models.Model):
    """
    Document Type model for categorizing documents.
    
    Defines different types of documents with specific
    requirements for templates, approval, and retention.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, validators=[
        RegexValidator(regex=r'^[A-Z0-9_]+$', message='Code must be uppercase letters, numbers, or underscores')
    ])
    description = models.TextField(blank=True)
    
    # Template and approval requirements
    template_required = models.BooleanField(default=False)
    template_path = models.CharField(max_length=500, blank=True)
    approval_required = models.BooleanField(default=True)
    review_required = models.BooleanField(default=True)
    
    # Retention and compliance
    retention_years = models.IntegerField(
        default=7,
        validators=[MinValueValidator(1)],
        help_text="Number of years to retain documents of this type"
    )
    
    # Numbering scheme
    numbering_prefix = models.CharField(max_length=10, blank=True)
    numbering_format = models.CharField(
        max_length=50,
        default='{prefix}-{year}-{sequence:04d}',
        help_text="Format for auto-generated document numbers"
    )
    
    # Status and lifecycle
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_document_types'
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_types'
        verbose_name = _('Document Type')
        verbose_name_plural = _('Document Types')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def natural_key(self):
        """Return the natural key for this document type (code)"""
        return (self.code,)

    @classmethod
    def get_by_natural_key(cls, code):
        """Get document type by natural key (code)"""
        return cls.objects.get(code=code)

    def __str__(self):
        return f"{self.name} ({self.code})"


class DocumentSource(models.Model):
    """
    Document Source model for tracking origin of documents.
    
    Defines how documents entered the system for
    compliance and audit purposes.
    """
    
    SOURCE_TYPES = [
        ('original_digital', 'Original Digital'),
        ('scanned_paper', 'Scanned Paper Document'),
        ('imported_system', 'Imported from Another System'),
        ('email_attachment', 'Email Attachment'),
        ('web_upload', 'Web Upload'),
        ('api_creation', 'API Creation'),
        ('template_generation', 'Generated from Template'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES)
    description = models.TextField(blank=True)
    
    # Validation requirements
    requires_verification = models.BooleanField(default=False)
    requires_signature = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_sources'
        verbose_name = _('Document Source')
        verbose_name_plural = _('Document Sources')
        ordering = ['name']
    
    def natural_key(self):
        """Return the natural key for this document source (name)"""
        return (self.name,)

    @classmethod
    def get_by_natural_key(cls, name):
        """Get document source by natural key (name)"""
        return cls.objects.get(name=name)

    def __str__(self):
        return self.name


class DocumentManager(models.Manager):
    """Custom manager for Document model with additional query methods."""
    
    def active(self):
        """Return only active documents."""
        return self.filter(is_active=True)
    
    def by_status(self, status):
        """Filter documents by status."""
        return self.filter(status=status)
    
    def effective(self):
        """Return documents that are currently effective."""
        from django.utils import timezone
        return self.filter(
            status='EFFECTIVE',
            effective_date__lte=timezone.now().date()
        )
    
    def pending_approval(self):
        """Return documents pending approval."""
        return self.filter(status__in=['PENDING_REVIEW', 'PENDING_APPROVAL'])


class Document(models.Model):
    """
    Main Document model for the EDMS system.
    
    Represents a controlled document with full lifecycle management,
    version control, and compliance tracking.
    """
    
    DOCUMENT_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('REVIEW_COMPLETED', 'Review Completed'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('UNDER_APPROVAL', 'Under Approval'),
        ('APPROVED', 'Approved'),
        ('APPROVED_PENDING_EFFECTIVE', 'Approved Pending Effective'),
        ('EFFECTIVE', 'Effective'),
        ('SCHEDULED_FOR_OBSOLESCENCE', 'Scheduled for Obsolescence'),
        ('SUPERSEDED', 'Superseded'),
        ('OBSOLETE', 'Obsolete'),
        ('TERMINATED', 'Terminated'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Primary identification
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    document_number = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        help_text="Auto-generated unique document number"
    )
    
    # Document content
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated keywords for search")
    
    # Version control
    version_major = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text="Major version number (1-99)"
    )
    version_minor = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        help_text="Minor version number (0-99)"
    )
    
    # Document classification
    document_type = models.ForeignKey(
        DocumentType, 
        on_delete=models.PROTECT,
        related_name='documents'
    )
    document_source = models.ForeignKey(
        DocumentSource, 
        on_delete=models.PROTECT,
        related_name='documents'
    )
    
    # Document lifecycle
    status = models.CharField(
        max_length=30, 
        choices=DOCUMENT_STATUS_CHOICES, 
        default='DRAFT',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='normal'
    )
    
    # People and roles
    author = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='authored_documents'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='reviewed_documents'
    )
    approver = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='approved_documents'
    )
    
    # File information
    file_name = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True, db_index=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Encryption and security
    is_encrypted = models.BooleanField(default=False)
    encryption_metadata = models.JSONField(default=dict, blank=True)
    
    # Important dates
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True, db_index=True)
    review_due_date = models.DateField(null=True, blank=True, db_index=True)
    obsolete_date = models.DateField(null=True, blank=True)
    
    # Periodic Review fields (added for regulatory compliance)
    review_period_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text='Number of months between periodic reviews (null if no periodic review required)'
    )
    last_review_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Date of the most recent periodic review'
    )
    next_review_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Scheduled date for next periodic review'
    )
    last_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='last_reviewed_documents',
        help_text='User who completed the most recent periodic review'
    )
    
    # Obsolescence workflow fields
    obsolescence_date = models.DateField(null=True, blank=True, db_index=True, 
                                        help_text="Scheduled date for document obsolescence")
    obsolescence_reason = models.TextField(blank=True, 
                                         help_text="Reason provided for obsolescence")
    obsoleted_by = models.ForeignKey(User, on_delete=models.PROTECT, 
                                   null=True, blank=True,
                                   related_name='obsoleted_documents',
                                   help_text="User who initiated obsolescence")
    
    # Change management
    reason_for_change = models.TextField(blank=True)
    change_summary = models.TextField(blank=True)
    supersedes = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='superseded_by'
    )
    
    # Compliance and audit
    is_active = models.BooleanField(default=True, db_index=True)
    requires_training = models.BooleanField(default=False)
    is_controlled = models.BooleanField(default=True)
    
    # Search and indexing
    search_vector = models.TextField(blank=True)  # For PostgreSQL full-text search
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Managers
    objects = DocumentManager()
    
    class Meta:
        app_label = "documents"
        db_table = 'documents'
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['status', 'effective_date']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['document_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['review_due_date']),
            models.Index(fields=['file_checksum']),
            models.Index(fields=['is_active', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(version_major__gte=1, version_major__lte=99),
                name='version_major_range'
            ),
            models.CheckConstraint(
                check=models.Q(version_minor__gte=0, version_minor__lte=99),
                name='version_minor_range'
            ),
        ]
    
    def natural_key(self):
        """Return the natural key for this document (document_number)"""
        return (self.document_number,)
    
    @classmethod
    def get_by_natural_key(cls, document_number):
        """Get document by natural key (document_number)"""
        # Backup optimization module removed - using direct lookup
        # Old NaturalKeyOptimizer no longer available
        
        # Cache miss - do database lookup
        obj = cls.objects.get(document_number=document_number)
        
        # Cache the result
        NaturalKeyOptimizer.cache_natural_key_lookup(cls, (document_number,), obj)
        return obj
    
    def __str__(self):
        return f"{self.document_number} - {self.title} (v{self.version_major:02d}.{self.version_minor:02d})"
    
    @property
    def version_string(self):
        """Return formatted version string with zero padding."""
        return f"{self.version_major:02d}.{self.version_minor:02d}"
    
    @property
    def full_file_path(self):
        """Return the full file path."""
        if self.file_path:
            # Handle both new and legacy file path formats
            if self.file_path.startswith('storage/documents/'):
                # Legacy format: storage/documents/uuid.docx
                return os.path.join(settings.BASE_DIR, self.file_path)
            else:
                # New format: documents/uuid/filename.docx
                return os.path.join(settings.MEDIA_ROOT, self.file_path)
        return None
    
    def save(self, *args, **kwargs):
        """Override save to handle auto-generation and validation."""
        # Auto-generate document number if not set
        if not self.document_number:
            base_number = self.generate_document_number()
            # Always use zero-padded version suffix for consistency
            self.document_number = f"{base_number}-v{self.version_major:02d}.{self.version_minor:02d}"
        
        # Calculate file checksum if file exists
        if self.file_path and not self.file_checksum:
            self.file_checksum = self.calculate_file_checksum()
        
        super().save(*args, **kwargs)
    
    def generate_document_number(self, document_type=None):
        """Generate unique document number based on document type."""
        from django.utils import timezone
        
        # Use provided document_type or fall back to instance document_type
        doc_type = document_type or self.document_type
        if not doc_type:
            # Fallback numbering if no type specified
            year = timezone.now().year
            count = Document.objects.filter(created_at__year=year).count() + 1
            return f"DOC-{year}-{count:04d}"
        
        year = timezone.now().year
        prefix = doc_type.numbering_prefix or doc_type.code
        
        # Find the next sequence number for this type and year
        # Look for documents with the pattern {prefix}-{year}-{sequence} (ignoring version suffixes)
        existing_docs = Document.objects.filter(
            document_type=doc_type,
            document_number__startswith=f"{prefix}-{year}-"
        ).values_list('document_number', flat=True)
        
        # Extract sequence numbers from existing documents
        sequence_numbers = []
        for doc_number in existing_docs:
            try:
                # Remove version suffix if present (e.g., "MAN-2025-0001-v1.0" -> "MAN-2025-0001")
                base_number = doc_number.split('-v')[0] if '-v' in doc_number else doc_number
                # Extract the sequence part (last segment after splitting by '-')
                parts = base_number.split('-')
                if len(parts) >= 3:
                    seq_str = parts[-1]
                    if seq_str.isdigit():
                        sequence_numbers.append(int(seq_str))
            except (ValueError, IndexError):
                continue
        
        # Find the next available sequence number
        if sequence_numbers:
            next_seq = max(sequence_numbers) + 1
        else:
            next_seq = 1
        
        # Format using document type's numbering format
        return doc_type.numbering_format.format(
            prefix=prefix,
            year=year,
            sequence=next_seq
        )
    
    def calculate_file_checksum(self):
        """Calculate SHA-256 checksum of the file."""
        if not self.file_path:
            return ''
        
        file_path = self.full_file_path
        if not file_path or not os.path.exists(file_path):
            return ''
        
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ''
    
    def verify_file_integrity(self):
        """Verify file integrity using stored checksum."""
        if not self.file_checksum:
            return False
        
        current_checksum = self.calculate_file_checksum()
        return current_checksum == self.file_checksum
    
    def get_next_version(self, major_increment=False):
        """Get the next version numbers."""
        if major_increment:
            return self.version_major + 1, 0
        else:
            return self.version_major, self.version_minor + 1
    
    def can_edit(self, user):
        """Check if user can edit this document."""
        if not self.is_active:
            return False
        
        # Author can edit in DRAFT status
        if self.author == user and self.status == 'DRAFT':
            return True
        
        # Admin users can always edit
        if user.is_superuser:
            return True
        
        # Check for document admin permissions
        return user.user_roles.filter(
            role__module='O1',
            role__permission_level='admin',
            is_active=True
        ).exists()
    
    def can_approve(self, user):
        """Check if user can approve this document."""
        if self.status != 'PENDING_APPROVAL':
            return False
        
        # Segregation of Duties: Author cannot approve their own document
        if self.author == user and not user.is_superuser:
            return False
        
        # Assigned approver can approve
        if self.approver == user:
            return True
        
        # Check for approval permissions
        return user.user_roles.filter(
            role__module='O1',
            role__permission_level__in=['approve', 'admin'],
            is_active=True
        ).exists()
    
    def can_review(self, user):
        """Check if user can review this document."""
        if self.status not in ['PENDING_REVIEW', 'UNDER_REVIEW']:
            return False
        
        # Segregation of Duties: Author cannot review their own document
        if self.author == user and not user.is_superuser:
            return False
        
        # Assigned reviewer can review
        if self.reviewer == user:
            return True
        
        # Check for review permissions
        return user.user_roles.filter(
            role__module='O1',
            role__permission_level__in=['review', 'approve', 'admin'],
            is_active=True
        ).exists()
    
    def can_terminate(self, user):
        """Check if user can terminate this document."""
        # Only author can terminate
        if self.author != user:
            return False
        
        # Only terminable statuses (pre-effective)
        terminable_statuses = ['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'PENDING_APPROVAL']
        return self.status in terminable_statuses
    
    def get_family_versions(self):
        """
        Get all versions of this document's family.
        
        Returns all documents with the same base document number,
        ordered by version (newest first).
        """
        import re
        
        # Extract base document number
        base_number = re.sub(r'-v\d+\.\d+$', '', self.document_number)
        
        # Get all documents with this base number
        family_documents = Document.objects.filter(
            document_number__startswith=base_number
        ).order_by('-version_major', '-version_minor')
        
        # Filter to only documents that match the base pattern exactly
        # This prevents matching "SOP-2025-0001" with "SOP-2025-00010"
        family_docs_filtered = []
        for doc in family_documents:
            doc_base = re.sub(r'-v\d+\.\d+$', '', doc.document_number)
            if doc_base == base_number:
                family_docs_filtered.append(doc)
        
        return family_docs_filtered
    
    def can_obsolete_family(self):
        """
        Check if this document's entire family can be obsoleted.
        
        Checks ALL versions (including SUPERSEDED) for active dependencies.
        Returns validation result with details of blocking dependencies.
        
        Returns:
            dict: {
                'can_obsolete': bool,
                'reason': str,
                'blocking_dependencies': [
                    {
                        'version': str,
                        'document_number': str,
                        'status': str,
                        'dependent_count': int,
                        'dependents': [
                            {
                                'uuid': str,
                                'document_number': str,
                                'title': str,
                                'status': str,
                                'author': str
                            }
                        ]
                    }
                ]
            }
        """
        from apps.documents.models import DocumentDependency
        
        # Get all versions of this family
        all_versions = self.get_family_versions()
        
        blocking_dependencies = []
        
        # Check each version for dependencies
        for version in all_versions:
            # Get documents that depend on this version
            dependencies = DocumentDependency.objects.filter(
                depends_on=version,
                is_active=True
            ).select_related('document')
            
            # Filter to only EFFECTIVE or APPROVED_PENDING_EFFECTIVE dependents
            active_dependents = [
                dep.document for dep in dependencies
                if dep.document.status in ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'APPROVED_AND_EFFECTIVE']
            ]
            
            if active_dependents:
                blocking_dependencies.append({
                    'version': version.version_string,
                    'document_number': version.document_number,
                    'status': version.status,
                    'dependent_count': len(active_dependents),
                    'dependents': [
                        {
                            'uuid': str(dep.uuid),
                            'document_number': dep.document_number,
                            'title': dep.title,
                            'status': dep.status,
                            'author': dep.author.username if dep.author else None,
                        }
                        for dep in active_dependents
                    ]
                })
        
        # Check if there's a newer version that's not OBSOLETE/SUPERSEDED
        # If so, this version should be SUPERSEDED, not OBSOLETE
        import re
        base_number = re.sub(r'-v\d+\.\d+$', '', self.document_number)
        newer_versions = Document.objects.filter(
            document_number__startswith=base_number,
            version_major__gte=self.version_major
        ).exclude(
            status__in=['OBSOLETE', 'SUPERSEDED', 'TERMINATED']
        ).exclude(
            uuid=self.uuid
        )
        
        # Filter to ensure version is actually higher
        truly_newer = []
        for doc in newer_versions:
            if (doc.version_major > self.version_major or 
                (doc.version_major == self.version_major and doc.version_minor > self.version_minor)):
                truly_newer.append(doc)
        
        if truly_newer:
            newest = max(truly_newer, key=lambda d: (d.version_major, d.version_minor))
            return {
                'can_obsolete': False,
                'reason': f'Cannot obsolete: A newer version exists ({newest.document_number} v{newest.version_major}.{newest.version_minor}). This document should be marked as SUPERSEDED instead.',
                'blocking_dependencies': [],
                'newer_version': {
                    'uuid': str(newest.uuid),
                    'document_number': newest.document_number,
                    'version': f'{newest.version_major}.{newest.version_minor}',
                    'status': newest.status
                }
            }
        
        if blocking_dependencies:
            total_blocking = sum(bd['dependent_count'] for bd in blocking_dependencies)
            
            return {
                'can_obsolete': False,
                'reason': f'Cannot obsolete: {total_blocking} active document(s) depend on this family',
                'blocking_dependencies': blocking_dependencies,
                'affected_versions': len(blocking_dependencies)
            }
        
        return {
            'can_obsolete': True,
            'reason': 'No active dependencies found on any version',
            'blocking_dependencies': [],
            'affected_versions': 0
        }
    
    def get_family_dependency_summary(self):
        """
        Get a summary of all dependencies across the document family.
        
        Returns:
            dict: Summary of dependencies for all versions
        """
        all_versions = self.get_family_versions()
        
        summary = {
            'total_versions': len(all_versions),
            'versions': []
        }
        
        for version in all_versions:
            # Get dependents (documents that depend on this version)
            dependents = DocumentDependency.objects.filter(
                depends_on=version,
                is_active=True
            ).select_related('document').count()
            
            # Get dependencies (documents this version depends on)
            dependencies = DocumentDependency.objects.filter(
                document=version,
                is_active=True
            ).select_related('depends_on').count()
            
            summary['versions'].append({
                'version': version.version_string,
                'document_number': version.document_number,
                'status': version.status,
                'dependents_count': dependents,
                'dependencies_count': dependencies
            })
        
        return summary
    
    def terminate_document(self, terminated_by, reason=''):
        """Terminate document before it becomes effective."""
        if not self.can_terminate(terminated_by):
            raise ValueError("User cannot terminate this document")
        
        # Update document status
        old_status = self.status
        self.status = 'TERMINATED'
        self.obsoleted_by = terminated_by
        self.obsolescence_reason = f"TERMINATED: {reason}" if reason else "TERMINATED: No reason provided"
        self.is_active = False  # Mark as inactive
        
        # Save changes
        self.save()
        
        # Clean up pending workflow tasks for terminated document
        from ..workflows.models import WorkflowInstance
        # WorkflowTask removed - using document filters instead
        from django.contrib.contenttypes.models import ContentType
        
        # Get all active workflow instances for this document
        content_type = ContentType.objects.get_for_model(self)
        workflow_instances = WorkflowInstance.objects.filter(
            content_type=content_type,
            object_id=str(self.id),
            is_active=True
        )
        
        # Cancel all pending tasks for this document
        cancelled_tasks_count = 0
        for instance in workflow_instances:
            pending_tasks = instance.tasks.filter(status__in=['PENDING', 'IN_PROGRESS'])
            for task in pending_tasks:
                task.status = 'CANCELLED'
                task.completed_at = tz.now()
                task.completion_note = f'Task cancelled due to document termination: {reason}'
                task.save()
                cancelled_tasks_count += 1
            
            # Mark workflow instances as completed
            instance.complete_workflow(f'Document terminated: {reason}')
        
        # Create audit trail
        from django.utils import timezone as tz
        from ..audit.models import AuditTrail
        
        AuditTrail.objects.create(
            user=terminated_by,
            action='DOCUMENT_TERMINATED',
            content_object=self,
            description=f'Document {self.document_number} terminated by author. Cancelled {cancelled_tasks_count} pending workflow tasks.',
            field_changes={
                'old_status': old_status,
                'new_status': 'TERMINATED',
                'termination_reason': reason,
                'terminated_at': tz.now().isoformat(),
                'cancelled_tasks_count': cancelled_tasks_count
            },
            ip_address=getattr(terminated_by, '_current_ip', None),
            user_agent=getattr(terminated_by, '_current_user_agent', 'System')
        )
        
        # Trigger automatic workflow task cleanup after termination
        try:
            from ..scheduler.automated_tasks import cleanup_workflow_tasks
            # Schedule cleanup to run in 30 seconds to ensure all related changes are committed
            cleanup_workflow_tasks.apply_async(
                kwargs={'dry_run': False},
                countdown=30
            )
            print(f"🧹 Scheduled automatic workflow cleanup after termination of {self.document_number}")
        except Exception as e:
            print(f"⚠️ Failed to schedule automatic cleanup: {str(e)}")
            # Don't fail termination if cleanup scheduling fails
            pass
        
        return True


class DocumentVersion(models.Model):
    """
    Document Version History model.
    
    Maintains a complete history of all document versions
    for compliance and audit purposes.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE,
        related_name='versions'
    )
    
    # Version information
    version_major = models.PositiveIntegerField()
    version_minor = models.PositiveIntegerField()
    version_comment = models.TextField(blank=True)
    
    # File information for this version
    file_name = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True)
    
    # Version lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=Document.DOCUMENT_STATUS_CHOICES)
    
    # Change tracking
    change_summary = models.TextField(blank=True)
    reason_for_change = models.TextField(blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_versions'
        verbose_name = _('Document Version')
        verbose_name_plural = _('Document Versions')
        ordering = ['-version_major', '-version_minor', '-created_at']
        unique_together = ['document', 'version_major', 'version_minor']
        indexes = [
            models.Index(fields=['document', 'version_major', 'version_minor']),
            models.Index(fields=['created_at']),
            models.Index(fields=['created_by']),
        ]
    
    def natural_key(self):
        """Return the natural key for this document version"""
        return (
            self.document.natural_key()[0],  # Document number
            self.version_major,
            self.version_minor
        )

    @classmethod
    def get_by_natural_key(cls, document_number, version_major, version_minor):
        """Get document version by natural key"""
        from apps.documents.models import Document
        document = Document.objects.get(document_number=document_number)
        return cls.objects.get(
            document=document,
            version_major=version_major,
            version_minor=version_minor
        )

    def __str__(self):
        return f"{self.document.document_number} v{self.version_major:02d}.{self.version_minor:02d}"
    
    @property
    def version_string(self):
        """Return formatted version string with zero padding."""
        return f"{self.version_major:02d}.{self.version_minor:02d}"

class DocumentDependency(models.Model):
    """
    Document Dependency model for tracking relationships between documents.
    
    Manages dependencies and relationships between documents
    to ensure proper change control and impact analysis.
    """
    
    DEPENDENCY_TYPES = [
        ('REFERENCE', 'References'),
        ('TEMPLATE', 'Uses as Template'),
        ('SUPERSEDES', 'Supersedes'),
        ('INCORPORATES', 'Incorporates'),
        ('SUPPORTS', 'Supports'),
        ('IMPLEMENTS', 'Implements'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='dependencies'
    )
    depends_on = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='dependents'
    )
    dependency_type = models.CharField(
        max_length=20,
        choices=DEPENDENCY_TYPES,
        default='REFERENCE'
    )
    
    # Dependency details
    description = models.TextField(blank=True)
    is_critical = models.BooleanField(
        default=False,
        help_text="Critical dependencies require notification on changes"
    )
    
    # Lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_dependencies'
        verbose_name = _('Document Dependency')
        verbose_name_plural = _('Document Dependencies')
        unique_together = ['document', 'depends_on', 'dependency_type']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'dependency_type']),
            models.Index(fields=['depends_on', 'is_critical']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(document=models.F('depends_on')),
                name='no_self_dependency'
            ),
        ]
    
    def natural_key(self):
        """Return the natural key for this document dependency"""
        return (
            self.document.natural_key()[0],     # Source document number
            self.depends_on.natural_key()[0],   # Target document number
            self.dependency_type                # Dependency type
        )

    @classmethod
    def get_by_natural_key(cls, source_doc_number, target_doc_number, dependency_type):
        """Get document dependency by natural key"""
        source_doc = Document.objects.get(document_number=source_doc_number)
        target_doc = Document.objects.get(document_number=target_doc_number)
        return cls.objects.get(
            document=source_doc,
            depends_on=target_doc,
            dependency_type=dependency_type
        )

    def __str__(self):
        return f"{self.document.document_number} {self.get_dependency_type_display()} {self.depends_on.document_number}"
    
    def clean(self):
        """Validate dependency to prevent circular references."""
        if self.document_id == self.depends_on_id:
            raise ValidationError("Document cannot depend on itself")
        
        # Check for circular dependencies using comprehensive algorithm
        if self._would_create_circular_dependency():
            raise ValidationError("Circular dependency detected")
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure validation is always called.
        This is a safety net to prevent circular dependencies even if clean() is bypassed.
        """
        # Always run validation before saving (unless explicitly skipped)
        if not kwargs.pop('skip_validation', False):
            self.clean()
        super().save(*args, **kwargs)
    
    def _would_create_circular_dependency(self):
        """
        Check if adding this dependency would create a circular dependency.
        Uses base document number approach for robust version-aware detection.
        """
        if not self.document_id or not self.depends_on_id:
            return False
        
        try:
            from_doc = Document.objects.get(id=self.document_id)
            to_doc = Document.objects.get(id=self.depends_on_id)
            
            # Extract base document numbers (remove version suffixes)
            from_base_number = self._get_base_document_number(from_doc.document_number)
            to_base_number = self._get_base_document_number(to_doc.document_number)
            
            # RULE 1: Document cannot depend on another version of itself
            if from_base_number == to_base_number:
                return True
            
            # RULE 2: Check if target document family has any dependencies back to source family
            return self._has_base_number_circular_dependency(from_base_number, to_base_number)
            
        except Document.DoesNotExist:
            # Fallback to ID-based checking if documents not found
            dependency_graph = self._build_dependency_graph()
            return self._has_path(dependency_graph, self.depends_on_id, self.document_id)
    
    def _get_base_document_number(self, document_number):
        """
        Extract base document number without version suffix.
        POL-2025-0001-v02.00 -> POL-2025-0001
        """
        if '-v' in document_number:
            return document_number.split('-v')[0]
        return document_number
    
    def _has_base_number_circular_dependency(self, from_base_number, to_base_number):
        """
        Check if target document family has any dependencies back to source family.
        Simple and robust base number approach.
        
        Example: POL-2025-0001 v2.0 → SOP-2025-0001
        - from_base_number = "POL-2025-0001" 
        - to_base_number = "SOP-2025-0001"
        - Check: Does any version of SOP-2025-0001 depend on any version of POL-2025-0001?
        """
        # Get all active dependencies
        all_dependencies = DocumentDependency.objects.filter(is_active=True).select_related('document', 'depends_on')
        
        # Build base number dependency map
        base_dependencies = {}
        for dep in all_dependencies:
            dep_from_base = self._get_base_document_number(dep.document.document_number)
            dep_to_base = self._get_base_document_number(dep.depends_on.document_number)
            
            if dep_from_base not in base_dependencies:
                base_dependencies[dep_from_base] = set()
            base_dependencies[dep_from_base].add(dep_to_base)
        
        # Check if target document family depends on source document family
        # Use simple BFS/DFS on base document numbers instead of IDs
        visited = set()
        
        def has_dependency_path(current_base, target_base):
            if current_base == target_base:
                return True
            
            if current_base in visited:
                return False
            
            visited.add(current_base)
            
            # Check all dependencies of current document family
            for dependent_base in base_dependencies.get(current_base, []):
                if has_dependency_path(dependent_base, target_base):
                    return True
            
            return False
        
        return has_dependency_path(to_base_number, from_base_number)
    
    def _build_dependency_graph(self):
        """
        Build a dependency graph as an adjacency list.
        Returns: dict where keys are document IDs and values are lists of dependent document IDs.
        """
        graph = {}
        
        # Get all active dependencies (excluding current one if updating)
        dependencies = DocumentDependency.objects.filter(is_active=True)
        if self.pk:  # If updating existing dependency, exclude it from graph
            dependencies = dependencies.exclude(pk=self.pk)
        
        for dep in dependencies:
            if dep.document_id not in graph:
                graph[dep.document_id] = []
            graph[dep.document_id].append(dep.depends_on_id)
        
        return graph
    
    def _has_path(self, graph, start_id, target_id, visited=None):
        """
        Check if there's a path from start_id to target_id in the dependency graph.
        Uses depth-first search with cycle detection.
        """
        if visited is None:
            visited = set()
        
        if start_id == target_id:
            return True
        
        if start_id in visited:
            return False  # Cycle detected, but not the one we're looking for
        
        visited.add(start_id)
        
        # Check all documents that start_id depends on
        for neighbor_id in graph.get(start_id, []):
            if self._has_path(graph, neighbor_id, target_id, visited.copy()):
                return True
        
        return False
    
    @classmethod
    def detect_circular_dependencies(cls):
        """
        Analyze the entire dependency system to detect existing circular dependencies.
        Uses base document number approach for robust version-aware detection.
        Returns: list of circular dependency chains found (base document numbers).
        """
        all_dependencies = cls.objects.filter(is_active=True).select_related('document', 'depends_on')
        
        # Build base number dependency graph
        base_dependency_graph = {}
        for dep in all_dependencies:
            from_base = cls._get_base_document_number_static(dep.document.document_number)
            to_base = cls._get_base_document_number_static(dep.depends_on.document_number)
            
            if from_base not in base_dependency_graph:
                base_dependency_graph[from_base] = set()
            base_dependency_graph[from_base].add(to_base)
        
        # Find all cycles using base document numbers
        cycles = []
        visited_global = set()
        
        for base_doc in base_dependency_graph:
            if base_doc not in visited_global:
                cycle = cls._find_base_cycle_from_node(base_dependency_graph, base_doc, visited_global)
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    @classmethod
    def _get_base_document_number_static(cls, document_number):
        """
        Static version of _get_base_document_number for class method use.
        Extract base document number without version suffix.
        """
        if '-v' in document_number:
            return document_number.split('-v')[0]
        return document_number
    
    @classmethod
    def _find_base_cycle_from_node(cls, graph, start_base, visited_global):
        """
        Find cycles starting from a specific base document number using DFS.
        Returns the cycle path if found, None otherwise.
        """
        visited_path = set()
        path = []
        
        def dfs(base_doc):
            if base_doc in visited_path:
                # Found a cycle - return the cycle portion
                try:
                    cycle_start_index = path.index(base_doc)
                    return path[cycle_start_index:] + [base_doc]
                except ValueError:
                    return [base_doc]  # Single node cycle
            
            if base_doc in visited_global:
                return None
            
            visited_path.add(base_doc)
            path.append(base_doc)
            
            for neighbor in graph.get(base_doc, set()):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            
            path.pop()
            visited_path.remove(base_doc)
            visited_global.add(base_doc)
            return None
        
        return dfs(start_base)
    
    @classmethod
    def _find_cycle_from_node(cls, graph, start_id, visited_global):
        """
        Find cycles starting from a specific node using DFS.
        Returns the cycle path if found, None otherwise.
        """
        visited_path = set()
        path = []
        
        def dfs(node_id):
            if node_id in visited_path:
                # Found a cycle - return the cycle portion
                cycle_start_index = path.index(node_id)
                return path[cycle_start_index:] + [node_id]
            
            if node_id in visited_global:
                return None
            
            visited_path.add(node_id)
            path.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            
            path.pop()
            visited_path.remove(node_id)
            visited_global.add(node_id)
            return None
        
        return dfs(start_id)
    
    @classmethod
    def get_dependency_chain(cls, document_id, max_depth=10):
        """
        Get the complete dependency chain for a document using BFS.
        
        Uses Breadth-First Search to explore ALL branches at each depth level
        before going deeper. This ensures complete width coverage and detects
        all dependencies/dependents at each level.
        
        Args:
            document_id: Starting document ID
            max_depth: Maximum depth to traverse (default 10)
            
        Returns:
            dict with 'dependencies' and 'dependents' lists containing:
                - document_id: Document ID
                - depth: Depth level (1-based)
                - type: Dependency type
                - is_critical: Boolean flag
        """
        dependencies = {}
        dependents = {}
        
        # Build bidirectional graph
        for dep in cls.objects.filter(is_active=True):
            # Forward dependencies (what this document depends on)
            if dep.document_id not in dependencies:
                dependencies[dep.document_id] = []
            dependencies[dep.document_id].append({
                'id': dep.depends_on_id,
                'type': dep.dependency_type,
                'is_critical': dep.is_critical
            })
            
            # Reverse dependencies (what depends on this document)
            if dep.depends_on_id not in dependents:
                dependents[dep.depends_on_id] = []
            dependents[dep.depends_on_id].append({
                'id': dep.document_id,
                'type': dep.dependency_type,
                'is_critical': dep.is_critical
            })
        
        def get_chain_bfs(start_doc_id, chain_type):
            """
            Breadth-First Search to get complete dependency chain.
            Explores all nodes at depth N before going to depth N+1.
            This ensures we see ALL branches at each level.
            
            Returns parent-child relationships for proper edge rendering.
            """
            source = dependencies if chain_type == 'dependencies' else dependents
            visited = set()
            result = []
            
            # Queue: (document_id, depth, parent_id)
            # BFS uses FIFO (First In, First Out)
            queue = [(start_doc_id, 0, None)]
            visited.add(start_doc_id)
            
            while queue:
                current_id, current_depth, parent_id = queue.pop(0)  # BFS: FIFO
                
                # Skip if we've reached max depth
                if current_depth >= max_depth:
                    continue
                
                # Get all direct dependencies/dependents of current node
                for item in source.get(current_id, []):
                    next_id = item['id']
                    next_depth = current_depth + 1
                    
                    # Add to result with parent information for edge creation
                    result.append({
                        'document_id': next_id,
                        'parent_id': current_id,  # ← Added: who this connects to
                        'depth': next_depth,
                        'type': item['type'],
                        'is_critical': item['is_critical']
                    })
                    
                    # Only explore further if not visited (prevents infinite loops)
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, next_depth, current_id))
            
            return result
        
        return {
            'dependencies': get_chain_bfs(document_id, 'dependencies'),
            'dependents': get_chain_bfs(document_id, 'dependents')
        }


class DocumentAccessLog(models.Model):
    """
    Document Access Log for tracking document access for compliance.
    
    Logs all access to documents for audit trail and
    regulatory compliance requirements.
    """
    
    ACCESS_TYPES = [
        ('VIEW', 'View'),
        ('DOWNLOAD', 'Download'),
        ('PRINT', 'Print'),
        ('EXPORT', 'Export'),
        ('EDIT', 'Edit'),
        ('DELETE', 'Delete'),
        ('SHARE', 'Share'),
        ('COMMENT', 'Comment'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='document_accesses'
    )
    
    # Access details
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    access_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True, null=True)
    
    # Access result
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    # Additional context
    document_version = models.CharField(max_length=20, blank=True)
    file_downloaded = models.BooleanField(default=False)
    access_duration = models.DurationField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_access_logs'
        verbose_name = _('Document Access Log')
        verbose_name_plural = _('Document Access Logs')
        ordering = ['-access_timestamp']
        indexes = [
            models.Index(fields=['document', 'access_timestamp']),
            models.Index(fields=['user', 'access_timestamp']),
            models.Index(fields=['access_type', 'access_timestamp']),
            models.Index(fields=['ip_address', 'access_timestamp']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.access_type} {self.document.document_number} at {self.access_timestamp}"


class DocumentComment(models.Model):
    """
    Document Comment model for review and collaboration.
    
    Allows reviewers and collaborators to add comments
    during the document review process.
    """
    
    COMMENT_TYPES = [
        ('GENERAL', 'General Comment'),
        ('REVIEW', 'Review Comment'),
        ('APPROVAL', 'Approval Comment'),
        ('REJECTION', 'Rejection Comment'),
        ('QUESTION', 'Question'),
        ('SUGGESTION', 'Suggestion'),
        ('CORRECTION', 'Correction'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='document_comments'
    )
    
    # Comment content
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES, default='GENERAL')
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Context and location
    page_number = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=100, blank=True)
    line_reference = models.CharField(max_length=50, blank=True)
    
    # Comment lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='resolved_comments'
    )
    
    # Threading support
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Status and visibility
    is_internal = models.BooleanField(default=False)
    requires_response = models.BooleanField(default=False)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_comments'
        verbose_name = _('Document Comment')
        verbose_name_plural = _('Document Comments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['comment_type', 'is_resolved']),
            models.Index(fields=['requires_response', 'is_resolved']),
        ]
    
    def natural_key(self):
        """Return the natural key for this document comment"""
        return (
            self.document.natural_key()[0],  # Document number
            str(self.id)                     # Comment ID (unique per document)
        )

    @classmethod
    def get_by_natural_key(cls, document_number, comment_id):
        """Get document comment by natural key"""
        document = Document.objects.get(document_number=document_number)
        return cls.objects.get(document=document, id=comment_id)

    def __str__(self):
        return f"Comment on {self.document.document_number} by {self.author.username}"


class DocumentAttachment(models.Model):
    """
    Document Attachment model for supporting files.
    
    Manages additional files attached to documents
    such as appendices, supporting data, or references.
    """
    
    ATTACHMENT_TYPES = [
        ('APPENDIX', 'Appendix'),
        ('SUPPORTING_DATA', 'Supporting Data'),
        ('REFERENCE', 'Reference Material'),
        ('TEMPLATE', 'Template'),
        ('FORM', 'Form'),
        ('CHECKLIST', 'Checklist'),
        ('WORKSHEET', 'Worksheet'),
        ('IMAGE', 'Image'),
        ('DIAGRAM', 'Diagram'),
        ('OTHER', 'Other'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    
    # Attachment details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    
    # File information
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    file_checksum = models.CharField(max_length=64, db_index=True)
    mime_type = models.CharField(max_length=100)
    
    # Upload information
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Status and visibility
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    requires_signature = models.BooleanField(default=False)
    
    # Version information
    version = models.PositiveIntegerField(default=1)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "documents"
        db_table = 'document_attachments'
        verbose_name = _('Document Attachment')
        verbose_name_plural = _('Document Attachments')
        ordering = ['name']
        indexes = [
            models.Index(fields=['document', 'attachment_type']),
            models.Index(fields=['file_checksum']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.document.document_number})"
    
    @property
    def full_file_path(self):
        """Return the full file path."""
        return os.path.join(settings.MEDIA_ROOT, self.file_path)
    
    def calculate_checksum(self):
        """Calculate and update file checksum."""
        if os.path.exists(self.full_file_path):
            sha256_hash = hashlib.sha256()
            with open(self.full_file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            self.file_checksum = sha256_hash.hexdigest()
    
    def verify_integrity(self):
        """Verify file integrity using stored checksum."""
        if not os.path.exists(self.full_file_path):
            return False
        
        sha256_hash = hashlib.sha256()
        with open(self.full_file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest() == self.file_checksum
