"""
Author Notification Service for Document Workflows

Handles notifications to document authors when review/approval is completed
and creates appropriate tasks for next workflow steps.
"""

from typing import List, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import WorkflowTask, WorkflowNotification, DocumentWorkflow
from ..scheduler.notification_service import notification_service
from ..documents.models import Document

User = get_user_model()


class AuthorNotificationService:
    """
    Service for managing author notifications and task creation in document workflows.
    """
    
    def notify_author_review_completed(self, document: Document, reviewer: User, 
                                     approved: bool, comment: str = '') -> bool:
        """
        Notify document author when review is completed.
        Creates task for author to route to approval or address review comments.
        
        Args:
            document: Document that was reviewed
            reviewer: User who completed the review
            approved: Whether review was approved
            comment: Review comments
            
        Returns:
            bool: Success status
        """
        try:
            with transaction.atomic():
                workflow = self._get_active_workflow(document)
                if not workflow:
                    return False
                
                # Create notification
                if approved:
                    notification_type = 'REVIEW_APPROVED'
                    subject = f"Review Approved: {document.document_number} - Action Required"
                    task_name = f"Route {document.document_number} for Approval"
                    task_description = f"Review has been approved by {reviewer.get_full_name()}. Please select an approver and route the document for final approval."
                    
                    message = f"""
Document Review Approved - Action Required

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Reviewed by: {reviewer.get_full_name()}
Review Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Review Comments:
{comment or 'No specific comments provided.'}

NEXT ACTION REQUIRED:
You need to route this document for final approval. Please:
1. Log into EDMS
2. Navigate to your tasks
3. Select an approver for the document
4. Route the document for approval

Access EDMS: http://localhost:3000/my-tasks

This document cannot proceed without your action to route it for approval.
                    """.strip()
                else:
                    notification_type = 'REVIEW_REJECTED'
                    subject = f"Review Rejected: {document.document_number} - Revision Required"
                    task_name = f"Revise {document.document_number} Based on Review"
                    task_description = f"Review was rejected by {reviewer.get_full_name()}. Please address the review comments and resubmit."
                    
                    message = f"""
Document Review Rejected - Revision Required

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Reviewed by: {reviewer.get_full_name()}
Review Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Review Comments:
{comment}

REQUIRED ACTIONS:
1. Review the feedback provided above
2. Make necessary revisions to the document
3. Address all concerns raised in the review
4. Resubmit the document for review when ready

Access EDMS: http://localhost:3000/my-tasks

The document has been returned to DRAFT status for revision.
                    """.strip()
                
                # Send notification
                notification_success = notification_service.send_immediate_notification(
                    recipients=[document.author],
                    subject=subject,
                    message=message,
                    notification_type=notification_type
                )
                
                # Create workflow notification record
                WorkflowNotification.objects.create(
                    workflow_instance=workflow,
                    notification_type='COMPLETION' if approved else 'REJECTION',
                    recipient=document.author,
                    subject=subject,
                    message=message,
                    status='SENT' if notification_success else 'FAILED',
                    sent_at=timezone.now() if notification_success else None
                )
                
                # Create task for author
                task = WorkflowTask.objects.create(
                    workflow_instance=workflow,
                    name=task_name,
                    description=task_description,
                    task_type='REVIEW' if not approved else 'APPROVE',
                    priority='HIGH' if not approved else 'NORMAL',
                    assigned_to=document.author,
                    assigned_by=reviewer,
                    due_date=timezone.now() + timezone.timedelta(days=3 if approved else 7)
                )
                
                return True
                
        except Exception as e:
            print(f"Failed to notify author of review completion: {e}")
            return False
    
    def notify_author_approval_completed(self, document: Document, approver: User, 
                                       approved: bool, comment: str = '', 
                                       effective_date=None) -> bool:
        """
        Notify document author when approval is completed.
        
        Args:
            document: Document that was approved/rejected
            approver: User who completed the approval
            approved: Whether document was approved
            comment: Approval comments
            effective_date: When document becomes effective (if approved)
            
        Returns:
            bool: Success status
        """
        try:
            with transaction.atomic():
                workflow = self._get_active_workflow(document)
                if not workflow:
                    return False
                
                if approved:
                    notification_type = 'APPROVAL_COMPLETED'
                    subject = f"Document Approved: {document.document_number}"
                    
                    if effective_date and effective_date > timezone.now().date():
                        status_message = f"Document approved and will become effective on {effective_date}"
                        task_required = False
                    else:
                        status_message = "Document approved and is now effective"
                        task_required = False
                    
                    message = f"""
Document Approval Completed

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Approved by: {approver.get_full_name()}
Approval Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}
Status: {status_message}

Approval Comments:
{comment or 'No specific comments provided.'}

Your document has been successfully approved and is now part of the controlled document system.

{'The document will automatically become effective on the scheduled date.' if effective_date and effective_date > timezone.now().date() else 'The document is immediately available for use.'}

Access EDMS: http://localhost:3000/document-management

Congratulations on the successful completion of your document workflow!
                    """.strip()
                else:
                    notification_type = 'APPROVAL_REJECTED'
                    subject = f"Document Approval Rejected: {document.document_number}"
                    task_required = True
                    
                    message = f"""
Document Approval Rejected - Revision Required

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Rejected by: {approver.get_full_name()}
Rejection Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Rejection Comments:
{comment}

REQUIRED ACTIONS:
1. Review the feedback provided by the approver
2. Make necessary revisions to address the concerns
3. Consider if a new review cycle is needed
4. Resubmit when ready

Access EDMS: http://localhost:3000/my-tasks

The document has been returned to DRAFT status for revision.
                    """.strip()
                
                # Send notification
                notification_success = notification_service.send_immediate_notification(
                    recipients=[document.author],
                    subject=subject,
                    message=message,
                    notification_type=notification_type
                )
                
                # Create workflow notification record
                WorkflowNotification.objects.create(
                    workflow_instance=workflow,
                    notification_type='COMPLETION' if approved else 'REJECTION',
                    recipient=document.author,
                    subject=subject,
                    message=message,
                    status='SENT' if notification_success else 'FAILED',
                    sent_at=timezone.now() if notification_success else None
                )
                
                # Create task for author if rejection
                if task_required:
                    WorkflowTask.objects.create(
                        workflow_instance=workflow,
                        name=f"Revise {document.document_number} Based on Approval Feedback",
                        description=f"Document was rejected by {approver.get_full_name()}. Address the feedback and resubmit.",
                        task_type='REVIEW',
                        priority='HIGH',
                        assigned_to=document.author,
                        assigned_by=approver,
                        due_date=timezone.now() + timezone.timedelta(days=10)
                    )
                
                return True
                
        except Exception as e:
            print(f"Failed to notify author of approval completion: {e}")
            return False
    
    def create_author_routing_task(self, document: Document, workflow: DocumentWorkflow) -> WorkflowTask:
        """
        Create a task for the author to route document after review approval.
        
        Args:
            document: Document needing routing
            workflow: Associated workflow
            
        Returns:
            Created WorkflowTask
        """
        return WorkflowTask.objects.create(
            workflow_instance=workflow,
            name=f"Route {document.document_number} for Approval",
            description=f"Select an approver and route the document for final approval. Document has been successfully reviewed and is ready for the approval stage.",
            task_type='APPROVE',
            priority='NORMAL',
            assigned_to=document.author,
            assigned_by=document.author,  # System task
            due_date=timezone.now() + timezone.timedelta(days=3),
            task_data={
                'action_required': 'route_for_approval',
                'document_status': document.status,
                'next_step': 'Select approver and route document'
            }
        )
    
    def get_author_pending_tasks(self, author: User) -> List[dict]:
        """
        Get all pending tasks for a document author.
        
        Args:
            author: User to get tasks for
            
        Returns:
            List of task dictionaries
        """
        try:
            # Get active workflow tasks
            active_tasks = WorkflowTask.objects.filter(
                assigned_to=author,
                status__in=['PENDING', 'IN_PROGRESS']
            ).select_related(
                'workflow_instance__content_object',
                'assigned_by'
            ).order_by('-priority', 'due_date')
            
            tasks = []
            for task in active_tasks:
                # Get the document from the workflow
                document = None
                if hasattr(task.workflow_instance, 'content_object'):
                    document = task.workflow_instance.content_object
                
                task_data = {
                    'id': task.uuid,
                    'name': task.name,
                    'description': task.description,
                    'task_type': task.task_type,
                    'priority': task.priority,
                    'status': task.status,
                    'created_at': task.created_at,
                    'due_date': task.due_date,
                    'is_overdue': task.is_overdue,
                    'assigned_by': task.assigned_by.get_full_name() if task.assigned_by else 'System',
                    'workflow_type': task.workflow_instance.workflow_type if hasattr(task.workflow_instance, 'workflow_type') else 'Unknown'
                }
                
                if document:
                    task_data.update({
                        'document_id': document.id,
                        'document_uuid': document.uuid,
                        'document_number': document.document_number,
                        'document_title': document.title,
                        'document_status': document.status,
                        'document_version': getattr(document, 'version_string', 'N/A')
                    })
                
                tasks.append(task_data)
            
            return tasks
            
        except Exception as e:
            print(f"Failed to get author pending tasks: {e}")
            return []
    
    def mark_task_completed(self, task_id: str, user: User, completion_note: str = '') -> bool:
        """
        Mark a workflow task as completed.
        
        Args:
            task_id: UUID of the task
            user: User completing the task
            completion_note: Optional completion note
            
        Returns:
            bool: Success status
        """
        try:
            task = WorkflowTask.objects.get(uuid=task_id, assigned_to=user)
            task.complete_task(completion_note=completion_note)
            return True
        except WorkflowTask.DoesNotExist:
            return False
        except Exception as e:
            print(f"Failed to complete task: {e}")
            return False
    
    def _get_active_workflow(self, document: Document) -> Optional[DocumentWorkflow]:
        """Get active workflow for a document."""
        try:
            from .models_simple import DocumentWorkflow
            return DocumentWorkflow.objects.filter(
                document=document
            ).order_by('-created_at').first()
        except:
            return None


# Service instance
author_notification_service = AuthorNotificationService()