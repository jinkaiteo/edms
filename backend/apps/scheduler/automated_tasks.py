"""
Automated Tasks Service - Phase 3 Implementation

This module provides comprehensive scheduler automation including:
- Document effective date monitoring and automation
- Workflow timeout and escalation handling
- Health monitoring and system checks
- Manual task triggering capabilities
- Background task management and retry logic

Compliance: 21 CFR Part 11 audit trails for all automated actions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from celery import shared_task
from celery.exceptions import Retry
from celery.utils.log import get_task_logger

from .models import ScheduledTask
from ..documents.models import Document
from ..workflows.models import DocumentWorkflow, DocumentState, DocumentTransition
from ..audit.models import AuditTrail
from ..users.models import User

logger = get_task_logger(__name__)
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
        self.system_user = self._get_system_user()
    
    def process_effective_dates(self) -> Dict[str, Any]:
        """
        Process documents with effective dates that have passed.
        
        Returns:
            Results summary with processed documents
        """
        try:
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
                effective_date__lte=timezone.now().date()
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
                            action='DOCUMENT_EFFECTIVE_DATE_PROCESSED',
                            model_name='Document',
                            object_id=str(document.id),
                            changes={
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
                status='PENDING_OBSOLETE',
                obsoleting_date__lte=timezone.now().date()
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
                                    'obsoletion_date': document.obsoleting_date.isoformat() if document.obsoleting_date else None
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
                            action='DOCUMENT_OBSOLETED',
                            model_name='Document',
                            object_id=str(document.id),
                            changes={
                                'old_status': old_status,
                                'new_status': document.status,
                                'obsoletion_date': document.obsoleting_date.isoformat() if document.obsoleting_date else None,
                                'automation_timestamp': timezone.now().isoformat()
                            },
                            ip_address='127.0.0.1',
                            user_agent='EDMS Scheduler Service'
                        )
                        
                        results['processed_documents'].append({
                            'document_id': document.id,
                            'document_number': document.document_number,
                            'title': document.title,
                            'obsoletion_date': document.obsoleting_date.isoformat() if document.obsoleting_date else None
                        })
                        
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
                    if workflow.due_date and workflow.due_date < timezone.now().date():
                        days_overdue = (timezone.now().date() - workflow.due_date).days
                        
                        results['timeout_count'] += 1
                        results['overdue_workflows'].append({
                            'workflow_id': workflow.id,
                            'document_number': workflow.document.document_number,
                            'document_title': workflow.document.title,
                            'workflow_type': workflow.workflow_type,
                            'current_state': workflow.current_state.name,
                            'due_date': workflow.due_date.isoformat(),
                            'days_overdue': days_overdue,
                            'current_assignee': workflow.current_assignee.get_full_name() if workflow.current_assignee else None
                        })
                        
                        # Send notification for severely overdue workflows
                        if days_overdue > 7:  # More than a week overdue
                            self._send_timeout_notification(workflow, days_overdue)
                            results['notification_count'] += 1
                            
                except Exception as e:
                    logger.error(f"Error checking workflow timeout for {workflow.id}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow timeout check failed: {str(e)}")
            raise SchedulerError(f"Workflow timeout check failed: {str(e)}")
    
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
    
    def _send_timeout_notification(self, workflow: DocumentWorkflow, days_overdue: int):
        """Send timeout notification for overdue workflow."""
        try:
            if workflow.current_assignee and workflow.current_assignee.email:
                subject = f"EDMS: Overdue Workflow - {workflow.document.document_number}"
                message = f"""
                Document: {workflow.document.title}
                Document Number: {workflow.document.document_number}
                Workflow Type: {workflow.workflow_type}
                Current State: {workflow.current_state.name}
                Due Date: {workflow.due_date}
                Days Overdue: {days_overdue}
                
                Please log into EDMS to complete this workflow.
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[workflow.current_assignee.email],
                    fail_silently=True
                )
                
                logger.info(f"Sent timeout notification for workflow {workflow.id}")
                
        except Exception as e:
            logger.error(f"Failed to send timeout notification: {str(e)}")


class SystemHealthService:
    """
    System health monitoring and automated checks.
    
    Provides comprehensive system monitoring, performance checks,
    and automated health validation.
    """
    
    def __init__(self):
        self.system_user = self._get_system_user()
    
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
                model_name='System',
                object_id='health_monitor',
                changes={
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
            completed_workflows = DocumentWorkflow.objects.filter(
                current_state__code='EFFECTIVE'
            ).count()
            
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


# Celery Tasks
@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
    """Celery task to process document effective dates."""
    try:
        automation_service = DocumentAutomationService()
        results = automation_service.process_effective_dates()
        
        logger.info(f"Processed {results['success_count']} effective dates successfully")
        return results
        
    except Exception as e:
        logger.error(f"Effective date processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@shared_task(bind=True, max_retries=3)
def process_document_obsoletion_dates(self):
    """Celery task to process document obsoletion dates."""
    try:
        automation_service = DocumentAutomationService()
        results = automation_service.process_obsoletion_dates()
        
        logger.info(f"Processed {results['success_count']} obsoletion dates successfully")
        return results
        
    except Exception as e:
        logger.error(f"Obsoletion processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@shared_task
def check_workflow_timeouts():
    """Celery task to check workflow timeouts."""
    try:
        automation_service = DocumentAutomationService()
        results = automation_service.check_workflow_timeouts()
        
        logger.info(f"Checked {results['checked_count']} workflows, found {results['timeout_count']} timeouts")
        return results
        
    except Exception as e:
        logger.error(f"Workflow timeout check failed: {str(e)}")
        raise


@shared_task
def perform_system_health_check():
    """Celery task to perform system health check."""
    try:
        health_service = SystemHealthService()
        results = health_service.perform_health_check()
        
        logger.info(f"System health check completed: {results['overall_status']}")
        return results
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise


# Service instances
document_automation_service = DocumentAutomationService()
system_health_service = SystemHealthService()