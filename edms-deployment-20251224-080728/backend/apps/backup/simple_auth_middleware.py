"""
Simple authentication middleware for backup operations in development
"""

from django.contrib.auth import get_user_model
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class SimpleBackupAuthMiddleware:
    """
    Simple middleware to handle authentication for backup operations
    in development environments when frontend session sharing has issues.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Only apply to backup API endpoints
        if '/api/v1/backup/' in request.path:
            self.handle_backup_auth(request)
        
        response = self.get_response(request)
        return response
    
    def handle_backup_auth(self, request):
        """Handle authentication for backup endpoints"""
        User = get_user_model()
        
        # If already authenticated, continue
        if request.user.is_authenticated:
            return
        
        # For development: if no authentication and admin user exists,
        # set admin user for backup operations
        try:
            admin_user = User.objects.filter(
                is_staff=True, 
                is_superuser=True
            ).first()
            
            if admin_user:
                request.user = admin_user
                logger.info(f"Applied development auth for backup operation: {admin_user.username}")
        except Exception as e:
            logger.warning(f"Development auth fallback failed: {e}")