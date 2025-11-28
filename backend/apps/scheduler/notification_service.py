"""
Notification Service for EDMS Scheduler

Handles automated notifications for document lifecycle events,
workflow timeouts, system alerts, and scheduled reminders.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction

from celery import shared_task
from celery.utils.log import get_task_logger

from .models import NotificationQueue, ScheduledTask
from ..documents.models import Document
from ..workflows.models import DocumentWorkflow
from ..users.models import User

logger = get_task_logger(__name__)
User = get_user_model()


class NotificationService:
    """
    Centralized notification service for EDMS.
    
    Handles email notifications, in-app alerts, and notification queuing
    for various system events and scheduler activities.
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edms.local')
        self.email_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    
    def queue_notification(self, 
                          notification_type: str,
                          recipients: List[User],
                          subject: str,
                          message: str,
                          scheduled_at: Optional[datetime] = None,
                          priority: str = 'NORMAL',
                          notification_data: Optional[Dict] = None,
                          created_by: Optional[User] = None) -> NotificationQueue:
        """
        Queue a notification for future delivery.
        
        Args:
            notification_type: Type of notification (TASK_REMINDER, DOCUMENT_DUE, etc.)
            recipients: List of User objects to receive the notification
            subject: Email subject line
            message: Email message body
            scheduled_at: When to send (default: now)
            priority: Priority level (LOW, NORMAL, HIGH, URGENT)
            notification_data: Additional context data
            created_by: User who triggered the notification
            
        Returns:
            NotificationQueue object
        """
        try:
            notification = NotificationQueue.objects.create(
                notification_type=notification_type,
                priority=priority,
                subject=subject,
                message=message,
                scheduled_at=scheduled_at or timezone.now(),
                notification_data=notification_data or {},
                created_by=created_by
            )
            
            # Add recipients
            notification.recipients.set(recipients)
            
            logger.info(f"Queued {notification_type} notification for {len(recipients)} recipients")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            raise
    
    def send_immediate_notification(self,
                                   recipients: List[User],
                                   subject: str,
                                   message: str,
                                   notification_type: str = 'SYSTEM_ALERT',
                                   html_message: Optional[str] = None) -> bool:
        """
        Send notification immediately without queuing.
        
        Args:
            recipients: List of User objects
            subject: Email subject
            message: Plain text message
            notification_type: Type for logging
            html_message: Optional HTML version
            
        Returns:
            Success status
        """
        try:
            recipient_emails = [user.email for user in recipients if user.email]
            
            if not recipient_emails:
                logger.warning(f"No valid email addresses for {notification_type} notification")
                return False
            
            if html_message:
                # Send HTML email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=recipient_emails
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=recipient_emails,
                    fail_silently=False
                )
            
            logger.info(f"Sent {notification_type} notification to {len(recipient_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send immediate notification: {e}")
            return False
    
    def send_document_effective_notification(self, document: Document) -> bool:
        """Send notification when document becomes effective."""
        try:
            # Get stakeholders
            recipients = [document.author]
            if document.approver:
                recipients.append(document.approver)
            
            # Filter out duplicates and users without email
            recipients = list(set([user for user in recipients if user.email]))
            
            if not recipients:
                return False
            
            subject = f"EDMS: Document {document.document_number} is Now Effective"
            message = f"""
Document Effective Notification

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Effective Date: {document.effective_date}
Status: {document.status}

The document has automatically transitioned to effective status as scheduled.

Access the document in EDMS: {settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}

This is an automated notification from the EDMS Scheduler.
            """.strip()
            
            return self.send_immediate_notification(
                recipients=recipients,
                subject=subject,
                message=message,
                notification_type='DOCUMENT_EFFECTIVE'
            )
            
        except Exception as e:
            logger.error(f"Failed to send document effective notification: {e}")
            return False
    
    def send_document_obsolete_notification(self, document: Document) -> bool:
        """Send notification when document becomes obsolete."""
        try:
            # Get stakeholders including dependent document authors
            recipients = [document.author]
            if document.approver:
                recipients.append(document.approver)
            
            # Add authors of dependent documents
            dependent_docs = document.dependents.filter(is_active=True)
            for dep in dependent_docs:
                recipients.append(dep.document.author)
            
            # Filter out duplicates and users without email
            recipients = list(set([user for user in recipients if user.email]))
            
            if not recipients:
                return False
            
            subject = f"EDMS: Document {document.document_number} is Now Obsolete"
            message = f"""
Document Obsolescence Notification

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Obsolescence Date: {document.obsolescence_date}
Status: {document.status}

The document has automatically transitioned to obsolete status as scheduled.

Important: Please review any documents that may depend on this obsoleted document.

Access EDMS: {settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}

This is an automated notification from the EDMS Scheduler.
            """.strip()
            
            return self.send_immediate_notification(
                recipients=recipients,
                subject=subject,
                message=message,
                notification_type='DOCUMENT_OBSOLETE'
            )
            
        except Exception as e:
            logger.error(f"Failed to send document obsolete notification: {e}")
            return False
    
    def send_workflow_timeout_notification(self, workflow: DocumentWorkflow, days_overdue: int) -> bool:
        """Send notification for overdue workflow."""
        try:
            recipients = []
            
            # Add current assignee
            if workflow.current_assignee:
                recipients.append(workflow.current_assignee)
            
            # Add document author
            if workflow.document.author:
                recipients.append(workflow.document.author)
            
            # Add reviewer and approver if available
            if workflow.document.reviewer:
                recipients.append(workflow.document.reviewer)
            if workflow.document.approver:
                recipients.append(workflow.document.approver)
            
            # Filter out duplicates and users without email
            recipients = list(set([user for user in recipients if user.email]))
            
            if not recipients:
                return False
            
            urgency = "URGENT" if days_overdue > 7 else "HIGH"
            subject = f"EDMS URGENT: Workflow Overdue - {workflow.document.document_number}"
            
            message = f"""
Overdue Workflow Alert

Document: {workflow.document.title}
Document Number: {workflow.document.document_number}
Workflow Type: {workflow.workflow_type}
Current State: {workflow.current_state.name}
Days Overdue: {days_overdue}
Due Date: {workflow.due_date}

IMMEDIATE ACTION REQUIRED: This workflow is significantly overdue.

Current Assignee: {workflow.current_assignee.get_full_name() if workflow.current_assignee else 'Not assigned'}

Please log into EDMS immediately to complete this workflow:
{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}

This is an automated urgent notification from the EDMS Scheduler.
            """.strip()
            
            return self.send_immediate_notification(
                recipients=recipients,
                subject=subject,
                message=message,
                notification_type='WORKFLOW_OVERDUE'
            )
            
        except Exception as e:
            logger.error(f"Failed to send workflow timeout notification: {e}")
            return False
    
    def send_system_health_alert(self, health_status: str, failed_components: List[str]) -> bool:
        """Send system health alert to administrators."""
        try:
            # Get system administrators
            recipients = User.objects.filter(is_superuser=True, email__isnull=False).exclude(email='')
            
            if not recipients:
                logger.warning("No administrator email addresses found for health alert")
                return False
            
            severity = "CRITICAL" if health_status == "CRITICAL" else "WARNING"
            subject = f"EDMS {severity}: System Health Alert"
            
            message = f"""
System Health Alert

Overall Status: {health_status}
Timestamp: {timezone.now()}

Failed Components:
{chr(10).join(['• ' + comp for comp in failed_components]) if failed_components else '• None'}

Please investigate the system status immediately:
Admin Dashboard: http://localhost:8000/admin/scheduler/scheduledtask/dashboard/

System Details:
- This alert was generated by the EDMS automated health monitoring
- Regular health checks run every 30 minutes
- Check the admin dashboard for detailed component status

This is an automated system alert.
            """.strip()
            
            return self.send_immediate_notification(
                recipients=list(recipients),
                subject=subject,
                message=message,
                notification_type='SYSTEM_ALERT'
            )
            
        except Exception as e:
            logger.error(f"Failed to send system health alert: {e}")
            return False
    
    def send_task_failure_notification(self, task_name: str, error_message: str) -> bool:
        """Send notification when a scheduled task fails."""
        try:
            # Get system administrators
            recipients = User.objects.filter(is_superuser=True, email__isnull=False).exclude(email='')
            
            if not recipients:
                return False
            
            subject = f"EDMS: Scheduled Task Failure - {task_name}"
            message = f"""
Scheduled Task Failure Alert

Task: {task_name}
Timestamp: {timezone.now()}
Error: {error_message[:500]}{'...' if len(error_message) > 500 else ''}

The scheduled task has failed and requires attention.

Actions needed:
1. Check the admin dashboard for task details
2. Review the task configuration
3. Check system logs for more information

Admin Dashboard: http://localhost:8000/admin/scheduler/scheduledtask/

This is an automated alert from the EDMS Scheduler.
            """.strip()
            
            return self.send_immediate_notification(
                recipients=list(recipients),
                subject=subject,
                message=message,
                notification_type='TASK_FAILURE'
            )
            
        except Exception as e:
            logger.error(f"Failed to send task failure notification: {e}")
            return False


