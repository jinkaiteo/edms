"""
URL Configuration for Scheduler App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create router for scheduler endpoints
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]