"""
Simplified Notification Service
Focus: Simple email notifications for workflow tasks (future implementation)
"""
from django.core.mail import send_mail
from django.conf import settings

class SimpleNotificationService:
    """Simplified notification service focusing on email delivery"""
    
    def send_task_email(self, user, task_type, document):
        """Send simple email when task is assigned (future implementation)"""
        subject = f"New Task Assigned: {task_type} - {document.document_number}"
        message = f"""
        A new {task_type.lower()} task has been assigned to you.
        
        Document: {document.document_number} - {document.title}
        Author: {document.author.get_full_name()}
        
        Please log in to the EDMS to review this document.
        """
        
        # Send email notification
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )
            print(f"✅ Email sent to {user.username}: {subject}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {user.username}: {e}")
            return False
        return True
    
    def send_document_effective_notification(self, document):
        """Send notification when document becomes effective"""
        subject = f"Document Now Effective: {document.document_number}"
        message = f"""
        Document: {document.document_number} - {document.title}
        Status: EFFECTIVE as of {document.effective_date}
        Author: {document.author.get_full_name()}
        
        This document is now effective and available for use.
        """
        
        # Send to document author and interested parties
        recipients = [document.author.email]
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False
            )
            print(f"✅ Effective date notification sent for document {document.document_number}")
            return True
        except Exception as e:
            print(f"❌ Failed to send effective date notification: {e}")
            return False
    
    def send_document_obsolete_notification(self, document):
        """Send notification when document becomes obsolete"""
        subject = f"Document Now Obsolete: {document.document_number}"
        message = f"""
        Document: {document.document_number} - {document.title}
        Status: OBSOLETE as of {document.obsolescence_date}
        Reason: {document.obsolescence_reason or 'Scheduled obsolescence'}
        
        This document is no longer valid for use.
        """
        
        # Send to document author and interested parties
        recipients = [document.author.email]
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False
            )
            print(f"✅ Obsolescence notification sent for document {document.document_number}")
            return True
        except Exception as e:
            print(f"❌ Failed to send obsolescence notification: {e}")
            return False
    
    def send_workflow_timeout_notification(self, workflow, days_overdue):
        """Send notification for overdue workflow"""
        if workflow.current_assignee:
            subject = f"Overdue Workflow: {workflow.document.document_number}"
            message = f"""
            Document: {workflow.document.document_number} - {workflow.document.title}
            Workflow Type: {workflow.workflow_type}
            Current State: {workflow.current_state.name}
            Days Overdue: {days_overdue}
            
            Please complete this workflow task immediately.
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [workflow.current_assignee.email],
                    fail_silently=False
                )
                print(f"✅ Timeout notification sent for workflow {workflow.id} ({days_overdue} days overdue)")
                return True
            except Exception as e:
                print(f"❌ Failed to send timeout notification: {e}")
                return False
        return False

# Single instance for application use
notification_service = SimpleNotificationService()
