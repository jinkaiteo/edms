"""
Enhanced Audit Middleware for API and Session Management

Fixes the session_id constraint issue for API calls and provides
proper audit context for both session-based and token-based authentication.
"""

import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from threading import local


# Thread-local storage for audit context
_audit_context = local()


class EnhancedAuditMiddleware(MiddlewareMixin):
    """
    Enhanced middleware to handle both session-based and API-based requests.
    
    Automatically generates session context for API calls to prevent
    null session_id constraint violations in audit trail.
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
        
        # Handle session for API requests
        session_id = self._get_or_create_session_id(request)
        
        # Create audit context
        audit_context = {
            'request_id': request_id,
            'timestamp': time.time(),
            'user': request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'request_method': request.method,
            'request_path': request.path,
            'request_params': dict(request.GET),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'is_api_request': request.path.startswith('/api/'),
        }
        
        # Store in thread-local storage
        _audit_context.current_request = audit_context
        
        # Also attach to request for easy access
        request.audit_context = audit_context
        
        return None
    
    def _get_or_create_session_id(self, request):
        """
        Get or create a session ID for audit trail compliance.
        
        For API requests without sessions, generates a pseudo-session ID
        based on user and request characteristics to maintain audit trail integrity.
        """
        # Try to get existing session ID
        if hasattr(request, 'session') and request.session.session_key:
            return request.session.session_key
        
        # For API requests, create a deterministic pseudo-session ID
        if request.path.startswith('/api/'):
            # Use Authorization header or user info to create consistent session ID
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            user_id = str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            
            # Create a deterministic session ID for API requests
            api_session_components = [
                'api',
                user_id,
                ip_address[:8],  # First 8 chars of IP for privacy
                auth_header[-8:] if auth_header else 'noauth'  # Last 8 chars of auth token
            ]
            
            api_session_id = f"api_{'_'.join(api_session_components)}"[:40]  # Limit to 40 chars
            return api_session_id
        
        # For non-API requests, try to initialize session
        if hasattr(request, 'session'):
            # Force session creation
            request.session.create()
            return request.session.session_key
        
        # Fallback: generate a temporary session ID
        return f"temp_{str(uuid.uuid4())[:8]}"
    
    def process_response(self, request, response):
        """Finalize audit context and optionally log request."""
        if hasattr(_audit_context, 'current_request'):
            context = _audit_context.current_request
            
            # Calculate request duration
            duration = time.time() - context['timestamp']
            context['duration'] = duration
            context['response_status'] = response.status_code
            
            # Log significant requests
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
            # API requests (especially POST/PUT/DELETE)
            (context['is_api_request'] and context['request_method'] in ['POST', 'PUT', 'DELETE', 'PATCH']) or
            # Admin actions
            context['request_path'].startswith('/admin/') or
            # Error responses
            response.status_code >= 400 or
            # Long-running requests
            context.get('duration', 0) > 5.0
        )
        
        if should_log:
            try:
                # Ensure we have a valid user for audit trail
                user = context.get('user')
                user_display_name = 'Anonymous'
                
                if user and user.is_authenticated:
                    user_display_name = user.get_full_name() or user.username
                elif context['is_api_request']:
                    # For API requests, try to extract user from the session ID pattern
                    session_id = context.get('session_id', '')
                    if session_id.startswith('api_') and '_' in session_id:
                        parts = session_id.split('_')
                        if len(parts) >= 2 and parts[1] != 'anonymous':
                            user_display_name = f"API User {parts[1]}"
                    
                AuditTrail.objects.create(
                    action='VIEW' if context['request_method'] == 'GET' else context['request_method'],
                    user=user,
                    user_display_name=user_display_name,
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
                        'is_api_request': context['is_api_request'],
                    }
                )
            except Exception as e:
                # Avoid breaking the application if audit logging fails
                print(f"Audit logging failed: {e}")
    
    def _log_exception(self, context, exception):
        """Log exceptions for audit trail."""
        from .models import AuditTrail
        
        try:
            user = context.get('user')
            user_display_name = 'Anonymous'
            
            if user and user.is_authenticated:
                user_display_name = user.get_full_name() or user.username
            
            AuditTrail.objects.create(
                action='ERROR',
                user=user,
                user_display_name=user_display_name,
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
                    'is_api_request': context['is_api_request'],
                }
            )
        except Exception as e:
            # Avoid breaking the application if audit logging fails
            print(f"Exception audit logging failed: {e}")


# Helper functions from original middleware
def get_current_audit_context():
    """Get the current audit context from thread-local storage."""
    return getattr(_audit_context, 'current_request', None)


def get_current_user():
    """Get the current user from audit context."""
    context = get_current_audit_context()
    return context.get('user') if context else None


def get_current_session_id():
    """Get the current session ID from audit context."""
    context = get_current_audit_context()
    return context.get('session_id') if context else None


def get_current_ip_address():
    """Get the current IP address from audit context."""
    context = get_current_audit_context()
    return context.get('ip_address') if context else None


def set_audit_context(**kwargs):
    """Set additional context for audit logging."""
    if hasattr(_audit_context, 'current_request'):
        _audit_context.current_request.update(kwargs)


def clear_audit_context():
    """Clear the current audit context."""
    if hasattr(_audit_context, 'current_request'):
        delattr(_audit_context, 'current_request')