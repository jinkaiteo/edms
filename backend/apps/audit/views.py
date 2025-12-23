"""
API Views for Audit Trail
"""

from django.db.models import Q
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime, timedelta

from .models import AuditTrail, LoginAudit, ComplianceReport, UserSession
from .serializers import (
    AuditTrailSerializer, AuditTrailDetailSerializer,
    LoginAuditSerializer, ComplianceReportSerializer,
    UserSessionSerializer, CombinedAuditSerializer
)


class AuditTrailPagination(PageNumberPagination):
    """Custom pagination for audit trail"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AuditTrail model - Read only for compliance
    """
    queryset = AuditTrail.objects.all().select_related('user').order_by('-timestamp')
    serializer_class = AuditTrailSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditTrailPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filterable fields
    filterset_fields = {
        'action': ['exact', 'icontains'],
        'user__username': ['exact', 'icontains'],
        'timestamp': ['gte', 'lte', 'exact'],
    }
    
    # Searchable fields
    search_fields = ['action', 'description', 'user__username']
    
    # Ordering fields
    ordering_fields = ['timestamp', 'action', 'user__username']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        """Return detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return AuditTrailDetailSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def actions(self, request):
        """Get list of all available actions for filtering"""
        actions = AuditTrail.objects.values_list('action', flat=True).distinct()
        return Response(sorted(actions))

    @action(detail=False, methods=['get'])
    def object_types(self, request):
        """Get list of all object types for filtering"""
        object_types = AuditTrail.objects.values_list('object_type', flat=True).distinct()
        return Response(sorted(object_types))

    @action(detail=False, methods=['get'])
    def users(self, request):
        """Get list of users who have audit records"""
        users = AuditTrail.objects.select_related('user').values(
            'user__id', 'user__username', 'user__first_name', 'user__last_name'
        ).distinct()
        return Response(users)


class LoginAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for LoginAudit model - Read only for compliance
    """
    queryset = LoginAudit.objects.all().select_related('user').order_by('-timestamp')
    serializer_class = LoginAuditSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditTrailPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'username': ['exact', 'icontains'],
        'success': ['exact'],
        'timestamp': ['gte', 'lte', 'exact'],
        'ip_address': ['exact'],
        'user__username': ['exact', 'icontains'],
    }
    
    search_fields = ['username', 'failure_reason', 'user__username']
    ordering_fields = ['timestamp', 'username', 'success']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get login audit summary statistics"""
        total = self.get_queryset().count()
        successful = self.get_queryset().filter(success=True).count()
        failed = total - successful
        
        # Last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        recent_total = self.get_queryset().filter(timestamp__gte=last_24h).count()
        recent_successful = self.get_queryset().filter(
            timestamp__gte=last_24h, success=True
        ).count()
        recent_failed = recent_total - recent_successful
        
        return Response({
            'total_logins': total,
            'successful_logins': successful,
            'failed_logins': failed,
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
            'last_24_hours': {
                'total': recent_total,
                'successful': recent_successful,
                'failed': recent_failed,
            }
        })


class ComplianceReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ComplianceReport model - Supports generation and download
    """
    queryset = ComplianceReport.objects.all().select_related('generated_by').order_by('-generated_at')
    serializer_class = ComplianceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditTrailPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'report_type': ['exact'],
        'generated_by__username': ['exact', 'icontains'],
        'generated_at': ['gte', 'lte', 'exact'],
        'is_archived': ['exact'],
        'status': ['exact'],
    }
    
    search_fields = ['name', 'description', 'report_type']
    ordering_fields = ['generated_at', 'name', 'report_type']
    ordering = ['-generated_at']
    
    def create(self, request, *args, **kwargs):
        """Generate a new compliance report"""
        from .services import generate_compliance_report_sync
        
        # Extract parameters
        report_type = request.data.get('report_type')
        name = request.data.get('name')
        description = request.data.get('description', '')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        filters = request.data.get('filters', {})
        
        # Validate required fields
        if not report_type:
            return Response(
                {'error': 'report_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not name:
            return Response(
                {'error': 'name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not date_from or not date_to:
            return Response(
                {'error': 'date_from and date_to are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate the report
            report = generate_compliance_report_sync(
                user=request.user,
                report_type=report_type,
                name=name,
                description=description,
                date_from=date_from,
                date_to=date_to,
                filters=filters
            )
            
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a generated report as PDF"""
        from django.http import FileResponse, HttpResponse
        import os
        
        report = self.get_object()
        
        # Check if report is completed
        if report.status != 'COMPLETED':
            return Response(
                {'error': 'Report is not yet completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if file exists
        if not report.file_path or not os.path.exists(report.file_path):
            return Response(
                {'error': 'Report file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return the file
        try:
            file_handle = open(report.file_path, 'rb')
            response = FileResponse(file_handle, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.name}.pdf"'
            response['Content-Length'] = report.file_size
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to download report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for UserSession model - Read only
    """
    queryset = UserSession.objects.all().select_related('user').order_by('-login_timestamp')
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditTrailPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'user__username': ['exact', 'icontains'],
        'is_active': ['exact'],
        'login_timestamp': ['gte', 'lte', 'exact'],
        'logout_timestamp': ['gte', 'lte', 'exact'],
    }
    
    search_fields = ['user__username', 'logout_reason']
    ordering_fields = ['login_timestamp', 'logout_timestamp', 'user__username']
    ordering = ['-login_timestamp']


class CombinedAuditViewSet(viewsets.GenericViewSet):
    """
    Combined audit trail from multiple sources
    Provides a unified view of all audit activities
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditTrailPagination
    
    def list(self, request):
        """Get combined audit trail from all sources"""
        # Get query parameters
        search = request.query_params.get('search', '')
        action_filter = request.query_params.get('action', '')
        user_filter = request.query_params.get('user', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        
        # Build combined data
        combined_data = []
        
        # Get AuditTrail records
        audit_qs = AuditTrail.objects.select_related('user').all()
        
        # Apply filters to AuditTrail
        if search:
            audit_qs = audit_qs.filter(
                Q(description__icontains=search) |
                Q(action__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        if action_filter:
            audit_qs = audit_qs.filter(action__icontains=action_filter)
        
        if user_filter:
            audit_qs = audit_qs.filter(user__username__icontains=user_filter)
        
        if date_from:
            try:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                audit_qs = audit_qs.filter(timestamp__gte=date_from_parsed)
            except:
                pass
        
        if date_to:
            try:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                audit_qs = audit_qs.filter(timestamp__lte=date_to_parsed)
            except:
                pass
        
        # Convert AuditTrail to combined format
        for audit in audit_qs:
            combined_data.append({
                'id': audit.id,
                'uuid': str(audit.uuid),
                'audit_type': 'audit_trail',
                'user_display': audit.user.username if audit.user else audit.user_display_name or 'System',
                'action': audit.action,
                'description': audit.description,
                'timestamp': audit.timestamp,
                'ip_address': audit.ip_address,
                'user_agent': audit.user_agent,
                'success': None,
                'additional_data': audit.metadata,
            })
        
        # Get LoginAudit records
        login_qs = LoginAudit.objects.select_related('user').all()
        
        # Apply filters to LoginAudit
        if search:
            login_qs = login_qs.filter(
                Q(username__icontains=search) |
                Q(failure_reason__icontains=search)
            )
        
        # Always include login audits unless specifically filtering for non-login actions
        if action_filter and action_filter.upper() in ['DOCUMENT_DELETE', 'DOCUMENT_CREATE', 'DOCUMENT_UPDATE']:
            # Exclude login audits if specifically filtering for document actions
            login_qs = login_qs.none()
        
        if user_filter:
            login_qs = login_qs.filter(username__icontains=user_filter)
        
        if date_from:
            try:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                login_qs = login_qs.filter(timestamp__gte=date_from_parsed)
            except:
                pass
        
        if date_to:
            try:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                login_qs = login_qs.filter(timestamp__lte=date_to_parsed)
            except:
                pass
        
        # Convert LoginAudit to combined format
        for login in login_qs:
            combined_data.append({
                'id': login.id,
                'uuid': str(login.uuid),
                'audit_type': 'login_audit',
                'user_display': login.username,
                'action': 'LOGIN_SUCCESS' if login.success else 'LOGIN_FAILED',
                'description': f"{'Successful' if login.success else 'Failed'} login attempt" + 
                             (f": {login.failure_reason}" if login.failure_reason else ""),
                'timestamp': login.timestamp,
                'ip_address': login.ip_address or '',
                'user_agent': login.user_agent or '',
                'success': login.success,
                'additional_data': getattr(login, 'additional_data', None),
            })
        
        # Sort by timestamp (newest first)
        combined_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined_data, request)
        
        if page is not None:
            serializer = CombinedAuditSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CombinedAuditSerializer(combined_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get audit trail statistics"""
        audit_count = AuditTrail.objects.count()
        login_count = LoginAudit.objects.count()
        
        # Recent activity (last 24 hours)
        last_24h = timezone.now() - timedelta(hours=24)
        recent_audit = AuditTrail.objects.filter(timestamp__gte=last_24h).count()
        recent_login = LoginAudit.objects.filter(timestamp__gte=last_24h).count()
        
        return Response({
            'total_audit_records': audit_count,
            'total_login_records': login_count,
            'total_records': audit_count + login_count,
            'last_24_hours': {
                'audit_records': recent_audit,
                'login_records': recent_login,
                'total': recent_audit + recent_login,
            }
        })