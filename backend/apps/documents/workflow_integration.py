"""
Document-Workflow Integration for EDMS.

Integrates Django-River workflows with document lifecycle management
for seamless state transitions and compliance tracking.
"""

from typing import Optional, Dict, Any, List
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from river.models import State
from river.core.instanceworkflowobject import InstanceWorkflowObject

from .models import Document, DocumentVersion, ElectronicSignature
from apps.workflows.models import WorkflowInstance, WorkflowType
from apps.workflows.services import workflow_service
from apps.audit.services import audit_service
from apps.users.models import Role

User = get_user_model()


class DocumentWorkflowManager:
    """
    Manages document lifecycle workflows using Django-River.
    
    Provides high-level interface for document workflow operations
    including state transitions, approvals, and lifecycle management.
    """

    def __init__(self):
        self.state_mapping = {
            'draft': 'draft',
            'pending_review': 'pending_review',
            'under_review': 'under_review',
            'review_completed': 'review_completed',
            'pending_approval': 'pending_approval',
            'under_approval': 'under_approval',
            'approved': 'approved',
            'effective': 'effective',
            'superseded': 'superseded',
            'obsolete': 'obsolete',
            'terminated': 'terminated'
        }

    def initiate_review_workflow(self, document: Document, reviewer: User, 
                                initiated_by: User, **kwargs) -> WorkflowInstance:
        """
        Initiate review workflow for a document.
        
        Args:
            document: Document to review
            reviewer: User assigned to review
            initiated_by: User initiating the workflow
            **kwargs: Additional workflow data
            
        Returns:
            WorkflowInstance: Created workflow instance
        """
        with transaction.atomic():
            # Create workflow instance
            workflow = workflow_service.initiate_workflow(
                document=document,
                workflow_type='REVIEW',
                initiated_by=initiated_by,
                assigned_to=reviewer,
                **kwargs
            )
            
            # Transition document to pending review
            self._transition_document_state(
                document=document,
                new_state='pending_review',
                user=initiated_by,
                reason='Review workflow initiated'
            )
            
            # Log audit trail
            audit_service.log_workflow_event(
                workflow_instance=workflow,
                event_type='REVIEW_WORKFLOW_INITIATED',
                user=initiated_by,
                description=f"Review workflow initiated for {document.document_number}",
                additional_data={
                    'reviewer': reviewer.username,
                    'document_number': document.document_number
                }
            )
            
            return workflow

    def start_review(self, document: Document, reviewer: User) -> bool:
        """
        Start the actual review process.
        
        Args:
            document: Document being reviewed
            reviewer: User starting the review
            
        Returns:
            bool: True if successful
        """
        if not self._can_transition(document, 'start_review', reviewer):
            return False
        
        with transaction.atomic():
            # Transition document state
            success = self._transition_document_state(
                document=document,
                new_state='under_review',
                user=reviewer,
                reason='Review started'
            )
            
            if success:
                # Update workflow instance
                workflow = self._get_active_workflow(document, 'REVIEW')
                if workflow:
                    workflow.current_assignee = reviewer
                    workflow.save()
                
                # Log audit trail
                audit_service.log_document_access(
                    user=reviewer,
                    document=document,
                    access_type='REVIEW_START'
                )
            
            return success

    def complete_review(self, document: Document, reviewer: User, 
                       review_result: str, comments: str = '') -> bool:
        """
        Complete the document review.
        
        Args:
            document: Document being reviewed
            reviewer: User completing the review
            review_result: Result of review (APPROVED, REJECTED, NEEDS_REVISION)
            comments: Review comments
            
        Returns:
            bool: True if successful
        """
        if not self._can_transition(document, 'complete_review', reviewer):
            return False
        
        with transaction.atomic():
            # Determine next state based on review result
            if review_result == 'APPROVED':
                next_state = 'review_completed'
            elif review_result == 'REJECTED':
                next_state = 'draft'  # Return to draft for revision
            else:
                next_state = 'draft'  # Needs revision
            
            # Transition document state
            success = self._transition_document_state(
                document=document,
                new_state=next_state,
                user=reviewer,
                reason=f'Review completed: {review_result}'
            )
            
            if success:
                # Update workflow instance
                workflow = self._get_active_workflow(document, 'REVIEW')
                if workflow:
                    if review_result == 'APPROVED':
                        # Move to approval workflow if approved
                        self._initiate_approval_workflow(document, workflow, reviewer)
                    else:
                        # Complete workflow if rejected/needs revision
                        workflow_service.complete_workflow(
                            workflow, 
                            reason=f'Review {review_result.lower()}: {comments}'
                        )
                
                # Log audit trail
                audit_service.log_document_access(
                    user=reviewer,
                    document=document,
                    access_type='REVIEW_COMPLETE',
                    additional_data={
                        'review_result': review_result,
                        'comments': comments
                    }
                )
            
            return success

    def initiate_approval_workflow(self, document: Document, approver: User,
                                 initiated_by: User, **kwargs) -> WorkflowInstance:
        """
        Initiate approval workflow for a document.
        
        Args:
            document: Document to approve
            approver: User assigned to approve
            initiated_by: User initiating the workflow
            **kwargs: Additional workflow data
            
        Returns:
            WorkflowInstance: Created workflow instance
        """
        with transaction.atomic():
            # Create workflow instance
            workflow = workflow_service.initiate_workflow(
                document=document,
                workflow_type='APPROVAL',
                initiated_by=initiated_by,
                assigned_to=approver,
                **kwargs
            )
            
            # Transition document to pending approval
            self._transition_document_state(
                document=document,
                new_state='pending_approval',
                user=initiated_by,
                reason='Approval workflow initiated'
            )
            
            # Log audit trail
            audit_service.log_workflow_event(
                workflow_instance=workflow,
                event_type='APPROVAL_WORKFLOW_INITIATED',
                user=initiated_by,
                description=f"Approval workflow initiated for {document.document_number}",
                additional_data={
                    'approver': approver.username,
                    'document_number': document.document_number
                }
            )
            
            return workflow

    def approve_document(self, document: Document, approver: User, 
                        signature_reason: str = '', **kwargs) -> bool:
        """
        Approve a document with electronic signature.
        
        Args:
            document: Document to approve
            approver: User approving the document
            signature_reason: Reason for electronic signature
            **kwargs: Additional approval data
            
        Returns:
            bool: True if successful
        """
        if not self._can_transition(document, 'approve', approver):
            return False
        
        with transaction.atomic():
            # Create electronic signature
            signature = ElectronicSignature.objects.create(
                document=document,
                user=approver,
                signature_type='APPROVAL',
                reason=signature_reason or f'Approval of document {document.document_number}',
                signature_timestamp=timezone.now()
            )
            
            # Transition document state
            success = self._transition_document_state(
                document=document,
                new_state='approved',
                user=approver,
                reason=f'Document approved by {approver.get_full_name()}'
            )
            
            if success:
                # Update document approval fields
                document.approved_by = approver
                document.approval_date = timezone.now()
                document.save(update_fields=['approved_by', 'approval_date'])
                
                # Complete approval workflow
                workflow = self._get_active_workflow(document, 'APPROVAL')
                if workflow:
                    workflow_service.complete_workflow(
                        workflow, 
                        reason=f'Document approved with electronic signature'
                    )
                
                # Schedule effective date if set
                if document.effective_date and document.effective_date <= timezone.now().date():
                    self._make_document_effective(document, approver)
                
                # Log audit trail
                audit_service.log_document_access(
                    user=approver,
                    document=document,
                    access_type='APPROVE',
                    additional_data={
                        'signature_id': signature.id,
                        'approval_timestamp': document.approval_date.isoformat()
                    }
                )
            
            return success

    def reject_document(self, document: Document, reviewer_or_approver: User,
                       rejection_reason: str, **kwargs) -> bool:
        """
        Reject a document during review or approval.
        
        Args:
            document: Document to reject
            reviewer_or_approver: User rejecting the document
            rejection_reason: Reason for rejection
            **kwargs: Additional rejection data
            
        Returns:
            bool: True if successful
        """
        with transaction.atomic():
            # Transition document back to draft
            success = self._transition_document_state(
                document=document,
                new_state='draft',
                user=reviewer_or_approver,
                reason=f'Document rejected: {rejection_reason}'
            )
            
            if success:
                # Complete active workflows
                active_workflows = WorkflowInstance.objects.filter(
                    content_type__model='document',
                    object_id=document.id,
                    is_active=True
                )
                
                for workflow in active_workflows:
                    workflow_service.complete_workflow(
                        workflow,
                        reason=f'Document rejected: {rejection_reason}'
                    )
                
                # Log audit trail
                audit_service.log_document_access(
                    user=reviewer_or_approver,
                    document=document,
                    access_type='REJECT',
                    additional_data={
                        'rejection_reason': rejection_reason
                    }
                )
            
            return success

    def make_document_effective(self, document: Document, user: User = None) -> bool:
        """
        Make an approved document effective.
        
        Args:
            document: Document to make effective
            user: User making the document effective (None for system)
            
        Returns:
            bool: True if successful
        """
        return self._make_document_effective(document, user)

    def initiate_obsolescence_workflow(self, document: Document, 
                                     initiated_by: User, reason: str,
                                     **kwargs) -> WorkflowInstance:
        """
        Initiate obsolescence workflow for a document.
        
        Args:
            document: Document to make obsolete
            initiated_by: User initiating obsolescence
            reason: Reason for obsolescence
            **kwargs: Additional workflow data
            
        Returns:
            WorkflowInstance: Created workflow instance
        """
        with transaction.atomic():
            # Create workflow instance
            workflow = workflow_service.initiate_workflow(
                document=document,
                workflow_type='OBSOLETE',
                initiated_by=initiated_by,
                reason=reason,
                **kwargs
            )
            
            # Log audit trail
            audit_service.log_workflow_event(
                workflow_instance=workflow,
                event_type='OBSOLESCENCE_WORKFLOW_INITIATED',
                user=initiated_by,
                description=f"Obsolescence workflow initiated for {document.document_number}",
                additional_data={
                    'reason': reason,
                    'document_number': document.document_number
                }
            )
            
            return workflow

    def make_document_obsolete(self, document: Document, user: User, 
                             reason: str, **kwargs) -> bool:
        """
        Make a document obsolete.
        
        Args:
            document: Document to make obsolete
            user: User making the document obsolete
            reason: Reason for obsolescence
            **kwargs: Additional data
            
        Returns:
            bool: True if successful
        """
        with transaction.atomic():
            # Transition document state
            success = self._transition_document_state(
                document=document,
                new_state='obsolete',
                user=user,
                reason=f'Document made obsolete: {reason}'
            )
            
            if success:
                # Update document obsolescence fields
                document.obsolete_date = timezone.now().date()
                document.save(update_fields=['obsolete_date'])
                
                # Complete obsolescence workflow
                workflow = self._get_active_workflow(document, 'OBSOLETE')
                if workflow:
                    workflow_service.complete_workflow(
                        workflow,
                        reason=f'Document made obsolete: {reason}'
                    )
                
                # Log audit trail
                audit_service.log_document_access(
                    user=user,
                    document=document,
                    access_type='MAKE_OBSOLETE',
                    additional_data={
                        'obsolescence_reason': reason,
                        'obsolete_date': document.obsolete_date.isoformat()
                    }
                )
            
            return success

    def get_available_transitions(self, document: Document, user: User) -> List[Dict[str, Any]]:
        """
        Get available workflow transitions for a document and user.
        
        Args:
            document: Document to check transitions for
            user: User requesting transitions
            
        Returns:
            List of available transitions
        """
        workflow_object = InstanceWorkflowObject(document)
        available_transitions = []
        
        try:
            transitions = workflow_object.get_available_transitions(user)
            
            for transition in transitions:
                available_transitions.append({
                    'name': transition.name,
                    'destination': transition.destination_state.label,
                    'can_perform': self._can_user_perform_transition(user, transition)
                })
                
        except Exception:
            pass  # No transitions available or error
        
        return available_transitions

    def _transition_document_state(self, document: Document, new_state: str,
                                 user: User, reason: str = '') -> bool:
        """Transition document state using Django-River."""
        try:
            workflow_object = InstanceWorkflowObject(document)
            
            # Find transition to new state
            transitions = workflow_object.get_available_transitions(user)
            target_transition = None
            
            for transition in transitions:
                if transition.destination_state.slug == new_state:
                    target_transition = transition
                    break
            
            if target_transition:
                workflow_object.proceed(user, target_transition.name)
                return True
                
        except Exception as e:
            # Log error but don't raise to avoid breaking the workflow
            audit_service.log_system_event(
                event_type='WORKFLOW_TRANSITION_ERROR',
                object_type='Document',
                object_id=document.id,
                description=f"Failed to transition document to {new_state}: {str(e)}"
            )
        
        return False

    def _can_transition(self, document: Document, transition_name: str, user: User) -> bool:
        """Check if user can perform a specific transition."""
        try:
            workflow_object = InstanceWorkflowObject(document)
            transitions = workflow_object.get_available_transitions(user)
            
            return any(t.name == transition_name for t in transitions)
            
        except Exception:
            return False

    def _can_user_perform_transition(self, user: User, transition) -> bool:
        """Check if user has permissions for a transition."""
        # Check role-based permissions
        required_permissions = {
            'submit_for_review': ['write'],
            'start_review': ['review'],
            'complete_review': ['review'],
            'submit_for_approval': ['review'],
            'approve': ['approve'],
            'reject': ['review', 'approve'],
            'make_effective': ['admin'],
            'make_obsolete': ['approve', 'admin']
        }
        
        transition_perms = required_permissions.get(transition.name, [])
        
        # Check user roles for required permissions
        for perm in transition_perms:
            if user.user_roles.filter(
                role__permission_level=perm,
                is_active=True
            ).exists():
                return True
        
        return user.is_superuser

    def _get_active_workflow(self, document: Document, workflow_type: str) -> Optional[WorkflowInstance]:
        """Get active workflow instance for a document."""
        try:
            return WorkflowInstance.objects.get(
                content_type__model='document',
                object_id=document.id,
                workflow_type__workflow_type=workflow_type,
                is_active=True
            )
        except WorkflowInstance.DoesNotExist:
            return None

    def _initiate_approval_workflow(self, document: Document, review_workflow: WorkflowInstance, 
                                  reviewer: User):
        """Automatically initiate approval workflow after successful review."""
        # Find an approver
        approver_role = Role.objects.filter(
            name__icontains='approver',
            permission_level='approve'
        ).first()
        
        if approver_role:
            approvers = User.objects.filter(
                user_roles__role=approver_role,
                user_roles__is_active=True
            ).first()
            
            if approvers:
                self.initiate_approval_workflow(
                    document=document,
                    approver=approvers,
                    initiated_by=reviewer,
                    parent_workflow=review_workflow.id
                )

    def _make_document_effective(self, document: Document, user: User = None) -> bool:
        """Internal method to make document effective."""
        with transaction.atomic():
            success = self._transition_document_state(
                document=document,
                new_state='effective',
                user=user,
                reason='Document made effective'
            )
            
            if success:
                # Update document effective date
                document.effective_date = timezone.now().date()
                document.save(update_fields=['effective_date'])
                
                # Log audit trail
                if user:
                    audit_service.log_document_access(
                        user=user,
                        document=document,
                        access_type='MAKE_EFFECTIVE'
                    )
                else:
                    audit_service.log_system_event(
                        event_type='DOCUMENT_MADE_EFFECTIVE',
                        object_type='Document',
                        object_id=document.id,
                        description=f"Document {document.document_number} automatically made effective"
                    )
            
            return success


# Global document workflow manager instance
document_workflow_manager = DocumentWorkflowManager()