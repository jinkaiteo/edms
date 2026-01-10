"""
API v1 URL Configuration.

Complete REST API endpoints with versioning, rate limiting,
and comprehensive documentation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework.documentation import include_docs_urls  # Temporarily disabled - missing coreapi dependency
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)
from apps.api.news_feed_views import my_documents, recent_notifications, system_status
from apps.api import dashboard_api_views
from apps.api.v1 import change_password_views, session_auth_views
# my_tasks import removed - using document filters instead
# task_views removed - using document filters instead

from .views import (
    # Core API views
    APIStatusView, APIInfoView, APIHealthView, DashboardStatsView,
    
    # Document management
    DocumentViewSet, DocumentTypeViewSet, DocumentVersionViewSet,
    
    # User management  
    UserViewSet, RoleViewSet, UserRoleViewSet,
    
    # Workflow management
    WorkflowViewSet, WorkflowInstanceViewSet,
    # WorkflowTaskViewSet removed - using document filters
    
    # Search functionality
    SearchViewSet, SavedSearchViewSet, SearchAnalyticsView,
    
    # Audit and compliance
    AuditTrailViewSet, ComplianceReportView,
    
    # Electronic signatures
    # ElectronicSignatureViewSet, CertificateViewSet,  # Temporarily disabled
    
    # Templates and placeholders
    DocumentTemplateViewSet, PlaceholderViewSet, DocumentGenerationViewSet,
    
    # Backup and system
    # BackupJobViewSet, HealthCheckViewSet, SystemMetricViewSet,  # Temporarily disabled
    
    # Settings and configuration
    # SystemConfigurationViewSet, UICustomizationViewSet, FeatureToggleViewSet,  # Temporarily disabled
)

# Import DocumentSourceViewSet directly from documents app
from apps.documents.views import DocumentSourceViewSet

# Import authentication views
from .auth_views import LoginView, LogoutView, CurrentUserView, CSRFTokenView, auth_status
from rest_framework_simplejwt.views import TokenObtainPairView

# Import notification views
# from .notification_views import NotificationViewSet  # Temporarily disabled

# Create router for ViewSets
router = DefaultRouter()

# Document management endpoints
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-types', DocumentTypeViewSet, basename='documenttype')
router.register(r'document-sources', DocumentSourceViewSet, basename='documentsource')
router.register(r'document-versions', DocumentVersionViewSet, basename='documentversion')

# User management endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

# Workflow management endpoints
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-instances', WorkflowInstanceViewSet, basename='workflowinstance')
# WorkflowTaskViewSet removed - using document filters instead

# Notification endpoints (temporarily disabled)
# router.register(r'notifications', NotificationViewSet, basename='notification')

# Search endpoints
router.register(r'search', SearchViewSet, basename='search')
router.register(r'saved-searches', SavedSearchViewSet, basename='savedsearch')

# Audit and compliance endpoints
router.register(r'audit-trail', AuditTrailViewSet, basename='audittrail')

# Electronic signatures endpoints (commented out due to import issues)
# router.register(r'electronic-signatures', ElectronicSignatureViewSet, basename='electronicsignature')
# router.register(r'certificates', CertificateViewSet, basename='certificate')

# Templates and placeholders endpoints
router.register(r'document-templates', DocumentTemplateViewSet, basename='documenttemplate')
router.register(r'placeholders', PlaceholderViewSet, basename='placeholder')
router.register(r'document-generations', DocumentGenerationViewSet, basename='documentgeneration')

# Backup and system endpoints (temporarily disabled)
# router.register(r'backup-jobs', BackupJobViewSet, basename='backupjob')
# router.register(r'health-checks', HealthCheckViewSet, basename='healthcheck')
# router.register(r'system-metrics', SystemMetricViewSet, basename='systemmetric')

# Settings and configuration endpoints (temporarily disabled)
# router.register(r'system-configurations', SystemConfigurationViewSet, basename='systemconfiguration')
# router.register(r'ui-customizations', UICustomizationViewSet, basename='uicustomization')
# router.register(r'feature-toggles', FeatureToggleViewSet, basename='featuretoggle')

# URL patterns
urlpatterns = [
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # path('docs-legacy/', include_docs_urls(title='EDMS API')),  # Temporarily disabled - missing coreapi dependency
    
    # API status and health
    path('status/', APIStatusView.as_view(), name='api-status'),
    path('info/', APIInfoView.as_view(), name='api-info'),
    path('health/', APIHealthView.as_view(), name='api-health'),
    path('dashboard/stats/', dashboard_api_views.get_dashboard_stats, name='dashboard-stats'),
    path('dashboard/activity/', dashboard_api_views.get_recent_activity, name='dashboard-activity'),
    path('dashboard/overview/', dashboard_api_views.get_dashboard_overview, name='dashboard-overview'),
    
    # Search analytics
    path('search/analytics/', SearchAnalyticsView.as_view(), name='search-analytics'),
    
    # Compliance reports
    path('compliance/reports/', ComplianceReportView.as_view(), name='compliance-reports'),
    
    # News feed endpoints (for dashboard)
    path('documents/my-documents/', my_documents, name='my-documents'),
    # my-tasks endpoint removed - using document filters instead 
    path('notifications/recent/', recent_notifications, name='recent-notifications'),
    path('scheduler/system-status/', system_status, name='system-status'),
    
    # Task endpoints removed - using document filters instead of separate task system
    
    # Authentication endpoints  
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/', TokenObtainPairView.as_view(), name='auth-token'),  # Proper JWT endpoint
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),  
    path('auth/user/', CurrentUserView.as_view(), name='auth-user'),  # Use existing CurrentUserView
    path('auth/profile/', CurrentUserView.as_view(), name='auth-profile'),
    path('auth/status/', auth_status, name='auth-status'),
    path('auth/csrf/', CSRFTokenView.as_view(), name='auth-csrf'),
    path('auth/api-change-password/', change_password_views.change_password, name='api-change-password'),
    path('auth/password-requirements/', change_password_views.password_requirements, name='api-password-requirements'),
    
    # Session-based authentication for frontend cookie sharing
    path('session/csrf/', session_auth_views.get_csrf_token, name='session-csrf'),
    path('session/login/', session_auth_views.session_login, name='session-login'),  
    path('session/user/', session_auth_views.current_user, name='session-user'),
    path('session/logout/', session_auth_views.session_logout, name='session-logout'),
    
    # Include router URLs
    path('', include(router.urls)),
]