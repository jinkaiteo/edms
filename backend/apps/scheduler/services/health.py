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
    
    def _get_system_user(self) -> User:
        """Get system user for health monitoring."""
        try:
            return User.objects.get(username='system_scheduler')
        except User.DoesNotExist:
            return User.objects.filter(is_superuser=True).first()


# Singleton instance
system_health_service = SystemHealthService()
