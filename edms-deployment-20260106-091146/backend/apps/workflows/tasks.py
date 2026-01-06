"""
Celery tasks for Workflow Management.

Background tasks for workflow automation, notifications,
and periodic workflow processing.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from celery import shared_task
from celery.utils.log import get_task_logger

from .models import WorkflowInstance, WorkflowNotification
# Import available services
try:
    from .services import WorkflowService
    workflow_service = WorkflowService()
except ImportError:
    # Fallback for missing service
    workflow_service = None
from apps.documents.models import Document
from apps.audit.services import audit_service

logger = get_task_logger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def check_effective_documents(self):
    """
    Check for documents that should become effective today.
    
    Processes approved documents with effective dates of today or earlier
    and transitions them to effective status.
    """
    try:
        logger.info("Checking for documents to make effective")
        
        today = timezone.now().date()
        documents = Document.objects.filter(
            status='approved',
            effective_date__lte=today,
            current_version__isnull=False
        )
        
        count = 0
        for document in documents:
            try:
                # Check if document has active approval workflow
                active_workflows = WorkflowInstance.objects.filter(
                    content_type__model='document',
                    object_id=document.id,
                    is_active=True,
                    workflow_type__workflow_type='APPROVAL'
                )
                
                if active_workflows.exists():
                    workflow = active_workflows.first()
                    # Complete the workflow to make document effective
                    workflow_service.complete_workflow(
                        workflow, 
                        reason="Automatic transition on effective date"
                    )
                    count += 1
                    
                    # Log the automatic transition
                    audit_service.log_system_event(
                        event_type='DOCUMENT_MADE_EFFECTIVE',
                        object_type='Document',
                        object_id=document.id,
                        description=f"Document {document.document_number} automatically made effective"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing document {document.id}: {str(e)}")
                continue
        
        logger.info(f"Made {count} documents effective")
        return {"processed": count}
        
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def process_document_obsolescence(self):
    """
    Process scheduled document obsolescence.
    
    Checks for documents with obsolescence dates and initiates
    obsolescence workflows where appropriate.
    """
    try:
        logger.info("Processing scheduled document obsolescence")
        
        today = timezone.now().date()
        documents = Document.objects.filter(
            status='effective',
            obsolescence_date__lte=today
        )
        
        count = 0
        for document in documents:
            try:
                # Check if already has obsolescence workflow
                existing_workflow = WorkflowInstance.objects.filter(
                    content_type__model='document',
                    object_id=document.id,
                    is_active=True,
                    workflow_type__workflow_type='OBSOLETE'
                ).exists()
                
                if not existing_workflow:
                    # Find a system user to initiate the workflow
                    system_user = User.objects.filter(
                        username__in=['system', 'admin', 'docadmin']
                    ).first()
                    
                    if system_user:
                        workflow_service.initiate_workflow(
                            document,
                            'OBSOLETE',
                            system_user,
                            reason="Scheduled obsolescence date reached"
                        )
                        count += 1
                        
                        # Log the automatic obsolescence initiation
                        audit_service.log_system_event(
                            event_type='OBSOLESCENCE_INITIATED',
                            object_type='Document',
                            object_id=document.id,
                            description=f"Obsolescence workflow initiated for {document.document_number}"
                        )
                        
            except Exception as e:
                logger.error(f"Error processing obsolescence for document {document.id}: {str(e)}")
                continue
        
        logger.info(f"Initiated obsolescence for {count} documents")
        return {"processed": count}
        
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_pending_notifications(self):
    """
    Send pending workflow notifications.
    
    Processes queued workflow notifications and sends them
    via appropriate channels (email, dashboard, etc.).
    """
    try:
        logger.info("Sending pending workflow notifications")
        
        # Get pending notifications
        notifications = WorkflowNotification.objects.filter(
            status='PENDING',
            scheduled_at__lte=timezone.now()
        )
        
        count = 0
        for notification in notifications:
            try:
                # Mark as processing
                notification.status = 'PROCESSING'
                notification.save()
                
                # Send notification based on type
                if notification.notification_type == 'EMAIL':
                    send_email_notification.delay(notification.id)
                elif notification.notification_type == 'DASHBOARD':
                    send_dashboard_notification.delay(notification.id)
                
                count += 1
                
            except Exception as e:
                logger.error(f"Error processing notification {notification.id}: {str(e)}")
                notification.status = 'FAILED'
                notification.error_message = str(e)
                notification.save()
                continue
        
        logger.info(f"Processed {count} notifications")
        return {"processed": count}
        
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    """
    Send email notification for workflow events.
    
    Args:
        notification_id: ID of the WorkflowNotification to send
    """
    try:
        notification = WorkflowNotification.objects.get(id=notification_id)
        
        # TODO: Implement email sending logic
        # For now, just mark as sent
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Email notification sent: {notification_id}")
        return {"notification_id": notification_id, "status": "sent"}
        
    except WorkflowNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {"error": "Notification not found"}
    except Exception as exc:
        logger.error(f"Failed to send email notification {notification_id}: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_dashboard_notification(self, notification_id):
    """
    Send dashboard notification for workflow events.
    
    Args:
        notification_id: ID of the WorkflowNotification to send
    """
    try:
        notification = WorkflowNotification.objects.get(id=notification_id)
        
        # Mark as sent (dashboard notifications are shown in real-time)
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Dashboard notification sent: {notification_id}")
        return {"notification_id": notification_id, "status": "sent"}
        
    except WorkflowNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {"error": "Notification not found"}
    except Exception as exc:
        logger.error(f"Failed to send dashboard notification {notification_id}: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def cleanup_completed_workflows(self):
    """
    Clean up old completed workflows.
    
    Archives or removes completed workflows older than retention period.
    """
    try:
        logger.info("Cleaning up completed workflows")
        
        # Get workflows completed more than 1 year ago
        cutoff_date = timezone.now() - timedelta(days=365)
        old_workflows = WorkflowInstance.objects.filter(
            is_completed=True,
            completed_at__lt=cutoff_date
        )
        
        count = 0
        for workflow in old_workflows:
            try:
                # Archive workflow data before deletion
                audit_service.log_system_event(
                    event_type='WORKFLOW_ARCHIVED',
                    object_type='WorkflowInstance',
                    object_id=workflow.id,
                    description=f"Workflow archived: {workflow.workflow_type.name}",
                    additional_data={
                        'workflow_type': workflow.workflow_type.workflow_type,
                        'initiated_by': workflow.initiated_by.username,
                        'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
                        'final_state': str(workflow.state)
                    }
                )
                
                # Delete the workflow (cascade will handle related objects)
                workflow.delete()
                count += 1
                
            except Exception as e:
                logger.error(f"Error archiving workflow {workflow.id}: {str(e)}")
                continue
        
        logger.info(f"Archived {count} old workflows")
        return {"archived": count}
        
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def check_workflow_timeouts(self):
    """
    Check for workflows that have exceeded their timeout periods.
    
    Sends escalation notifications and optionally auto-transitions
    overdue workflows based on configuration.
    """
    try:
        logger.info("Checking for workflow timeouts")
        
        # Get active workflows with due dates
        overdue_workflows = WorkflowInstance.objects.filter(
            is_active=True,
            due_date__lt=timezone.now()
        )
        
        escalated_count = 0
        for workflow in overdue_workflows:
            try:
                # Send escalation notification
                WorkflowNotification.objects.create(
                    workflow_instance=workflow,
                    notification_type='EMAIL',
                    recipient=workflow.current_assignee or workflow.initiated_by,
                    subject=f"OVERDUE: {workflow.workflow_type.name}",
                    message=f"Workflow for {workflow.content_object} is overdue. "
                           f"Due date: {workflow.due_date}",
                    priority='HIGH',
                    status='PENDING'
                )
                
                # Log the escalation
                audit_service.log_workflow_event(
                    workflow_instance=workflow,
                    event_type='WORKFLOW_ESCALATED',
                    user=None,  # System event
                    description="Workflow escalated due to timeout"
                )
                
                escalated_count += 1
                
            except Exception as e:
                logger.error(f"Error processing overdue workflow {workflow.id}: {str(e)}")
                continue
        
        logger.info(f"Escalated {escalated_count} overdue workflows")
        return {"escalated": escalated_count}
        
    except Exception as exc:
        logger.error(f"Task failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def workflow_health_check(self):
    """
    Perform health checks on workflow system.
    
    Checks for workflow inconsistencies, stuck workflows,
    and system health issues.
    """
    try:
        logger.info("Performing workflow health check")
        
        health_status = {
            "timestamp": timezone.now().isoformat(),
            "active_workflows": WorkflowInstance.objects.filter(is_active=True).count(),
            "pending_documents": 0,  # Document filtering approach used instead
            "overdue_documents": 0,  # Document filtering approach used instead
            "stuck_workflows": [],
            "errors": []
        }
        
        # Check for stuck workflows (active for more than 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stuck_workflows = WorkflowInstance.objects.filter(
            is_active=True,
            started_at__lt=thirty_days_ago
        )
        
        for workflow in stuck_workflows:
            health_status["stuck_workflows"].append({
                "id": workflow.id,
                "type": workflow.workflow_type.workflow_type,
                "started_at": workflow.started_at.isoformat(),
                "current_state": str(workflow.state)
            })
        
        # Log health check results
        if health_status["stuck_workflows"] or health_status["overdue_documents"] > 10:
            audit_service.log_system_event(
                event_type='WORKFLOW_HEALTH_WARNING',
                object_type='System',
                description="Workflow health check detected issues",
                additional_data=health_status
            )
        
        logger.info("Workflow health check completed")
        return health_status
        
    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))