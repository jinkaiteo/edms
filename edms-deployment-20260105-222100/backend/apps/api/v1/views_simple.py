"""
Simplified API v1 Views for testing integration.
Only includes implemented models and basic functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings

from apps.documents.models import Document, DocumentType, DocumentVersion
from apps.users.models import User, Role, UserRole
from apps.audit.models import AuditTrail


class APIStatusView(APIView):
    """API status endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'environment': getattr(settings, 'ENVIRONMENT', 'development')
        })


class APIInfoView(APIView):
    """API information endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'name': 'EDMS API',
            'version': '1.0.0',
            'description': '21 CFR Part 11 Compliant Electronic Document Management System',
            'endpoints': {
                'documents': '/api/v1/documents/',
                'users': '/api/v1/users/',
                'audit': '/api/v1/audit-trail/',
                'status': '/api/v1/status/',
            }
        })


class SimpleDocumentViewSet(viewsets.ModelViewSet):
    """Simple document management viewset."""
    queryset = Document.objects.all()
    permission_classes = [permissions.AllowAny]  # Temporarily for testing
    
    def get_serializer_class(self):
        # Simple inline serializer for now
        from rest_framework import serializers
        
        class SimpleDocumentSerializer(serializers.ModelSerializer):
            class Meta:
                model = Document
                fields = ['uuid', 'title', 'document_type', 'current_version', 'status', 'created_at', 'created_by']
                read_only_fields = ['uuid', 'created_at', 'created_by']
        
        return SimpleDocumentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SimpleUserViewSet(viewsets.ModelViewSet):
    """Simple user management viewset."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]  # Temporarily for testing
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class SimpleUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['uuid', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
                read_only_fields = ['uuid', 'date_joined']
        
        return SimpleUserSerializer


class SimpleAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """Simple audit trail viewset."""
    queryset = AuditTrail.objects.all()
    permission_classes = [permissions.AllowAny]  # Temporarily for testing
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class SimpleAuditSerializer(serializers.ModelSerializer):
            class Meta:
                model = AuditTrail
                fields = ['uuid', 'timestamp', 'action', 'table_name', 'record_id', 'user', 'ip_address']
                read_only_fields = ['uuid', 'timestamp']
        
        return SimpleAuditSerializer