"""
Workflow Services for EDMS.

Provides workflow management services for document lifecycle
management with Enhanced Simple Workflow Engine.
"""

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
# from river.models import State, Transition
# from river.core.instanceworkflowobject import InstanceWorkflowObject
# River workflow engine removed - using custom workflow implementation

from .models import (
    WorkflowType, WorkflowInstance, WorkflowTransition, 
    WorkflowTask, WorkflowRule, WorkflowNotification,
    WorkflowTemplate, DOCUMENT_STATES
)
from apps.documents.models import Document


User = get_user_model()


class WorkflowService:
    """
    Main workflow service for managing document workflows.
    
    Provides high-level workflow operations including initiation,
    transition management, and completion handling.
    """
    
    def __init__(self):
        # Lazy initialization to avoid database access during import
        self._document_content_type = None
    
    @property
    def document_content_type(self):
        if self._document_content_type is None:
            from django.contrib.contenttypes.models import ContentType
            self._document_content_type = ContentType.objects.get_for_model(Document)
        return self._document_content_type
    
    def initiate_workflow(self, document: Document, workflow_type: str, 
                         initiated_by: User, **kwargs) -> WorkflowInstance:
        """
        Initiate a new workflow for a document.
        
        Args:
            document: Document instance
            workflow_type: Type of workflow to initiate
            initiated_by: User initiating the workflow
            **kwargs: Additional workflow data
            
        Returns:
            WorkflowInstance: Created workflow instance
        """
        with transaction.atomic():
            # Get workflow type configuration
            wf_type = WorkflowType.objects.get(
                workflow_type=workflow_type,
                is_active=True
            )
            
            # Create workflow instance
            instance = WorkflowInstance.objects.create(
                workflow_type=wf_type,
                content_type=self.document_content_type,
                object_id=str(document.id),  # Use integer ID instead of UUID
                initiated_by=initiated_by,
                workflow_data=kwargs,
                due_date=self._calculate_due_date(wf_type)
            )
            
            # Set initial state
            initial_state = self._get_initial_state(workflow_type)
            instance.state = initial_state
            instance.save()
            
            # Create initial tasks
            self._create_initial_tasks(instance, document, initiated_by)
            
            # Send notifications
            self._send_workflow_notifications(
                instance, 
                'ASSIGNMENT',
                f"Workflow initiated: {wf_type.name}"
            )
            
            return instance
    
    def transition_workflow(self, workflow_instance: WorkflowInstance, 
                          transition_name: str, user: User, 
                          comment: str = '', **kwargs) -> bool:
        """
        Execute a workflow transition.
        
        Args:
            workflow_instance: Workflow instance to transition
            transition_name: Name of the transition to execute
            user: User executing the transition
            comment: Optional comment for the transition
            **kwargs: Additional transition data
            
        Returns:
            bool: True if transition was successful
        """
        try:
            with transaction.atomic():
                # Get current state
                current_state = workflow_instance.state
                
                # Validate transition permissions
                if not self._can_transition(workflow_instance, transition_name, user):
                    raise ValueError(f"User {user.username} cannot execute transition {transition_name}")
                
                # Use simple state transition instead of River
                # Define valid transitions
                valid_transitions = {
                    'draft': {
                        'submit_for_review': 'pending_review'
                    },
                    'pending_review': {
                        'start_review': 'under_review', 
                        'reject': 'draft'
                    },
                    'under_review': {
                        'complete_review': 'reviewed',
                        'reject': 'draft'
                    },
                    'reviewed': {
                        'approve': 'approved'
                    },
                    'approved': {
                        'make_effective': 'effective'
                    }
                }
                
                # Check if transition is valid
                current_transitions = valid_transitions.get(current_state, {})
                if transition_name not in current_transitions:
                    raise ValueError(f"Transition {transition_name} not available from state {current_state}")
                
                # Get new state
                new_state = current_transitions[transition_name]
                
                # Store transition data
                transition_data = {
                    'comment': comment,
                    'user': user.username,
                    'timestamp': timezone.now().isoformat(),
                    **kwargs
                }
                
                # Execute transition (simple state change)
                workflow_instance.state = new_state
                workflow_instance.current_assignee = self._get_next_assignee(
                    workflow_instance, new_state
                )
                workflow_instance.save()
                
                # Log transition
                self._log_transition(
                    workflow_instance, current_state, new_state, 
                    transition_name, user, comment, transition_data
                )
                
                # Handle post-transition actions
                self._handle_post_transition(workflow_instance, transition_name, user)
                
                # Check for completion
                if self._is_terminal_state(new_state):
                    self._complete_workflow(workflow_instance, 'Workflow completed')
                
                return True
                
        except Exception as e:
            # Log error and return failure
            self._log_workflow_error(workflow_instance, f"Transition failed: {str(e)}")
            return False
    
    def complete_workflow(self, workflow_instance: WorkflowInstance, 
                         reason: str = 'Completed') -> bool:
        """
        Complete a workflow instance.
        
        Args:
            workflow_instance: Workflow instance to complete
            reason: Reason for completion
            
        Returns:
            bool: True if completion was successful
        """
        try:
            with transaction.atomic():
                # Update workflow instance
                workflow_instance.complete_workflow(reason)
                
                # Complete all pending tasks
                pending_tasks = workflow_instance.tasks.filter(
                    status__in=['PENDING', 'IN_PROGRESS']
                )
                for task in pending_tasks:
                    task.status = 'COMPLETED'
                    task.completed_at = timezone.now()
                    task.completion_note = f'Workflow completed: {reason}'
                    task.save()
                
                # Send completion notifications
                self._send_workflow_notifications(
                    workflow_instance,
                    'COMPLETION',
                    f"Workflow completed: {reason}"
                )
                
                # Update document status if applicable
                self._update_document_status(workflow_instance)
                
                return True
                
        except Exception as e:
            self._log_workflow_error(workflow_instance, f"Completion failed: {str(e)}")
            return False
    
    def get_workflow_history(self, document: Document) -> List[Dict[str, Any]]:
        """
        Get workflow history for a document.
        
        Args:
            document: Document instance
            
        Returns:
            List of workflow history entries
        """
        instances = WorkflowInstance.objects.filter(
            content_type=self.document_content_type,
            object_id=str(document.id)  # Use integer ID instead of UUID
        ).prefetch_related('transitions', 'tasks')
        
        history = []
        for instance in instances:
            history.append({
                'workflow_type': instance.workflow_type.name,
                'started_at': instance.started_at,
                'completed_at': instance.completed_at,
                'initiated_by': instance.initiated_by.get_full_name(),
                'current_state': str(instance.state),
                'is_completed': instance.is_completed,
                'transitions': [
                    {
                        'from_state': t.from_state,
                        'to_state': t.to_state,
                        'transitioned_by': t.transitioned_by.get_full_name(),
                        'transitioned_at': t.transitioned_at,
                        'comment': t.comment
                    }
                    for t in instance.transitions.all()
                ],
                'tasks': [
                    {
                        'name': task.name,
                        'assigned_to': task.assigned_to.get_full_name(),
                        'status': task.status,
                        'due_date': task.due_date,
                        'completed_at': task.completed_at
                    }
                    for task in instance.tasks.all()
                ]
            })
        
        return history
    
    def get_pending_tasks(self, user: User) -> List[WorkflowTask]:
        """
        Get pending workflow tasks for a user.
        
        Args:
            user: User to get tasks for
            
        Returns:
            List of pending WorkflowTask instances
        """
        return WorkflowTask.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS'],
            workflow_instance__is_active=True
        ).select_related(
            'workflow_instance', 'workflow_instance__workflow_type'
        ).order_by('due_date', '-created_at')
    
    def get_overdue_tasks(self, user: User = None) -> List[WorkflowTask]:
        """
        Get overdue workflow tasks.
        
        Args:
            user: Optional user to filter tasks for
            
        Returns:
            List of overdue WorkflowTask instances
        """
        queryset = WorkflowTask.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['PENDING', 'IN_PROGRESS'],
            workflow_instance__is_active=True
        )
        
        if user:
            queryset = queryset.filter(assigned_to=user)
        
        return queryset.select_related(
            'workflow_instance', 'workflow_instance__workflow_type', 'assigned_to'
        ).order_by('due_date')
    
    def _get_initial_state(self, workflow_type: str) -> str:
        """Get initial state for a workflow type."""
        state_mapping = {
            'REVIEW': 'draft',
            'UP_VERSION': 'draft',
            'OBSOLETE': 'pending_approval',
            'TERMINATE': 'pending_approval',
        }
        return state_mapping.get(workflow_type, 'draft')
    
    def _calculate_due_date(self, workflow_type: WorkflowType) -> Optional[timezone.datetime]:
        """Calculate due date for workflow based on type configuration."""
        if workflow_type.timeout_days:
            return timezone.now() + timezone.timedelta(days=workflow_type.timeout_days)
        return None
    
    def _can_transition(self, workflow_instance: WorkflowInstance, 
                       transition_name: str, user: User) -> bool:
        """Check if user can execute a specific transition."""
        # Check if user is assigned to the workflow
        if workflow_instance.current_assignee and workflow_instance.current_assignee != user:
            return False
        
        # Check user permissions based on transition type
        permission_map = {
            'submit_for_review': ['write', 'admin'],
            'start_review': ['review', 'admin'],
            'complete_review': ['review', 'admin'],
            'approve': ['approve', 'admin'],
            'reject': ['review', 'approve', 'admin'],
            'make_effective': ['approve', 'admin'],
        }
        
        required_permissions = permission_map.get(transition_name, ['admin'])
        user_permissions = user.user_roles.filter(
            role__module='O1',
            role__permission_level__in=required_permissions,
            is_active=True
        ).exists()
        
        return user_permissions or user.is_superuser
    
    def _get_next_assignee(self, workflow_instance: WorkflowInstance, 
                          new_state: str) -> Optional[User]:
        """Determine next assignee based on new state."""
        document = workflow_instance.content_object
        
        assignee_map = {
            'pending_review': document.reviewer,
            'under_review': document.reviewer,
            'pending_approval': document.approver,
            'under_approval': document.approver,
        }
        
        return assignee_map.get(new_state)
    
    def _create_initial_tasks(self, workflow_instance: WorkflowInstance, 
                            document: Document, user: User):
        """Create initial tasks for the workflow."""
        workflow_type = workflow_instance.workflow_type.workflow_type
        
        if workflow_type == 'REVIEW':
            if document.reviewer:
                WorkflowTask.objects.create(
                    workflow_instance=workflow_instance,
                    name='Review Document',
                    description=f'Review document: {document.title}',
                    task_type='REVIEW',
                    assigned_to=document.reviewer,
                    assigned_by=user,
                    due_date=workflow_instance.due_date
                )
        
        elif workflow_type == 'UP_VERSION':
            WorkflowTask.objects.create(
                workflow_instance=workflow_instance,
                name='Version Update',
                description=f'Update document version: {document.title}',
                task_type='VALIDATE',
                assigned_to=document.author,
                assigned_by=user,
                due_date=workflow_instance.due_date
            )
    
    def _log_transition(self, workflow_instance: WorkflowInstance, 
                       from_state: str, to_state: str, transition_name: str,
                       user: User, comment: str, transition_data: Dict[str, Any]):
        """Log workflow transition for audit trail."""
        try:
            from apps.audit.middleware import get_current_ip_address, get_current_session_id
            
            # Get session info, provide defaults if not available
            ip_address = get_current_ip_address() or '127.0.0.1'
            session_id = get_current_session_id() or 'system'
            
            WorkflowTransition.objects.create(
                workflow_instance=workflow_instance,
                from_state=from_state,
                to_state=to_state,
                transition_name=transition_name,
                transitioned_by=user,
                ip_address=ip_address,
                session_id=session_id,
                comment=comment,
                transition_data=transition_data
            )
        except Exception as e:
            # If logging fails, don't fail the transition
            print(f"Warning: Failed to log workflow transition: {e}")
    
    def _handle_post_transition(self, workflow_instance: WorkflowInstance, 
                              transition_name: str, user: User):
        """Handle actions after successful transition."""
        # Update tasks based on transition
        if transition_name == 'start_review':
            # Mark review tasks as in progress
            review_tasks = workflow_instance.tasks.filter(
                task_type='REVIEW',
                status='PENDING'
            )
            for task in review_tasks:
                task.status = 'IN_PROGRESS'
                task.started_at = timezone.now()
                task.save()
        
        # Send notifications for new assignments
        if workflow_instance.current_assignee:
            self._send_workflow_notifications(
                workflow_instance,
                'ASSIGNMENT',
                f"New task assigned: {transition_name}"
            )
    
    def _send_workflow_notifications(self, workflow_instance: WorkflowInstance,
                                   notification_type: str, message: str):
        """Send workflow notifications to relevant users."""
        recipients = []
        
        # Add current assignee
        if workflow_instance.current_assignee:
            recipients.append(workflow_instance.current_assignee)
        
        # Add workflow initiator for status updates
        if notification_type in ['COMPLETION', 'REJECTION', 'CANCELLATION']:
            recipients.append(workflow_instance.initiated_by)
        
        # Create notification records
        for recipient in set(recipients):  # Remove duplicates
            WorkflowNotification.objects.create(
                workflow_instance=workflow_instance,
                notification_type=notification_type,
                recipient=recipient,
                subject=f"Workflow Update: {workflow_instance.workflow_type.name}",
                message=message
            )
    
    def _is_terminal_state(self, state: str) -> bool:
        """Check if state is a terminal state."""
        terminal_states = ['effective', 'superseded', 'obsolete', 'terminated']
        return state in terminal_states
    
    def _complete_workflow(self, workflow_instance: WorkflowInstance, reason: str):
        """Handle workflow completion."""
        workflow_instance.complete_workflow(reason)
    
    def _update_document_status(self, workflow_instance: WorkflowInstance):
        """Update document status based on workflow completion."""
        document = workflow_instance.content_object
        final_state = workflow_instance.state
        
        # Map workflow states to document statuses
        status_map = {
            'effective': 'EFFECTIVE',
            'superseded': 'SUPERSEDED',
            'obsolete': 'OBSOLETE',
            'terminated': 'TERMINATED',
        }
        
        new_status = status_map.get(final_state)
        if new_status and document.status != new_status:
            document.status = new_status
            if new_status == 'EFFECTIVE':
                document.effective_date = timezone.now().date()
            elif new_status in ['OBSOLETE', 'SUPERSEDED']:
                document.obsolete_date = timezone.now().date()
            
            document.save()
    
    def _log_workflow_error(self, workflow_instance: WorkflowInstance, error_message: str):
        """Log workflow errors for debugging and audit."""
        from apps.audit.models import AuditTrail
        
        AuditTrail.objects.create(
            content_object=workflow_instance,
            action='WORKFLOW_ERROR',
            description=f"Workflow error: {error_message}",
            severity='ERROR',
            module='S5',
            metadata={
                'workflow_type': workflow_instance.workflow_type.workflow_type,
                'current_state': str(workflow_instance.state),
                'error_message': error_message
            }
        )