# Celery Tasks for Notification Processing
@shared_task(bind=True, max_retries=3)
def process_notification_queue(self):
    """
    Process queued notifications and send them.
    
    Runs every 5 minutes to check for pending notifications.
    """
    try:
        notification_service = NotificationService()
        
        # Get pending notifications that are due
        pending_notifications = NotificationQueue.objects.filter(
            status='PENDING',
            scheduled_at__lte=timezone.now()
        ).order_by('priority', 'scheduled_at')
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for notification in pending_notifications:
            try:
                with transaction.atomic():
                    # Get recipients
                    recipients = list(notification.recipients.all())
                    
                    # Add any additional emails
                    additional_emails = notification.recipient_emails or []
                    
                    if recipients or additional_emails:
                        # Prepare email
                        recipient_emails = [user.email for user in recipients if user.email]
                        recipient_emails.extend(additional_emails)
                        recipient_emails = list(set(recipient_emails))  # Remove duplicates
                        
                        if recipient_emails:
                            # Send email
                            send_mail(
                                subject=notification.subject,
                                message=notification.message,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=recipient_emails,
                                fail_silently=False
                            )
                            
                            # Update notification status
                            notification.status = 'SENT'
                            notification.sent_at = timezone.now()
                            notification.delivery_attempts += 1
                            success_count += 1
                        else:
                            # No valid recipients
                            notification.status = 'FAILED'
                            notification.error_message = 'No valid recipient email addresses'
                            error_count += 1
                    else:
                        # No recipients
                        notification.status = 'FAILED'
                        notification.error_message = 'No recipients specified'
                        error_count += 1
                    
                    notification.save()
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process notification {notification.id}: {e}")
                
                # Update notification with error
                notification.delivery_attempts += 1
                notification.error_message = str(e)
                
                if notification.delivery_attempts >= notification.max_attempts:
                    notification.status = 'FAILED'
                else:
                    # Will retry later
                    pass
                
                notification.save()
                error_count += 1
        
        logger.info(f"Processed {processed_count} notifications: {success_count} sent, {error_count} failed")
        
        return {
            'processed_count': processed_count,
            'success_count': success_count,
            'error_count': error_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Notification queue processing failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)  # Retry in 5 minutes
        raise


@shared_task
def send_daily_summary_notifications():
    """
    Send daily summary notifications to stakeholders.
    
    Runs daily at 8 AM to send summary of system activity.
    """
    try:
        notification_service = NotificationService()
        
        # Get system statistics
        from datetime import date
        today = date.today()
        
        # Document statistics
        docs_made_effective_today = Document.objects.filter(
            status='EFFECTIVE',
            effective_date=today
        ).count()
        
        docs_made_obsolete_today = Document.objects.filter(
            status='OBSOLETE',
            obsolescence_date=today
        ).count()
        
        # Workflow statistics
        from ..workflows.models import DocumentWorkflow
        overdue_workflows = DocumentWorkflow.objects.filter(
            is_terminated=False,
            due_date__lt=today
        ).count()
        
        # Only send if there's activity or issues
        if docs_made_effective_today > 0 or docs_made_obsolete_today > 0 or overdue_workflows > 0:
            # Get users who want daily summaries (for now, all active users)
            recipients = User.objects.filter(
                is_active=True,
                email__isnull=False
            ).exclude(email='')
            
            subject = f"EDMS Daily Summary - {today.strftime('%B %d, %Y')}"
            message = f"""
Daily EDMS System Summary

Date: {today.strftime('%B %d, %Y')}

Document Activity:
• Documents made effective today: {docs_made_effective_today}
• Documents made obsolete today: {docs_made_obsolete_today}

Workflow Status:
• Overdue workflows requiring attention: {overdue_workflows}

{'ATTENTION NEEDED: There are overdue workflows requiring immediate action.' if overdue_workflows > 0 else 'System operating normally.'}

Access EDMS: {settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}

This is an automated daily summary from EDMS.
            """.strip()
            
            return notification_service.send_immediate_notification(
                recipients=list(recipients),
                subject=subject,
                message=message,
                notification_type='DAILY_SUMMARY'
            )
        
        logger.info("No significant activity today - skipping daily summary")
        return True
        
    except Exception as e:
        logger.error(f"Daily summary notification failed: {e}")
        raise


# Service instance
notification_service = NotificationService()