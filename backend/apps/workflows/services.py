"""
Simple Workflow Services for EDMS.

Provides workflow management services using the Simple Approach only.
Uses DocumentWorkflow + DocumentLifecycleService for all workflow operations.
"""

from typing import Dict, List, Optional, Any
from datetime import date
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from .models import DocumentWorkflow, DocumentState, DocumentTransition
from .document_lifecycle import get_document_lifecycle_service

User = get_user_model()


class SimpleWorkflowService:
    """
    Main workflow service using the Simple Approach.
    
    Provides high-level workflow operations using DocumentLifecycleService
    for EDMS-compliant document lifecycle management.
    """
    
    def __init__(self):
        self.lifecycle_service = get_document_lifecycle_service()
    
    def start_review_workflow(self, document: Document, initiated_by: User, 
                            reviewer: User = None, approver: User = None) -> DocumentWorkflow:
        """Start a review workflow for a document."""
        return self.lifecycle_service.start_review_workflow(
            document=document,
            initiated_by=initiated_by,
            reviewer=reviewer,
            approver=approver
        )
    
    def submit_for_review(self, document: Document, user: User, 
                         comment: str = '') -> bool:
        """Submit document for review."""
        return self.lifecycle_service.submit_for_review(document, user, comment)
    
    def start_review(self, document: Document, user: User, 
                    comment: str = '') -> bool:
        """Start reviewing a document."""
        return self.lifecycle_service.start_review(document, user, comment)
    
    def complete_review(self, document: Document, user: User, 
                       approved: bool = True, comment: str = '') -> bool:
        """Complete document review."""
        return self.lifecycle_service.complete_review(document, user, approved, comment)
    
    def route_for_approval(self, document: Document, user: User, 
                          approver: User, comment: str = '') -> bool:
        """Route document for approval after review completion."""
        return self.lifecycle_service.route_for_approval(document, user, approver, comment)
    
    def approve_document(self, document: Document, user: User, 
                        effective_date: date, comment: str = '', 
                        approved: bool = True, review_period_months: int = None,
                        sensitivity_label: str = None, sensitivity_change_reason: str = '') -> bool:
        """Approve document with required effective date, sensitivity label, and optional periodic review."""
        return self.lifecycle_service.approve_document(
            document, user, effective_date, comment, approved, review_period_months,
            sensitivity_label, sensitivity_change_reason
        )
    
    # make_effective method removed - documents become effective automatically
    # via scheduler or immediately upon approval based on effective_date
    
    def start_version_workflow(self, existing_document: Document, user: User,
                              new_version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start up-versioning workflow."""
        return self.lifecycle_service.start_version_workflow(existing_document, user, new_version_data)
    
    def start_obsolete_workflow(self, document: Document, user: User,
                               reason: str, target_date = None) -> DocumentWorkflow:
        """Start obsolescence workflow."""
        return self.lifecycle_service.start_obsolete_workflow(document, user, reason, target_date)
    
    def terminate_workflow(self, document: Document, user: User,
                          reason: str) -> bool:
        """Terminate active workflow."""
        return self.lifecycle_service.terminate_workflow(document, user, reason)
    
    def get_document_workflow_status(self, document: Document) -> Dict[str, Any]:
        """Get current workflow status for a document."""
        return self.lifecycle_service.get_document_workflow_status(document)
    
    def get_workflow_history(self, document: Document) -> List[Dict[str, Any]]:
        """Get workflow history for a document."""
        workflow = DocumentWorkflow.objects.filter(document=document).first()
        if not workflow:
            return []
        
        transitions = DocumentTransition.objects.filter(
            workflow=workflow
        ).select_related('from_state', 'to_state', 'transitioned_by').order_by('transitioned_at')
        
        history = []
        for transition in transitions:
            history.append({
                'from_state': transition.from_state.name,
                'to_state': transition.to_state.name,
                'transitioned_by': transition.transitioned_by.get_full_name(),
                'transitioned_at': transition.transitioned_at,
                'comment': transition.comment
            })
        
        return history
    
    def get_pending_tasks(self, user: User) -> List[Dict[str, Any]]:
        """Get pending workflow tasks for a user."""
        # Get workflows where user is current assignee
        assigned_workflows = DocumentWorkflow.objects.filter(
            current_assignee=user,
            is_terminated=False
        ).select_related('document', 'current_state')
        
        tasks = []
        for workflow in assigned_workflows:
            document = workflow.document
            task_info = {
                'document_id': str(document.uuid),
                'document_number': document.document_number,
                'document_title': document.title,
                'workflow_type': workflow.workflow_type,
                'current_state': workflow.current_state.name,
                'due_date': workflow.due_date,
                'created_at': workflow.created_at,
                'initiated_by': workflow.initiated_by.get_full_name(),
                'available_actions': self._get_available_actions(workflow, user)
            }
            tasks.append(task_info)
        
        return tasks
    
    def _get_available_actions(self, workflow: DocumentWorkflow, user: User) -> List[str]:
        """Get available actions for a workflow and user."""
        document = workflow.document
        current_state = workflow.current_state.code
        actions = []
        
        # Check user permissions and current state
        if current_state == 'DRAFT' and document.author == user:
            actions.append('submit_for_review')
        elif current_state == 'PENDING_REVIEW' and document.reviewer == user:
            actions.append('start_review')
        elif current_state == 'UNDER_REVIEW' and document.reviewer == user:
            actions.extend(['complete_review', 'reject'])
        elif current_state == 'REVIEWED' and document.author == user:
            actions.append('route_for_approval')
        elif current_state == 'PENDING_APPROVAL' and document.approver == user:
            actions.extend(['approve_document', 'reject'])
        elif current_state == 'APPROVED' and document.approver == user:
            actions.append('make_effective')
        
        # Termination is available for authors and admins
        if current_state not in ['EFFECTIVE', 'SUPERSEDED', 'OBSOLETE', 'TERMINATED']:
            if document.author == user or user.is_superuser:
                actions.append('terminate_workflow')
        
        return actions


# Global service instance
_simple_workflow_service = None

def get_simple_workflow_service():
    """Get the global simple workflow service instance."""
    global _simple_workflow_service
    if _simple_workflow_service is None:
        _simple_workflow_service = SimpleWorkflowService()
    return _simple_workflow_service

# Alias for backward compatibility
def get_workflow_service():
    """Alias for get_simple_workflow_service for backward compatibility."""
    return get_simple_workflow_service()

def get_document_workflow_service():
    """Alias for get_simple_workflow_service for backward compatibility."""
    return get_simple_workflow_service()