"""
Serializers for Backup Management.

DRF serializers for backup models and API responses.
"""

from rest_framework import serializers
from .models import BackupConfiguration, BackupJob, RestoreJob, HealthCheck, SystemMetric, DisasterRecoveryPlan


class BackupConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for backup configurations."""
    
    class Meta:
        model = BackupConfiguration
        fields = [
            'uuid', 'name', 'description', 'backup_type', 'frequency',
            'schedule_time', 'schedule_days', 'retention_days', 'max_backups',
            'storage_path', 'compression_enabled', 'encryption_enabled',
            'status', 'is_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def validate_storage_path(self, value):
        """Validate storage path is accessible."""
        import os
        parent_dir = os.path.dirname(value)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except PermissionError:
                raise serializers.ValidationError(
                    f"Cannot create storage directory: {parent_dir}"
                )
        return value

    def validate_schedule_days(self, value):
        """Validate schedule days for weekly backups."""
        if value:
            for day in value:
                if not isinstance(day, int) or day < 0 or day > 6:
                    raise serializers.ValidationError(
                        "Schedule days must be integers between 0 (Monday) and 6 (Sunday)"
                    )
        return value


class BackupJobSerializer(serializers.ModelSerializer):
    """Serializer for backup jobs."""
    
    configuration_name = serializers.CharField(source='configuration.name', read_only=True)
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)
    file_size_human = serializers.SerializerMethodField()
    duration_human = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupJob
        fields = [
            'uuid', 'job_name', 'backup_type', 'started_at', 'completed_at',
            'duration', 'duration_human', 'status', 'backup_file_path',
            'backup_size', 'file_size_human', 'compression_ratio',
            'error_message', 'retry_count', 'max_retries', 'checksum',
            'is_valid', 'validation_errors', 'created_at',
            'configuration_name', 'triggered_by_username'
        ]
        read_only_fields = [
            'uuid', 'job_name', 'backup_type', 'started_at', 'completed_at',
            'duration', 'status', 'backup_file_path', 'backup_size',
            'compression_ratio', 'error_message', 'retry_count', 'max_retries',
            'checksum', 'is_valid', 'validation_errors', 'created_at'
        ]
    
    def get_file_size_human(self, obj):
        """Get human-readable file size."""
        if obj.backup_size:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if obj.backup_size < 1024.0:
                    return f"{obj.backup_size:.1f} {unit}"
                obj.backup_size /= 1024.0
            return f"{obj.backup_size:.1f} PB"
        return "Unknown"
    
    def get_duration_human(self, obj):
        """Get human-readable duration."""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Unknown"


class RestoreJobSerializer(serializers.ModelSerializer):
    """Serializer for restore jobs."""
    
    backup_job_name = serializers.CharField(source='backup_job.job_name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    duration_human = serializers.SerializerMethodField()
    
    class Meta:
        model = RestoreJob
        fields = [
            'uuid', 'restore_type', 'target_location', 'restore_options',
            'started_at', 'completed_at', 'duration', 'duration_human',
            'status', 'restored_items_count', 'failed_items_count',
            'error_message', 'restore_log', 'created_at',
            'backup_job_name', 'requested_by_username', 'approved_by_username'
        ]
        read_only_fields = [
            'uuid', 'started_at', 'completed_at', 'duration', 'status',
            'restored_items_count', 'failed_items_count', 'error_message',
            'restore_log', 'created_at'
        ]
    
    def get_duration_human(self, obj):
        """Get human-readable duration."""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Unknown"


class HealthCheckSerializer(serializers.ModelSerializer):
    """Serializer for health checks."""
    
    response_time_human = serializers.SerializerMethodField()
    checked_at_human = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthCheck
        fields = [
            'uuid', 'check_name', 'check_type', 'status', 'response_time',
            'response_time_human', 'message', 'details', 'metrics',
            'checked_at', 'checked_at_human'
        ]
        read_only_fields = '__all__'
    
    def get_response_time_human(self, obj):
        """Get human-readable response time."""
        if obj.response_time:
            if obj.response_time < 1:
                return f"{obj.response_time * 1000:.0f}ms"
            else:
                return f"{obj.response_time:.2f}s"
        return "Unknown"
    
    def get_checked_at_human(self, obj):
        """Get relative time since check."""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.checked_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer for system metrics."""
    
    value_human = serializers.SerializerMethodField()
    recorded_at_human = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemMetric
        fields = [
            'uuid', 'metric_name', 'metric_type', 'value', 'value_human',
            'unit', 'warning_threshold', 'critical_threshold', 'status',
            'metadata', 'recorded_at', 'recorded_at_human'
        ]
        read_only_fields = '__all__'
    
    def get_value_human(self, obj):
        """Get human-readable metric value."""
        if obj.unit:
            if obj.unit in ['B', 'bytes']:
                # Convert bytes to human readable
                value = obj.value
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if value < 1024.0:
                        return f"{value:.1f} {unit}"
                    value /= 1024.0
                return f"{value:.1f} PB"
            elif obj.unit == '%':
                return f"{obj.value:.1f}%"
            else:
                return f"{obj.value} {obj.unit}"
        return str(obj.value)
    
    def get_recorded_at_human(self, obj):
        """Get relative time since recorded."""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.recorded_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = diff.days
            return f"{days}d ago"


