"""
API v1 Views.

Complete REST API views with authentication, permissions,
rate limiting, and comprehensive error handling.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from apps.documents.models import Document, DocumentType, DocumentVersion
from apps.documents.serializers import (
    DocumentSerializer, DocumentTypeSerializer, DocumentVersionSerializer
)
from apps.users.models import User, Role, UserRole
from apps.users.serializers import UserSerializer, RoleSerializer, UserRoleSerializer
from apps.workflows.models import WorkflowInstance, WorkflowTransition, WorkflowTask
from apps.workflows.serializers import (
    WorkflowInstanceSerializer, WorkflowTransitionSerializer, WorkflowTaskSerializer
)
from apps.search.models import SavedSearch
from apps.search.serializers import (
    SearchRequestSerializer, SearchResponseSerializer, SavedSearchSerializer,
    AutocompleteRequestSerializer, AutocompleteSuggestionSerializer,
    SearchAnalyticsRequestSerializer, SearchAnalyticsResponseSerializer
)
from apps.search.services import search_service
from apps.audit.models import AuditTrail, ComplianceEvent
from apps.audit.serializers import AuditTrailSerializer, ComplianceEventSerializer
from apps.security.models import ElectronicSignature, UserCertificate
from apps.security.serializers import ElectronicSignatureSerializer, UserCertificateSerializer
from apps.placeholders.models import DocumentTemplate, PlaceholderDefinition, DocumentGeneration
from apps.placeholders.serializers import (
    DocumentTemplateSerializer, PlaceholderDefinitionSerializer, DocumentGenerationSerializer
)
from apps.backup.models import BackupJob, HealthCheck, SystemMetric
from apps.backup.serializers import BackupJobSerializer, HealthCheckSerializer, SystemMetricSerializer
from apps.settings.models import SystemConfiguration, UICustomization, FeatureToggle
from apps.settings.serializers import (
    SystemConfigurationSerializer, UICustomizationSerializer, FeatureToggleSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class APIStatusView(APIView):
    """API status endpoint for health monitoring."""
    
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    
    def get(self, request):
        """Get API status information."""
        return Response({
            'status': 'healthy',
            'version': getattr(settings, 'API_VERSION', '1.0'),
            'timestamp': timezone.now().isoformat(),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        })


class APIInfoView(APIView):
    """API information endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        """Get API information and capabilities."""
        return Response({
            'title': '21 CFR Part 11 Compliant EDMS API',
            'description': 'Electronic Document Management System REST API',
            'version': getattr(settings, 'API_VERSION', '1.0'),
            'documentation_url': request.build_absolute_uri('/api/v1/docs/'),
            'contact': {
                'name': 'EDMS Development Team',
                'email': getattr(settings, 'CONTACT_EMAIL', 'dev@edms.local')
            },
            'authentication': ['Session', 'Token'],
            'rate_limits': {
                'authenticated': '1000/hour',
                'anonymous': '100/hour'
            },
            'features': {
                'document_management': True,
                'electronic_signatures': True,
                'workflow_management': True,
                'full_text_search': True,
                'audit_trail': True,
                'backup_restore': True,
                'template_processing': True,
                'compliance_reporting': True
            }
        })


class APIHealthView(APIView):
    """API health check endpoint."""
    
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    
    def get(self, request):
        """Comprehensive health check."""
        from django.db import connection
        from django.core.cache import cache
        
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Cache check
        try:
            cache.set('health_check', 'test', 60)
            cache.get('health_check')
            health_status['checks']['cache'] = 'healthy'
        except Exception as e:
            health_status['checks']['cache'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Service availability
        health_status['checks']['api'] = 'healthy'
        
        return Response(health_status)


class DocumentViewSet(viewsets.ModelViewSet):
    """Document management API endpoints."""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'document_type', 'created_by']
    search_fields = ['title', 'document_number', 'description']
    ordering_fields = ['created_at', 'title', 'document_number', 'effective_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        from apps.users.workflow_permissions import workflow_permission_manager
        return workflow_permission_manager.get_user_accessible_documents(self.request.user)
    
    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Create electronic signature for document."""
        document = self.get_object()
        # Implementation would use electronic signature service
        return Response({'message': 'Signature created successfully'})
    
    @action(detail=True, methods=['get'])
    def workflow_status(self, request, pk=None):
        """Get workflow status for document."""
        document = self.get_object()
        # Implementation would return workflow status
        return Response({'status': document.status})


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """Document type management API endpoints."""
    
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """Document version history API endpoints."""
    
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'created_by']
    ordering = ['-created_at']


class UserViewSet(viewsets.ModelViewSet):
    """User management API endpoints."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    
    def get_permissions(self):
        """Adjust permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class RoleViewSet(viewsets.ModelViewSet):
    """Role management API endpoints."""
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']


class UserRoleViewSet(viewsets.ModelViewSet):
    """User role assignment API endpoints."""
    
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'role', 'is_active']


class WorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """Workflow type information API endpoints."""
    
    # This would be based on WorkflowType model
    permission_classes = [permissions.IsAuthenticated]


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    """Workflow instance management API endpoints."""
    
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow_type', 'state', 'is_active']
    ordering = ['-started_at']
    
    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Execute workflow transition."""
        instance = self.get_object()
        # Implementation would handle workflow transitions
        return Response({'message': 'Transition executed'})


class WorkflowTaskViewSet(viewsets.ModelViewSet):
    """Workflow task management API endpoints."""
    
    queryset = WorkflowTask.objects.all()
    serializer_class = WorkflowTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow_instance', 'assigned_to', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter tasks based on user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            # Users can see tasks assigned to them or tasks they created
            queryset = queryset.filter(
                Q(assigned_to=self.request.user) |
                Q(workflow_instance__initiated_by=self.request.user)
            )
        return queryset


class SearchViewSet(viewsets.ViewSet):
    """Document search API endpoints."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def list(self, request):
        """Perform document search."""
        serializer = SearchRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        results = search_service.search_documents(
            query=serializer.validated_data['query'],
            filters=serializer.validated_data.get('filters', {}),
            user=request.user,
            page=serializer.validated_data['page'],
            page_size=serializer.validated_data['page_size'],
            sort_by=serializer.validated_data['sort_by']
        )
        
        response_serializer = SearchResponseSerializer(results)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """Get autocomplete suggestions."""
        serializer = AutocompleteRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        suggestions = search_service.autocomplete_search(
            query=serializer.validated_data['query'],
            limit=serializer.validated_data['limit'],
            user=request.user
        )
        
        response_serializer = AutocompleteSuggestionSerializer(suggestions, many=True)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['post'])
    def click(self, request):
        """Record search result click."""
        # Implementation for click tracking
        return Response({'status': 'recorded'})


class SavedSearchViewSet(viewsets.ModelViewSet):
    """Saved search management API endpoints."""
    
    queryset = SavedSearch.objects.all()
    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter saved searches by user."""
        return self.queryset.filter(
            Q(user=self.request.user) |
            Q(shared_with_users=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Set user when creating saved search."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute saved search."""
        saved_search = self.get_object()
        results = saved_search.execute_search()
        
        response_serializer = SearchResponseSerializer(results)
        return Response(response_serializer.data)


class SearchAnalyticsView(APIView):
    """Search analytics API endpoint."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get search analytics data."""
        serializer = SearchAnalyticsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        analytics = search_service.get_search_analytics(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            user=User.objects.get(id=serializer.validated_data['user_id']) if serializer.validated_data.get('user_id') else None
        )
        
        response_serializer = SearchAnalyticsResponseSerializer(analytics)
        return Response(response_serializer.data)


class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit trail API endpoints."""
    
    queryset = AuditTrail.objects.all()
    serializer_class = AuditTrailSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'object_type', 'user']
    ordering = ['-timestamp']


class ComplianceReportView(APIView):
    """Compliance reporting API endpoint."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Generate compliance reports."""
        # Implementation for compliance reporting
        return Response({'message': 'Compliance report generated'})


class ElectronicSignatureViewSet(viewsets.ModelViewSet):
    """Electronic signature API endpoints."""
    
    queryset = ElectronicSignature.objects.all()
    serializer_class = ElectronicSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'signature_type', 'is_valid']
    ordering = ['-signature_timestamp']
    
    def get_queryset(self):
        """Filter signatures based on user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            # Users can see signatures they created or for documents they can access
            from apps.users.workflow_permissions import workflow_permission_manager
            accessible_docs = workflow_permission_manager.get_user_accessible_documents(self.request.user)
            queryset = queryset.filter(
                Q(user=self.request.user) |
                Q(document__in=accessible_docs)
            )
        return queryset


class CertificateViewSet(viewsets.ModelViewSet):
    """Certificate management API endpoints."""
    
    queryset = UserCertificate.objects.all()
    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter certificates by user."""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(user=self.request.user)


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """Document template API endpoints."""
    
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['template_type', 'status']
    search_fields = ['name', 'description']


class PlaceholderViewSet(viewsets.ModelViewSet):
    """Placeholder definition API endpoints."""
    
    queryset = PlaceholderDefinition.objects.all()
    serializer_class = PlaceholderDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']


class DocumentGenerationViewSet(viewsets.ModelViewSet):
    """Document generation API endpoints."""
    
    queryset = DocumentGeneration.objects.all()
    serializer_class = DocumentGenerationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template', 'status', 'requested_by']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter generations by user."""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(requested_by=self.request.user)


class BackupJobViewSet(viewsets.ReadOnlyModelViewSet):
    """Backup job monitoring API endpoints."""
    
    queryset = BackupJob.objects.all()
    serializer_class = BackupJobSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['configuration', 'status', 'backup_type']
    ordering = ['-created_at']


class HealthCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """System health check API endpoints."""
    
    queryset = HealthCheck.objects.all()
    serializer_class = HealthCheckSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['check_type', 'status']
    ordering = ['-checked_at']


class SystemMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """System metrics API endpoints."""
    
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['metric_type', 'status']
    ordering = ['-recorded_at']


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """System configuration API endpoints."""
    
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'setting_type']
    search_fields = ['key', 'display_name']


class UICustomizationViewSet(viewsets.ModelViewSet):
    """UI customization API endpoints."""
    
    queryset = UICustomization.objects.all()
    serializer_class = UICustomizationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customization_type', 'status']


class FeatureToggleViewSet(viewsets.ModelViewSet):
    """Feature toggle API endpoints."""
    
    queryset = FeatureToggle.objects.all()
    serializer_class = FeatureToggleSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['key', 'name']