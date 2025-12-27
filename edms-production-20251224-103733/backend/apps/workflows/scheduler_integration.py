"""
Scheduler Integration for EDMS Workflows.

Implements automated state transitions as required by EDMS_details_workflow.txt:
- Line 18: Scheduler checks effective date and activates documents
- Line 26: Scheduler supersedes parent documents during up-versioning
- Line 44: Scheduler makes documents obsolete
"""

from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import DocumentWorkflow, DocumentState
from .workflow_manager import WorkflowManager
from apps.audit.models import AuditTrail
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(name='check_effective_dates')
def check_effective_dates():
    """
    Check and activate documents with effective dates <= today.
    EDMS specification line 18.
    """
    today = timezone.now().date()
    
    # Get system user for automated transitions
    system_user = User.objects.filter(username='system').first()
    if not system_user:
        system_user = User.objects.filter(is_superuser=True).first()
    
    # Find documents pending effective date
    pending_workflows = DocumentWorkflow.objects.filter(
        current_state_id=DocumentState.APPROVED_PENDING_EFFECTIVE,
        effective_date__lte=today,
        is_terminated=False
    ).select_related('document')
    
    activated_count = 0
    errors = []
    
    for workflow in pending_workflows:
        try:
            logger.info(f"Activating document {workflow.document.id} on effective date {workflow.effective_date}")
            
            # Handle up-versioning workflow
            if workflow.workflow_type == 'UP_VERSION':
                parent = workflow.document.parent_document
                if parent and parent.status == DocumentState.APPROVED_AND_EFFECTIVE:
                    # Supersede parent document
                    parent.status = DocumentState.SUPERSEDED
                    parent.superseded_by = workflow.document
                    parent.superseded_at = timezone.now()
                    parent.save()
                    
                    logger.info(f"Superseded parent document {parent.id}")
            
            # Activate document
            workflow.transition_to(
                DocumentState.APPROVED_AND_EFFECTIVE,
                system_user,
                comment=f"Automatically activated on effective date {today}"
            )
            
            workflow.document.status = DocumentState.APPROVED_AND_EFFECTIVE
            workflow.document.effective_date = today
            workflow.document.save()
            
            activated_count += 1
            
            # Log for audit
            AuditTrail.objects.create(
                user=system_user,
                action='DOCUMENT_ACTIVATED',
                content_object=workflow.document,
                details=f"Document automatically activated by scheduler on effective date {today}"
            )
            
        except Exception as e:
            error_msg = f"Error activating document {workflow.document.id}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Activated {activated_count} documents on {today}")
    
    return {
        'date': str(today),
        'activated_count': activated_count,
        'errors': errors
    }


@shared_task(name='check_obsoleting_dates')
def check_obsoleting_dates():
    """
    Check and obsolete documents with obsoleting dates <= today.
    EDMS specification line 44.
    """
    today = timezone.now().date()
    
    # Get system user for automated transitions
    system_user = User.objects.filter(username='system').first()
    if not system_user:
        system_user = User.objects.filter(is_superuser=True).first()
    
    # Find documents pending obsoletion
    obsoleting_workflows = DocumentWorkflow.objects.filter(
        current_state_id=DocumentState.PENDING_OBSOLETION,
        obsoleting_date__lte=today,
        is_terminated=False
    ).select_related('document')
    
    obsoleted_count = 0
    errors = []
    
    for workflow in obsoleting_workflows:
        try:
            logger.info(f"Obsoleting document {workflow.document.id} on obsoleting date {workflow.obsoleting_date}")
            
            # Final dependency check per specification
            from .dependency_manager import DocumentDependencyManager
            final_check = DocumentDependencyManager.validate_obsoleting_workflow(workflow.document)
            
            if not final_check['valid']:
                # Terminate workflow if dependencies found
                workflow.is_terminated = True
                workflow.termination_reason = f"Obsoleting terminated by scheduler: {final_check['reason']}"
                workflow.last_approved_state = workflow.current_state_id
                workflow.save()
                
                logger.warning(f"Obsoleting terminated for document {workflow.document.id}: {final_check['reason']}")
                continue
            
            # Make document obsolete
            workflow.transition_to(
                DocumentState.OBSOLETE,
                system_user,
                comment=f"Automatically obsoleted on obsoleting date {today}"
            )
            
            workflow.document.status = DocumentState.OBSOLETE
            workflow.document.obsoleted_at = timezone.now()
            workflow.document.save()
            
            obsoleted_count += 1
            
            # Log for audit
            AuditTrail.objects.create(
                user=system_user,
                action='DOCUMENT_OBSOLETED',
                content_object=workflow.document,
                details=f"Document automatically obsoleted by scheduler on obsoleting date {today}"
            )
            
        except Exception as e:
            error_msg = f"Error obsoleting document {workflow.document.id}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Obsoleted {obsoleted_count} documents on {today}")
    
    return {
        'date': str(today),
        'obsoleted_count': obsoleted_count,
        'errors': errors
    }


@shared_task(name='cleanup_terminated_workflows')
def cleanup_terminated_workflows():
    """
    Clean up terminated workflows and ensure document states are correct.
    """
    terminated_workflows = DocumentWorkflow.objects.filter(
        is_terminated=True,
        updated_at__lt=timezone.now() - timezone.timedelta(days=30)
    )
    
    cleanup_count = 0
    
    for workflow in terminated_workflows:
        try:
            # Ensure document is in correct state
            if workflow.last_approved_state:
                workflow.document.status = workflow.last_approved_state
                workflow.document.save()
            
            cleanup_count += 1
            
        except Exception as e:
            logger.error(f"Error cleaning up terminated workflow {workflow.id}: {str(e)}")
    
    logger.info(f"Cleaned up {cleanup_count} terminated workflows")
    
    return {
        'cleanup_count': cleanup_count,
        'date': str(timezone.now().date())
    }


@shared_task(name='workflow_health_check')
def workflow_health_check():
    """
    Perform health check on workflow system.
    """
    health_data = {
        'timestamp': timezone.now().isoformat(),
        'active_workflows': DocumentWorkflow.objects.filter(
            is_terminated=False,
            current_state_id__in=[
                DocumentState.PENDING_REVIEW,
                DocumentState.PENDING_APPROVAL,
                DocumentState.APPROVED_PENDING_EFFECTIVE,
                DocumentState.PENDING_OBSOLETION
            ]
        ).count(),
        'pending_effective': DocumentWorkflow.objects.filter(
            current_state_id=DocumentState.APPROVED_PENDING_EFFECTIVE
        ).count(),
        'pending_obsoletion': DocumentWorkflow.objects.filter(
            current_state_id=DocumentState.PENDING_OBSOLETION
        ).count(),
        'terminated_workflows': DocumentWorkflow.objects.filter(
            is_terminated=True
        ).count(),
        'overdue_workflows': DocumentWorkflow.objects.filter(
            due_date__lt=timezone.now(),
            current_state_id__in=[
                DocumentState.PENDING_REVIEW,
                DocumentState.PENDING_APPROVAL
            ]
        ).count()
    }
    
    logger.info(f"Workflow health check: {health_data}")
    
    return health_data


# Celery Beat Schedule for Workflow Tasks
WORKFLOW_SCHEDULE = {
    'check-effective-dates': {
        'task': 'check_effective_dates',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-obsoleting-dates': {
        'task': 'check_obsoleting_dates', 
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-terminated-workflows': {
        'task': 'cleanup_terminated_workflows',
        'schedule': 86400.0,  # Daily
    },
    'workflow-health-check': {
        'task': 'workflow_health_check',
        'schedule': 900.0,  # Every 15 minutes
    },
}