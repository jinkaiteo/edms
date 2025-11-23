"""
Audit Services for EDMS S2 Module.

Provides comprehensive audit trail services for compliance
with 21 CFR Part 11 requirements.
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from django.core.serializers import serialize

from .models import (
    AuditTrail, SystemEvent, LoginAudit, UserSession,
    DatabaseChangeLog, ComplianceEvent
)
from .middleware import get_current_audit_context

User = get_user_model()


class AuditService:
    """
    Main audit service for EDMS compliance logging.
    
    Provides methods for logging various types of audit events
    while maintaining data integrity and tamper resistance.
    """

    def __init__(self):
        self.hash_algorithm = 'sha256'

    def log_user_action(self, user: User, action: str, object_type: str = None,
                       object_id: int = None, description: str = None,
                       additional_data: Dict[str, Any] = None) -> AuditTrail:
        """
        Log a user action for audit trail.
        
        Args:
            user: User performing the action
            action: Action type (CREATE, UPDATE, DELETE, VIEW, etc.)
            object_type: Type of object being acted upon
            object_id: ID of the object
            description: Human-readable description
            additional_data: Additional audit data
            
        Returns:
            AuditTrail: Created audit trail entry
        """
        audit_context = get_current_audit_context()
        
        with transaction.atomic():
            # Create audit trail entry
            audit_entry = AuditTrail.objects.create(
                user=user,
                action=action,
                object_type=object_type,
                object_id=object_id,
                description=description or f"User {action.lower()} {object_type}",
                ip_address=audit_context.get('ip_address') if audit_context else None,
                user_agent=audit_context.get('user_agent') if audit_context else None,
                session_id=audit_context.get('session_id') if audit_context else None,
                request_id=audit_context.get('request_id') if audit_context else None,
                additional_data=additional_data or {}
            )
            
            # Generate integrity hash
            audit_entry.integrity_hash = self._generate_integrity_hash(audit_entry)
            audit_entry.save(update_fields=['integrity_hash'])
            
            return audit_entry

    def log_system_event(self, event_type: str, object_type: str = None,
                        object_id: int = None, description: str = None,
                        additional_data: Dict[str, Any] = None) -> SystemEvent:
        """
        Log a system event for audit trail.
        
        Args:
            event_type: Type of system event
            object_type: Type of object involved
            object_id: ID of the object
            description: Description of the event
            additional_data: Additional event data
            
        Returns:
            SystemEvent: Created system event entry
        """
        with transaction.atomic():
            event = SystemEvent.objects.create(
                event_type=event_type,
                object_type=object_type,
                object_id=object_id,
                description=description or f"System {event_type}",
                additional_data=additional_data or {}
            )
            
            # Generate integrity hash
            event.integrity_hash = self._generate_system_event_hash(event)
            event.save(update_fields=['integrity_hash'])
            
            return event

    def log_workflow_event(self, workflow_instance, event_type: str,
                          user: User = None, description: str = None,
                          additional_data: Dict[str, Any] = None) -> AuditTrail:
        """
        Log workflow-related events.
        
        Args:
            workflow_instance: WorkflowInstance object
            event_type: Type of workflow event
            user: User performing the action (None for system events)
            description: Description of the workflow event
            additional_data: Additional workflow data
            
        Returns:
            AuditTrail: Created audit trail entry
        """
        workflow_data = {
            'workflow_id': str(workflow_instance.uuid),
            'workflow_type': workflow_instance.workflow_type.workflow_type,
            'current_state': str(workflow_instance.state),
            'document_id': workflow_instance.object_id,
            **(additional_data or {})
        }
        
        if user:
            return self.log_user_action(
                user=user,
                action=event_type,
                object_type='WorkflowInstance',
                object_id=workflow_instance.id,
                description=description,
                additional_data=workflow_data
            )
        else:
            return self.log_system_event(
                event_type=event_type,
                object_type='WorkflowInstance',
                object_id=workflow_instance.id,
                description=description,
                additional_data=workflow_data
            )

    def log_document_access(self, user: User, document, access_type: str,
                           additional_data: Dict[str, Any] = None) -> AuditTrail:
        """
        Log document access events for compliance.
        
        Args:
            user: User accessing the document
            document: Document being accessed
            access_type: Type of access (VIEW, DOWNLOAD, PRINT, etc.)
            additional_data: Additional access data
            
        Returns:
            AuditTrail: Created audit trail entry
        """
        document_data = {
            'document_number': document.document_number,
            'document_title': document.title,
            'document_version': str(document.version),
            'document_status': document.status,
            **(additional_data or {})
        }
        
        return self.log_user_action(
            user=user,
            action=f'DOCUMENT_{access_type}',
            object_type='Document',
            object_id=document.id,
            description=f"User {access_type.lower()} document {document.document_number}",
            additional_data=document_data
        )

    def log_login_event(self, user: User, success: bool, failure_reason: str = None) -> LoginAudit:
        """
        Log user login events.
        
        Args:
            user: User attempting to log in
            success: Whether login was successful
            failure_reason: Reason for login failure (if applicable)
            
        Returns:
            LoginAudit: Created login audit entry
        """
        audit_context = get_current_audit_context()
        
        return LoginAudit.objects.create(
            user=user,
            username=user.username if user else None,
            success=success,
            failure_reason=failure_reason,
            ip_address=audit_context.get('ip_address') if audit_context else None,
            user_agent=audit_context.get('user_agent') if audit_context else None
        )

    def start_user_session(self, user: User, session_key: str) -> UserSession:
        """
        Start tracking a user session.
        
        Args:
            user: User starting the session
            session_key: Django session key
            
        Returns:
            UserSession: Created or existing user session entry
        """
        audit_context = get_current_audit_context()
        
        session, created = UserSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user': user,
                'ip_address': audit_context.get('ip_address') if audit_context else None,
                'user_agent': audit_context.get('user_agent') if audit_context else None,
                'is_active': True
            }
        )
        
        # If session exists but for different user, update it
        if not created:
            session.user = user
            session.is_active = True
            session.last_activity = timezone.now()
            session.save(update_fields=['user', 'is_active', 'last_activity'])
        
        return session

    def end_user_session(self, session_key: str):
        """
        End tracking for a user session.
        
        Args:
            session_key: Django session key to end
        """
        try:
            session = UserSession.objects.get(
                session_key=session_key,
                logout_timestamp__isnull=True
            )
            session.logout_timestamp = timezone.now()
            session.save()
        except UserSession.DoesNotExist:
            pass  # Session not tracked

    def log_database_change(self, model_instance, action: str, user: User = None,
                          old_values: Dict = None, new_values: Dict = None) -> DatabaseChangeLog:
        """
        Log database changes for audit trail.
        
        Args:
            model_instance: Django model instance that changed
            action: Type of change (INSERT, UPDATE, DELETE)
            user: User making the change
            old_values: Previous field values (for UPDATE/DELETE)
            new_values: New field values (for INSERT/UPDATE)
            
        Returns:
            DatabaseChangeLog: Created change log entry
        """
        audit_context = get_current_audit_context()
        
        with transaction.atomic():
            change_log = DatabaseChangeLog.objects.create(
                content_type=ContentType.objects.get_for_model(model_instance),
                object_id=model_instance.pk,
                action=action,
                user=user,
                old_values=old_values or {},
                new_values=new_values or {},
                ip_address=audit_context.get('ip_address') if audit_context else None,
                session_id=audit_context.get('session_id') if audit_context else None
            )
            
            # Generate integrity hash
            change_log.integrity_hash = self._generate_change_log_hash(change_log)
            change_log.save(update_fields=['integrity_hash'])
            
            return change_log

    def log_compliance_event(self, event_type: str, description: str,
                            user: User = None, severity: str = 'INFO') -> ComplianceEvent:
        """
        Log compliance-related events.
        
        Args:
            event_type: Type of compliance event
            description: Description of the compliance event
            user: User associated with the event
            object_type: Type of object involved
            object_id: ID of the object
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            additional_data: Additional compliance data
            
        Returns:
            ComplianceEvent: Created compliance event entry
        """
        audit_context = get_current_audit_context()
        
        with transaction.atomic():
            event = ComplianceEvent.objects.create(
                event_type=event_type,
                description=description,
                user=user,
                severity=severity
            )
            
            # Note: ComplianceEvent doesn't have integrity_hash field
            # Skip integrity hash for now
            
            return event

    def verify_audit_integrity(self, audit_entry) -> bool:
        """
        Verify the integrity of an audit trail entry.
        
        Args:
            audit_entry: AuditTrail, SystemEvent, or other audit model instance
            
        Returns:
            bool: True if integrity check passes
        """
        if hasattr(audit_entry, 'integrity_hash'):
            if isinstance(audit_entry, AuditTrail):
                expected_hash = self._generate_integrity_hash(audit_entry)
            elif isinstance(audit_entry, SystemEvent):
                expected_hash = self._generate_system_event_hash(audit_entry)
            elif isinstance(audit_entry, DatabaseChangeLog):
                expected_hash = self._generate_change_log_hash(audit_entry)
            elif isinstance(audit_entry, ComplianceEvent):
                expected_hash = self._generate_compliance_event_hash(audit_entry)
            else:
                return False
                
            return audit_entry.integrity_hash == expected_hash
        
        return False

    def get_audit_trail(self, object_type: str = None, object_id: int = None,
                       user: User = None, start_date=None, end_date=None) -> List[Dict]:
        """
        Retrieve audit trail entries with optional filtering.
        
        Args:
            object_type: Filter by object type
            object_id: Filter by object ID
            user: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of audit trail entries
        """
        queryset = AuditTrail.objects.all()
        
        if object_type:
            queryset = queryset.filter(object_type=object_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        if user:
            queryset = queryset.filter(user=user)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset.order_by('-timestamp')

    def _generate_integrity_hash(self, audit_entry: AuditTrail) -> str:
        """Generate integrity hash for audit trail entry."""
        hash_data = {
            'user_id': audit_entry.user.id if audit_entry.user else None,
            'action': audit_entry.action,
            'object_type': audit_entry.object_type,
            'object_id': audit_entry.object_id,
            'description': audit_entry.description,
            'timestamp': audit_entry.timestamp.isoformat(),
            'ip_address': audit_entry.ip_address,
            'additional_data': audit_entry.additional_data
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _generate_system_event_hash(self, event: SystemEvent) -> str:
        """Generate integrity hash for system event."""
        hash_data = {
            'event_type': event.event_type,
            'object_type': event.object_type,
            'object_id': event.object_id,
            'description': event.description,
            'timestamp': event.timestamp.isoformat(),
            'additional_data': event.additional_data
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _generate_change_log_hash(self, change_log: DatabaseChangeLog) -> str:
        """Generate integrity hash for database change log."""
        hash_data = {
            'content_type_id': change_log.content_type.id,
            'object_id': change_log.object_id,
            'action': change_log.action,
            'user_id': change_log.user.id if change_log.user else None,
            'timestamp': change_log.timestamp.isoformat(),
            'old_values': change_log.old_values,
            'new_values': change_log.new_values
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _generate_compliance_event_hash(self, event: ComplianceEvent) -> str:
        """Generate integrity hash for compliance event."""
        hash_data = {
            'event_type': event.event_type,
            'description': event.description,
            'user_id': event.user.id if event.user else None,
            'severity': event.severity,
            'timestamp': event.timestamp.isoformat()
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()


# Global audit service instance
audit_service = AuditService()