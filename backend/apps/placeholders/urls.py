"""
URL Configuration for Placeholders App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create router for placeholder management endpoints
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]