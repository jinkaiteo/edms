"""
Backup API Authentication Middleware

This middleware enables Django admin users to access backup APIs
by checking for Django session authentication when API token auth fails.
"""

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class BackupAPIAuthMiddleware(MiddlewareMixin):
    """
    Middleware to enable Django admin session authentication for backup APIs.
    
    This allows users logged into Django admin to access backup API endpoints
    without requiring separate API token authentication.
    """
    
    def process_request(self, request):
        """
        Check if this is a backup API request and handle authentication.
        """
        # Only process backup API requests
        if not request.path.startswith('/api/v1/backup/'):
            return None
        
        # Skip if already authenticated via DRF
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None
        
        # Check for Django session authentication - be more permissive
        if request.user.is_authenticated:
            logger.info(f'Backup API access granted via Django session for user: {request.user.username}')
            # Force the user to be staff for this request
            request.user.is_staff = True
            return None
        
        # Check session manually if needed
        session_key = request.COOKIES.get('sessionid')
        if session_key:
            try:
                session = Session.objects.get(session_key=session_key)
                session_data = session.get_decoded()
                
                if '_auth_user_id' in session_data:
                    user_id = session_data['_auth_user_id']
                    user = User.objects.get(id=user_id)
                    
                    if user.is_active and user.is_staff:
                        # Set the user for this request
                        request.user = user
                        logger.info(f'Backup API access granted via manual session check for user: {user.username}')
                        return None
                        
            except (Session.DoesNotExist, User.DoesNotExist, KeyError) as e:
                logger.warning(f'Session authentication failed for backup API: {str(e)}')
        
        # If we reach here, no valid authentication found
        logger.warning(f'Unauthenticated backup API request from {request.META.get("REMOTE_ADDR", "unknown")}')
        return None  # Let DRF handle the 401 response


class BackupAPICORSMiddleware(MiddlewareMixin):
    """
    Additional CORS handling specifically for backup API requests.
    """
    
    def process_response(self, request, response):
        """
        Add CORS headers for backup API requests.
        """
        if request.path.startswith('/api/v1/backup/'):
            response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response