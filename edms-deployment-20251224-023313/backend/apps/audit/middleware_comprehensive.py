"""
Comprehensive Audit Middleware for API Session Handling
This middleware provides complete session context for API requests to resolve audit trail constraints
"""

import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.backends.base import SessionBase

logger = logging.getLogger(__name__)


class APISessionWrapper:
    """
    Minimal session wrapper for API requests
    """
    def __init__(self, session_key=None):
        self.session_key = session_key or f"api-{uuid.uuid4().hex[:12]}"
        self._session_key = self.session_key
        self.accessed = False
        self.modified = False
        
    def get(self, key, default=None):
        self.accessed = True
        return default
        
    def __getitem__(self, key):
        self.accessed = True
        return None
        
    def __setitem__(self, key, value):
        self.modified = True
        
    def __delitem__(self, key):
        self.modified = True
        
    def __contains__(self, key):
        self.accessed = True
        return False
        
    def setdefault(self, key, value):
        self.modified = True
        return value
        
    def flush(self):
        self.modified = True
        
    def cycle_key(self):
        self.session_key = f"api-{uuid.uuid4().hex[:12]}"
        self._session_key = self.session_key
        self.modified = True


class ComprehensiveAuditMiddleware(MiddlewareMixin):
    """
    Comprehensive middleware to handle audit trail session requirements for API requests
    """
    
    def process_request(self, request):
        """
        Process incoming request and ensure proper session context for audit trail
        """
        # Only process API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Check if this is an authenticated API request
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
            
        try:
            # Ensure request has proper session for audit trail
            if not hasattr(request, 'session') or not getattr(request, 'session', None):
                # Create API session wrapper
                api_session = APISessionWrapper()
                request.session = api_session
                logger.debug(f"Created API session: {api_session.session_key}")
                
            elif not hasattr(request.session, 'session_key') or not request.session.session_key:
                # Existing session but no session_key
                session_key = f"api-{uuid.uuid4().hex[:12]}"
                request.session.session_key = session_key
                request.session._session_key = session_key
                logger.debug(f"Added session_key to existing session: {session_key}")
                
            # Add additional audit context
            request.audit_context = {
                'session_id': request.session.session_key,
                'request_type': 'API',
                'client_ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            }
            
        except Exception as e:
            logger.error(f"Error setting up API session: {e}")
            # Create minimal fallback
            class FallbackSession:
                def __init__(self):
                    self.session_key = f"api-fallback-{uuid.uuid4().hex[:8]}"
                    self._session_key = self.session_key
            
            request.session = FallbackSession()
            
        return None
    
    def _get_client_ip(self, request):
        """
        Get the client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def process_response(self, request, response):
        """
        Clean up any temporary session data if needed
        """
        return response
    
    def process_exception(self, request, exception):
        """
        Handle any exceptions that might occur during session processing
        """
        if hasattr(request, 'audit_context'):
            logger.error(f"Exception in request with audit context: {exception}")
        return None