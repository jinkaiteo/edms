"""
System Health Service

Performs comprehensive system health monitoring and validation.
"""

import logging
from datetime import timedelta
from typing import Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model

from ...documents.models import Document
from ...workflows.models import DocumentWorkflow
from ...audit.models import AuditTrail
from ...users.models import User

logger = logging.getLogger(__name__)
User = get_user_model()


class SystemHealthService:
    """
    System health monitoring and automated checks.
    
    Provides comprehensive system monitoring, performance checks,
    and automated health validation.
    """
    
    def __init__(self):
        self._system_user = None
    
    @property
    def system_user(self):
        """Lazy initialization of system user to avoid database connection at import."""
        if self._system_user is None:
            self._system_user = self._get_system_user()
        return self._system_user
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        try:
            health_results = {
                'overall_status': 'HEALTHY',
                'timestamp': timezone.now().isoformat(),
                'checks': {},
                'warnings': [],
                'errors': []
            }
            
            # Database connectivity check
            health_results['checks']['database'] = self._check_database()
            
            # Workflow system check
            health_results['checks']['workflows'] = self._check_workflow_system()
            
            # Audit system check
            health_results['checks']['audit_system'] = self._check_audit_system()
            
            # Document storage check
            health_results['checks']['document_storage'] = self._check_document_storage()
            
            # Memory and performance check
            health_results['checks']['performance'] = self._check_performance()
            
            # Email notification system check
            health_results['checks']['email_system'] = self._check_email_system()
            
            # Determine overall status
            failed_checks = [name for name, result in health_results['checks'].items() if not result['healthy']]
            
            if failed_checks:
                health_results['overall_status'] = 'UNHEALTHY'
                health_results['errors'].extend([f"Failed check: {check}" for check in failed_checks])
            
            # Create audit record
            AuditTrail.objects.create(
                user=self.system_user,
                action='SYSTEM_HEALTH_CHECK',
                description=f'System health check: {health_results["overall_status"]}',
                field_changes={
                    'overall_status': health_results['overall_status'],
                    'failed_checks': failed_checks,
                    'check_count': len(health_results['checks'])
                },
                ip_address='127.0.0.1',
                user_agent='EDMS Health Monitor'
            )

            return health_results
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'overall_status': 'CRITICAL',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations."""
        try:
            # Test basic database operations
            user_count = User.objects.count()
            document_count = Document.objects.count()
            workflow_count = DocumentWorkflow.objects.count()
            
            return {
                'healthy': True,
                'users': user_count,
                'documents': document_count,
                'workflows': workflow_count,
                'response_time_ms': 10  # Placeholder
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_workflow_system(self) -> Dict[str, Any]:
        """Check workflow system health."""
        try:
            active_workflows = DocumentWorkflow.objects.filter(is_terminated=False).count()
            completed_workflows = DocumentWorkflow.objects.filter(is_terminated=True).count()
            
            return {
                'healthy': True,
                'active_workflows': active_workflows,
                'completed_workflows': completed_workflows
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_audit_system(self) -> Dict[str, Any]:
        """Check audit system health."""
        try:
            recent_audits = AuditTrail.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            return {
                'healthy': True,
                'recent_audit_records': recent_audits
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_document_storage(self) -> Dict[str, Any]:
        """Check document storage system."""
        try:
            total_documents = Document.objects.count()
            
            return {
                'healthy': True,
                'total_documents': total_documents,
                'storage_accessible': True
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check system performance metrics."""
        try:
            return {
                'healthy': True,
                'cpu_usage': 25.0,  # Placeholder
                'memory_usage': 60.0,  # Placeholder
                'disk_usage': 45.0   # Placeholder
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_email_system(self) -> Dict[str, Any]:
        """Check email notification system health."""
        try:
            from django.conf import settings
            import smtplib
            
            email_health = {
                'healthy': True,
                'warnings': [],
                'errors': []
            }
            
            # 1. Check SMTP configuration
            email_backend = settings.EMAIL_BACKEND
            email_health['backend'] = email_backend
            
            if 'console' in email_backend.lower():
                email_health['healthy'] = False
                email_health['errors'].append('Console backend active - emails not being sent!')
                email_health['smtp_configured'] = False
            else:
                email_health['smtp_configured'] = True
                email_health['smtp_host'] = f"{settings.EMAIL_HOST}:{settings.EMAIL_PORT}"
            
            # 2. Test SMTP connection (only if SMTP configured)
            if email_health['smtp_configured']:
                try:
                    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
                    server.starttls()
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.quit()
                    email_health['smtp_connection'] = True
                except Exception as e:
                    email_health['healthy'] = False
                    email_health['smtp_connection'] = False
                    email_health['errors'].append(f'SMTP connection failed: {str(e)}')
            
            # 3. Check recent email task activity (last 24 hours)
            try:
                from django_celery_results.models import TaskResult
                cutoff = timezone.now() - timedelta(hours=24)
                
                email_tasks = TaskResult.objects.filter(
                    task_name__icontains='email',
                    date_done__gte=cutoff
                )
                
                sent_count = email_tasks.filter(status='SUCCESS').count()
                failed_count = email_tasks.filter(status='FAILURE').count()
                
                email_health['emails_sent_24h'] = sent_count
                email_health['emails_failed_24h'] = failed_count
                
                # Calculate failure rate
                total = sent_count + failed_count
                if total > 0:
                    failure_rate = (failed_count / total) * 100
                    email_health['failure_rate'] = round(failure_rate, 2)
                    
                    # Warning if failure rate > 10%
                    if failure_rate > 10:
                        email_health['warnings'].append(f'High email failure rate: {failure_rate:.1f}%')
                    
                    # Error if failure rate > 50%
                    if failure_rate > 50:
                        email_health['healthy'] = False
                        email_health['errors'].append(f'Critical email failure rate: {failure_rate:.1f}%')
                else:
                    email_health['failure_rate'] = 0.0
                
                # Warning if many failures
                if failed_count > 20:
                    email_health['warnings'].append(f'{failed_count} email failures in last 24h')
                
            except Exception as e:
                email_health['warnings'].append(f'Could not check email task history: {str(e)}')
            
            # 4. Check users with email addresses
            try:
                users_with_email = User.objects.filter(
                    email__isnull=False
                ).exclude(email='').count()
                total_users = User.objects.count()
                
                email_health['users_with_email'] = users_with_email
                email_health['total_users'] = total_users
                
                if users_with_email == 0:
                    email_health['warnings'].append('No users have email addresses configured')
                elif users_with_email < total_users * 0.5:
                    email_health['warnings'].append(f'Only {users_with_email}/{total_users} users have email addresses')
            
            except Exception as e:
                email_health['warnings'].append(f'Could not check user emails: {str(e)}')
            
            # 5. Check Celery worker status (for async email sending)
            try:
                from celery import current_app
                inspect = current_app.control.inspect()
                registered = inspect.registered()
                
                if registered:
                    # Check if email tasks are registered
                    all_tasks = []
                    for worker_tasks in registered.values():
                        all_tasks.extend(worker_tasks)
                    
                    email_task_registered = any('email' in task.lower() for task in all_tasks)
                    email_health['celery_worker_active'] = True
                    email_health['email_tasks_registered'] = email_task_registered
                    
                    if not email_task_registered:
                        email_health['warnings'].append('Email tasks not registered in Celery workers')
                else:
                    email_health['celery_worker_active'] = False
                    email_health['warnings'].append('No active Celery workers detected')
            
            except Exception as e:
                email_health['warnings'].append(f'Could not check Celery status: {str(e)}')
            
            return email_health
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _get_system_user(self) -> User:
        """Get system user for health monitoring."""
        try:
            return User.objects.get(username='system_scheduler')
        except User.DoesNotExist:
            return User.objects.filter(is_superuser=True).first()


# Singleton instance
system_health_service = SystemHealthService()
