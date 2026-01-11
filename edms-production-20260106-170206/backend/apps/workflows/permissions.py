"""
Workflow-specific permissions for EDMS.

Custom permission classes for workflow operations
integrating with role-based access control.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

from apps.users.workflow_permissions import workflow_permission_manager
from apps.users.permissions import CanManageDocuments, CanManageWorkflows

User = get_user_model()


class CanInitiateWorkflow(permissions.BasePermission):
    """
    Permission to initiate workflows.
    
    Checks if user has appropriate role to initiate
    specific workflow types for documents.
    """
    
    def has_permission(self, request, view):
        """Check if user has general workflow initiation permission."""
        if not request.user.is_authenticated:
            return False
        
        return workflow_permission_manager.can_user_perform_action(
            request.user, 'workflow_initiate'
        )
    
    def has_object_permission(self, request, view, obj):
        """Check object-level workflow initiation permission."""
        # Get workflow type from request data
        workflow_type = getattr(request.data, 'workflow_type', 'REVIEW')
        
        return workflow_permission_manager.can_initiate_workflow(
            request.user, obj, workflow_type
        )


class CanManageWorkflowTransitions(permissions.BasePermission):
    """
    Permission to manage workflow transitions.
    
    Checks if user can perform specific workflow transitions
    based on their role and workflow context.
    """
    
    def has_permission(self, request, view):
        """Check if user has general transition permission."""
        if not request.user.is_authenticated:
            return False
        
        return workflow_permission_manager.can_user_perform_action(
            request.user, 'workflow_review'
        ) or workflow_permission_manager.can_user_perform_action(
            request.user, 'workflow_approve'
        )
    
    def has_object_permission(self, request, view, obj):
        """Check object-level transition permission."""
        # Get transition name from request
        transition_name = getattr(request.data, 'transition_name', '')
        
        return workflow_permission_manager.can_transition_workflow(
            request.user, obj, transition_name
        )


class CanCompleteWorkflowTasks(permissions.BasePermission):
    """
    Permission to complete workflow tasks.
    
    Checks if user can complete specific tasks
    based on assignment and role permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has general task completion permission."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check object-level task completion permission."""
        # Users can complete tasks assigned to them
        if obj.assigned_to == request.user:
            return True
        
        # Check role-based permissions
        task_permissions = {
            'REVIEW': ['review', 'admin'],
            'APPROVAL': ['approve', 'admin'],
            'DOCUMENT_EDIT': ['write', 'admin'],
            'VERIFICATION': ['review', 'approve', 'admin']
        }
        
        required_levels = task_permissions.get(obj.task_type, ['admin'])
        
        return workflow_permission_manager._has_permission_level(
            request.user, required_levels
        )


class CanViewWorkflowHistory(permissions.BasePermission):
    """
    Permission to view workflow history.
    
    Checks if user can view workflow history
    based on document access and role permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has workflow history access."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check object-level workflow history permission."""
        # Check if user can access the related document
        if hasattr(obj, 'content_object'):
            document = obj.content_object
            return workflow_permission_manager.can_access_document(
                request.user, document, 'read'
            )
        
        # For direct document access
        return workflow_permission_manager.can_access_document(
            request.user, obj, 'read'
        )


class CanAccessWorkflowReports(permissions.BasePermission):
    """
    Permission to access workflow reports and metrics.
    
    Restricts access to workflow analytics and reports
    based on administrative roles.
    """
    
    def has_permission(self, request, view):
        """Check if user has workflow reporting access."""
        if not request.user.is_authenticated:
            return False
        
        return workflow_permission_manager.can_user_perform_action(
            request.user, 'audit_access'
        )


class CanManageWorkflowConfiguration(permissions.BasePermission):
    """
    Permission to manage workflow configuration.
    
    Restricts workflow type and template management
    to administrative users only.
    """
    
    def has_permission(self, request, view):
        """Check if user has workflow configuration access."""
        if not request.user.is_authenticated:
            return False
        
        return workflow_permission_manager.can_user_perform_action(
            request.user, 'system_configuration'
        )


class DocumentWorkflowPermission(permissions.BasePermission):
    """
    Combined permission for document-workflow operations.
    
    Integrates document access permissions with workflow
    operations for comprehensive access control.
    """
    
    def has_permission(self, request, view):
        """Check general document-workflow permission."""
        if not request.user.is_authenticated:
            return False
        
        # Check if user has any document access
        return (
            workflow_permission_manager.can_user_perform_action(
                request.user, 'document_create'
            ) or
            workflow_permission_manager.can_user_perform_action(
                request.user, 'workflow_review'
            ) or
            workflow_permission_manager.can_user_perform_action(
                request.user, 'workflow_approve'
            )
        )
    
    def has_object_permission(self, request, view, obj):
        """Check object-level document-workflow permission."""
        # Determine the action based on HTTP method and view
        action_mapping = {
            'GET': 'read',
            'POST': 'write',
            'PUT': 'write',
            'PATCH': 'write',
            'DELETE': 'delete'
        }
        
        access_type = action_mapping.get(request.method, 'read')
        
        # Check document access permission
        return workflow_permission_manager.can_access_document(
            request.user, obj, access_type
        )