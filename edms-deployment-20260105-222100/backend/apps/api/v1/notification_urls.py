"""
Simplified notification URL configuration
"""
from django.urls import path
from . import notification_views

urlpatterns = [
    path('my_notifications/', notification_views.my_notifications, name='my-notifications'),
    path('mark_read/<int:notification_id>/', notification_views.mark_notification_read, name='mark-notification-read'),
]
