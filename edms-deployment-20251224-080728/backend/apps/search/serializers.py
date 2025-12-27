"""
Search Serializers for EDMS Search API.

DRF serializers for search operations, analytics,
and search configuration management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    SearchIndex, SearchQuery, SearchResult, SavedSearch,
    SearchFacet, SearchSynonym, SearchConfiguration
)

User = get_user_model()


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for search requests."""
    
    query = serializers.CharField(
        max_length=1000,
        allow_blank=True,
        help_text="Search query text"
    )
    filters = serializers.JSONField(
        default=dict,
        required=False,
        help_text="Additional search filters"
    )
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Page number (1-based)"
    )
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="Number of results per page"
    )
    sort_by = serializers.ChoiceField(
        choices=[
            ('relevance', 'Relevance'),
            ('title', 'Title'),
            ('document_number', 'Document Number'),
            ('created_date', 'Created Date'),
            ('effective_date', 'Effective Date'),
            ('author', 'Author'),
            ('status', 'Status'),
            ('type', 'Document Type'),
        ],
        default='relevance'
    )


class DocumentResultSerializer(serializers.Serializer):
    """Serializer for document search results."""
    
    id = serializers.IntegerField()
    document_number = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    document_type = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    version = serializers.CharField()
    created_by = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    effective_date = serializers.DateTimeField(allow_null=True)
    relevance_score = serializers.FloatField()
    url = serializers.CharField()
    metadata = serializers.JSONField()


class SearchFacetValueSerializer(serializers.Serializer):
    """Serializer for search facet values."""
    
    value = serializers.CharField()
    label = serializers.CharField(required=False)
    count = serializers.IntegerField()
    selected = serializers.BooleanField()


class SearchFacetSerializer(serializers.Serializer):
    """Serializer for search facets."""
    
    display_name = serializers.CharField()
    type = serializers.CharField()
    values = SearchFacetValueSerializer(many=True)


class SearchResponseSerializer(serializers.Serializer):
    """Serializer for search responses."""
    
    query = serializers.CharField()
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    documents = DocumentResultSerializer(many=True)
    facets = serializers.DictField(child=SearchFacetSerializer())
    suggestions = serializers.ListField(child=serializers.CharField())
    response_time = serializers.FloatField()
    applied_filters = serializers.JSONField()
    error = serializers.CharField(required=False)


class AutocompleteRequestSerializer(serializers.Serializer):
    """Serializer for autocomplete requests."""
    
    query = serializers.CharField(
        max_length=200,
        min_length=1,
        help_text="Partial search query"
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum number of suggestions"
    )


class AutocompleteSuggestionSerializer(serializers.Serializer):
    """Serializer for autocomplete suggestions."""
    
    text = serializers.CharField()
    document_number = serializers.CharField(required=False)
    document_type = serializers.CharField(required=False)
    url = serializers.CharField(required=False)
    rank = serializers.FloatField(required=False)
    type = serializers.CharField(required=False)
    frequency = serializers.IntegerField(required=False)


class SavedSearchSerializer(serializers.ModelSerializer):
    """Serializer for SavedSearch model."""
    
    user = serializers.StringRelatedField(read_only=True)
    shared_with_users = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = SavedSearch
        fields = [
            'id', 'uuid', 'name', 'description', 'query_text', 'filters',
            'user', 'is_shared', 'shared_with_users', 'notification_type',
            'last_notification', 'usage_count', 'last_used',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'user', 'usage_count', 'last_used',
            'last_notification', 'created_at', 'updated_at'
        ]


class SavedSearchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating saved searches."""
    
    shared_with_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = SavedSearch
        fields = [
            'name', 'description', 'query_text', 'filters',
            'is_shared', 'shared_with_user_ids', 'notification_type'
        ]
    
    def create(self, validated_data):
        shared_user_ids = validated_data.pop('shared_with_user_ids', [])
        saved_search = super().create(validated_data)
        
        if shared_user_ids:
            shared_users = User.objects.filter(id__in=shared_user_ids)
            saved_search.shared_with_users.set(shared_users)
        
        return saved_search


class SearchAnalyticsRequestSerializer(serializers.Serializer):
    """Serializer for search analytics requests."""
    
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    user_id = serializers.IntegerField(required=False)


class SearchAnalyticsResponseSerializer(serializers.Serializer):
    """Serializer for search analytics responses."""
    
    period = serializers.DictField()
    summary = serializers.DictField()
    popular_queries = serializers.ListField()
    zero_result_queries = serializers.ListField()
    query_types = serializers.ListField()
    daily_volume = serializers.ListField()


class SearchFacetConfigSerializer(serializers.ModelSerializer):
    """Serializer for SearchFacet configuration."""
    
    class Meta:
        model = SearchFacet
        fields = [
            'id', 'uuid', 'name', 'display_name', 'description',
            'facet_type', 'field_name', 'field_path', 'sort_order',
            'is_enabled', 'show_count', 'allowed_values',
            'min_value', 'max_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class SearchSynonymSerializer(serializers.ModelSerializer):
    """Serializer for SearchSynonym model."""
    
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = SearchSynonym
        fields = [
            'id', 'uuid', 'primary_term', 'synonym_term',
            'synonym_type', 'is_bidirectional', 'context',
            'weight', 'is_active', 'usage_count',
            'created_at', 'created_by'
        ]
        read_only_fields = ['uuid', 'usage_count', 'created_at']


class SearchConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SearchConfiguration model."""
    
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = SearchConfiguration
        fields = [
            'id', 'uuid', 'name', 'description', 'default_operator',
            'fuzzy_matching', 'stemming_enabled', 'synonym_expansion',
            'default_page_size', 'max_page_size', 'max_results',
            'cache_duration', 'timeout_seconds', 'title_weight',
            'content_weight', 'metadata_weight', 'is_active',
            'version', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class SearchIndexSerializer(serializers.ModelSerializer):
    """Serializer for SearchIndex model."""
    
    document = serializers.StringRelatedField(read_only=True)
    is_stale = serializers.SerializerMethodField()
    
    class Meta:
        model = SearchIndex
        fields = [
            'id', 'uuid', 'document', 'index_type', 'language',
            'status', 'index_size', 'created_at', 'updated_at',
            'last_accessed', 'is_stale'
        ]
        read_only_fields = [
            'uuid', 'index_size', 'created_at', 'updated_at',
            'last_accessed'
        ]
    
    def get_is_stale(self, obj):
        """Check if index is stale compared to document."""
        if obj.document:
            return obj.updated_at < obj.document.updated_at
        return False


class SearchIndexUpdateSerializer(serializers.Serializer):
    """Serializer for search index update requests."""
    
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Specific document IDs to reindex"
    )
    force_update = serializers.BooleanField(
        default=False,
        help_text="Force update even if index is current"
    )
    index_type = serializers.ChoiceField(
        choices=[
            ('DOCUMENT', 'Document Index'),
            ('METADATA', 'Metadata Index'),
            ('CONTENT', 'Content Index'),
            ('COMBINED', 'Combined Index'),
        ],
        default='COMBINED'
    )


class SearchQueryLogSerializer(serializers.ModelSerializer):
    """Serializer for SearchQuery log entries."""
    
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = SearchQuery
        fields = [
            'id', 'uuid', 'query_type', 'query_text', 'processed_query',
            'filters', 'sort_criteria', 'result_count', 'response_time',
            'user', 'session_id', 'executed_at'
        ]
        read_only_fields = ['uuid', 'executed_at']


class SearchResultClickSerializer(serializers.Serializer):
    """Serializer for recording search result clicks."""
    
    query_id = serializers.UUIDField()
    document_id = serializers.IntegerField()
    rank = serializers.IntegerField()
    
    def validate(self, data):
        """Validate that query and document exist."""
        try:
            SearchQuery.objects.get(uuid=data['query_id'])
        except SearchQuery.DoesNotExist:
            raise serializers.ValidationError("Invalid query ID")
        
        try:
            from apps.documents.models import Document
            Document.objects.get(id=data['document_id'])
        except Document.DoesNotExist:
            raise serializers.ValidationError("Invalid document ID")
        
        return data


class BulkIndexingSerializer(serializers.Serializer):
    """Serializer for bulk indexing operations."""
    
    operation = serializers.ChoiceField(
        choices=[
            ('UPDATE_ALL', 'Update All Indices'),
            ('UPDATE_STALE', 'Update Stale Indices'),
            ('REBUILD_ALL', 'Rebuild All Indices'),
            ('DELETE_ORPHANED', 'Delete Orphaned Indices'),
        ]
    )
    batch_size = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000,
        help_text="Number of documents to process in each batch"
    )
    document_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Specific document types to process"
    )
    force_update = serializers.BooleanField(default=False)