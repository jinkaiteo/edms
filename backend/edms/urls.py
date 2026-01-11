"""
EDMS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.api.dashboard_stats import DashboardStatsView

# API URL patterns
api_urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication endpoints
    # Note: We don't include apps.users.urls here to avoid conflicts with apps.api.v1.urls
    # apps.api.v1.urls contains all auth endpoints including JWT token endpoints
    path('', include('apps.api.v1.urls')),  # All auth endpoints: auth/login/, auth/token/, auth/logout/, etc.
    path('session/', include('apps.api.v1.session_urls')),  # Session auth endpoints
    
    # User management - Removed duplicate registration
    # UserViewSet is already registered in apps.api.v1.urls.py at /api/v1/users/
    # This prevented /users/{id}/assign_role/ and other actions from working
    # path('users/', include(('apps.users.urls', 'users-api'), namespace='users-api')),
    
    # Dashboard statistics
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Core modules
    path('documents/', include('apps.documents.urls')),
    path('workflows/', include('apps.workflows.urls')),
    path('workflows/', include('apps.workflows.urls_enhanced')),
    path('audit/', include('apps.audit.urls')),
    
    # Notification endpoints
    path('notifications/', include('apps.api.v1.notification_urls')),
    
    # Service modules
    path('placeholders/', include('apps.placeholders.urls')),
    path('scheduler/', include('apps.scheduler.urls')),
    path('settings/', include('apps.settings.urls')),
    path('security/', include('apps.security.urls')),
]

# Main URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', include('apps.admin_pages.urls')),  # Custom admin pages
    path('admin/scheduler/', include('apps.scheduler.urls')),  # Scheduler monitoring
    path('admin/django/', admin.site.urls),  # Django admin (moved to /admin/django/)
    
    # API v1
    path('api/v1/', include(api_urlpatterns)),
    
    # Health check endpoint (unauthenticated)
    path('health/', include('edms.health_urls')),
    
    # Handle favicon.ico requests to prevent 404 errors
    path('favicon.ico', lambda request: HttpResponse(status=204)),  # No Content
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom admin site configuration
admin.site.site_header = 'EDMS Administration'
admin.site.site_title = 'EDMS Admin'
admin.site.index_title = 'Electronic Document Management System'