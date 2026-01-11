"""
Health check URLs for EDMS.
Provides unauthenticated health endpoints for monitoring and testing.
"""

from django.urls import path
from .health_check import health_check, simple_health_check

urlpatterns = [
    path('', health_check, name='health_check'),
    path('simple/', simple_health_check, name='simple_health_check'),
]