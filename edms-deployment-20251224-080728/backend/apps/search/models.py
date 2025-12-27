"""
Search Models for EDMS Search Module.

Models for search indexing, query logging, and search analytics
with PostgreSQL full-text search capabilities.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class SearchIndex(models.Model):
    """
    Search Index model for document search indexing.
    
    Stores pre-computed search vectors and metadata
    for fast full-text search operations.
    """
    
    INDEX_TYPES = [
        ('DOCUMENT', 'Document Index'),
        ('METADATA', 'Metadata Index'),
        ('CONTENT', 'Content Index'),
        ('COMBINED', 'Combined Index'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('UPDATING', 'Updating'),
        ('STALE', 'Stale'),
        ('ERROR', 'Error'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Document reference
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='search_indices'
    )
    
    # Index configuration
    index_type = models.CharField(max_length=20, choices=INDEX_TYPES)
    language = models.CharField(max_length=10, default='english')
    
    # Search vectors
    search_vector = SearchVectorField(null=True, blank=True)
    metadata_vector = SearchVectorField(null=True, blank=True)
    content_vector = SearchVectorField(null=True, blank=True)
    
    # Index content and metadata
    indexed_content = models.TextField(
        blank=True,
        help_text="Preprocessed content for search indexing"
    )
    indexed_metadata = models.JSONField(
        default=dict,
        help_text="Preprocessed metadata for search"
    )
    
    # Status and performance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    index_size = models.PositiveIntegerField(
        default=0,
        help_text="Size of indexed content in characters"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = "search"
        db_table = 'search_indices'
        verbose_name = _('Search Index')
        verbose_name_plural = _('Search Indices')
        ordering = ['-updated_at']
        indexes = [
            GinIndex(fields=['search_vector']),
            GinIndex(fields=['metadata_vector']),
            GinIndex(fields=['content_vector']),
            models.Index(fields=['document', 'index_type']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'index_type'],
                name='unique_document_index_type'
            ),
        ]
    
    def __str__(self):
        return f"Index for {self.document.document_number} ({self.index_type})"
    
    def mark_accessed(self):
        """Mark index as accessed for usage tracking."""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])


class SearchQuery(models.Model):
    """
    Search Query model for search analytics and logging.
    
    Tracks user search queries for analytics, optimization,
    and audit purposes.
    """
    
    QUERY_TYPES = [
        ('SIMPLE', 'Simple Text Search'),
        ('ADVANCED', 'Advanced Search'),
        ('FILTER', 'Filtered Search'),
        ('FACETED', 'Faceted Search'),
        ('AUTOCOMPLETE', 'Autocomplete'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Query details
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES)
    query_text = models.TextField(
        help_text="Original search query"
    )
    processed_query = models.TextField(
        blank=True,
        help_text="Processed/normalized query"
    )
    
    # Search parameters
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Applied search filters"
    )
    sort_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="Sort criteria used"
    )
    
    # Results and performance
    result_count = models.PositiveIntegerField(default=0)
    response_time = models.FloatField(
        null=True, blank=True,
        help_text="Query response time in seconds"
    )
    
    # User context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='search_queries'
    )
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Metadata
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "search"
        db_table = 'search_queries'
        verbose_name = _('Search Query')
        verbose_name_plural = _('Search Queries')
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['query_type', 'executed_at']),
            models.Index(fields=['user', 'executed_at']),
            models.Index(fields=['result_count']),
            models.Index(fields=['response_time']),
        ]
    
    def __str__(self):
        return f"Search: '{self.query_text[:50]}' by {self.user}"


class SearchResult(models.Model):
    """
    Search Result model for tracking individual search results.
    
    Records which documents were returned for specific queries
    for relevance analysis and improvement.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Query reference
    query = models.ForeignKey(
        SearchQuery,
        on_delete=models.CASCADE,
        related_name='results'
    )
    
    # Result details
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='search_results'
    )
    rank = models.PositiveIntegerField(
        help_text="Result ranking position"
    )
    relevance_score = models.FloatField(
        null=True, blank=True,
        help_text="Search relevance score"
    )
    
    # User interaction
    clicked = models.BooleanField(
        default=False,
        help_text="Whether user clicked on this result"
    )
    click_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "search"
        db_table = 'search_results'
        verbose_name = _('Search Result')
        verbose_name_plural = _('Search Results')
        ordering = ['query', 'rank']
        indexes = [
            models.Index(fields=['query', 'rank']),
            models.Index(fields=['document']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['clicked']),
        ]
    
    def __str__(self):
        return f"Result {self.rank} for query {self.query.id}"
    
    def record_click(self):
        """Record that user clicked on this result."""
        self.clicked = True
        self.click_timestamp = timezone.now()
        self.save(update_fields=['clicked', 'click_timestamp'])


