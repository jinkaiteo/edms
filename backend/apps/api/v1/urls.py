"""
API v1 URL Configuration.

Complete REST API endpoints with versioning, rate limiting,
and comprehensive documentation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)

from .views import (
    # Core API views
    APIStatusView, APIInfoView, APIHealthView,
    
    # Document management
    DocumentViewSet, DocumentTypeViewSet, DocumentVersionViewSet,
    
    # User management  
    UserViewSet, RoleViewSet, UserRoleViewSet,
    
    # Workflow management
    WorkflowViewSet, WorkflowInstanceViewSet, WorkflowTaskViewSet,
    
    # Search functionality
    SearchViewSet, SavedSearchViewSet, SearchAnalyticsView,
    
    # Audit and compliance
    AuditTrailViewSet, ComplianceReportView,
    
    # Electronic signatures
    ElectronicSignatureViewSet, CertificateViewSet,
    
    # Templates and placeholders
    DocumentTemplateViewSet, PlaceholderViewSet, DocumentGenerationViewSet,
    
    # Backup and system
    BackupJobViewSet, HealthCheckViewSet, SystemMetricViewSet,
    
    # Settings and configuration
    SystemConfigurationViewSet, UICustomizationViewSet, FeatureToggleViewSet,
)

# Create router for ViewSets
router = DefaultRouter()

# Document management endpoints
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-types', DocumentTypeViewSet, basename='documenttype')
router.register(r'document-versions', DocumentVersionViewSet, basename='documentversion')

# User management endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

# Workflow management endpoints
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-instances', WorkflowInstanceViewSet, basename='workflowinstance')
router.register(r'workflow-tasks', WorkflowTaskViewSet, basename='workflowtask')

# Search endpoints
router.register(r'search', SearchViewSet, basename='search')
router.register(r'saved-searches', SavedSearchViewSet, basename='savedsearch')

# Audit and compliance endpoints
router.register(r'audit-trail', AuditTrailViewSet, basename='audittrail')

# Electronic signatures endpoints
router.register(r'electronic-signatures', ElectronicSignatureViewSet, basename='electronicsignature')
router.register(r'certificates', CertificateViewSet, basename='certificate')

# Templates and placeholders endpoints
router.register(r'document-templates', DocumentTemplateViewSet, basename='documenttemplate')
router.register(r'placeholders', PlaceholderViewSet, basename='placeholder')
router.register(r'document-generations', DocumentGenerationViewSet, basename='documentgeneration')

# Backup and system endpoints
router.register(r'backup-jobs', BackupJobViewSet, basename='backupjob')
router.register(r'health-checks', HealthCheckViewSet, basename='healthcheck')
router.register(r'system-metrics', SystemMetricViewSet, basename='systemmetric')

# Settings and configuration endpoints
router.register(r'system-configurations', SystemConfigurationViewSet, basename='systemconfiguration')
router.register(r'ui-customizations', UICustomizationViewSet, basename='uicustomization')
router.register(r'feature-toggles', FeatureToggleViewSet, basename='featuretoggle')

# URL patterns
urlpatterns = [
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('docs-legacy/', include_docs_urls(title='EDMS API')),
    
    # API status and health
    path('status/', APIStatusView.as_view(), name='api-status'),
    path('info/', APIInfoView.as_view(), name='api-info'),
    path('health/', APIHealthView.as_view(), name='api-health'),
    
    # Search analytics
    path('search/analytics/', SearchAnalyticsView.as_view(), name='search-analytics'),
    
    # Compliance reports
    path('compliance/reports/', ComplianceReportView.as_view(), name='compliance-reports'),
    
    # Include router URLs
    path('', include(router.urls)),
]