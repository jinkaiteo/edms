"""
Document Automation Service

Handles automated document lifecycle management including:
- Effective date processing
- Obsolescence date processing
- Workflow timeout monitoring
- Workflow task cleanup
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from ..models import ScheduledTask
from ...documents.models import Document
from ...workflows.models import DocumentWorkflow, DocumentState, DocumentTransition
from ...audit.models import AuditTrail
from ...users.models import User

logger = logging.getLogger(__name__)
User = get_user_model()


class SchedulerError(Exception):
    """Custom exception for scheduler-related errors."""
    pass


class DocumentAutomationService:
    """
    Document lifecycle automation service.
    
    Handles automated document state transitions, effective date processing,
    and workflow timeout management.
    """
    
    def __init__(self):
        self._system_user = None
    
    @property
    def system_user(self):
        """Lazy initialization of system user to avoid database connection at import."""
        if self._system_user is None:
            self._system_user = self._get_system_user()
        return self._system_user
    
    def process_effective_dates(self) -> Dict[str, Any]:
        """
        Process documents with effective dates that have passed.
        
        Returns:
            Results summary with processed documents
        """
        try:
            # Import notification service here to avoid circular imports
            from ..notification_service import notification_service
            
            results = {
                'processed_count': 0,
                'success_count': 0,
                'error_count': 0,
                'processed_documents': [],
                'errors': [],
                'timestamp': timezone.now().isoformat()
            }
            
            # Find documents pending effective date
            pending_effective = Document.objects.filter(
                status='APPROVED_PENDING_EFFECTIVE',
                effective_date__lte=timezone.now().date(),
                is_active=True
            )

            results['processed_count'] = pending_effective.count()
            
            for document in pending_effective:
                try:
                    with transaction.atomic():
                        # Update document status
                        old_status = document.status
                        document.status = 'EFFECTIVE'
                        document.save()
                        
                        # Update workflow if exists
                        try:
                            workflow = DocumentWorkflow.objects.get(document=document)
                            effective_state = DocumentState.objects.get(code='EFFECTIVE')
                            
                            # Create transition record
                            DocumentTransition.objects.create(
                                workflow=workflow,
                                from_state=workflow.current_state,
                                to_state=effective_state,
                                transitioned_by=self.system_user,
                                comment=f"Automated effective date processing on {timezone.now().date()}",
                                transition_data={
                                    'automated': True,
                                    'effective_date': document.effective_date.isoformat() if document.effective_date else None
                                }
                            )

                            workflow.current_state = effective_state
                            workflow.save()
                            
                        except DocumentWorkflow.DoesNotExist:
                            logger.warning(f"No workflow found for document {document.id}")
                        
                        # Create audit trail
                        AuditTrail.objects.create(
                            user=self.system_user,
                            action='DOC_EFFECTIVE_PROCESSED',
                            content_object=document,
                            field_changes={
                                'old_status': old_status,
                                'new_status': document.status,
                                'effective_date': document.effective_date.isoformat() if document.effective_date else None,
                                'automation_timestamp': timezone.now().isoformat()
                            },
                            ip_address='127.0.0.1',
                            user_agent='EDMS Scheduler Service'
                        )

                        results['processed_documents'].append({
                            'document_id': document.id,
                            'document_number': document.document_number,
                            'title': document.title,
                            'effective_date': document.effective_date.isoformat() if document.effective_date else None
                        })
                        
                        # Send notification
                        try:
                            notification_service.send_document_effective_notification(document)
                            logger.info(f"Sent effective date notification for document {document.document_number}")
                        except Exception as e:
                            logger.warning(f"Failed to send notification for document {document.document_number}: {e}")
                        
                        results['success_count'] += 1
                        logger.info(f"Processed effective date for document {document.document_number}")
                        
                except Exception as e:
                    results['error_count'] += 1
                    error_msg = f"Failed to process document {document.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Effective date processing failed: {str(e)}")
            raise SchedulerError(f"Effective date processing failed: {str(e)}")
    
    def process_obsoletion_dates(self) -> Dict[str, Any]:
        """Process documents with obsoletion dates that have passed."""
        try:
            from ..notification_service import notification_service
            
            results = {
                'processed_count': 0,
                'success_count': 0,
                'error_count': 0,
                'processed_documents': [],
                'errors': [],
                'timestamp': timezone.now().isoformat()
            }
            
            # Find documents pending obsoletion
            pending_obsolete = Document.objects.filter(
                status='SCHEDULED_FOR_OBSOLESCENCE',
                obsolescence_date__lte=timezone.now().date(),
                is_active=True
            )

            results['processed_count'] = pending_obsolete.count()
            
            for document in pending_obsolete:
                try:
                    with transaction.atomic():
                        # Update document status
                        old_status = document.status
                        document.status = 'OBSOLETE'
                        document.save()
                        
                        # Update workflow if exists
                        try:
                            workflow = DocumentWorkflow.objects.get(document=document)
                            obsolete_state = DocumentState.objects.get(code='OBSOLETE')
                            
                            # Create transition record
                            DocumentTransition.objects.create(
                                workflow=workflow,
                                from_state=workflow.current_state,
                                to_state=obsolete_state,
                                transitioned_by=self.system_user,
                                comment=f"Automated obsoletion processing on {timezone.now().date()}",
                                transition_data={
                                    'automated': True,
                                    'obsoletion_date': document.obsolescence_date.isoformat() if document.obsolescence_date else None
                                }
                            )

                            workflow.current_state = obsolete_state
                            workflow.is_terminated = True
                            workflow.save()
                            
                        except DocumentWorkflow.DoesNotExist:
                            logger.warning(f"No workflow found for document {document.id}")
                        
                        # Create audit trail
                        AuditTrail.objects.create(
                            user=self.system_user,
                            action='DOC_OBSOLETED',
                            content_object=document,
                            field_changes={
                                'old_status': old_status,
                                'new_status': document.status,
                                'obsoletion_date': document.obsolescence_date.isoformat() if document.obsolescence_date else None,
                                'automation_timestamp': timezone.now().isoformat()
                            }
                        )

                        results['processed_documents'].append({
                            'document_id': document.id,
                            'document_number': document.document_number,
                            'title': document.title,
                            'obsoletion_date': document.obsolescence_date.isoformat() if document.obsolescence_date else None
                        })
                        
                        # Send notification
                        try:
                            notification_service.send_document_obsolete_notification(document)
                            logger.info(f"Sent obsolescence notification for document {document.document_number}")
                        except Exception as e:
                            logger.warning(f"Failed to send notification for document {document.document_number}: {e}")
                        
                        results['success_count'] += 1
                        logger.info(f"Processed obsoletion for document {document.document_number}")
                        
                except Exception as e:
                    results['error_count'] += 1
                    error_msg = f"Failed to obsolete document {document.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Obsoletion processing failed: {str(e)}")
            raise SchedulerError(f"Obsoletion processing failed: {str(e)}")
    
    def check_workflow_timeouts(self) -> Dict[str, Any]:
        """Check for workflow timeouts and send notifications."""
        try:
            from ..notification_service import notification_service
            
            results = {
                'checked_count': 0,
                'timeout_count': 0,
                'notification_count': 0,
                'overdue_workflows': [],
                'timestamp': timezone.now().isoformat()
            }
            
            # Find active workflows
            active_workflows = DocumentWorkflow.objects.filter(
                is_terminated=False,
                current_state__is_final=False
            )

            results['checked_count'] = active_workflows.count()
            
            for workflow in active_workflows:
                try:
                    # Check if workflow is overdue
                    if workflow.due_date:
                        # Convert due_date to date if it's datetime
                        due_date = workflow.due_date.date() if hasattr(workflow.due_date, 'date') else workflow.due_date
                        today = timezone.now().date()
                        
                        if due_date < today:
                            days_overdue = (today - due_date).days
                            
                            results['timeout_count'] += 1
                            results['overdue_workflows'].append({
                                'workflow_id': workflow.id,
                                'document_number': workflow.document.document_number,
                                'document_title': workflow.document.title,
                                'workflow_type': workflow.workflow_type,
                                'current_state': workflow.current_state.name,
                                'due_date': due_date.isoformat(),
                                'days_overdue': days_overdue,
                                'current_assignee': workflow.current_assignee.get_full_name() if workflow.current_assignee else None
                            })
                            
                            # Send notification for severely overdue workflows
                            if days_overdue > 7:  # More than a week overdue
                                try:
                                    notification_service.send_workflow_timeout_notification(workflow, days_overdue)
                                    results['notification_count'] += 1
                                    logger.info(f"Sent timeout notification for workflow {workflow.id}")
                                except Exception as e:
                                    logger.warning(f"Failed to send timeout notification for workflow {workflow.id}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error checking workflow timeout for {workflow.id}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow timeout check failed: {str(e)}")
            raise SchedulerError(f"Workflow timeout check failed: {str(e)}")
    
    def cleanup_workflow_tasks(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up orphaned, irrelevant, or completed workflow tasks.
        
        Note: This is now a no-op since WorkflowTask model was removed
        in favor of document-filtering approach.
        """
        logger.info("🧹 Starting workflow task cleanup (legacy no-op)...")
        
        results = {
            'status': 'completed',
            'message': 'WorkflowTask model removed - no cleanup needed',
            'dry_run': dry_run,
            'results': {
                'terminated_document_tasks': 0,
                'obsolete_document_tasks': 0,
                'orphaned_tasks': 0,
                'duplicate_tasks': 0,
                'expired_tasks': 0,
                'nonexistent_document_tasks': 0,
                'details': []
            },
            'execution_time': '0.0s',
            'next_run': (timezone.now() + timedelta(hours=6)).isoformat()
        }
        
        logger.info("✅ Workflow task cleanup completed (no-op)")
        return results
    
    def _get_system_user(self) -> User:
        """Get or create system user for automated actions."""
        try:
            system_user, created = User.objects.get_or_create(
                username='system_scheduler',
                defaults={
                    'email': 'system@edms.local',
                    'first_name': 'System',
                    'last_name': 'Scheduler',
                    'is_active': True,
                    'is_staff': False
                }
            )

            return system_user
        except Exception as e:
            logger.error(f"Failed to get system user: {str(e)}")
            # Fallback to first superuser
            return User.objects.filter(is_superuser=True).first()


# Singleton instance
document_automation_service = DocumentAutomationService()
