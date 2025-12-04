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
        
        # Future: Uncomment when email is configured
        # send_mail(
        #     subject,
        #     message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [user.email],
        #     fail_silently=True
        # )
        
        print(f"📧 Email notification prepared for {user.username}: {subject}")
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
        
        print(f"📧 Effective date notification prepared for document {document.document_number}")
        return True
    
    def send_document_obsolete_notification(self, document):
        """Send notification when document becomes obsolete"""
        subject = f"Document Now Obsolete: {document.document_number}"
        message = f"""
        Document: {document.document_number} - {document.title}
        Status: OBSOLETE as of {document.obsolescence_date}
        Reason: {document.obsolescence_reason or 'Scheduled obsolescence'}
        
        This document is no longer valid for use.
        """
        
        print(f"📧 Obsolescence notification prepared for document {document.document_number}")
        return True
    
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
            
            print(f"📧 Timeout notification prepared for workflow {workflow.id} ({days_overdue} days overdue)")
        return True

# Single instance for application use
notification_service = SimpleNotificationService()