class DocumentWorkflowService:
    """
    Document-specific workflow service.
    
    Provides document-focused workflow operations with
    integration to the document lifecycle.
    """
    
    def __init__(self):
        self.workflow_service = WorkflowService()
    
    def start_review_workflow(self, document: Document, initiated_by: User, 
                            reviewer: User = None, due_date: timezone.datetime = None) -> WorkflowInstance:
        """Start a review workflow for a document."""
        if reviewer:
            document.reviewer = reviewer
            document.save()
        
        return self.workflow_service.initiate_workflow(
            document=document,
            workflow_type='REVIEW',
            initiated_by=initiated_by,
            due_date=due_date
        )
    
    def submit_for_review(self, document: Document, user: User, 
                         comment: str = '') -> bool:
        """Submit document for review."""
        # Get active review workflow
        workflow = self._get_active_workflow(document, 'REVIEW')
        if not workflow:
            # Start new review workflow
            workflow = self.start_review_workflow(document, user)
        
        return self.workflow_service.transition_workflow(
            workflow, 'submit_for_review', user, comment
        )
    
    def approve_document(self, document: Document, user: User, 
                        comment: str = '') -> bool:
        """Approve document in workflow."""
        workflow = self._get_active_workflow(document)
        if not workflow:
            return False
        
        return self.workflow_service.transition_workflow(
            workflow, 'approve', user, comment
        )
    
    def reject_document(self, document: Document, user: User, 
                       comment: str = '') -> bool:
        """Reject document in workflow."""
        workflow = self._get_active_workflow(document)
        if not workflow:
            return False
        
        return self.workflow_service.transition_workflow(
            workflow, 'reject', user, comment
        )
    
    def make_effective(self, document: Document, user: User, 
                      effective_date: date = None) -> bool:
        """Make document effective."""
        workflow = self._get_active_workflow(document)
        if not workflow:
            return False
        
        transition_data = {}
        if effective_date:
            transition_data['effective_date'] = effective_date.isoformat()
        
        return self.workflow_service.transition_workflow(
            workflow, 'make_effective', user, '', **transition_data
        )
    
    def start_version_workflow(self, document: Document, user: User, 
                             new_version: Document) -> WorkflowInstance:
        """Start up-versioning workflow."""
        return self.workflow_service.initiate_workflow(
            document=new_version,
            workflow_type='UP_VERSION',
            initiated_by=user,
            previous_version=document.uuid
        )
    
    def start_obsolete_workflow(self, document: Document, user: User, 
                              reason: str = '') -> WorkflowInstance:
        """Start obsolescence workflow."""
        return self.workflow_service.initiate_workflow(
            document=document,
            workflow_type='OBSOLETE',
            initiated_by=user,
            obsolete_reason=reason
        )
    
    def get_document_workflow_status(self, document: Document) -> Dict[str, Any]:
        """Get current workflow status for a document."""
        workflow = self._get_active_workflow(document)
        if not workflow:
            return {'has_active_workflow': False}
        
        return {
            'has_active_workflow': True,
            'workflow_type': workflow.workflow_type.workflow_type,
            'current_state': str(workflow.state),
            'current_assignee': workflow.current_assignee.get_full_name() if workflow.current_assignee else None,
            'started_at': workflow.started_at,
            'due_date': workflow.due_date,
            'is_overdue': workflow.is_overdue,
            'pending_tasks': workflow.tasks.filter(
                status__in=['PENDING', 'IN_PROGRESS']
            ).count()
        }
    
    def _get_active_workflow(self, document: Document, 
                           workflow_type: str = None) -> Optional[WorkflowInstance]:
        """Get active workflow for a document."""
        queryset = WorkflowInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(Document),
            object_id=str(document.id),  # Use integer ID instead of UUID
            is_active=True
        )
        
        if workflow_type:
            queryset = queryset.filter(workflow_type__workflow_type=workflow_type)
        
        return queryset.first()


# Global service instances - initialize lazily to avoid database access during import
workflow_service = None
document_workflow_service = None

def get_workflow_service():
    global workflow_service
    if workflow_service is None:
        workflow_service = WorkflowService()
    return workflow_service

def get_document_workflow_service():
    global document_workflow_service
    if document_workflow_service is None:
        document_workflow_service = DocumentWorkflowService()
    return document_workflow_service