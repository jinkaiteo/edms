"""
Workflow-specific permissions for EDMS users.

Integrates role-based access control with document workflows
to ensure proper authorization for workflow operations.
"""

from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Role, UserRole
from .permissions import CanManageDocuments, CanManageWorkflows
from apps.documents.models import Document, DocumentType
from apps.workflows.models import WorkflowInstance, WorkflowType

User = get_user_model()


class WorkflowPermissionManager:
    """
    Manages workflow-specific permissions for users.
    
    Provides centralized permission checking for workflow operations
    based on user roles, document types, and workflow states.
    """

    def __init__(self):
        self.permission_matrix = {
            # Document creation and editing
            'document_create': ['write', 'admin'],
            'document_edit': ['write', 'admin'],
            'document_delete': ['admin'],
            
            # Workflow operations
            'workflow_initiate': ['write', 'admin'],
            'workflow_review': ['review', 'admin'],
            'workflow_approve': ['approve', 'admin'],
            'workflow_complete': ['approve', 'admin'],
            'workflow_cancel': ['admin'],
            
            # Document state transitions
            'submit_for_review': ['write', 'admin'],
            'start_review': ['review', 'admin'],
            'complete_review': ['review', 'admin'],
            'submit_for_approval': ['review', 'admin'],
            'approve_document': ['approve', 'admin'],
            'reject_document': ['review', 'approve', 'admin'],
            'make_effective': ['approve', 'admin'],
            'make_obsolete': ['approve', 'admin'],
            
            # Special operations
            'electronic_signature': ['approve', 'admin'],
            'emergency_stop': ['admin'],
            'audit_access': ['admin'],
            'system_configuration': ['admin']
        }

    def can_user_perform_action(self, user: User, action: str, 
                               document: Document = None, **kwargs) -> bool:
        """
        Check if user can perform a specific action.
        
        Args:
            user: User to check permissions for
            action: Action to check (from permission_matrix)
            document: Document context (if applicable)
            **kwargs: Additional context
            
        Returns:
            bool: True if user has permission
        """
        # Superusers can do everything
        if user.is_superuser:
            return True
        
        # Check if action is in permission matrix
        required_levels = self.permission_matrix.get(action, [])
        if not required_levels:
            return False
        
        # Get user's active roles
        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True
        ).select_related('role')
        
        # Check if user has any required permission level
        for user_role in user_roles:
            if user_role.role.permission_level in required_levels:
                # Additional context-specific checks
                if self._check_contextual_permissions(
                    user, action, document, user_role.role, **kwargs
                ):
                    return True
        
        return False

    def can_initiate_workflow(self, user: User, document: Document, 
                            workflow_type: str) -> bool:
        """
        Check if user can initiate a specific workflow for a document.
        
        Args:
            user: User requesting to initiate workflow
            document: Document for workflow
            workflow_type: Type of workflow (REVIEW, APPROVAL, etc.)
            
        Returns:
            bool: True if user can initiate the workflow
        """
        # Basic permission check
        if not self.can_user_perform_action(user, 'workflow_initiate', document):
            return False
        
        # Document-specific checks
        if document.created_by == user:
            # Authors can initiate review workflows for their own documents
            if workflow_type in ['REVIEW', 'UP_VERSION']:
                return True
        
        # Check if user has appropriate role for the workflow type
        workflow_permissions = {
            'REVIEW': ['write', 'review', 'admin'],
            'APPROVAL': ['approve', 'admin'],
            'UP_VERSION': ['write', 'review', 'admin'],
            'OBSOLETE': ['approve', 'admin'],
            'TERMINATE': ['admin']
        }
        
        required_levels = workflow_permissions.get(workflow_type, ['admin'])
        return self._has_permission_level(user, required_levels)

    def can_transition_workflow(self, user: User, workflow_instance: WorkflowInstance,
                              transition_name: str) -> bool:
        """
        Check if user can perform a workflow transition.
        
        Args:
            user: User requesting the transition
            workflow_instance: Workflow instance
            transition_name: Name of the transition
            
        Returns:
            bool: True if user can perform the transition
        """
        document = workflow_instance.content_object
        
        # Define transition permissions
        transition_permissions = {
            'submit_for_review': ['write', 'admin'],
            'start_review': ['review', 'admin'],
            'complete_review': ['review', 'admin'],
            'submit_for_approval': ['review', 'admin'],
            'approve': ['approve', 'admin'],
            'reject': ['review', 'approve', 'admin'],
            'make_effective': ['approve', 'admin'],
            'cancel': ['admin'],
            'terminate': ['admin']
        }
        
        required_levels = transition_permissions.get(transition_name, ['admin'])
        
        # Check basic permission
        if not self._has_permission_level(user, required_levels):
            return False
        
        # Additional contextual checks
        if transition_name == 'submit_for_review':
            # Only document author or users with write permission
            return document.created_by == user or self._has_permission_level(user, ['write', 'admin'])
        
        elif transition_name in ['start_review', 'complete_review']:
            # Check if user is assigned as reviewer or has review role
            return (
                workflow_instance.current_assignee == user or
                self._has_permission_level(user, ['review', 'admin'])
            )
        
        elif transition_name == 'approve':
            # Check if user is assigned as approver or has approve role
            return (
                workflow_instance.current_assignee == user or
                self._has_permission_level(user, ['approve', 'admin'])
            )
        
        elif transition_name == 'reject':
            # Reviewers and approvers can reject
            return (
                workflow_instance.current_assignee == user or
                self._has_permission_level(user, ['review', 'approve', 'admin'])
            )
        
        return True  # Default to allowing if basic permission check passed

    def can_access_document(self, user: User, document: Document, 
                          access_type: str = 'read') -> bool:
        """
        Check if user can access a document.
        
        Args:
            user: User requesting access
            document: Document to access
            access_type: Type of access (read, write, download, print)
            
        Returns:
            bool: True if user can access the document
        """
        # Public documents can be read by anyone
        if access_type == 'read' and getattr(document, 'is_public', False):
            return True
        
        # Document creators can always access their own documents
        if document.created_by == user:
            return True
        
        # Check role-based permissions
        access_permissions = {
            'read': ['read', 'write', 'review', 'approve', 'admin'],
            'write': ['write', 'admin'],
            'download': ['read', 'write', 'review', 'approve', 'admin'],
            'print': ['read', 'write', 'review', 'approve', 'admin'],
            'delete': ['admin']
        }
        
        required_levels = access_permissions.get(access_type, ['admin'])
        return self._has_permission_level(user, required_levels)

    def get_user_accessible_documents(self, user: User) -> List[Document]:
        """
        Get list of documents accessible to a user.
        
        Args:
            user: User to get documents for
            
        Returns:
            QuerySet of accessible documents
        """
        if user.is_superuser:
            return Document.objects.all()
        
        # Get user's permission levels
        user_levels = self._get_user_permission_levels(user)
        
        # Build filter conditions
        conditions = Q()
        
        # Documents created by user
        conditions |= Q(created_by=user)
        
        # Public documents (if any)
        conditions |= Q(is_public=True)
        
        # Documents based on role permissions
        if 'admin' in user_levels:
            return Document.objects.all()
        elif any(level in user_levels for level in ['read', 'write', 'review', 'approve']):
            # Users with any document access role can see documents
            # Additional filtering can be added based on document type, department, etc.
            pass
        
        return Document.objects.filter(conditions)

    def get_user_manageable_workflows(self, user: User) -> List[WorkflowInstance]:
        """
        Get list of workflows a user can manage.
        
        Args:
            user: User to get workflows for
            
        Returns:
            QuerySet of manageable workflow instances
        """
        if user.is_superuser:
            return WorkflowInstance.objects.all()
        
        conditions = Q()
        
        # Workflows initiated by user
        conditions |= Q(initiated_by=user)
        
        # Workflows assigned to user
        conditions |= Q(current_assignee=user)
        
        # Workflows for documents user created
        conditions |= Q(content_type__model='document', object_id__in=
            Document.objects.filter(created_by=user).values_list('id', flat=True)
        )
        
        # Workflows based on role permissions
        user_levels = self._get_user_permission_levels(user)
        
        if 'admin' in user_levels:
            return WorkflowInstance.objects.all()
        elif 'approve' in user_levels:
            # Approvers can see approval workflows
            conditions |= Q(workflow_type__workflow_type__in=['APPROVAL', 'OBSOLETE'])
        elif 'review' in user_levels:
            # Reviewers can see review workflows
            conditions |= Q(workflow_type__workflow_type='REVIEW')
        
        return WorkflowInstance.objects.filter(conditions)

    def get_available_workflow_types(self, user: User, document: Document = None) -> List[Dict[str, Any]]:
        """
        Get workflow types available to a user for a document.
        
        Args:
            user: User to check workflow types for
            document: Document context (optional)
            
        Returns:
            List of available workflow type information
        """
        user_levels = self._get_user_permission_levels(user)
        available_workflows = []
        
        workflow_configs = [
            {
                'type': 'REVIEW',
                'name': 'Document Review',
                'required_levels': ['write', 'admin'],
                'description': 'Submit document for review'
            },
            {
                'type': 'APPROVAL',
                'name': 'Document Approval',
                'required_levels': ['approve', 'admin'],
                'description': 'Submit document for approval'
            },
            {
                'type': 'UP_VERSION',
                'name': 'Version Update',
                'required_levels': ['write', 'admin'],
                'description': 'Create new version of document'
            },
            {
                'type': 'OBSOLETE',
                'name': 'Mark Obsolete',
                'required_levels': ['approve', 'admin'],
                'description': 'Mark document as obsolete'
            },
            {
                'type': 'TERMINATE',
                'name': 'Emergency Termination',
                'required_levels': ['admin'],
                'description': 'Emergency termination of document'
            }
        ]
        
        for config in workflow_configs:
            if any(level in user_levels for level in config['required_levels']):
                # Additional document-specific checks
                if document and not self._check_document_workflow_compatibility(
                    document, config['type']
                ):
                    continue
                
                available_workflows.append(config)
        
        return available_workflows

    def _has_permission_level(self, user: User, required_levels: List[str]) -> bool:
        """Check if user has any of the required permission levels."""
        user_levels = self._get_user_permission_levels(user)
        return any(level in user_levels for level in required_levels)

    def _get_user_permission_levels(self, user: User) -> List[str]:
        """Get all permission levels for a user."""
        if user.is_superuser:
            return ['admin']
        
        return list(
            UserRole.objects.filter(
                user=user,
                is_active=True
            ).values_list('role__permission_level', flat=True).distinct()
        )

    def _check_contextual_permissions(self, user: User, action: str, 
                                    document: Document, role: Role, **kwargs) -> bool:
        """Check additional contextual permission requirements."""
        
        # Document type specific permissions
        if document and hasattr(document, 'document_type'):
            # Check if role applies to this document type
            # This could be extended to include department, project, etc.
            pass
        
        # Time-based permissions (e.g., only during business hours)
        # Location-based permissions
        # Project-based permissions
        
        # For now, return True if basic role check passed
        return True

    def _check_document_workflow_compatibility(self, document: Document, 
                                             workflow_type: str) -> bool:
        """Check if document is compatible with workflow type."""
        
        # Check document status
        status_compatibility = {
            'REVIEW': ['draft', 'under_revision'],
            'APPROVAL': ['review_completed', 'reviewed'],
            'UP_VERSION': ['effective', 'approved'],
            'OBSOLETE': ['effective'],
            'TERMINATE': ['draft', 'under_review', 'pending_approval']
        }
        
        compatible_statuses = status_compatibility.get(workflow_type, [])
        
        return document.status in compatible_statuses


# Global workflow permission manager instance
workflow_permission_manager = WorkflowPermissionManager()