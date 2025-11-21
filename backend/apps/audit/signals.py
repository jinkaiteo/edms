"""
Django signals for automatic audit trail logging.

Automatically captures model changes, user actions, and system events
for compliance with 21 CFR Part 11 requirements.
"""

import json
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.serializers import serialize
from django.forms.models import model_to_dict

from .services import audit_service
from .middleware import get_audit_context
from apps.documents.models import Document, DocumentVersion, ElectronicSignature
from apps.workflows.models import WorkflowInstance, WorkflowTransition, WorkflowTask
from apps.users.models import UserRole, Role

User = get_user_model()


# Store original values for comparison in post_save
_pre_save_instances = {}


@receiver(pre_save)
def store_original_instance(sender, instance, **kwargs):
    """Store original instance values before save for audit comparison."""
    # Only track specific models that require audit trail
    audit_models = [
        Document, DocumentVersion, ElectronicSignature,
        WorkflowInstance, WorkflowTransition, WorkflowTask,
        User, UserRole, Role
    ]
    
    if sender in audit_models and instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            _pre_save_instances[f"{sender.__name__}_{instance.pk}"] = model_to_dict(original)
        except sender.DoesNotExist:
            pass  # New instance


@receiver(post_save, sender=Document)
def audit_document_changes(sender, instance, created, **kwargs):
    """Audit document creation and modifications."""
    audit_context = get_audit_context()
    user = audit_context.get('user') if audit_context else None
    
    if created:
        audit_service.log_user_action(
            user=user,
            action='DOCUMENT_CREATE',
            object_type='Document',
            object_id=instance.id,
            description=f"Created document {instance.document_number}: {instance.title}",
            additional_data={
                'document_number': instance.document_number,
                'title': instance.title,
                'document_type': instance.document_type.name if instance.document_type else None,
                'status': instance.status,
                'version': str(instance.version)
            }
        )
    else:
        # Get original values for comparison
        key = f"Document_{instance.pk}"
        old_values = _pre_save_instances.get(key, {})
        new_values = model_to_dict(instance)
        
        # Find changed fields
        changed_fields = {}
        for field, new_value in new_values.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changed_fields[field] = {
                    'old': old_value,
                    'new': new_value
                }
        
        if changed_fields:
            audit_service.log_user_action(
                user=user,
                action='DOCUMENT_UPDATE',
                object_type='Document',
                object_id=instance.id,
                description=f"Updated document {instance.document_number}",
                additional_data={
                    'document_number': instance.document_number,
                    'changed_fields': changed_fields
                }
            )
            
            # Log database change
            audit_service.log_database_change(
                model_instance=instance,
                action='UPDATE',
                user=user,
                old_values=old_values,
                new_values=new_values
            )
        
        # Clean up stored values
        if key in _pre_save_instances:
            del _pre_save_instances[key]


@receiver(post_delete, sender=Document)
def audit_document_deletion(sender, instance, **kwargs):
    """Audit document deletion."""
    audit_context = get_audit_context()
    user = audit_context.get('user') if audit_context else None
    
    audit_service.log_user_action(
        user=user,
        action='DOCUMENT_DELETE',
        object_type='Document',
        object_id=instance.id,
        description=f"Deleted document {instance.document_number}: {instance.title}",
        additional_data={
            'document_number': instance.document_number,
            'title': instance.title,
            'status': instance.status
        }
    )


@receiver(post_save, sender=ElectronicSignature)
def audit_electronic_signature(sender, instance, created, **kwargs):
    """Audit electronic signature events."""
    if created:
        audit_service.log_user_action(
            user=instance.user,
            action='ELECTRONIC_SIGNATURE',
            object_type='Document',
            object_id=instance.document.id,
            description=f"Electronic signature applied to document {instance.document.document_number}",
            additional_data={
                'document_number': instance.document.document_number,
                'signature_type': instance.signature_type,
                'reason': instance.reason,
                'signature_timestamp': instance.signature_timestamp.isoformat()
            }
        )
        
        # Log compliance event
        audit_service.log_compliance_event(
            event_type='ELECTRONIC_SIGNATURE_APPLIED',
            description=f"Electronic signature applied by {instance.user.get_full_name()}",
            user=instance.user,
            object_type='Document',
            object_id=instance.document.id,
            additional_data={
                'document_number': instance.document.document_number,
                'signature_method': instance.signature_type
            }
        )


@receiver(post_save, sender=WorkflowInstance)
def audit_workflow_changes(sender, instance, created, **kwargs):
    """Audit workflow instance changes."""
    audit_context = get_audit_context()
    user = audit_context.get('user') if audit_context else None
    
    if created:
        audit_service.log_workflow_event(
            workflow_instance=instance,
            event_type='WORKFLOW_INITIATED',
            user=user or instance.initiated_by,
            description=f"Workflow initiated: {instance.workflow_type.name}",
            additional_data={
                'workflow_type': instance.workflow_type.workflow_type,
                'initiated_by': instance.initiated_by.username
            }
        )
    else:
        # Check for state changes
        key = f"WorkflowInstance_{instance.pk}"
        old_values = _pre_save_instances.get(key, {})
        
        if old_values.get('state') != str(instance.state):
            audit_service.log_workflow_event(
                workflow_instance=instance,
                event_type='WORKFLOW_TRANSITION',
                user=user,
                description=f"Workflow state changed: {old_values.get('state')} -> {instance.state}",
                additional_data={
                    'from_state': old_values.get('state'),
                    'to_state': str(instance.state),
                    'current_assignee': instance.current_assignee.username if instance.current_assignee else None
                }
            )
        
        # Clean up stored values
        if key in _pre_save_instances:
            del _pre_save_instances[key]


