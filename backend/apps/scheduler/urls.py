"""
URL Configuration for Scheduler App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import NotificationViewSet, SystemStatusViewSet

# Create router for scheduler endpoints
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'system-status', SystemStatusViewSet, basename='system-status')

urlpatterns = [
    path('', include(router.urls)),
    path('api/health/', views.system_health_api, name='scheduler_health_api'),
    path('api/tasks/', views.tasks_status_api, name='scheduler_tasks_api'),
]