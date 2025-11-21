"""
EDMS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API URL patterns
api_urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication
    path('auth/', include('apps.users.urls')),
    
    # Core modules
    path('documents/', include('apps.documents.urls')),
    path('workflows/', include('apps.workflows.urls')),
    path('audit/', include('apps.audit.urls')),
    
    # Service modules
    path('placeholders/', include('apps.placeholders.urls')),
    path('scheduler/', include('apps.scheduler.urls')),
    path('backup/', include('apps.backup.urls')),
    path('settings/', include('apps.settings.urls')),
]

# Main URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include(api_urlpatterns)),
    
    # Health check endpoint
    path('health/', include('apps.backup.urls', namespace='health')),
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