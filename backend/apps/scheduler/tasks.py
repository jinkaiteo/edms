"""
Scheduler Tasks - Thin @shared_task Wrappers

This module contains all Celery task definitions for the scheduler.
Tasks are automatically discovered by Celery's autodiscover_tasks().

All business logic is delegated to service classes in services/
"""

from celery import shared_task
from celery.utils.log import get_task_logger

from .services.automation import document_automation_service
from .services.health import system_health_service
from .services.cleanup import celery_cleanup_service

logger = get_task_logger(__name__)


# ============================================================================
# Document Lifecycle Tasks
# ============================================================================

@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
    """
    Process documents with effective dates that have passed.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every hour via Celery Beat.
    """
    try:
        results = document_automation_service.process_effective_dates()
        logger.info(f"Processed {results['success_count']} effective dates successfully")
        return results
    except Exception as e:
        logger.error(f"Effective date processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@shared_task(bind=True, max_retries=3)
def process_document_obsoletion_dates(self):
    """
    Process documents with obsoletion dates that have passed.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every hour via Celery Beat.
    """
    try:
        results = document_automation_service.process_obsoletion_dates()
        logger.info(f"Processed {results['success_count']} obsoletion dates successfully")
        return results
    except Exception as e:
        logger.error(f"Obsoletion processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


# ============================================================================
# Workflow Monitoring Tasks
# ============================================================================

@shared_task
def check_workflow_timeouts():
    """
    Check for workflow timeouts and send escalation notifications.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every 4 hours via Celery Beat.
    """
    try:
        results = document_automation_service.check_workflow_timeouts()
        logger.info(f"Checked {results['checked_count']} workflows, found {results['timeout_count']} timeouts")
        return results
    except Exception as e:
        logger.error(f"Workflow timeout check failed: {str(e)}")
        raise


@shared_task
def cleanup_workflow_tasks(dry_run: bool = False):
    """
    Clean up orphaned and irrelevant workflow tasks.
    
    Note: This is now a no-op since WorkflowTask model was removed.
    Kept for backward compatibility with scheduled jobs.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every 6 hours via Celery Beat.
    """
    try:
        results = document_automation_service.cleanup_workflow_tasks(dry_run=dry_run)
        logger.info("Workflow task cleanup completed (no-op)")
        return results
    except Exception as e:
        logger.error(f"Workflow task cleanup failed: {str(e)}")
        raise


# ============================================================================
# System Maintenance Tasks
# ============================================================================

@shared_task
def perform_system_health_check():
    """
    Perform comprehensive system health check.
    
    Celery task wrapper that delegates to SystemHealthService.
    Runs every 30 minutes via Celery Beat.
    """
    try:
        results = system_health_service.perform_health_check()
        logger.info(f"System health check completed: {results['overall_status']}")
        return results
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise


@shared_task(name='apps.scheduler.celery_cleanup.cleanup_celery_results')
def cleanup_celery_results(days_to_keep: int = 7, remove_revoked: bool = True):
    """
    Clean up old Celery task execution records.
    
    Celery task wrapper that delegates to CeleryResultsCleanupService.
    Runs daily at 03:00 via Celery Beat.
    
    Args:
        days_to_keep: Number of days of history to keep (default: 7)
        remove_revoked: Whether to remove all REVOKED tasks (default: True)
    """
    try:
        results = celery_cleanup_service.cleanup(days_to_keep, remove_revoked)
        
        if results['success']:
            logger.info(
                f"Celery results cleanup completed: "
                f"Deleted {results['total_deleted']} records "
                f"({results['total_before']} → {results['total_after']})"
            )
        else:
            logger.error(f"Celery results cleanup failed: {results.get('error')}")
        
        return results
    except Exception as e:
        logger.error(f"Celery results cleanup task failed: {str(e)}")
        raise


# ============================================================================
# Periodic Review Tasks
# ============================================================================

@shared_task
def process_periodic_reviews():
    """
    Check for documents that need periodic review.
    
    Celery task wrapper that delegates to PeriodicReviewService.
    Runs daily via Celery Beat.
    """
    try:
        from .services.periodic_review_service import get_periodic_review_service
        periodic_review_service = get_periodic_review_service()
        
        results = periodic_review_service.process_periodic_reviews()
        logger.info(
            f"Periodic review check completed: "
            f"{results['workflows_created']} workflows created, "
            f"{results['notifications_created']} notifications sent"
        )
        return results
    except Exception as e:
        logger.error(f"Periodic review processing failed: {str(e)}")
        raise


# ============================================================================
# Email Notification Tasks
# ============================================================================

@shared_task
def send_test_email_to_self():
    """
    Send a test email to the requesting user to verify email configuration.
    
    This is a manual-trigger-only task available in the scheduler UI.
    It allows users to test email functionality without waiting for
    actual system events.
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get all admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        if not admin_users.exists():
            logger.warning("No admin users found to send test email")
            return {
                'success': False,
                'error': 'No admin users found',
                'sent_count': 0
            }
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        for user in admin_users:
            if not user.email:
                logger.warning(f"User {user.username} has no email address")
                failed_count += 1
                continue
            
            try:
                send_mail(
                    subject='EDMS Email Test - Configuration Verification',
                    message=f'''Hello {user.get_full_name() or user.username},

This is a test email from your EDMS (Enterprise Document Management System).

If you received this email, it means:
✅ Email configuration is working correctly
✅ SMTP connection is successful
✅ Email notifications are operational

System Information:
- Email Backend: {settings.EMAIL_BACKEND}
- SMTP Host: {settings.EMAIL_HOST}
- SMTP Port: {settings.EMAIL_PORT}
- From Address: {settings.DEFAULT_FROM_EMAIL}

You can safely delete this email.

---
EDMS Automated Email Test
Sent via Scheduler Task''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sent_count += 1
                logger.info(f"Test email sent successfully to {user.email}")
                
            except Exception as e:
                failed_count += 1
                error_msg = f"{user.email}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to send test email to {user.email}: {e}")
        
        result = {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_admins': admin_users.count(),
        }
        
        if errors:
            result['errors'] = errors
        
        logger.info(f"Test email task completed: {sent_count} sent, {failed_count} failed")
        return result
        
    except Exception as e:
        logger.error(f"Test email task failed: {str(e)}")
        raise


@shared_task
def send_daily_health_report():
    """
    Send daily system health report to all admin users.
    
    Scheduled to run daily at 7:00 AM via Celery Beat.
    Provides administrators with a summary of system status,
    pending tasks, and any issues requiring attention.
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from apps.documents.models import Document
        from apps.workflows.models import WorkflowInstance
        
        User = get_user_model()
        
        # Get all admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True, email__isnull=False).exclude(email='')
        
        if not admin_users.exists():
            logger.warning("No admin users with email addresses found")
            return {
                'success': False,
                'error': 'No admin users with email addresses',
                'sent_count': 0
            }
        
        # Perform health check
        health_results = system_health_service.perform_health_check()
        
        # Gather statistics
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Document statistics
        total_documents = Document.objects.count()
        draft_documents = Document.objects.filter(status='DRAFT').count()
        in_review_documents = Document.objects.filter(status='IN_REVIEW').count()
        effective_documents = Document.objects.filter(status='EFFECTIVE').count()
        
        # New documents today
        new_documents_today = Document.objects.filter(created_at__gte=today_start).count()
        
        # Workflow statistics
        active_workflows = WorkflowInstance.objects.filter(is_completed=False, is_active=True).count()
        
        # Overdue workflows (simplified check - workflows older than 7 days)
        seven_days_ago = now - timezone.timedelta(days=7)
        overdue_workflows = WorkflowInstance.objects.filter(
            is_completed=False,
            is_active=True,
            started_at__lt=seven_days_ago
        ).count()
        
        # Build email content
        overall_status = health_results.get('overall_status', 'UNKNOWN')
        status_emoji = '✅' if overall_status == 'HEALTHY' else '⚠️' if overall_status == 'WARNING' else '❌'
        
        email_subject = f"EDMS Daily Health Report - {now.strftime('%Y-%m-%d')} - {status_emoji} {overall_status}"
        
        email_body = f'''EDMS Daily Health Report
Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
SYSTEM STATUS: {status_emoji} {overall_status}
{'='*70}

DOCUMENT STATISTICS
-------------------
Total Documents:        {total_documents}
├─ Draft:              {draft_documents}
├─ In Review:          {in_review_documents}
└─ Effective:          {effective_documents}

New Documents Today:    {new_documents_today}

WORKFLOW STATISTICS
-------------------
Active Workflows:       {active_workflows}
Overdue Workflows:      {overdue_workflows} {'⚠️' if overdue_workflows > 0 else '✅'}

SYSTEM HEALTH DETAILS
---------------------
'''
        
        # Add component health status
        if 'components' in health_results:
            for component_name, component_data in health_results['components'].items():
                status = component_data.get('status', 'UNKNOWN')
                status_symbol = '✅' if status == 'HEALTHY' else '⚠️' if status == 'WARNING' else '❌'
                email_body += f"{status_symbol} {component_name.replace('_', ' ').title()}: {status}\n"
                
                if status != 'HEALTHY' and 'details' in component_data:
                    email_body += f"   Details: {component_data['details']}\n"
        
        email_body += f'''
{'='*70}

ACTIONS REQUIRED
----------------
'''
        
        # Add action items
        action_items = []
        
        if overdue_workflows > 0:
            action_items.append(f"• Review {overdue_workflows} overdue workflow(s)")
        
        if in_review_documents > 10:
            action_items.append(f"• {in_review_documents} documents awaiting review")
        
        if overall_status != 'HEALTHY':
            action_items.append("• Investigate system health issues (see details above)")
        
        if action_items:
            email_body += '\n'.join(action_items)
        else:
            email_body += "✅ No immediate actions required"
        
        email_body += '''

---
This is an automated daily health report from EDMS.
To stop receiving these reports, contact your system administrator.
'''
        
        # Send email to all admins
        sent_count = 0
        failed_count = 0
        errors = []
        
        for user in admin_users:
            try:
                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sent_count += 1
                logger.info(f"Daily health report sent to {user.email}")
                
            except Exception as e:
                failed_count += 1
                error_msg = f"{user.email}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to send health report to {user.email}: {e}")
        
        result = {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_admins': admin_users.count(),
            'overall_status': overall_status,
            'stats': {
                'total_documents': total_documents,
                'active_workflows': active_workflows,
                'overdue_workflows': overdue_workflows,
                'new_documents_today': new_documents_today,
            }
        }
        
        if errors:
            result['errors'] = errors
        
        logger.info(
            f"Daily health report completed: {sent_count} sent, {failed_count} failed, "
            f"System: {overall_status}"
        )
        return result
        
    except Exception as e:
        logger.error(f"Daily health report task failed: {str(e)}")
        raise


# ============================================================================
# Backward Compatibility Exports
# ============================================================================
# These are imported by monitoring_dashboard.py for manual triggering

__all__ = [
    'process_document_effective_dates',
    'process_document_obsoletion_dates',
    'check_workflow_timeouts',
    'perform_system_health_check',
    'cleanup_workflow_tasks',
    'cleanup_celery_results',
    'process_periodic_reviews',
    'send_test_email_to_self',
    'send_daily_health_report',
]
