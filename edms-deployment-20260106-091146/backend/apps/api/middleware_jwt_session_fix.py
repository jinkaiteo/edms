"""
Middleware to prevent session authentication issues with JWT on API endpoints.

Django's SessionMiddleware and AuthenticationMiddleware try to use sessions
even for JWT-authenticated API requests, causing FallbackSession errors.
This middleware prevents session access for API endpoints.
"""
from django.utils.deprecation import MiddlewareMixin


class DisableSessionForAPIMiddleware(MiddlewareMixin):
    """
    Disable session operations for API endpoints that use JWT authentication.
    
    This prevents the FallbackSession error that occurs when Django's
    AuthenticationMiddleware tries to access request.session for API requests.
    """
    
    def process_request(self, request):
        """Disable session for API requests before other middleware runs."""
        if request.path.startswith('/api/'):
            # Set a dummy session that won't cause errors
            request.session = DummySession()
        return None


class DummySession(dict):
    """
    A dummy session object that acts like a dict but doesn't cause errors.
    
    This allows Django's session and auth middleware to run without crashing
    on API endpoints that use JWT instead of sessions.
    """
    
    def __init__(self):
        super().__init__()
        self.modified = False
        self.accessed = False
    
    def __getitem__(self, key):
        """Allow getting items without KeyError."""
        return self.get(key, None)
    
    def __setitem__(self, key, value):
        """Allow setting items without side effects."""
        self.modified = True
        super().__setitem__(key, value)
    
    def save(self):
        """No-op save method."""
        pass
    
    def delete(self):
        """No-op delete method."""
        pass
    
    def flush(self):
        """No-op flush method."""
        pass
    
    def cycle_key(self):
        """No-op cycle_key method."""
        pass
    
    @property
    def session_key(self):
        """Return a dummy session key."""
        return 'jwt-no-session'
    
    def create(self):
        """No-op create method."""
        pass
