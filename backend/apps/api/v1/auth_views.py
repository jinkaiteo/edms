"""
Authentication views for API v1.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.users.models import User
from apps.audit.models import AuditTrail, LoginAudit


class LoginView(APIView):
    """
    User login endpoint.
    """
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
        
        # Get client IP for audit
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Login successful
                login(request, user)
                
                # Create login audit record
                LoginAudit.objects.create(
                    user=user,
                    username=username,
                    success=True,
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Update user login tracking
                user.last_login = timezone.now()
                user.failed_login_attempts = 0
                user.save(update_fields=['last_login', 'failed_login_attempts'])
                
                return Response({
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,  # Primary key for database operations
                        'uuid': str(user.uuid),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'last_login': user.last_login,
                        'full_name': user.get_full_name(),
                        'is_active': user.is_active
                    },
                    'session_id': request.session.session_key
                }, status=status.HTTP_200_OK)
            else:
                # Account disabled
                LoginAudit.objects.create(
                    user=user,
                    username=username,
                    success=False,
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    failure_reason='Account disabled'
                )
                
                return Response({
                    'error': 'Account is disabled',
                    'code': 'ACCOUNT_DISABLED'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # Authentication failed
            LoginAudit.objects.create(
                username=username,
                success=False,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                failure_reason='Invalid credentials'
            )
            
            # Track failed attempts if user exists
            try:
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                user.save(update_fields=['failed_login_attempts'])
            except User.DoesNotExist:
                pass
            
            return Response({
                'error': 'Invalid username or password',
                'code': 'INVALID_CREDENTIALS'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    User logout endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        session_key = request.session.session_key
        
        # Get client IP for audit
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Update user session audit
        from apps.audit.models import UserSession
        try:
            session = UserSession.objects.get(
                session_key=session_key,
                user=user,
                is_active=True
            )
            session.logout_timestamp = timezone.now()
            session.is_active = False
            session.logout_reason = 'normal'
            session.save(update_fields=['logout_timestamp', 'is_active', 'logout_reason'])
        except UserSession.DoesNotExist:
            pass
        
        # Logout user
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """
    Get current authenticated user information.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        return Response({
            'user': {
                'id': user.id,  # Primary key for database operations
                'uuid': str(user.uuid),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'last_login': user.last_login,
                'full_name': user.get_full_name(),
                'date_joined': user.date_joined,
                'is_active': user.is_active
            },
            'session': {
                'session_key': request.session.session_key,
                'is_authenticated': request.user.is_authenticated
            }
        }, status=status.HTTP_200_OK)


class CSRFTokenView(APIView):
    """
    Get CSRF token for forms.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        token = get_token(request)
        return Response({
            'csrf_token': token
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def auth_status(request):
    """
    Check authentication status.
    """
    return Response({
        'is_authenticated': request.user.is_authenticated,
        'user': {
            'username': request.user.username if request.user.is_authenticated else None,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False,
            'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
        } if request.user.is_authenticated else None
    })