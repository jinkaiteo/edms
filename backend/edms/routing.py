"""
WebSocket URL routing for EDMS real-time features.

Defines WebSocket routes for dashboard updates and notifications.
"""

from django.urls import re_path
from apps.api.websocket_consumers import DashboardConsumer
from apps.api.notification_websocket_consumer import NotificationConsumer

websocket_urlpatterns = [
    # Dashboard real-time updates
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
    
    # User notifications real-time
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]