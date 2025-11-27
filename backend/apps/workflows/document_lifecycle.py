"""
Document Lifecycle Workflows for EDMS

Implements the 4 simple workflows described in EDMS_details_workflow.txt:
1. Review Workflow: DRAFT → PENDING_REVIEW → UNDER_REVIEW → APPROVED → EFFECTIVE
2. Up-versioning Workflow: Create new version and supersede old
3. Obsolete Workflow: Mark documents obsolete with dependency checks
4. Workflow Termination: Return to last approved state

Using the static workflow engine with DocumentState and WorkflowType.
"""

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import DocumentWorkflow, DocumentState, DocumentTransition, WorkflowType
from apps.documents.models import Document

User = get_user_model()


class DocumentLifecycleService:
    """
    Simple document lifecycle service implementing the 4 basic workflows.
    
    Provides straightforward workflow operations without complex configuration,
    focusing on the essential document lifecycle paths.
    """
    
    def __init__(self):
        # Cache commonly used objects
        self._states = None
        self._workflow_types = None
    
    @property
    def states(self):
        """Cached access to document states."""
        if self._states is None:
            self._states = {
                state.code: state for state in DocumentState.objects.all()
            }
        return self._states
    
    @property
    def workflow_types(self):
        """Cached access to workflow types."""
        if self._workflow_types is None:
            self._workflow_types = {
                wt.workflow_type: wt for wt in WorkflowType.objects.filter(is_active=True)
            }
        return self._workflow_types
    
    # =================================================================
    # 1. REVIEW WORKFLOW (Primary document workflow)
    # =================================================================
    
    def start_review_workflow(self, document: Document, initiated_by: User, 
                             reviewer: User = None, approver: User = None) -> DocumentWorkflow:
        """
        Start a standard review workflow for a document.
        
        Workflow Path: DRAFT → PENDING_REVIEW → UNDER_REVIEW → APPROVED → EFFECTIVE
        
        Args:
            document: Document to start workflow for
            initiated_by: User starting the workflow
            reviewer: Optional reviewer assignment
            approver: Optional approver assignment
            
        Returns:
            DocumentWorkflow: Created workflow instance
        """
        with transaction.atomic():
            # Validate document can start workflow
            if document.status not in ['DRAFT']:
                raise ValidationError(f"Cannot start review workflow. Document status: {document.status}")
            
            # Assign reviewer and approver if provided
            if reviewer:
                document.reviewer = reviewer
            if approver:
                document.approver = approver
            document.save()
            
            # Get appropriate workflow type (prefer Document Review for standard process)
            workflow_type = (self.workflow_types.get('REVIEW') or 
                           WorkflowType.objects.filter(workflow_type='REVIEW').first())
            
            if not workflow_type:
                raise ValidationError("No REVIEW workflow type found")
            
            # Create workflow
            workflow = DocumentWorkflow.objects.create(
                document=document,
                workflow_type=workflow_type,
                current_state=self.states['DRAFT'],
                initiated_by=initiated_by,
                current_assignee=document.author,
                due_date=self._calculate_due_date(workflow_type),
                workflow_data={'review_type': 'standard'}
            )
            
            # Set document to initial workflow state
            document.status = 'DRAFT'
            document.save()
            
            return workflow
    
    def submit_for_review(self, document: Document, user: User, 
                         comment: str = '') -> bool:
        """
        Submit document for review (DRAFT → PENDING_REVIEW).
        
        Args:
            document: Document to submit
            user: User submitting (must be author)
            comment: Optional submission comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can submit
        if document.author != user and not user.is_superuser:
            raise ValidationError("Only document author can submit for review")
        
        # Validate current state
        if workflow.current_state.code != 'DRAFT':
            raise ValidationError(f"Cannot submit from state: {workflow.current_state.code}")
        
        # Validate reviewer is assigned
        if not document.reviewer:
            raise ValidationError("Document must have a reviewer assigned")
        
        return self._transition_workflow(
            workflow=workflow,
            to_state_code='PENDING_REVIEW',
            user=user,
            comment=comment or 'Document submitted for review',
            assignee=document.reviewer
        )
    
    def start_review(self, document: Document, user: User, 
                    comment: str = '') -> bool:
        """
        Start reviewing document (PENDING_REVIEW → UNDER_REVIEW).
        
        Args:
            document: Document to start reviewing
            user: User starting review (must be assigned reviewer)
            comment: Optional review start comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can review
        if not self._can_review(document, user):
            raise ValidationError("User is not authorized to review this document")
        
        # Validate current state
        if workflow.current_state.code != 'PENDING_REVIEW':
            raise ValidationError(f"Cannot start review from state: {workflow.current_state.code}")
        
        return self._transition_workflow(
            workflow=workflow,
            to_state_code='UNDER_REVIEW',
            user=user,
            comment=comment or 'Review started',
            assignee=user
        )
    
    def complete_review(self, document: Document, user: User, 
                       approved: bool = True, comment: str = '') -> bool:
        """
        Complete document review (UNDER_REVIEW → PENDING_APPROVAL or back to DRAFT).
        
        Args:
            document: Document being reviewed
            user: User completing review
            approved: True if review passed, False to reject back to DRAFT
            comment: Review comment (required)
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can complete review
        if not self._can_review(document, user):
            raise ValidationError("User is not authorized to complete review")
        
        # Validate current state
        if workflow.current_state.code != 'UNDER_REVIEW':
            raise ValidationError(f"Cannot complete review from state: {workflow.current_state.code}")
        
        if not comment:
            raise ValidationError("Review comment is required")
        
        if approved:
            # Review approved - transition to REVIEWED state for author to route to approval
            return self._transition_workflow(
                workflow=workflow,
                to_state_code='REVIEWED',
                user=user,
                comment=comment,
                assignee=document.author  # Return to author to select approver
            )
        else:
            # Reject back to draft
            return self._transition_workflow(
                workflow=workflow,
                to_state_code='DRAFT',
                user=user,
                comment=f'Review rejected: {comment}',
                assignee=document.author
            )
    
    def route_for_approval(self, document: Document, user: User, 
                          approver: User, comment: str = '') -> bool:
        """
        Route document for approval after review completion (REVIEWED → PENDING_APPROVAL).
        
        Args:
            document: Document to route for approval
            user: User routing (must be document author)
            approver: User to assign as approver
            comment: Routing comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can route for approval
        if document.author != user and not user.is_superuser:
            raise ValidationError("Only document author can route for approval")
        
        # Validate current state
        if workflow.current_state.code != 'REVIEWED':
            raise ValidationError(f"Cannot route for approval from state: {workflow.current_state.code}")
        
        # Assign approver and route
        document.approver = approver
        document.save()
        
        return self._transition_workflow(
            workflow=workflow,
            to_state_code='PENDING_APPROVAL',
            user=user,
            comment=comment or f'Document routed to {approver.get_full_name()} for approval',
            assignee=approver
        )

    def approve_document(self, document: Document, user: User, 
                        effective_date: date, comment: str = '') -> bool:
        """
        Approve document with required effective date (PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE or APPROVED_AND_EFFECTIVE).
        
        Args:
            document: Document to approve
            user: User approving (must be assigned approver)
            effective_date: Date when document becomes effective (REQUIRED)
            comment: Approval comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow found for document")
        
        # Validate user can approve
        if not self._can_approve(document, user):
            raise ValidationError("User is not authorized to approve this document")
        
        # Validate current state
        if workflow.current_state.code != 'PENDING_APPROVAL':
            raise ValidationError(f"Cannot approve from state: {workflow.current_state.code}")
        
        # Validate effective_date is provided
        if not effective_date:
            raise ValidationError("Effective date is required for approval")

        # Set effective date and approval date
        document.effective_date = effective_date
        document.approval_date = timezone.now()
        document.save()

        # Determine target state based on effective date
        today = timezone.now().date()
        if effective_date <= today:
            # Effective today or in the past = immediately effective
            target_state = 'APPROVED_AND_EFFECTIVE'
            comment_suffix = f' - Effective immediately ({effective_date})'
        else:
            # Effective in the future = pending effective
            target_state = 'APPROVED_PENDING_EFFECTIVE'
            comment_suffix = f' - Pending effective {effective_date}'

        # Transition to appropriate state
        return self._transition_workflow(
            workflow=workflow,
            to_state_code=target_state,
            user=user,
            comment=(comment or f'Document approved by {user.get_full_name()}') + comment_suffix,
            assignee=None  # No further assignment needed for intentional workflow
        )
    
    def activate_pending_effective_documents(self, user: User = None) -> int:
        """
        Scheduler task: Activate documents that are APPROVED_PENDING_EFFECTIVE and due today.
        Called daily at midnight to check and update document statuses.
        
        Args:
            user: System user for audit trail (optional, defaults to system)
            
        Returns:
            int: Number of documents activated
        """
        from django.contrib.auth import get_user_model
        
        if not user:
            User = get_user_model()
            user, _ = User.objects.get_or_create(
                username='system',
                defaults={'first_name': 'System', 'last_name': 'Scheduler', 'is_staff': True}
            )
        
        today = timezone.now().date()
        activated_count = 0
        
        # Find documents that are pending effective and due today or earlier
        pending_docs = Document.objects.filter(
            status='APPROVED_PENDING_EFFECTIVE',
            effective_date__lte=today
        )
        
        for document in pending_docs:
            try:
                with transaction.atomic():
                    workflow = self._get_active_workflow(document)
                    if workflow and workflow.current_state.code == 'APPROVED_PENDING_EFFECTIVE':
                        # Transition to APPROVED_AND_EFFECTIVE
                        success = self._transition_workflow(
                            workflow=workflow,
                            to_state_code='APPROVED_AND_EFFECTIVE',
                            user=user,
                            comment=f'Document automatically activated on scheduled effective date: {document.effective_date}',
                            assignee=None
                        )
                        if success:
                            activated_count += 1
                            
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Failed to activate document {document.document_number}: {e}")
        
        return activated_count
    
    # =================================================================
    # 2. UP-VERSIONING WORKFLOW
    # =================================================================
    
    def start_version_workflow(self, existing_document: Document, user: User,
                              new_version_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start up-versioning workflow to create new version and supersede old.
        
        Process:
        1. Create new document version
        2. Start review workflow for new version
        3. When new version becomes effective, mark old as SUPERSEDED
        
        Args:
            existing_document: Current effective document
            user: User initiating versioning
            new_version_data: Data for new version (title, description, etc.)
            
        Returns:
            dict: Contains new_document and workflow info
        """
        with transaction.atomic():
            # Validate existing document
            if existing_document.status not in ['EFFECTIVE', 'APPROVED_AND_EFFECTIVE']:
                raise ValidationError("Can only version EFFECTIVE documents")
            
            # Create new version
            major, minor = existing_document.get_next_version(
                major_increment=new_version_data.get('major_increment', False)
            )
            
            # Generate versioned document number to maintain uniqueness while showing relationship
            # Extract base document number by removing any existing version suffix
            base_doc_number = existing_document.document_number
            if '-v' in base_doc_number:
                # Remove existing version (e.g., "SOP-2025-0001-v1.0" -> "SOP-2025-0001")
                base_doc_number = base_doc_number.split('-v')[0]
            versioned_doc_number = f"{base_doc_number}-v{major}.{minor}"
            
            new_document = Document.objects.create(
                document_number=versioned_doc_number,  # Versioned document number
                title=new_version_data.get('title', existing_document.title),
                description=new_version_data.get('description', existing_document.description),
                document_type=existing_document.document_type,
                document_source=existing_document.document_source,
                author=user,
                reviewer=new_version_data.get('reviewer', existing_document.reviewer),
                approver=new_version_data.get('approver', existing_document.approver),
                version_major=major,
                version_minor=minor,
                supersedes=existing_document,
                reason_for_change=new_version_data.get('reason_for_change', ''),
                change_summary=new_version_data.get('change_summary', ''),
                status='DRAFT'
            )
            
            # Start review workflow for new version
            workflow = self.start_review_workflow(
                document=new_document,
                initiated_by=user,
                reviewer=new_document.reviewer,
                approver=new_document.approver
            )
            
            # Use up-versioning workflow type if available
            upversion_type = self.workflow_types.get('UP_VERSION')
            if upversion_type:
                workflow.workflow_type = upversion_type.workflow_type
                workflow.save()
            
            return {
                'new_document': new_document,
                'workflow': workflow,
                'superseded_document': existing_document
            }
    
    def complete_versioning(self, new_document: Document, user: User) -> bool:
        """
        Complete versioning by making old document SUPERSEDED.
        Called automatically when new version becomes EFFECTIVE.
        
        Args:
            new_document: New effective document
            user: User completing the versioning
            
        Returns:
            bool: True if successful
        """
        if not new_document.supersedes:
            return True  # Nothing to supersede
        
        if new_document.status not in ['EFFECTIVE', 'APPROVED_AND_EFFECTIVE']:
            raise ValidationError("New document must be EFFECTIVE to supersede old version")
        
        with transaction.atomic():
            old_document = new_document.supersedes
            old_document.status = 'SUPERSEDED'
            old_document.obsolete_date = timezone.now().date()
            old_document.save()
            
            # Record transition if old document has workflow
            old_workflow = self._get_active_workflow(old_document)
            if old_workflow:
                self._transition_workflow(
                    workflow=old_workflow,
                    to_state_code='SUPERSEDED',
                    user=user,
                    comment=f'Superseded by {new_document.document_number}',
                    assignee=None
                )
        
        return True
    
    # =================================================================
    # 3. OBSOLETE WORKFLOW
    # =================================================================
    
    def start_obsolete_workflow(self, document: Document, user: User,
                               reason: str, target_date: date = None) -> DocumentWorkflow:
        """
        Start obsolescence workflow with dependency checking.
        
        Args:
            document: Document to make obsolete
            user: User initiating obsolescence
            reason: Reason for obsolescence (required)
            target_date: Target obsolescence date
            
        Returns:
            DocumentWorkflow: Obsolescence workflow
        """
        with transaction.atomic():
            # Validate document can be obsoleted
            if document.status not in ['EFFECTIVE', 'APPROVED_AND_EFFECTIVE']:
                raise ValidationError("Can only obsolete EFFECTIVE documents")
            
            if not reason:
                raise ValidationError("Reason for obsolescence is required")
            
            # Check for dependent documents
            dependencies = document.dependents.filter(is_active=True, is_critical=True)
            if dependencies.exists():
                dependent_docs = [dep.document.document_number for dep in dependencies]
                raise ValidationError(
                    f"Cannot obsolete document with critical dependencies: {', '.join(dependent_docs)}"
                )
            
            # Get obsolete workflow type - use simple string instead of WorkflowType object
            obsolete_workflow_type = 'OBSOLETE'
            
            # Get or update existing workflow for obsolescence
            workflow, created = DocumentWorkflow.objects.get_or_create(
                document=document,
                defaults={
                    'workflow_type': obsolete_workflow_type,
                    'current_state': self.states['PENDING_APPROVAL'],
                    'initiated_by': user,
                    'current_assignee': document.approver or document.author,
                    'due_date': None,
                    'workflow_data': {
                        'obsolete_reason': reason,
                        'target_obsolete_date': target_date.isoformat() if target_date else None
                    }
                }
            )
            
            # If workflow already exists, update it for obsolescence
            if not created:
                workflow.workflow_type = obsolete_workflow_type
                workflow.current_state = self.states['PENDING_APPROVAL']
                workflow.current_assignee = document.approver or document.author
                workflow.workflow_data.update({
                    'obsolete_reason': reason,
                    'target_obsolete_date': target_date.isoformat() if target_date else None
                })
                workflow.save()
            
            return workflow
    
    def approve_obsolescence(self, document: Document, user: User,
                            comment: str = '') -> bool:
        """
        Approve document obsolescence (PENDING_APPROVAL → OBSOLETE).
        
        Args:
            document: Document to obsolete
            user: User approving obsolescence
            comment: Approval comment
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow or 'OBSOLETE' not in workflow.workflow_type:
            raise ValidationError("No active obsolescence workflow found")
        
        # Validate user can approve obsolescence
        if not self._can_approve(document, user):
            raise ValidationError("User is not authorized to approve obsolescence")
        
        success = self._transition_workflow(
            workflow=workflow,
            to_state_code='OBSOLETE',
            user=user,
            comment=comment or 'Obsolescence approved',
            assignee=None
        )
        
        if success:
            # Update document
            document.status = 'OBSOLETE'
            document.obsolete_date = timezone.now().date()
            document.save()
        
        return success
    
    # =================================================================
    # 4. WORKFLOW TERMINATION
    # =================================================================
    
    def terminate_workflow(self, document: Document, user: User,
                          reason: str) -> bool:
        """
        Terminate active workflow and return document to last approved state.
        
        Args:
            document: Document with workflow to terminate
            user: User terminating workflow
            reason: Reason for termination (required)
            
        Returns:
            bool: True if successful
        """
        workflow = self._get_active_workflow(document)
        if not workflow:
            raise ValidationError("No active workflow to terminate")
        
        if not reason:
            raise ValidationError("Reason for termination is required")
        
        # Validate user can terminate
        if (document.author != user and 
            not self._can_approve(document, user) and 
            not user.is_superuser):
            raise ValidationError("User not authorized to terminate workflow")
        
        with transaction.atomic():
            # Determine return state based on document history
            return_state = self._determine_return_state(document)
            
            # Terminate workflow
            success = self._transition_workflow(
                workflow=workflow,
                to_state_code='TERMINATED',
                user=user,
                comment=f'Workflow terminated: {reason}',
                assignee=None
            )
            
            if success:
                # Update document to return state
                document.status = return_state
                document.save()
                
                # Note: DocumentWorkflow doesn't have is_active/completed_at fields
                # The workflow state is already set to TERMINATED above
        
        return success
    
    # =================================================================
    # UTILITY METHODS
    # =================================================================
    
    def get_document_workflow_status(self, document: Document) -> Dict[str, Any]:
        """Get current workflow status for a document."""
        workflow = self._get_active_workflow(document)
        
        if not workflow:
            return {
                'has_active_workflow': False,
                'document_status': document.status,
                'next_actions': self._get_available_actions(document, None)
            }
        
        return {
            'has_active_workflow': True,
            'workflow_type': workflow.workflow_type,
            'current_state': workflow.current_state.code,
            'current_assignee': workflow.current_assignee.username if workflow.current_assignee else None,
            'started_at': workflow.created_at,
            'due_date': workflow.due_date,
            'is_overdue': workflow.due_date and workflow.due_date < timezone.now(),
            'document_status': document.status,
            'next_actions': self._get_available_actions(document, workflow)
        }
    
    def _get_active_workflow(self, document: Document) -> Optional[DocumentWorkflow]:
        """Get active workflow for a document."""
        # DocumentWorkflow doesn't have is_active field, so get the most recent one
        return DocumentWorkflow.objects.filter(
            document=document
        ).order_by('-created_at').first()
    
    def _transition_workflow(self, workflow: DocumentWorkflow, to_state_code: str,
                           user: User, comment: str, assignee: User = None) -> bool:
        """Execute a workflow state transition."""
        try:
            with transaction.atomic():
                from_state = workflow.current_state
                to_state = self.states[to_state_code]
                
                # Create transition record
                transition = DocumentTransition.objects.create(
                    workflow=workflow,
                    from_state=from_state,
                    to_state=to_state,
                    transitioned_by=user,
                    comment=comment,
                    transition_data={'assignee': assignee.username if assignee else None}
                )
                
                # Update workflow state
                workflow.current_state = to_state
                workflow.current_assignee = assignee
                
                # Handle workflow completion - DocumentWorkflow doesn't have is_active/completed_at fields
                # Just update the state
                
                workflow.save()
                
                # Update document status
                workflow.document.status = to_state_code
                workflow.document.save()
                
                # Handle post-transition actions
                self._handle_post_transition(workflow, transition)
                
                return True
                
        except Exception as e:
            # Log error for debugging
            print(f"Workflow transition failed: {e}")
            return False
    
    def _handle_post_transition(self, workflow: DocumentWorkflow, 
                              transition: DocumentTransition):
        """Handle actions after successful transition."""
        # Auto-complete versioning when new version becomes effective
        if (transition.to_state.code in ['EFFECTIVE', 'APPROVED_AND_EFFECTIVE'] and 
            workflow.document.supersedes):
            self.complete_versioning(workflow.document, transition.transitioned_by)
    
    def _calculate_due_date(self, workflow_type: WorkflowType):
        """Calculate due date based on workflow type."""
        if workflow_type.timeout_days:
            return timezone.now() + timezone.timedelta(days=workflow_type.timeout_days)
        return None
    
    def _can_review(self, document: Document, user: User) -> bool:
        """Check if user can review document."""
        return (document.reviewer == user or
                user.user_roles.filter(
                    role__module='O1',
                    role__permission_level__in=['review', 'approve', 'admin'],
                    is_active=True
                ).exists() or
                user.is_superuser)
    
    def _can_approve(self, document: Document, user: User) -> bool:
        """Check if user can approve document."""
        return (document.approver == user or
                user.user_roles.filter(
                    role__module='O1', 
                    role__permission_level__in=['approve', 'admin'],
                    is_active=True
                ).exists() or
                user.is_superuser)
    
    def _determine_return_state(self, document: Document) -> str:
        """Determine state to return to when terminating workflow."""
        # Look for last non-workflow state or default to DRAFT
        if hasattr(document, 'approval_date') and document.approval_date:
            return 'APPROVED'
        elif document.status in ['EFFECTIVE']:
            return 'EFFECTIVE'
        else:
            return 'DRAFT'
    
    def _get_available_actions(self, document: Document, 
                             workflow: DocumentWorkflow = None) -> List[str]:
        """Get available actions for current document/workflow state."""
        if not workflow:
            if document.status == 'DRAFT':
                return ['start_review_workflow', 'start_version_workflow']
            elif document.status == 'EFFECTIVE':
                return ['start_version_workflow', 'start_obsolete_workflow']
            return []
        
        state = workflow.current_state.code
        actions = []
        
        if state == 'DRAFT':
            actions.append('submit_for_review')
        elif state == 'PENDING_REVIEW':
            actions.append('start_review')
        elif state == 'UNDER_REVIEW':
            actions.extend(['complete_review', 'reject_to_draft'])
        elif state == 'REVIEWED':
            actions.append('route_for_approval')
        elif state == 'PENDING_APPROVAL':
            if 'OBSOLETE' in workflow.workflow_type:
                actions.append('approve_obsolescence')
            else:
                actions.extend(['approve_document', 'reject_to_draft'])
        elif state == 'APPROVED':
            actions.append('make_effective')
        
        # Termination is always available for workflows not in terminal states
        if workflow and state not in ['EFFECTIVE', 'SUPERSEDED', 'OBSOLETE', 'TERMINATED']:
            actions.append('terminate_workflow')
        
        return actions


# Global service instance
_document_lifecycle_service = None

def get_document_lifecycle_service():
    """Get the global document lifecycle service instance."""
    global _document_lifecycle_service
    if _document_lifecycle_service is None:
        _document_lifecycle_service = DocumentLifecycleService()
    return _document_lifecycle_service