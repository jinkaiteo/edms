"""
URL Configuration for Admin Pages

Provides simple HTML interfaces for admin functions accessible
through the frontend navigation submenu.
"""

from django.urls import path
from . import views, api_views

app_name = 'admin_pages'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('settings/', views.system_settings, name='system_settings'),
    path('audit/', views.audit_trail, name='audit_trail'),
    path('scheduler/', views.redirect_to_scheduler, name='scheduler_redirect'),
    # API endpoints
]