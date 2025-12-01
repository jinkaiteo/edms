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

# Single instance for application use
notification_service = SimpleNotificationService()
