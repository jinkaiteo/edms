"""
Django Signals for Workflow Management.

Handles automatic audit logging and workflow-related events
for compliance and integration with other modules.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    WorkflowInstance, WorkflowTransition, WorkflowTask,
    WorkflowNotification
)


@receiver(post_save, sender=WorkflowInstance)
def create_workflow_audit_record(sender, instance, created, **kwargs):
    """Create audit record when workflow instance is created or updated."""
    from apps.audit.models import AuditLog
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    action = 'WORKFLOW_CREATED' if created else 'WORKFLOW_UPDATED'
    current_user = get_current_user()
    
    AuditLog.objects.create(
        content_object=instance,
        action=action,
        user=current_user or instance.initiated_by,
        user_display_name=(current_user or instance.initiated_by).get_full_name(),
        ip_address=get_current_ip_address(),
        object_representation=str(instance),
        description=f"Workflow {action.lower()}: {instance.workflow_type.name}",
        module='S5',
        metadata={
            'workflow_type': instance.workflow_type.workflow_type,
            'workflow_state': str(instance.state),
            'content_object': str(instance.content_object) if instance.content_object else None,
            'initiated_by': instance.initiated_by.username,
            'current_assignee': instance.current_assignee.username if instance.current_assignee else None,
        }
    )


@receiver(post_save, sender=WorkflowTransition)
def create_transition_audit_record(sender, instance, created, **kwargs):
    """Create audit record for workflow transitions."""
    if created:
        from apps.audit.models import AuditLog
        
        AuditLog.objects.create(
            content_object=instance.workflow_instance,
            action='WORKFLOW_TRANSITION',
            user=instance.transitioned_by,
            user_display_name=instance.transitioned_by.get_full_name(),
            ip_address=instance.ip_address,
            session_id=instance.session_id,
            description=f"Workflow transition: {instance.from_state} → {instance.to_state}",
            module='S5',
            metadata={
                'transition_name': instance.transition_name,
                'from_state': instance.from_state,
                'to_state': instance.to_state,
                'comment': instance.comment,
                'workflow_type': instance.workflow_instance.workflow_type.workflow_type,
            }
        )


@receiver(post_save, sender=WorkflowTask)
def create_task_audit_record(sender, instance, created, **kwargs):
    """Create audit record for workflow task events."""
    from apps.audit.models import AuditLog
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    if created:
        action = 'TASK_CREATED'
        description = f"Task created: {instance.name}"
    elif instance.status == 'COMPLETED' and hasattr(instance, '_was_completed'):
        action = 'TASK_COMPLETED'
        description = f"Task completed: {instance.name}"
    else:
        return  # Don't log other updates
    
    current_user = get_current_user()
    
    AuditLog.objects.create(
        content_object=instance.workflow_instance,
        action=action,
        user=current_user or instance.assigned_to,
        user_display_name=(current_user or instance.assigned_to).get_full_name(),
        ip_address=get_current_ip_address(),
        description=description,
        module='S5',
        metadata={
            'task_name': instance.name,
            'task_type': instance.task_type,
            'assigned_to': instance.assigned_to.username,
            'assigned_by': instance.assigned_by.username,
            'status': instance.status,
            'due_date': instance.due_date.isoformat() if instance.due_date else None,
            'completion_note': instance.completion_note if instance.status == 'COMPLETED' else None,
        }
    )


@receiver(pre_save, sender=WorkflowTask)
def track_task_completion(sender, instance, **kwargs):
    """Track when tasks are completed for audit purposes."""
    if instance.pk:
        try:
            old_instance = WorkflowTask.objects.get(pk=instance.pk)
            if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
                instance._was_completed = True
        except WorkflowTask.DoesNotExist:
            pass


@receiver(post_save, sender=WorkflowNotification)
def log_notification_events(sender, instance, created, **kwargs):
    """Log workflow notification events for audit."""
    if created:
        from apps.audit.models import AuditLog
        
        AuditLog.objects.create(
            content_object=instance.workflow_instance,
            action='NOTIFICATION_SENT',
            user=instance.recipient,
            description=f"Workflow notification sent: {instance.subject}",
            severity='INFO',
            module='S5',
            metadata={
                'notification_type': instance.notification_type,
                'recipient': instance.recipient.username,
                'subject': instance.subject,
                'workflow_type': instance.workflow_instance.workflow_type.workflow_type,
            }
        )


# Integration with document status changes
@receiver(post_save, sender='documents.Document')
def handle_document_status_workflow_integration(sender, instance, created, **kwargs):
    """Handle workflow integration when document status changes."""
    if not created and hasattr(instance, '_field_changes'):
        changes = instance._field_changes
        
        # Check if status changed
        if 'status' in changes:
            old_status = changes['status']['old']
            new_status = changes['status']['new']
            
            # Auto-trigger workflows based on status changes
            if new_status == 'PENDING_REVIEW':
                # Auto-start review workflow if not already active
                from .services import document_workflow_service
                from apps.audit.middleware import get_current_user
                
                current_user = get_current_user()
                if current_user and not document_workflow_service._get_active_workflow(instance, 'REVIEW'):
                    document_workflow_service.start_review_workflow(instance, current_user)