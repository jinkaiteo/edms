"""
Custom authentication views with LoginAudit tracking.

Extends SimpleJWT views to trigger Django's user_logged_in signal
for proper audit trail logging.
"""

from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.signals import user_logged_in
from rest_framework.response import Response
from rest_framework import status


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that triggers user_logged_in signal.
    
    This ensures that LoginAudit entries are created when users
    authenticate via JWT tokens.
    """
    
    def post(self, request, *args, **kwargs):
        # Get the standard JWT response
        response = super().post(request, *args, **kwargs)
        
        # If authentication was successful, trigger the login signal
        if response.status_code == status.HTTP_200_OK:
            # Get the user from the request
            # The serializer validates the credentials
            serializer = self.get_serializer(data=request.data)
            
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.user
                
                # Trigger the user_logged_in signal
                # This will be caught by audit signals and create LoginAudit entry
                user_logged_in.send(
                    sender=user.__class__,
                    request=request,
                    user=user
                )
                
            except Exception as e:
                # Log the error but don't fail the authentication
                print(f"Warning: Failed to trigger login signal: {e}")
        
        return response
