"""
URL Configuration for Scheduler App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import NotificationViewSet, SystemStatusViewSet
from .monitoring_dashboard import scheduler_status_api, manual_trigger_api, scheduler_dashboard

# Create router for scheduler endpoints
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'system-status', SystemStatusViewSet, basename='system-status')

urlpatterns = [
    path('', include(router.urls)),
    
    # Legacy API endpoints
    path('api/health/', views.system_health_api, name='scheduler_health_api'),
    path('api/tasks/', views.tasks_status_api, name='scheduler_tasks_api'),
    
    # Enhanced monitoring endpoints
    path('monitoring/dashboard/', scheduler_dashboard, name='scheduler_dashboard'),
    path('monitoring/status/', scheduler_status_api, name='scheduler_status_api'),
    path('monitoring/manual-trigger/', manual_trigger_api, name='manual_trigger_api'),
    
    # Admin integration endpoints
    path('admin/dashboard/', scheduler_dashboard, name='scheduler_admin_dashboard'),
    path('admin/status/', scheduler_status_api, name='scheduler_admin_status'),
    path('admin/manual-trigger/', manual_trigger_api, name='scheduler_admin_manual_trigger'),
]