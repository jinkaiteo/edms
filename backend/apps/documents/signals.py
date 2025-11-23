"""
Django Signals for Document Management (O1).

Handles automatic audit logging, file integrity checks,
and document lifecycle events for compliance.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    Document, DocumentVersion, DocumentDependency, 
    DocumentAccessLog, DocumentComment, DocumentAttachment
)


@receiver(post_save, sender=Document)
def create_document_audit_record(sender, instance, created, **kwargs):
    """Create audit record when document is created or updated."""
    from apps.audit.models import AuditTrail
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    action = 'CREATE' if created else 'UPDATE'
    current_user = get_current_user()
    
    AuditTrail.objects.create(
        content_object=instance,
        action=action,
        user=current_user,
        user_display_name=current_user.get_full_name() if current_user else 'System',
        ip_address=get_current_ip_address(),
        object_representation=str(instance),
        field_changes=getattr(instance, '_field_changes', {}),
        description=f"Document {action.lower()}: {instance.document_number}",
        module='O1',
        metadata={
            'document_number': instance.document_number,
            'title': instance.title,
            'version': instance.version_string,
            'status': instance.status,
            'document_type': instance.document_type.name if instance.document_type else None,
            'author': instance.author.username if instance.author else None,
        }
    )
    
    # Create version record for new documents
    if created:
        DocumentVersion.objects.create(
            document=instance,
            version_major=instance.version_major,
            version_minor=instance.version_minor,
            file_name=instance.file_name,
            file_path=instance.file_path,
            file_size=instance.file_size,
            file_checksum=instance.file_checksum,
            created_by=current_user or instance.author,
            status=instance.status,
            change_summary="Initial document creation",
            metadata={
                'initial_version': True,
                'document_type': instance.document_type.name if instance.document_type else None,
            }
        )


@receiver(post_save, sender=DocumentAccessLog)
def create_access_audit_record(sender, instance, created, **kwargs):
    """Create audit record for document access."""
    if created:
        from apps.audit.models import AuditLog
        
        severity = 'WARNING' if not instance.success else 'INFO'
        
        AuditTrail.objects.create(
            content_object=instance.document,
            action='VIEW' if instance.access_type == 'VIEW' else instance.access_type,
            user=instance.user,
            user_display_name=instance.user.get_full_name(),
            ip_address=instance.ip_address,
            session_id=instance.session_id,
            object_representation=str(instance.document),
            description=f"Document {instance.access_type.lower()}: {instance.document.document_number}",
            severity=severity,
            module='O1',
            metadata={
                'access_type': instance.access_type,
                'success': instance.success,
                'failure_reason': instance.failure_reason,
                'document_version': instance.document_version,
                'file_downloaded': instance.file_downloaded,
            }
        )


@receiver(post_save, sender=DocumentDependency)
def create_dependency_audit_record(sender, instance, created, **kwargs):
    """Create audit record for document dependencies."""
    from apps.audit.models import AuditLog
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    if created:
        current_user = get_current_user()
        
        AuditTrail.objects.create(
            content_object=instance.document,
            action='DEPENDENCY_ADDED',
            user=current_user or instance.created_by,
            user_display_name=(current_user or instance.created_by).get_full_name(),
            ip_address=get_current_ip_address(),
            object_representation=str(instance),
            description=f"Dependency added: {instance.document.document_number} {instance.dependency_type} {instance.depends_on.document_number}",
            module='O1',
            metadata={
                'source_document': instance.document.document_number,
                'target_document': instance.depends_on.document_number,
                'dependency_type': instance.dependency_type,
                'is_critical': instance.is_critical,
            }
        )


@receiver(post_delete, sender=DocumentDependency)
def create_dependency_removal_audit(sender, instance, **kwargs):
    """Create audit record for dependency removal."""
    from apps.audit.models import AuditLog
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    current_user = get_current_user()
    
    AuditTrail.objects.create(
        content_object=None,  # Object deleted
        action='DEPENDENCY_REMOVED',
        user=current_user,
        user_display_name=current_user.get_full_name() if current_user else 'System',
        ip_address=get_current_ip_address(),
        description=f"Dependency removed: {instance.document.document_number} {instance.dependency_type} {instance.depends_on.document_number}",
        module='O1',
        metadata={
            'source_document': instance.document.document_number,
            'target_document': instance.depends_on.document_number,
            'dependency_type': instance.dependency_type,
            'was_critical': instance.is_critical,
        }
    )


@receiver(post_save, sender=DocumentComment)
def create_comment_audit_record(sender, instance, created, **kwargs):
    """Create audit record for document comments."""
    if created:
        from apps.audit.models import AuditLog
        
        AuditTrail.objects.create(
            content_object=instance.document,
            action='COMMENT_ADDED',
            user=instance.author,
            user_display_name=instance.author.get_full_name(),
            object_representation=str(instance.document),
            description=f"Comment added to {instance.document.document_number}: {instance.subject}",
            module='O1',
            metadata={
                'comment_type': instance.comment_type,
                'subject': instance.subject,
                'requires_response': instance.requires_response,
                'is_internal': instance.is_internal,
                'page_number': instance.page_number,
                'section': instance.section,
            }
        )


@receiver(pre_save, sender=Document)
def track_document_field_changes(sender, instance, **kwargs):
    """Track field changes for audit purposes."""
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            changes = {}
            
            # Track specific field changes
            tracked_fields = [
                'title', 'description', 'status', 'version_major', 'version_minor',
                'reviewer', 'approver', 'effective_date', 'obsolete_date',
                'file_path', 'file_checksum', 'is_active'
            ]
            
            for field in tracked_fields:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(instance, field, None)
                
                # Handle foreign key fields
                if field in ['reviewer', 'approver'] and old_value:
                    old_value = old_value.username
                if field in ['reviewer', 'approver'] and new_value:
                    new_value = new_value.username
                
                if old_value != new_value:
                    changes[field] = {
                        'old': str(old_value) if old_value else None,
                        'new': str(new_value) if new_value else None
                    }
            
            # Store changes on instance for use in post_save signal
            instance._field_changes = changes
            
        except Document.DoesNotExist:
            # New document, no changes to track
            instance._field_changes = {}


@receiver(post_save, sender=DocumentAttachment)
def create_attachment_audit_record(sender, instance, created, **kwargs):
    """Create audit record for document attachments."""
    if created:
        from apps.audit.models import AuditLog
        
        AuditTrail.objects.create(
            content_object=instance.document,
            action='ATTACHMENT_ADDED',
            user=instance.uploaded_by,
            user_display_name=instance.uploaded_by.get_full_name(),
            object_representation=str(instance.document),
            description=f"Attachment added to {instance.document.document_number}: {instance.name}",
            module='O1',
            metadata={
                'attachment_name': instance.name,
                'attachment_type': instance.attachment_type,
                'file_name': instance.file_name,
                'file_size': instance.file_size,
                'mime_type': instance.mime_type,
            }
        )


@receiver(post_delete, sender=DocumentAttachment)
def create_attachment_removal_audit(sender, instance, **kwargs):
    """Create audit record for attachment removal."""
    from apps.audit.models import AuditLog
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    current_user = get_current_user()
    
    AuditTrail.objects.create(
        content_object=instance.document,
        action='ATTACHMENT_REMOVED',
        user=current_user,
        user_display_name=current_user.get_full_name() if current_user else 'System',
        ip_address=get_current_ip_address(),
        description=f"Attachment removed from {instance.document.document_number}: {instance.name}",
        module='O1',
        metadata={
            'attachment_name': instance.name,
            'attachment_type': instance.attachment_type,
            'file_name': instance.file_name,
            'was_public': instance.is_public,
        }
    )


# Document status change notifications
@receiver(post_save, sender=Document)
def handle_status_changes(sender, instance, created, **kwargs):
    """Handle document status changes and notifications."""
    if not created and hasattr(instance, '_field_changes'):
        changes = instance._field_changes
        
        # Check if status changed
        if 'status' in changes:
            old_status = changes['status']['old']
            new_status = changes['status']['new']
            
            # Handle specific status transitions
            if new_status == 'EFFECTIVE':
                # Document became effective
                instance.effective_date = timezone.now().date()
                instance.save(update_fields=['effective_date'])
                
                # Supersede previous version if applicable
                if instance.supersedes:
                    instance.supersedes.status = 'SUPERSEDED'
                    instance.supersedes.obsolete_date = timezone.now().date()
                    instance.supersedes.save(update_fields=['status', 'obsolete_date'])
                
                # TODO: Send notifications to dependent document owners
                
            elif new_status == 'OBSOLETE':
                # Document became obsolete
                instance.obsolete_date = timezone.now().date()
                instance.save(update_fields=['obsolete_date'])