class DisasterRecoveryPlanSerializer(serializers.ModelSerializer):
    """Serializer for disaster recovery plans."""
    
    estimated_recovery_time_human = serializers.SerializerMethodField()
    last_tested_human = serializers.SerializerMethodField()
    
    class Meta:
        model = DisasterRecoveryPlan
        fields = [
            'uuid', 'name', 'description', 'disaster_type',
            'recovery_procedures', 'estimated_recovery_time',
            'estimated_recovery_time_human', 'required_resources',
            'responsible_team', 'emergency_contacts', 'status',
            'version', 'last_tested', 'last_tested_human',
            'test_results', 'next_test_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']
    
    def get_estimated_recovery_time_human(self, obj):
        """Get human-readable recovery time."""
        if obj.estimated_recovery_time:
            total_seconds = int(obj.estimated_recovery_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            elif minutes > 0:
                return f"{minutes}m"
            else:
                return f"{seconds}s"
        return "Unknown"
    
    def get_last_tested_human(self, obj):
        """Get relative time since last test."""
        if obj.last_tested:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            diff = now - obj.last_tested
            
            if diff < timedelta(days=1):
                return "Today"
            elif diff < timedelta(days=7):
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff < timedelta(days=30):
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months != 1 else ''} ago"
        return "Never"


# Additional serializers for API responses

class BackupSummarySerializer(serializers.Serializer):
    """Serializer for backup summary statistics."""
    
    total_backups = serializers.IntegerField()
    successful_backups = serializers.IntegerField()
    failed_backups = serializers.IntegerField()
    success_rate = serializers.FloatField()
    active_configurations = serializers.IntegerField()
    last_backup_date = serializers.DateTimeField(allow_null=True)
    total_backup_size = serializers.IntegerField()


class SystemStatusSerializer(serializers.Serializer):
    """Serializer for system status response."""
    
    status = serializers.ChoiceField(choices=['healthy', 'warning', 'critical', 'unknown'])
    statistics = BackupSummarySerializer()
    recent_backups = BackupJobSerializer(many=True)
    active_configurations = BackupConfigurationSerializer(many=True)
    recent_health_checks = HealthCheckSerializer(many=True)


class ExportPackageRequestSerializer(serializers.Serializer):
    """Serializer for export package creation request."""
    
    include_users = serializers.BooleanField(default=True)
    compress = serializers.BooleanField(default=True)
    encrypt = serializers.BooleanField(default=False)
    include_audit_trail = serializers.BooleanField(default=True)
    custom_options = serializers.JSONField(required=False)


class RestoreRequestSerializer(serializers.Serializer):
    """Serializer for restore operation request."""
    
    backup_job_id = serializers.UUIDField(required=False)
    restore_type = serializers.ChoiceField(
        choices=['FULL_RESTORE', 'DATABASE_RESTORE', 'FILES_RESTORE', 'SELECTIVE_RESTORE'],
        default='FULL_RESTORE'
    )
    target_location = serializers.CharField(default='/tmp/restore')
    force_restore = serializers.BooleanField(default=False)
    restore_options = serializers.JSONField(required=False)