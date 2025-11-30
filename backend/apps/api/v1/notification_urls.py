"""
Notification URL configuration for v1 API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .notification_views import NotificationViewSet

# Create router for notification endpoints
router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]