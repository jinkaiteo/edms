"""
Serializers for Placeholder Management.

DRF serializers for template processing, placeholder management,
and document generation APIs.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    PlaceholderDefinition, DocumentTemplate, TemplatePlaceholder,
    DocumentGeneration, PlaceholderCache
)
from apps.users.serializers import UserSerializer

User = get_user_model()


class PlaceholderDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for PlaceholderDefinition model."""
    
    created_by = UserSerializer(read_only=True)
    template_syntax = serializers.CharField(source='get_template_syntax', read_only=True)
    
    class Meta:
        model = PlaceholderDefinition
        fields = [
            'id', 'uuid', 'name', 'display_name', 'description',
            'placeholder_type', 'data_source', 'source_field',
            'format_string', 'date_format', 'default_value',
            'validation_rules', 'is_active', 'requires_permission',
            'cache_duration', 'created_at', 'updated_at',
            'created_by', 'template_syntax'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'template_syntax']
    
    def validate_name(self, value):
        """Validate placeholder name format."""
        if not value.isupper():
            raise serializers.ValidationError("Placeholder name must be uppercase")
        if not all(c.isalnum() or c == '_' for c in value):
            raise serializers.ValidationError("Placeholder name can only contain letters, numbers, and underscores")
        return value


class TemplatePlaceholderSerializer(serializers.ModelSerializer):
    """Serializer for TemplatePlaceholder relationship."""
    
    placeholder = PlaceholderDefinitionSerializer(read_only=True)
    placeholder_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TemplatePlaceholder
        fields = [
            'id', 'uuid', 'placeholder', 'placeholder_id',
            'is_required', 'default_value', 'validation_rules',
            'order', 'format_override', 'created_at'
        ]
        read_only_fields = ['uuid', 'created_at']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DocumentTemplate model."""
    
    created_by = UserSerializer(read_only=True)
    placeholders_count = serializers.SerializerMethodField()
    usage_statistics = serializers.SerializerMethodField()
    template_placeholders = TemplatePlaceholderSerializer(many=True, read_only=True)
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'uuid', 'name', 'description', 'template_type',
            'file_path', 'output_filename_pattern', 'processing_rules',
            'version', 'status', 'is_default', 'usage_count',
            'last_used', 'created_at', 'updated_at', 'created_by',
            'placeholders_count', 'usage_statistics', 'template_placeholders'
        ]
        read_only_fields = ['uuid', 'usage_count', 'last_used', 'created_at', 'updated_at']
    
    def get_placeholders_count(self, obj):
        """Get count of placeholders in this template."""
        return obj.placeholders.count()
    
    def get_usage_statistics(self, obj):
        """Get usage statistics for this template."""
        return {
            'total_generations': obj.generations.count(),
            'successful_generations': obj.generations.filter(status='COMPLETED').count(),
            'failed_generations': obj.generations.filter(status='FAILED').count(),
            'last_used': obj.last_used
        }


class DocumentGenerationSerializer(serializers.ModelSerializer):
    """Serializer for DocumentGeneration model."""
    
    template = DocumentTemplateSerializer(read_only=True)
    requested_by = UserSerializer(read_only=True)
    processing_time_seconds = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentGeneration
        fields = [
            'id', 'uuid', 'template', 'source_document', 'output_format',
            'context_data', 'generation_options', 'status', 'output_file_path',
            'output_filename', 'file_size', 'file_size_mb', 'file_checksum',
            'started_at', 'completed_at', 'processing_time', 'processing_time_seconds',
            'error_message', 'requested_by', 'created_at'
        ]
        read_only_fields = [
            'uuid', 'status', 'output_file_path', 'output_filename',
            'file_size', 'file_checksum', 'started_at', 'completed_at',
            'processing_time', 'error_message', 'created_at'
        ]
    
    def get_processing_time_seconds(self, obj):
        """Get processing time in seconds."""
        if obj.processing_time:
            return obj.processing_time.total_seconds()
        return None
    
    def get_file_size_mb(self, obj):
        """Get file size in megabytes."""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None


# Action-specific serializers

class DocumentGenerationRequestSerializer(serializers.Serializer):
    """Serializer for document generation requests."""
    
    template_id = serializers.IntegerField()
    output_format = serializers.ChoiceField(
        choices=['DOCX', 'PDF', 'HTML', 'TEXT'],
        required=False
    )
    context_data = serializers.JSONField(default=dict)
    generation_options = serializers.JSONField(default=dict)
    
    def validate_template_id(self, value):
        """Validate template exists and is active."""
        try:
            template = DocumentTemplate.objects.get(id=value, status='ACTIVE')
            return value
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found or inactive")


class PlaceholderValidationSerializer(serializers.Serializer):
    """Serializer for placeholder validation."""
    
    placeholder_name = serializers.CharField(max_length=100)
    placeholder_value = serializers.CharField(allow_blank=True)
    context_data = serializers.JSONField(default=dict)
    
    def validate_placeholder_name(self, value):
        """Validate placeholder exists."""
        try:
            PlaceholderDefinition.objects.get(name=value.upper(), is_active=True)
            return value.upper()
        except PlaceholderDefinition.DoesNotExist:
            raise serializers.ValidationError("Placeholder not found")


class TemplatePreviewSerializer(serializers.Serializer):
    """Serializer for template preview generation."""
    
    template_id = serializers.IntegerField()
    sample_data = serializers.JSONField(default=dict)
    include_placeholders = serializers.BooleanField(default=True)
    
    def validate_template_id(self, value):
        """Validate template exists."""
        try:
            DocumentTemplate.objects.get(id=value)
            return value
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found")


class PlaceholderBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk placeholder updates."""
    
    placeholder_updates = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_placeholder_updates(self, value):
        """Validate placeholder update data."""
        for update in value:
            if 'id' not in update:
                raise serializers.ValidationError("Each update must include 'id' field")
            
            # Validate placeholder exists
            try:
                PlaceholderDefinition.objects.get(id=update['id'])
            except PlaceholderDefinition.DoesNotExist:
                raise serializers.ValidationError(f"Placeholder with id {update['id']} not found")
        
        return value


