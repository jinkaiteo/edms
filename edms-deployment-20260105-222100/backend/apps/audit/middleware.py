"""
Audit Middleware for EDMS

Automatically captures request/response information for audit trail
and provides context for audit logging throughout the request lifecycle.
"""

import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from threading import local


# Thread-local storage for audit context
_audit_context = local()


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to capture audit context for all requests.
    
    Provides audit trail context including user information,
    session details, and request metadata for compliance logging.
    """
    
    def process_request(self, request):
        """Initialize audit context for the request."""
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Extract client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create audit context
        audit_context = {
            'request_id': request_id,
            'timestamp': time.time(),
            'user': request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
            'session_id': request.session.session_key if hasattr(request, 'session') else None,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'request_method': request.method,
            'request_path': request.path,
            'request_params': dict(request.GET),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Store in thread-local storage
        _audit_context.current_request = audit_context
        
        # Also attach to request for easy access
        request.audit_context = audit_context
        
        return None
    
    def process_response(self, request, response):
        """Finalize audit context and optionally log request."""
        if hasattr(_audit_context, 'current_request'):
            context = _audit_context.current_request
            
            # Calculate request duration
            duration = time.time() - context['timestamp']
            context['duration'] = duration
            context['response_status'] = response.status_code
            
            # Log significant requests (can be customized)
            self._log_request_if_needed(context, response)
            
            # Clear context
            delattr(_audit_context, 'current_request')
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions in audit context."""
        if hasattr(_audit_context, 'current_request'):
            context = _audit_context.current_request
            context['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception)
            }
            
            # Log error for audit purposes
            self._log_exception(context, exception)
        
        return None
    
    def _log_request_if_needed(self, context, response):
        """Log requests that meet certain criteria."""
        # Only import here to avoid circular imports
        from .models import AuditTrail
        
        # Define what should be logged automatically
        should_log = (
            # API requests
            context['request_path'].startswith('/api/') or
            # Admin actions
            context['request_path'].startswith('/admin/') or
            # POST, PUT, DELETE requests
            context['request_method'] in ['POST', 'PUT', 'DELETE', 'PATCH'] or
            # Error responses
            response.status_code >= 400 or
            # Long-running requests
            context.get('duration', 0) > 5.0
        )
        
        if should_log and context.get('user'):
            try:
                AuditTrail.objects.create(
                    action='VIEW' if context['request_method'] == 'GET' else context['request_method'],
                    user=context['user'],
                    user_display_name=context['user'].get_full_name() or context['user'].username,
                    session_id=context.get('session_id', ''),
                    ip_address=context.get('ip_address'),
                    user_agent=context.get('user_agent', ''),
                    request_path=context['request_path'],
                    request_method=context['request_method'],
                    description=f"{context['request_method']} {context['request_path']} - {response.status_code}",
                    severity='INFO' if response.status_code < 400 else 'WARNING',
                    metadata={
                        'duration': context.get('duration'),
                        'response_status': response.status_code,
                        'request_params': context.get('request_params'),
                        'content_type': context.get('content_type'),
                    }
                )
            except Exception:
                # Avoid breaking the application if audit logging fails
                pass
    
    def _log_exception(self, context, exception):
        """Log exceptions for audit trail."""
        from .models import AuditTrail
        
        try:
            AuditTrail.objects.create(
                action='ERROR',
                user=context.get('user'),
                user_display_name=context['user'].get_full_name() if context.get('user') else 'Anonymous',
                session_id=context.get('session_id', ''),
                ip_address=context.get('ip_address'),
                user_agent=context.get('user_agent', ''),
                request_path=context['request_path'],
                request_method=context['request_method'],
                description=f"Exception in {context['request_method']} {context['request_path']}: {str(exception)}",
                severity='ERROR',
                metadata={
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'duration': context.get('duration'),
                    'request_params': context.get('request_params'),
                }
            )
        except Exception:
            # Avoid breaking the application if audit logging fails
            pass


def get_current_audit_context():
    """
    Get the current audit context from thread-local storage.
    
    Returns:
        dict: Current audit context or None if not available
    """
    return getattr(_audit_context, 'current_request', None)


def get_current_user():
    """
    Get the current user from audit context.
    
    Returns:
        User: Current user or None if not available
    """
    context = get_current_audit_context()
    return context.get('user') if context else None


def get_current_session_id():
    """
    Get the current session ID from audit context.
    
    Returns:
        str: Session ID or None if not available
    """
    context = get_current_audit_context()
    return context.get('session_id') if context else None


def get_current_ip_address():
    """
    Get the current IP address from audit context.
    
    Returns:
        str: IP address or None if not available
    """
    context = get_current_audit_context()
    return context.get('ip_address') if context else None


def set_audit_context(**kwargs):
    """
    Set additional context for audit logging.
    
    Args:
        **kwargs: Additional context to merge with current context
    """
    if hasattr(_audit_context, 'current_request'):
        _audit_context.current_request.update(kwargs)


def clear_audit_context():
    """Clear the current audit context."""
    if hasattr(_audit_context, 'current_request'):
        delattr(_audit_context, 'current_request')