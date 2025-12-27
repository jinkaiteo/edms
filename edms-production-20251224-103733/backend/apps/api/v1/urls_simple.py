"""
Simplified API v1 URL Configuration for testing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_simple import (
    APIStatusView, APIInfoView, 
    SimpleDocumentViewSet, SimpleUserViewSet, SimpleAuditViewSet
)
from .auth_views_simple import SimpleLoginView, SimpleLogoutView, SimpleCurrentUserView

# Create router for ViewSets
router = DefaultRouter()

# Register simple viewsets
router.register(r'documents', SimpleDocumentViewSet, basename='document')
router.register(r'users', SimpleUserViewSet, basename='user') 
router.register(r'audit-trail', SimpleAuditViewSet, basename='audittrail')

# URL patterns
urlpatterns = [
    # API status and health
    path('status/', APIStatusView.as_view(), name='api-status'),
    path('info/', APIInfoView.as_view(), name='api-info'),
    
    # Authentication endpoints (simplified)
    path('auth/login/', SimpleLoginView.as_view(), name='auth-login'),
    path('auth/logout/', SimpleLogoutView.as_view(), name='auth-logout'),
    path('auth/user/', SimpleCurrentUserView.as_view(), name='auth-user'),
    
    # Include router URLs
    path('', include(router.urls)),
]