class SavedSearch(models.Model):
    """
    Saved Search model for user search preferences.
    
    Allows users to save frequently used searches
    and receive notifications for new matching content.
    """
    
    NOTIFICATION_TYPES = [
        ('NONE', 'No Notifications'),
        ('IMMEDIATE', 'Immediate'),
        ('DAILY', 'Daily Digest'),
        ('WEEKLY', 'Weekly Digest'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Search configuration
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    query_text = models.TextField()
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Saved search filters"
    )
    
    # User and sharing
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_searches'
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether search is shared with other users"
    )
    shared_with_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_saved_searches'
    )
    
    # Notifications
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='NONE'
    )
    last_notification = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = "search"
        db_table = 'saved_searches'
        verbose_name = _('Saved Search')
        verbose_name_plural = _('Saved Searches')
        ordering = ['user', '-last_used', 'name']
        indexes = [
            models.Index(fields=['user', 'is_shared']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['last_used']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.user.username}"
    
    def execute_search(self):
        """Execute the saved search and return results."""
        from .services import search_service
        
        # Update usage tracking
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
        
        # Execute search
        return search_service.search_documents(
            query=self.query_text,
            filters=self.filters,
            user=self.user
        )


class SearchFacet(models.Model):
    """
    Search Facet model for search categorization.
    
    Defines available facets for search filtering
    and categorization.
    """
    
    FACET_TYPES = [
        ('CATEGORY', 'Category Facet'),
        ('DATE_RANGE', 'Date Range Facet'),
        ('NUMERIC_RANGE', 'Numeric Range Facet'),
        ('TAG', 'Tag Facet'),
        ('STATUS', 'Status Facet'),
        ('USER', 'User Facet'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Facet configuration
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    facet_type = models.CharField(max_length=20, choices=FACET_TYPES)
    
    # Field mapping
    field_name = models.CharField(
        max_length=100,
        help_text="Document model field name for this facet"
    )
    field_path = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nested field path (e.g., metadata.department)"
    )
    
    # Display configuration
    sort_order = models.PositiveIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)
    show_count = models.BooleanField(
        default=True,
        help_text="Show document count for each facet value"
    )
    
    # Value constraints
    allowed_values = models.JSONField(
        default=list,
        blank=True,
        help_text="Predefined facet values (for category facets)"
    )
    min_value = models.FloatField(
        null=True, blank=True,
        help_text="Minimum value (for numeric range facets)"
    )
    max_value = models.FloatField(
        null=True, blank=True,
        help_text="Maximum value (for numeric range facets)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = "search"
        db_table = 'search_facets'
        verbose_name = _('Search Facet')
        verbose_name_plural = _('Search Facets')
        ordering = ['sort_order', 'display_name']
        indexes = [
            models.Index(fields=['facet_type', 'is_enabled']),
            models.Index(fields=['sort_order']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.facet_type})"
    
    def get_facet_values(self, query_filters=None):
        """Get available values for this facet."""
        from .services import search_service
        
        return search_service.get_facet_values(
            facet=self,
            filters=query_filters or {}
        )


class SearchSynonym(models.Model):
    """
    Search Synonym model for query expansion.
    
    Defines synonyms and related terms to improve
    search recall and user experience.
    """
    
    SYNONYM_TYPES = [
        ('EXACT', 'Exact Synonym'),
        ('RELATED', 'Related Term'),
        ('ABBREVIATION', 'Abbreviation'),
        ('ACRONYM', 'Acronym'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Synonym configuration
    primary_term = models.CharField(max_length=200)
    synonym_term = models.CharField(max_length=200)
    synonym_type = models.CharField(max_length=20, choices=SYNONYM_TYPES)
    
    # Bi-directional mapping
    is_bidirectional = models.BooleanField(
        default=True,
        help_text="Whether synonym works in both directions"
    )
    
    # Context and domain
    context = models.CharField(
        max_length=100,
        blank=True,
        help_text="Context or domain where synonym applies"
    )
    weight = models.FloatField(
        default=1.0,
        help_text="Synonym weight for relevance scoring"
    )
    
    # Status and validation
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_synonyms'
    )
    
    class Meta:
        app_label = "search"
        db_table = 'search_synonyms'
        verbose_name = _('Search Synonym')
        verbose_name_plural = _('Search Synonyms')
        ordering = ['primary_term', 'synonym_term']
        constraints = [
            models.UniqueConstraint(
                fields=['primary_term', 'synonym_term'],
                name='unique_synonym_pair'
            ),
        ]
        indexes = [
            models.Index(fields=['primary_term', 'is_active']),
            models.Index(fields=['synonym_term', 'is_active']),
            models.Index(fields=['context']),
        ]
    
    def __str__(self):
        arrow = '↔' if self.is_bidirectional else '→'
        return f"{self.primary_term} {arrow} {self.synonym_term}"


class SearchConfiguration(models.Model):
    """
    Search Configuration model for search settings.
    
    Stores global search configuration and performance
    tuning parameters.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Configuration name and description
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Search behavior settings
    default_operator = models.CharField(
        max_length=10,
        choices=[('AND', 'AND'), ('OR', 'OR')],
        default='AND'
    )
    fuzzy_matching = models.BooleanField(
        default=True,
        help_text="Enable fuzzy matching for typos"
    )
    stemming_enabled = models.BooleanField(
        default=True,
        help_text="Enable word stemming"
    )
    synonym_expansion = models.BooleanField(
        default=True,
        help_text="Enable automatic synonym expansion"
    )
    
    # Result settings
    default_page_size = models.PositiveIntegerField(default=20)
    max_page_size = models.PositiveIntegerField(default=100)
    max_results = models.PositiveIntegerField(default=10000)
    
    # Performance settings
    cache_duration = models.PositiveIntegerField(
        default=300,
        help_text="Search result cache duration in seconds"
    )
    timeout_seconds = models.PositiveIntegerField(
        default=30,
        help_text="Search timeout in seconds"
    )
    
    # Ranking and relevance
    title_weight = models.FloatField(
        default=2.0,
        help_text="Weight for title matches"
    )
    content_weight = models.FloatField(
        default=1.0,
        help_text="Weight for content matches"
    )
    metadata_weight = models.FloatField(
        default=1.5,
        help_text="Weight for metadata matches"
    )
    
    # Status and versioning
    is_active = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='search_configurations'
    )
    
    class Meta:
        app_label = "search"
        db_table = 'search_configurations'
        verbose_name = _('Search Configuration')
        verbose_name_plural = _('Search Configurations')
        ordering = ['-is_active', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_search_config'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"
    
    def activate(self):
        """Activate this configuration and deactivate others."""
        SearchConfiguration.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.save()