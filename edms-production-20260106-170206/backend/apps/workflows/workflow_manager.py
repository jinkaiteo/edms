"""
Workflow Manager implementing EDMS workflow specification.

Implements all 4 workflow types from EDMS_details_workflow.txt:
1. Review Workflow
2. Up-versioning Workflow  
3. Obsolete Workflow
4. Termination Workflow
"""

from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import DocumentState, DocumentWorkflow, DocumentTransition
from .dependency_manager import DocumentDependencyManager
from .comment_manager import WorkflowCommentManager

User = get_user_model()


class WorkflowManager:
    """Manages document workflows per EDMS specification."""
    
    @staticmethod
    def start_review_workflow(document, author, reviewer=None, approver=None):
        """
        Start Review Workflow (EDMS specification lines 3-18).
        
        Flow: DRAFT → Pending Review → Reviewed → Pending Approval → 
              Approved, Pending Effective → Approved and Effective
        """
        # Create workflow instance
        workflow = DocumentWorkflow.objects.create(
            document=document,
            workflow_type='REVIEW',
            current_state_id=DocumentState.DRAFT,
            initiated_by=author,
            selected_reviewer=reviewer,
            selected_approver=approver
        )
        
        # Set document status to DRAFT
        document.status = DocumentState.DRAFT
        document.save()
        
        return workflow
    
    @staticmethod
    def submit_for_review(workflow, reviewer, due_date=None):
        """
        Submit document for review (EDMS specification line 6).
        DRAFT → Pending Review
        """
        if workflow.current_state_id != DocumentState.DRAFT:
            raise ValueError(f"Cannot submit for review from state {workflow.current_state_id}")
        
        workflow.transition_to(
            DocumentState.PENDING_REVIEW,
            workflow.initiated_by,
            comment="Document submitted for review",
            assignee=reviewer,
            due_date=due_date
        )
        
        # Update document status
        workflow.document.status = DocumentState.PENDING_REVIEW
        workflow.document.save()
        
        return workflow
    
    @staticmethod
    def complete_review(workflow, reviewer, approved, comment=""):
        """
        Complete document review (EDMS specification lines 8-10).
        
        Pending Review → DRAFT (if rejected) or Reviewed (if approved)
        """
        if workflow.current_state_id != DocumentState.PENDING_REVIEW:
            raise ValueError("Workflow not in pending review state")
        
        if approved:
            workflow.transition_to(
                DocumentState.REVIEWED,
                reviewer,
                comment=f"Review approved: {comment}"
            )
            workflow.document.status = DocumentState.REVIEWED
        else:
            workflow.transition_to(
                DocumentState.DRAFT,
                reviewer, 
                comment=f"Review rejected: {comment}"
            )
            workflow.document.status = DocumentState.DRAFT
        
        workflow.document.save()
        
        # Store reviewer comment
        WorkflowCommentManager.add_comment(
            workflow=workflow,
            user=reviewer,
            comment_type='REVIEW',
            comment=comment,
            decision='APPROVED' if approved else 'REJECTED'
        )
        
        return workflow
    
    @staticmethod
    def submit_for_approval(workflow, approver, due_date=None):
        """
        Submit document for approval (EDMS specification line 11).
        Reviewed → Pending Approval
        """
        if workflow.current_state_id != DocumentState.REVIEWED:
            raise ValueError("Document must be reviewed before approval")
        
        workflow.transition_to(
            DocumentState.PENDING_APPROVAL,
            workflow.initiated_by,
            comment="Document submitted for approval",
            assignee=approver,
            due_date=due_date
        )
        
        workflow.document.status = DocumentState.PENDING_APPROVAL
        workflow.document.save()
        
        return workflow
    
    @staticmethod
    def complete_approval(workflow, approver, approved, effective_date=None, comment=""):
        """
        Complete document approval (EDMS specification lines 13-16).
        
        Pending Approval → DRAFT (rejected) or Approved, Pending Effective (approved)
        """
        if workflow.current_state_id != DocumentState.PENDING_APPROVAL:
            raise ValueError("Workflow not in pending approval state")
        
        if approved:
            if not effective_date:
                effective_date = timezone.now().date()
            
            workflow.effective_date = effective_date
            workflow.transition_to(
                DocumentState.APPROVED_PENDING_EFFECTIVE,
                approver,
                comment=f"Approval granted, effective {effective_date}: {comment}"
            )
            workflow.document.status = DocumentState.APPROVED_PENDING_EFFECTIVE
        else:
            workflow.transition_to(
                DocumentState.DRAFT,
                approver,
                comment=f"Approval rejected: {comment}"
            )
            workflow.document.status = DocumentState.DRAFT
        
        workflow.save()
        workflow.document.save()
        
        # Store approver comment
        WorkflowCommentManager.add_comment(
            workflow=workflow,
            user=approver,
            comment_type='APPROVAL',
            comment=comment,
            decision='APPROVED' if approved else 'REJECTED'
        )
        
        return workflow
    
    @staticmethod
    def start_up_versioning_workflow(parent_document, author, reason):
        """
        Start Up-versioning Workflow (EDMS specification lines 20-26).
        
        Requirements:
        - Parent document must be "Approved and Effective"
        - Provide reason for up-versioning
        - Follows Review Workflow
        """
        if parent_document.status != DocumentState.APPROVED_AND_EFFECTIVE:
            raise ValueError("Parent document must be 'Approved and Effective'")
        
        # Get impact analysis
        impact = DocumentDependencyManager.get_impact_analysis(parent_document)
        
        # Create new document version
        new_document = Document.objects.create(
            title=parent_document.title,
            document_type=parent_document.document_type,
            version=parent_document.get_next_version(),
            parent_document=parent_document,
            author=author,
            status=DocumentState.DRAFT
        )
        
        # Create up-versioning workflow
        workflow = DocumentWorkflow.objects.create(
            document=new_document,
            workflow_type='UP_VERSION',
            current_state_id=DocumentState.DRAFT,
            initiated_by=author,
            up_version_reason=reason,
            workflow_data={'impact_analysis': impact}
        )
        
        return workflow
    
    @staticmethod
    def start_obsolete_workflow(document, author, reason):
        """
        Start Obsolete Workflow (EDMS specification lines 28-44).
        
        Requirements:
        - Check for dependent documents
        - Prevent if dependencies exist
        - Get approval before obsoleting
        """
        # Check if obsoleting is allowed
        dependency_check = DocumentDependencyManager.can_obsolete(document)
        
        if not dependency_check['can_obsolete']:
            raise ValueError(f"Cannot obsolete: {dependency_check['reason']}")
        
        # Create obsolete workflow
        workflow = DocumentWorkflow.objects.create(
            document=document,
            workflow_type='OBSOLETE',
            current_state_id=document.status,  # Keep current state initially
            initiated_by=author,
            obsoleting_reason=reason
        )
        
        return workflow
    
    @staticmethod
    def approve_obsoleting(workflow, approver, approved, obsoleting_date=None, comment=""):
        """
        Complete obsoleting approval (EDMS specification lines 37-44).
        """
        if workflow.workflow_type != 'OBSOLETE':
            raise ValueError("Not an obsoleting workflow")
        
        if approved:
            if not obsoleting_date:
                obsoleting_date = timezone.now().date()
                
            # Final dependency check per specification
            final_check = DocumentDependencyManager.validate_obsoleting_workflow(
                workflow.document
            )
            
            if not final_check['valid']:
                # Terminate workflow if dependencies found
                return WorkflowManager.terminate_workflow(
                    workflow, 
                    approver,
                    f"Obsoleting terminated: {final_check['reason']}"
                )
            
            workflow.obsoleting_date = obsoleting_date
            workflow.transition_to(
                DocumentState.PENDING_OBSOLETION,
                approver,
                comment=f"Obsoleting approved for {obsoleting_date}: {comment}"
            )
            workflow.document.status = DocumentState.PENDING_OBSOLETION
        else:
            # No change to document per specification
            workflow.transition_to(
                workflow.current_state_id,  # Stay in same state
                approver,
                comment=f"Obsoleting rejected: {comment}"
            )
        
        workflow.save()
        workflow.document.save()
        
        return workflow
    
    @staticmethod
    def terminate_workflow(workflow, user, reason):
        """
        Terminate workflow (EDMS specification lines 46-47).
        
        Author can terminate before approval, returns to last approved state.
        """
        if user != workflow.initiated_by:
            raise ValueError("Only workflow initiator can terminate workflow")
        
        if workflow.current_state_id in [DocumentState.APPROVED_AND_EFFECTIVE, DocumentState.OBSOLETE]:
            raise ValueError("Cannot terminate completed workflows")
        
        # Get last approved state
        last_approved = workflow.get_last_approved_state()
        
        workflow.is_terminated = True
        workflow.termination_reason = reason
        workflow.last_approved_state = last_approved
        
        workflow.transition_to(
            last_approved,
            user,
            comment=f"Workflow terminated: {reason}"
        )
        
        workflow.document.status = last_approved
        workflow.save()
        workflow.document.save()
        
        return workflow
    
    @staticmethod
    def activate_effective_documents():
        """
        Scheduler function: Check effective dates and activate documents.
        EDMS specification lines 18, 26, 44.
        """
        today = timezone.now().date()
        
        # Find documents pending effective date
        pending_workflows = DocumentWorkflow.objects.filter(
            current_state_id=DocumentState.APPROVED_PENDING_EFFECTIVE,
            effective_date__lte=today
        )
        
        for workflow in pending_workflows:
            if workflow.workflow_type == 'UP_VERSION':
                # For up-versioning: supersede parent document
                parent = workflow.document.parent_document
                if parent:
                    parent.status = DocumentState.SUPERSEDED
                    parent.superseded_by = workflow.document
                    parent.save()
            
            # Make document effective
            workflow.transition_to(
                DocumentState.APPROVED_AND_EFFECTIVE,
                None,  # System transition
                comment=f"Automatically activated on effective date {today}"
            )
            workflow.document.status = DocumentState.APPROVED_AND_EFFECTIVE
            workflow.document.save()
        
        # Find documents pending obsoletion
        obsoleting_workflows = DocumentWorkflow.objects.filter(
            current_state_id=DocumentState.PENDING_OBSOLETION,
            obsoleting_date__lte=today
        )
        
        for workflow in obsoleting_workflows:
            workflow.transition_to(
                DocumentState.OBSOLETE,
                None,  # System transition
                comment=f"Automatically obsoleted on date {today}"
            )
            workflow.document.status = DocumentState.OBSOLETE
            workflow.document.save()