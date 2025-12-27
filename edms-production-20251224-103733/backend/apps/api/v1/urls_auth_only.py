"""
Clean authentication-only URL Configuration for testing.
"""

from django.urls import path
from .views_clean import CleanAPIStatusView, CleanLoginView, CleanLogoutView, CleanCurrentUserView

# URL patterns - clean authentication only
urlpatterns = [
    # API status and health
    path('status/', CleanAPIStatusView.as_view(), name='api-status'),
    
    # Authentication endpoints (clean)
    path('auth/login/', CleanLoginView.as_view(), name='auth-login'),
    path('auth/logout/', CleanLogoutView.as_view(), name='auth-logout'),
    path('auth/user/', CleanCurrentUserView.as_view(), name='auth-user'),
]