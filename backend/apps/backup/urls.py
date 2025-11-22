"""
URL Configuration for Backup App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create router for backup management endpoints
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]