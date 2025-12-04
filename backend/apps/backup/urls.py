"""
URL Configuration for Backup App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    BackupConfigurationViewSet,
    BackupJobViewSet,
    RestoreJobViewSet,
    SystemBackupViewSet,
    HealthCheckViewSet
)

# Create router for backup management endpoints
router = DefaultRouter()
router.register(r'configurations', BackupConfigurationViewSet, basename='backup-configuration')
router.register(r'jobs', BackupJobViewSet, basename='backup-job')
router.register(r'restores', RestoreJobViewSet, basename='restore-job')
router.register(r'system', SystemBackupViewSet, basename='system-backup')
router.register(r'health', HealthCheckViewSet, basename='health-check')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', include(router.urls)),  # For backward compatibility
]