"""
URL Configuration for Settings App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create router for system settings endpoints
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]