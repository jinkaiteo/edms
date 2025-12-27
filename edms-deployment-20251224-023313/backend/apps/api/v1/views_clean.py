"""
Clean API views without audit dependencies for basic authentication testing.
"""

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.users.models import User


class CleanAPIStatusView(APIView):
    """Clean API status endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'environment': 'development'
        })


class CleanLoginView(APIView):
    """Clean user login endpoint without audit complications."""
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required',
                'code': 'MISSING_CREDENTIALS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Login successful
                login(request, user)
                
                # Update user login tracking (without signals)
                user.last_login = timezone.now()
                user.failed_login_attempts = 0
                user.save(update_fields=['last_login', 'failed_login_attempts'])
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'uuid': str(user.uuid),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Account is disabled',
                    'code': 'ACCOUNT_DISABLED'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'error': 'Invalid username or password',
                'code': 'INVALID_CREDENTIALS'
            }, status=status.HTTP_401_UNAUTHORIZED)


class CleanLogoutView(APIView):
    """Clean user logout endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Not logged in'
            }, status=status.HTTP_200_OK)


class CleanCurrentUserView(APIView):
    """Get current authenticated user information."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            return Response({
                'authenticated': True,
                'user': {
                    'uuid': str(user.uuid),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'date_joined': user.date_joined.isoformat()
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'authenticated': False,
                'user': None
            }, status=status.HTTP_200_OK)