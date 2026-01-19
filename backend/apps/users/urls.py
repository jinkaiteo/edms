"""
URL configuration for User Management (S1).

Provides REST API endpoints for authentication, user management,
and role-based access control.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .auth_views import CustomTokenObtainPairView
from .views import (
    UserViewSet,
    RoleViewSet,
    UserRoleViewSet,
    MFADeviceViewSet,
    UserProfileView,
    LogoutView,
    ChangePasswordView,
    SetupMFAView,
    VerifyMFAView,
)

# Router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'user-roles', UserRoleViewSet)
router.register(r'mfa-devices', MFADeviceViewSet)

app_name = 'users'

urlpatterns = [
    # JWT Authentication (with LoginAudit tracking)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User profile and management
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Multi-Factor Authentication
    path('mfa/setup/', SetupMFAView.as_view(), name='setup_mfa'),
    path('mfa/verify/', VerifyMFAView.as_view(), name='verify_mfa'),
    
    # ViewSet URLs
    path('', include(router.urls)),
]