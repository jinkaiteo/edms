"""
Change Password API Views for EDMS

Provides secure password change functionality for authenticated users.
Includes validation, authentication checks, and proper error handling.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password with proper validation and security checks.
    
    Expected payload:
    {
        "current_password": "user's current password",
        "new_password": "new password meeting requirements"
    }
    
    Returns:
    - 200: Password changed successfully
    - 400: Invalid current password or new password doesn't meet requirements
    - 401: Authentication required
    """
    try:
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        # Note: We handle password confirmation in frontend, not backend for better UX
        
        # Validate required fields
        if not current_password:
            return Response(
                {'detail': 'Current password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_password:
            return Response(
                {'detail': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current password
        if not user.check_password(current_password):
            logger.warning(f"Failed password change attempt for user {user.username}: incorrect current password")
            return Response(
                {'detail': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password is different from current
        if user.check_password(new_password):
            return Response(
                {'detail': 'New password must be different from current password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password against Django's password validators
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'detail': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Update last login time
        update_last_login(None, user)
        
        # Log successful password change
        logger.info(f"Password successfully changed for user {user.username}")
        
        # Generate new tokens (optional - invalidates other sessions)
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                'detail': 'Password changed successfully',
                'message': 'Your password has been updated successfully. Please use your new password for future logins.',
                # Optionally return new tokens to keep user logged in
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error changing password for user {request.user.username}: {str(e)}")
        return Response(
            {'detail': 'An error occurred while changing your password. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def password_requirements(request):
    """
    Get password requirements for the frontend to display.
    
    Returns the current password validation requirements configured in Django.
    """
    try:
        # Get Django password validator settings
        from django.conf import settings
        from django.contrib.auth.password_validation import get_default_password_validators
        
        validators = get_default_password_validators()
        requirements = []
        
        # Extract requirements from validators
        for validator in validators:
            validator_name = validator.__class__.__name__
            
            if 'MinimumLengthValidator' in validator_name:
                min_length = getattr(validator, 'min_length', 8)
                requirements.append(f'At least {min_length} characters long')
            
            elif 'CommonPasswordValidator' in validator_name:
                requirements.append('Cannot be a commonly used password')
            
            elif 'NumericPasswordValidator' in validator_name:
                requirements.append('Cannot be entirely numeric')
            
            elif 'AttributeSimilarityValidator' in validator_name:
                requirements.append('Cannot be too similar to your personal information')
        
        # Add default requirements if no validators configured
        if not requirements:
            requirements = [
                'At least 8 characters long',
                'Must contain at least one uppercase letter',
                'Must contain at least one lowercase letter', 
                'Must contain at least one number',
                'Must contain at least one special character'
            ]
        
        return Response(
            {
                'requirements': requirements,
                'detail': 'Password requirements retrieved successfully'
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error retrieving password requirements: {str(e)}")
        return Response(
            {'detail': 'Error retrieving password requirements'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )