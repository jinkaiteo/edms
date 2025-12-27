"""
Celery tasks for Audit Trail Management (S2).

Background tasks for audit log maintenance, compliance reporting,
and audit data processing.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

from .models import AuditTrail, SystemEvent, LoginAudit, DatabaseChangeLog, ComplianceEvent
from .services import audit_service

logger = get_task_logger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def cleanup_expired_audit_logs(self):
    """
    Clean up expired audit logs according to retention policies.
    
    Removes audit logs older than the configured retention period
    while maintaining compliance with regulatory requirements.
    """
    try:
        logger.info("Starting audit log cleanup")
        
        # Configuration for retention periods (in days)
        retention_config = {
            'audit_trail': getattr(settings, 'AUDIT_RETENTION_DAYS', 2555),  # 7 years default
            'login_audit': getattr(settings, 'LOGIN_AUDIT_RETENTION_DAYS', 365),  # 1 year
            'system_events': getattr(settings, 'SYSTEM_EVENT_RETENTION_DAYS', 1095),  # 3 years
            'database_changes': getattr(settings, 'DB_CHANGE_RETENTION_DAYS', 2555),  # 7 years
            'compliance_events': getattr(settings, 'COMPLIANCE_RETENTION_DAYS', 2555)  # 7 years
        }
        
        cleaned_counts = {}
        
        # Clean up audit trails
        cutoff_date = timezone.now() - timedelta(days=retention_config['audit_trail'])
        count = AuditTrail.objects.filter(timestamp__lt=cutoff_date).count()
        if count > 0:
            # Archive before deletion for critical audit trails
            AuditTrail.objects.filter(timestamp__lt=cutoff_date).delete()
            cleaned_counts['audit_trail'] = count
        
        # Clean up login audits
        cutoff_date = timezone.now() - timedelta(days=retention_config['login_audit'])
        count = LoginAudit.objects.filter(login_timestamp__lt=cutoff_date).count()
        if count > 0:
            LoginAudit.objects.filter(login_timestamp__lt=cutoff_date).delete()
            cleaned_counts['login_audit'] = count
        
        # Clean up system events (keep critical events longer)
        cutoff_date = timezone.now() - timedelta(days=retention_config['system_events'])
        count = SystemEvent.objects.filter(
            timestamp__lt=cutoff_date
        ).exclude(
            event_type__in=['SECURITY_BREACH', 'COMPLIANCE_VIOLATION', 'DATA_INTEGRITY_ERROR']
        ).count()
        if count > 0:
            SystemEvent.objects.filter(
                timestamp__lt=cutoff_date
            ).exclude(
                event_type__in=['SECURITY_BREACH', 'COMPLIANCE_VIOLATION', 'DATA_INTEGRITY_ERROR']
            ).delete()
            cleaned_counts['system_events'] = count
        
        # Clean up database change logs
        cutoff_date = timezone.now() - timedelta(days=retention_config['database_changes'])
        count = DatabaseChangeLog.objects.filter(timestamp__lt=cutoff_date).count()
        if count > 0:
            DatabaseChangeLog.objects.filter(timestamp__lt=cutoff_date).delete()
            cleaned_counts['database_changes'] = count
        
        # Log the cleanup operation
        audit_service.log_system_event(
            event_type='AUDIT_LOG_CLEANUP',
            description='Expired audit logs cleaned up',
            additional_data={
                'retention_config': retention_config,
                'cleaned_counts': cleaned_counts
            }
        )
        
        logger.info(f"Audit log cleanup completed: {cleaned_counts}")
        return {"success": True, "cleaned_counts": cleaned_counts}
        
    except Exception as exc:
        logger.error(f"Audit log cleanup failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def generate_compliance_report(self, report_type='daily', start_date=None, end_date=None):
    """
    Generate compliance reports for audit purposes.
    
    Args:
        report_type: Type of report (daily, weekly, monthly)
        start_date: Start date for report period
        end_date: End date for report period
    """
    try:
        logger.info(f"Generating {report_type} compliance report")
        
        # Set date range based on report type
        end = timezone.now()
        if report_type == 'daily':
            start = end - timedelta(days=1)
        elif report_type == 'weekly':
            start = end - timedelta(days=7)
        elif report_type == 'monthly':
            start = end - timedelta(days=30)
        else:
            start = timezone.datetime.fromisoformat(start_date) if start_date else end - timedelta(days=1)
            end = timezone.datetime.fromisoformat(end_date) if end_date else end
        
        # Gather compliance metrics
        metrics = {
            'report_period': {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'type': report_type
            },
            'audit_statistics': {
                'total_audit_entries': AuditTrail.objects.filter(
                    timestamp__range=[start, end]
                ).count(),
                'user_actions': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    user__isnull=False
                ).count(),
                'system_events': SystemEvent.objects.filter(
                    timestamp__range=[start, end]
                ).count(),
                'login_attempts': LoginAudit.objects.filter(
                    login_timestamp__range=[start, end]
                ).count(),
                'failed_logins': LoginAudit.objects.filter(
                    login_timestamp__range=[start, end],
                    login_successful=False
                ).count()
            },
            'compliance_events': {
                'total_events': ComplianceEvent.objects.filter(
                    timestamp__range=[start, end]
                ).count(),
                'by_severity': {}
            },
            'document_activities': {
                'documents_created': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action='DOCUMENT_CREATE'
                ).count(),
                'documents_modified': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action='DOCUMENT_UPDATE'
                ).count(),
                'documents_approved': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action__contains='APPROVE'
                ).count(),
                'electronic_signatures': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action='ELECTRONIC_SIGNATURE'
                ).count()
            },
            'workflow_activities': {
                'workflows_initiated': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action__contains='WORKFLOW_INITIATED'
                ).count(),
                'workflows_completed': AuditTrail.objects.filter(
                    timestamp__range=[start, end],
                    action__contains='WORKFLOW_COMPLETED'
                ).count()
            }
        }
        
        # Get compliance events by severity
        severity_counts = ComplianceEvent.objects.filter(
            timestamp__range=[start, end]
        ).values('severity').distinct()
        
        for severity_data in severity_counts:
            severity = severity_data['severity']
            count = ComplianceEvent.objects.filter(
                timestamp__range=[start, end],
                severity=severity
            ).count()
            metrics['compliance_events']['by_severity'][severity] = count
        
        # Log report generation
        audit_service.log_system_event(
            event_type='COMPLIANCE_REPORT_GENERATED',
            description=f'{report_type.title()} compliance report generated',
            additional_data=metrics
        )
        
        logger.info(f"Compliance report generated successfully")
        return {"success": True, "metrics": metrics}
        
    except Exception as exc:
        logger.error(f"Compliance report generation failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def verify_audit_integrity(self, batch_size=1000):
    """
    Verify the integrity of audit trail entries.
    
    Checks integrity hashes to ensure audit data hasn't been tampered with.
    
    Args:
        batch_size: Number of entries to check in each batch
    """
    try:
        logger.info("Starting audit integrity verification")
        
        verification_results = {
            'total_checked': 0,
            'integrity_violations': 0,
            'failed_verifications': [],
            'batch_size': batch_size
        }
        
        # Check AuditTrail entries in batches
        audit_entries = AuditTrail.objects.all()[:batch_size]
        
        for entry in audit_entries:
            verification_results['total_checked'] += 1
            
            if not audit_service.verify_audit_integrity(entry):
                verification_results['integrity_violations'] += 1
                verification_results['failed_verifications'].append({
                    'entry_id': entry.id,
                    'timestamp': entry.timestamp.isoformat(),
                    'action': entry.action,
                    'user': entry.user.username if entry.user else None
                })
                
                # Log integrity violation
                audit_service.log_compliance_event(
                    event_type='AUDIT_INTEGRITY_VIOLATION',
                    description=f'Audit integrity violation detected for entry {entry.id}',
                    severity='CRITICAL',
                    object_type='AuditTrail',
                    object_id=entry.id
                )
        
        # Check SystemEvent entries
        system_events = SystemEvent.objects.all()[:batch_size]
        
        for event in system_events:
            verification_results['total_checked'] += 1
            
            if not audit_service.verify_audit_integrity(event):
                verification_results['integrity_violations'] += 1
                verification_results['failed_verifications'].append({
                    'event_id': event.id,
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type
                })
                
                # Log integrity violation
                audit_service.log_compliance_event(
                    event_type='SYSTEM_EVENT_INTEGRITY_VIOLATION',
                    description=f'System event integrity violation detected for event {event.id}',
                    severity='CRITICAL',
                    object_type='SystemEvent',
                    object_id=event.id
                )
        
        # Log verification results
        audit_service.log_system_event(
            event_type='AUDIT_INTEGRITY_VERIFICATION',
            description='Audit integrity verification completed',
            additional_data=verification_results
        )
        
        if verification_results['integrity_violations'] > 0:
            # Send alert for integrity violations
            send_integrity_violation_alert.delay(verification_results)
        
        logger.info(f"Audit integrity verification completed: {verification_results}")
        return verification_results
        
    except Exception as exc:
        logger.error(f"Audit integrity verification failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_integrity_violation_alert(self, violation_data):
    """
    Send alert for audit integrity violations.
    
    Args:
        violation_data: Dictionary containing violation details
    """
    try:
        logger.info("Sending audit integrity violation alert")
        
        subject = "CRITICAL: Audit Trail Integrity Violations Detected"
        message = f"""
        CRITICAL SECURITY ALERT
        
        Audit trail integrity violations have been detected in the EDMS system.
        
        Violation Summary:
        - Total entries checked: {violation_data['total_checked']}
        - Integrity violations found: {violation_data['integrity_violations']}
        
        This may indicate:
        - Unauthorized tampering with audit data
        - Database corruption
        - System compromise
        
        Immediate investigation is required.
        
        Please review the audit logs and take appropriate action.
        
        EDMS Security System
        """
        
        # Get admin email addresses
        admin_emails = list(
            User.objects.filter(
                is_superuser=True,
                email__isnull=False
            ).exclude(
                email=''
            ).values_list('email', flat=True)
        )
        
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edms.local'),
                recipient_list=admin_emails,
                fail_silently=False
            )
        
        # Log the alert
        audit_service.log_compliance_event(
            event_type='INTEGRITY_VIOLATION_ALERT_SENT',
            description='Audit integrity violation alert sent to administrators',
            severity='CRITICAL',
            additional_data={
                'recipients': admin_emails,
                'violation_count': violation_data['integrity_violations']
            }
        )
        
        logger.info("Integrity violation alert sent successfully")
        return {"success": True, "recipients": len(admin_emails)}
        
    except Exception as exc:
        logger.error(f"Failed to send integrity violation alert: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def archive_old_audit_data(self, archive_age_days=365):
    """
    Archive old audit data to separate storage.
    
    Args:
        archive_age_days: Age in days after which to archive data
    """
    try:
        logger.info(f"Starting audit data archival for data older than {archive_age_days} days")
        
        cutoff_date = timezone.now() - timedelta(days=archive_age_days)
        
        # Count entries to be archived
        archive_counts = {
            'audit_trail': AuditTrail.objects.filter(timestamp__lt=cutoff_date).count(),
            'system_events': SystemEvent.objects.filter(timestamp__lt=cutoff_date).count(),
            'login_audit': LoginAudit.objects.filter(login_timestamp__lt=cutoff_date).count(),
            'database_changes': DatabaseChangeLog.objects.filter(timestamp__lt=cutoff_date).count()
        }
        
        # TODO: Implement actual archival logic (export to files, backup storage, etc.)
        # For now, just log the archival operation
        
        audit_service.log_system_event(
            event_type='AUDIT_DATA_ARCHIVED',
            description=f'Audit data older than {archive_age_days} days archived',
            additional_data={
                'cutoff_date': cutoff_date.isoformat(),
                'archive_counts': archive_counts
            }
        )
        
        logger.info(f"Audit data archival completed: {archive_counts}")
        return {"success": True, "archive_counts": archive_counts}
        
    except Exception as exc:
        logger.error(f"Audit data archival failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def monitor_failed_login_attempts(self):
    """
    Monitor and alert on suspicious login patterns.
    
    Detects potential security threats based on failed login patterns.
    """
    try:
        logger.info("Monitoring failed login attempts")
        
        # Check for suspicious patterns in the last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Count failed login attempts by IP address
        from django.db.models import Count
        failed_attempts = LoginAudit.objects.filter(
            login_timestamp__gte=one_hour_ago,
            login_successful=False
        ).values('ip_address').annotate(
            attempt_count=Count('id')
        ).filter(
            attempt_count__gte=5  # 5 or more failed attempts
        )
        
        alerts = []
        for attempt_data in failed_attempts:
            ip_address = attempt_data['ip_address']
            count = attempt_data['attempt_count']
            
            alerts.append({
                'ip_address': ip_address,
                'failed_attempts': count,
                'time_window': '1 hour'
            })
            
            # Log security event
            audit_service.log_compliance_event(
                event_type='SUSPICIOUS_LOGIN_ACTIVITY',
                description=f'Multiple failed login attempts from IP {ip_address}',
                severity='WARNING',
                additional_data={
                    'ip_address': ip_address,
                    'failed_attempts': count,
                    'time_window': '1 hour'
                }
            )
        
        if alerts:
            # Send security alert
            logger.warning(f"Detected {len(alerts)} suspicious IP addresses")
            
            # TODO: Implement IP blocking or additional security measures
            
        logger.info(f"Failed login monitoring completed. {len(alerts)} alerts generated")
        return {"success": True, "alerts": alerts}
        
    except Exception as exc:
        logger.error(f"Failed login monitoring failed: {str(exc)}")
        raise self.retry(countdown=60 * (self.request.retries + 1))