@receiver(post_save, sender=WorkflowTransition)
def audit_workflow_transition(sender, instance, created, **kwargs):
    """Audit workflow transitions."""
    if created:
        audit_service.log_workflow_event(
            workflow_instance=instance.workflow_instance,
            event_type='WORKFLOW_TRANSITION_RECORDED',
            user=instance.transitioned_by,
            description=f"Workflow transition: {instance.from_state} -> {instance.to_state}",
            additional_data={
                'from_state': instance.from_state,
                'to_state': instance.to_state,
                'reason': instance.reason,
                'transition_timestamp': instance.transitioned_at.isoformat()
            }
        )


@receiver(post_save, sender=UserRole)
def audit_user_role_changes(sender, instance, created, **kwargs):
    """Audit user role assignments."""
    audit_context = get_audit_context()
    user = audit_context.get('user') if audit_context else None
    
    if created:
        audit_service.log_user_action(
            user=user,
            action='USER_ROLE_ASSIGNED',
            object_type='User',
            object_id=instance.user.id,
            description=f"Role '{instance.role.name}' assigned to {instance.user.username}",
            additional_data={
                'assigned_user': instance.user.username,
                'role_name': instance.role.name,
                'role_module': instance.role.module,
                'permission_level': instance.role.permission_level
            }
        )
        
        # Log compliance event for role assignment
        audit_service.log_compliance_event(
            event_type='USER_ROLE_ASSIGNED',
            description=f"User role assignment: {instance.role.name} to {instance.user.username}",
            user=user,
            object_type='User',
            object_id=instance.user.id,
            additional_data={
                'assigned_user': instance.user.username,
                'role_details': {
                    'name': instance.role.name,
                    'module': instance.role.module,
                    'permission_level': instance.role.permission_level
                }
            }
        )


@receiver(post_delete, sender=UserRole)
def audit_user_role_removal(sender, instance, **kwargs):
    """Audit user role removal."""
    audit_context = get_audit_context()
    user = audit_context.get('user') if audit_context else None
    
    audit_service.log_user_action(
        user=user,
        action='USER_ROLE_REMOVED',
        object_type='User',
        object_id=instance.user.id,
        description=f"Role '{instance.role.name}' removed from {instance.user.username}",
        additional_data={
            'affected_user': instance.user.username,
            'role_name': instance.role.name,
            'role_module': instance.role.module
        }
    )


@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Audit successful user logins."""
    audit_service.log_login_event(user=user, success=True)
    
    # Start session tracking
    if hasattr(request, 'session'):
        audit_service.start_user_session(user, request.session.session_key)
    
    # Log compliance event
    audit_service.log_compliance_event(
        event_type='USER_LOGIN_SUCCESS',
        description=f"Successful login for user {user.username}",
        user=user,
        additional_data={
            'username': user.username,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    )


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Audit user logouts."""
    if user:
        audit_service.log_user_action(
            user=user,
            action='USER_LOGOUT',
            description=f"User {user.username} logged out"
        )
        
        # End session tracking
        if hasattr(request, 'session'):
            audit_service.end_user_session(request.session.session_key)


@receiver(user_login_failed)
def audit_failed_login(sender, credentials, request, **kwargs):
    """Audit failed login attempts."""
    username = credentials.get('username', 'unknown')
    
    # Try to get user for failed login
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    
    audit_service.log_login_event(
        user=user,
        success=False,
        failure_reason='Invalid credentials'
    )
    
    # Log compliance event for security
    audit_service.log_compliance_event(
        event_type='USER_LOGIN_FAILED',
        description=f"Failed login attempt for username: {username}",
        user=user,
        severity='WARNING',
        additional_data={
            'attempted_username': username,
            'failure_reason': 'Invalid credentials'
        }
    )


# Custom signal handlers for specific audit events

def audit_document_access(user, document, access_type, **kwargs):
    """Manual audit function for document access events."""
    audit_service.log_document_access(
        user=user,
        document=document,
        access_type=access_type,
        additional_data=kwargs
    )


def audit_compliance_violation(event_type, description, user=None, 
                             object_type=None, object_id=None, **kwargs):
    """Manual audit function for compliance violations."""
    audit_service.log_compliance_event(
        event_type=event_type,
        description=description,
        user=user,
        object_type=object_type,
        object_id=object_id,
        severity='ERROR',
        additional_data=kwargs
    )


def audit_security_event(event_type, description, user=None, severity='WARNING', **kwargs):
    """Manual audit function for security events."""
    audit_service.log_compliance_event(
        event_type=event_type,
        description=description,
        user=user,
        severity=severity,
        additional_data=kwargs
    )