class TemplateBulkAssignSerializer(serializers.Serializer):
    """Serializer for bulk template placeholder assignment."""
    
    template_id = serializers.IntegerField()
    placeholder_assignments = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_template_id(self, value):
        """Validate template exists."""
        try:
            DocumentTemplate.objects.get(id=value)
            return value
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found")
    
    def validate_placeholder_assignments(self, value):
        """Validate placeholder assignment data."""
        for assignment in value:
            if 'placeholder_id' not in assignment:
                raise serializers.ValidationError("Each assignment must include 'placeholder_id' field")
            
            # Validate placeholder exists
            try:
                PlaceholderDefinition.objects.get(id=assignment['placeholder_id'])
            except PlaceholderDefinition.DoesNotExist:
                raise serializers.ValidationError(f"Placeholder with id {assignment['placeholder_id']} not found")
        
        return value


class PlaceholderCacheSerializer(serializers.ModelSerializer):
    """Serializer for PlaceholderCache model."""
    
    placeholder = PlaceholderDefinitionSerializer(read_only=True)
    is_expired = serializers.BooleanField(source='is_expired', read_only=True)
    
    class Meta:
        model = PlaceholderCache
        fields = [
            'id', 'uuid', 'placeholder', 'cache_key', 'cached_value',
            'context_hash', 'created_at', 'expires_at', 'hit_count',
            'is_expired'
        ]
        read_only_fields = ['uuid', 'created_at', 'hit_count']


class PlaceholderUsageStatsSerializer(serializers.Serializer):
    """Serializer for placeholder usage statistics."""
    
    placeholder_id = serializers.IntegerField()
    placeholder_name = serializers.CharField()
    usage_count = serializers.IntegerField()
    template_count = serializers.IntegerField()
    last_used = serializers.DateTimeField(allow_null=True)
    cache_hit_rate = serializers.FloatField()
    average_resolution_time = serializers.FloatField()


class TemplateUsageStatsSerializer(serializers.Serializer):
    """Serializer for template usage statistics."""
    
    template_id = serializers.IntegerField()
    template_name = serializers.CharField()
    total_generations = serializers.IntegerField()
    successful_generations = serializers.IntegerField()
    failed_generations = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_generation_time = serializers.FloatField()
    last_used = serializers.DateTimeField(allow_null=True)


class SystemStatsSerializer(serializers.Serializer):
    """Serializer for system-wide placeholder statistics."""
    
    total_placeholders = serializers.IntegerField()
    active_placeholders = serializers.IntegerField()
    total_templates = serializers.IntegerField()
    active_templates = serializers.IntegerField()
    total_generations = serializers.IntegerField()
    successful_generations = serializers.IntegerField()
    failed_generations = serializers.IntegerField()
    cache_entries = serializers.IntegerField()
    cache_hit_rate = serializers.FloatField()
    most_used_placeholders = PlaceholderUsageStatsSerializer(many=True)
    most_used_templates = TemplateUsageStatsSerializer(many=True)