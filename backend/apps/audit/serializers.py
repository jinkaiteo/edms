"""
Serializers for Audit Trail API
"""

from rest_framework import serializers
from .models import AuditTrail, LoginAudit, ComplianceReport, UserSession
from apps.users.serializers import UserSerializer


class AuditTrailSerializer(serializers.ModelSerializer):
    """Serializer for AuditTrail model"""
    user_display = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditTrail
        fields = [
            'id', 'uuid', 'user', 'user_display', 'user_full_name',
            'action', 'description', 'timestamp'
        ]
        read_only_fields = ['id', 'uuid', 'timestamp']


class LoginAuditSerializer(serializers.ModelSerializer):
    """Serializer for LoginAudit model"""
    user_display = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = LoginAudit
        fields = [
            'id', 'uuid', 'user', 'user_display', 'username', 'success',
            'timestamp', 'ip_address', 'user_agent', 'session_id',
            'failure_reason', 'additional_data'
        ]
        read_only_fields = ['id', 'uuid', 'timestamp']


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceReport model"""
    generated_by_display = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'uuid', 'report_type', 'title', 'description',
            'date_from', 'date_to', 'generated_by', 'generated_by_display',
            'generated_at', 'file_path', 'file_size', 'checksum',
            'is_archived', 'archived_at'
        ]
        read_only_fields = ['id', 'uuid', 'generated_at', 'file_size', 'checksum']


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model"""
    user_display = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'uuid', 'user', 'user_display', 'session_key',
            'login_timestamp', 'logout_timestamp', 'is_active',
            'ip_address', 'user_agent', 'logout_reason'
        ]
        read_only_fields = ['id', 'uuid', 'login_timestamp']


class AuditTrailDetailSerializer(AuditTrailSerializer):
    """Detailed serializer for AuditTrail with user information"""
    user = UserSerializer(read_only=True)
    
    class Meta(AuditTrailSerializer.Meta):
        fields = AuditTrailSerializer.Meta.fields


class CombinedAuditSerializer(serializers.Serializer):
    """Combined audit data from multiple sources"""
    id = serializers.IntegerField()
    uuid = serializers.CharField()
    audit_type = serializers.CharField()  # 'audit_trail' or 'login_audit'
    user_display = serializers.CharField()
    action = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.CharField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)
    success = serializers.BooleanField(allow_null=True)
    additional_data = serializers.JSONField(allow_null=True)