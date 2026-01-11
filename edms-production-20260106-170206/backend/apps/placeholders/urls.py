"""
URL Configuration for Placeholders App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import placeholder_definitions

# Create router for placeholder management endpoints
router = DefaultRouter()

urlpatterns = [
    path('definitions/', placeholder_definitions, name='placeholder_definitions'),
    path('', include(router.urls)),
]