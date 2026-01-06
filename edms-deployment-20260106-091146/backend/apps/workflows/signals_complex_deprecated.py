"""
Django Signals for Workflow Management.

Handles automatic audit logging and workflow-related events
for compliance and integration with other modules.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import DocumentWorkflow, DocumentTransition
# Note: Complex workflow models (WorkflowInstance, WorkflowTask, etc.) are deprecated


@receiver(post_save, sender=DocumentWorkflow)
def create_workflow_audit_record(sender, instance, created, **kwargs):
    """Create audit record when document workflow is created or updated."""
    from apps.audit.models import AuditTrail
    from apps.audit.middleware import get_current_user, get_current_ip_address
    
    action = 'WORKFLOW_CREATED' if created else 'WORKFLOW_UPDATED'
    current_user = get_current_user()
    
    try:
        AuditTrail.objects.create(
            content_object=instance,
            action=action,
            user=current_user or instance.initiated_by,
            user_display_name=(current_user or instance.initiated_by).get_full_name(),
            ip_address=get_current_ip_address() or '127.0.0.1',
            object_representation=str(instance),
            description=f"Workflow {action.lower()}: {instance.workflow_type}",
            module='S5',
            metadata={
                'workflow_type': instance.workflow_type,
                'workflow_state': str(instance.current_state.code),
                'document': str(instance.document.document_number),
                'initiated_by': instance.initiated_by.username,
                'current_assignee': instance.current_assignee.username if instance.current_assignee else None,
            }
        )
    except Exception:
        # If audit logging fails, don't fail the workflow creation
        pass


@receiver(post_save, sender=DocumentTransition)
def create_transition_audit_record(sender, instance, created, **kwargs):
    """Create audit record for document workflow transitions."""
    if created:
        from apps.audit.models import AuditTrail
        
        try:
            AuditTrail.objects.create(
                content_object=instance.workflow,
                action='WORKFLOW_TRANSITION',
                user=instance.transitioned_by,
                user_display_name=instance.transitioned_by.get_full_name(),
                ip_address='127.0.0.1',  # Default IP for system actions
                description=f"Workflow transition: {instance.from_state.name} → {instance.to_state.name}",
                module='S5',
                metadata={
                    'from_state': instance.from_state.code,
                    'to_state': instance.to_state.code,
                    'comment': instance.comment,
                    'workflow_type': instance.workflow.workflow_type,
                    'document': str(instance.workflow.document.document_number),
                }
            )
        except Exception:
            # If audit logging fails, don't fail the transition
            pass


# Deprecated signal handlers for complex workflow models removed


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
                try:
                    from .services import get_simple_workflow_service
                    from apps.audit.middleware import get_current_user
                    
                    current_user = get_current_user()
                    if current_user:
                        # Check if workflow already exists
                        existing_workflow = DocumentWorkflow.objects.filter(document=instance).first()
                        if not existing_workflow:
                            workflow_service = get_simple_workflow_service()
                            workflow_service.start_review_workflow(instance, current_user)
                except Exception:
                    # If auto-start fails, just continue - user can start manually
                    pass