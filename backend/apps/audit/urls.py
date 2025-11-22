"""
URL Configuration for Audit App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# For now, just create an empty router since audit functionality
# may be accessed through other modules
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]