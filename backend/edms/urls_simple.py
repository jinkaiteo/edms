"""
Simple URL configuration for development testing.
Includes basic Django admin and simple API endpoints for frontend testing.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout
from rest_framework import status

@api_view(['GET'])
def api_status(request):
    """Simple API status endpoint for testing."""
    return Response({
        'status': 'ok',
        'message': 'EDMS API is running',
        'user': str(request.user) if request.user.is_authenticated else 'Anonymous'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_login(request):
    """Simple login endpoint for frontend testing."""
    # Debug logging (fixed)
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    
    if not username or not password:
        return Response({
            'success': False,
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user:
        login(request, user)
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'uuid': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
        })
    else:
        return Response({
            'success': False,
            'error': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def simple_logout(request):
    """Simple logout endpoint."""
    logout(request)
    return Response({
        'success': True,
        'message': 'Logout successful'
    })

@api_view(['GET'])
def current_user(request):
    """Get current user information."""
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'uuid': str(request.user.id),
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
            }
        })
    else:
        return Response({
            'authenticated': False,
            'user': None
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/status/', api_status, name='api_status'),
    path('api/v1/auth/login/', simple_login, name='simple_login'),
    path('api/v1/auth/logout/', simple_logout, name='simple_logout'),
    path('api/v1/auth/user/', current_user, name='current_user'),
]