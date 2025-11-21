"""
Django signals for User Management (S1).

Handles automatic creation of audit records, role assignments,
and other user lifecycle events for compliance tracking.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone

from .models import User, UserRole, UserSession


@receiver(post_save, sender=User)
def create_user_audit_record(sender, instance, created, **kwargs):
    """Create audit record when user is created or updated."""
    from apps.audit.models import AuditLog
    
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        content_object=instance,
        action=action,
        user=getattr(instance, '_current_user', None),
        changes=getattr(instance, '_field_changes', {}),
        metadata={
            'model': 'User',
            'user_uuid': str(instance.uuid),
            'username': instance.username,
        }
    )


@receiver(post_save, sender=UserRole)
def create_role_assignment_audit(sender, instance, created, **kwargs):
    """Create audit record for role assignments."""
    from apps.audit.models import AuditLog
    
    if created:
        AuditLog.objects.create(
            content_object=instance,
            action='ROLE_ASSIGNED',
            user=instance.assigned_by,
            metadata={
                'model': 'UserRole',
                'user': instance.user.username,
                'role': instance.role.name,
                'module': instance.role.module,
                'permission_level': instance.role.permission_level,
                'reason': instance.assignment_reason,
            }
        )


@receiver(post_delete, sender=UserRole)
def create_role_removal_audit(sender, instance, **kwargs):
    """Create audit record for role removals."""
    from apps.audit.models import AuditLog
    
    AuditLog.objects.create(
        content_object=None,  # Object deleted
        action='ROLE_REMOVED',
        user=getattr(instance, '_removed_by', None),
        metadata={
            'model': 'UserRole',
            'user': instance.user.username,
            'role': instance.role.name,
            'module': instance.role.module,
            'permission_level': instance.role.permission_level,
            'removal_reason': getattr(instance, '_removal_reason', ''),
        }
    )


@receiver(user_logged_in)
def create_login_session(sender, request, user, **kwargs):
    """Create session record when user logs in."""
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Create or update session record
    session, created = UserSession.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={
            'user': user,
            'ip_address': ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'login_timestamp': timezone.now(),
        }
    )
    
    if not created:
        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])
    
    # Reset failed login attempts
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.save(update_fields=['failed_login_attempts'])


@receiver(user_logged_out)
def update_logout_session(sender, request, user, **kwargs):
    """Update session record when user logs out."""
    if request and hasattr(request, 'session'):
        try:
            session = UserSession.objects.get(
                session_key=request.session.session_key,
                user=user,
                is_active=True
            )
            session.logout_timestamp = timezone.now()
            session.is_active = False
            session.logout_reason = 'normal'
            session.save(update_fields=[
                'logout_timestamp', 'is_active', 'logout_reason'
            ])
        except UserSession.DoesNotExist:
            pass


@receiver(pre_save, sender=User)
def track_user_field_changes(sender, instance, **kwargs):
    """Track field changes for audit purposes."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            changes = {}
            
            # Track specific field changes
            tracked_fields = [
                'username', 'email', 'first_name', 'last_name',
                'is_active', 'is_staff', 'is_superuser', 'is_validated',
                'department', 'position', 'phone_number'
            ]
            
            for field in tracked_fields:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(instance, field, None)
                if old_value != new_value:
                    changes[field] = {
                        'old': old_value,
                        'new': new_value
                    }
            
            # Store changes on instance for use in post_save signal
            instance._field_changes = changes
            
        except User.DoesNotExist:
            # New user, no changes to track
            instance._field_changes = {}