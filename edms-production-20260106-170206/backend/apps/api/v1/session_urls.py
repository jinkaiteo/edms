"""
URL configuration for session-based authentication.
"""

from django.urls import path
from . import session_auth_views

app_name = 'session_auth'

urlpatterns = [
    path('csrf/', session_auth_views.get_csrf_token, name='csrf'),
    path('login/', session_auth_views.session_login, name='login'),
    path('user/', session_auth_views.current_user, name='user'),
    path('logout/', session_auth_views.session_logout, name='logout'),
]