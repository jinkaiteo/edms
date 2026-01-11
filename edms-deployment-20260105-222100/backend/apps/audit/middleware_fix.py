"""
Audit Middleware Fix for API Session Handling
Generates session_id for API requests that don't have Django sessions
"""

import uuid
from django.utils.deprecation import MiddlewareMixin


class APIAuditSessionMiddleware(MiddlewareMixin):
    """
    Middleware to handle audit trail session_id for API requests
    """
    
    def process_request(self, request):
        """
        Generate a session_id for API requests that don't have a Django session
        """
        # Check if this is an API request
        if request.path.startswith('/api/'):
            # Check if request has Authorization header (JWT token)
            if 'HTTP_AUTHORIZATION' in request.META:
                # Generate a unique session ID for this API request
                if not hasattr(request, 'session') or not getattr(request.session, 'session_key', None):
                    # Create a session-like object with session_key
                    api_session_id = f"api-{uuid.uuid4().hex[:12]}"
                    
                    # Add session_id to request for audit trail
                    request.audit_session_id = api_session_id
                    
                    # If request has no session, create a minimal session object
                    if not hasattr(request, 'session'):
                        class APISession:
                            def __init__(self, session_key):
                                self.session_key = session_key
                                self._session_key = session_key
                            
                            def get(self, key, default=None):
                                return default
                                
                            def __getitem__(self, key):
                                raise KeyError(key)
                                
                            def __setitem__(self, key, value):
                                pass
                        
                        request.session = APISession(api_session_id)
        
        return None
    
    def process_response(self, request, response):
        """
        Clean up any API session data if needed
        """
        return response