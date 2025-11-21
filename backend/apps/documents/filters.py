"""
Filters for Document Management (O1).

Provides advanced filtering capabilities for documents
with support for complex queries and date ranges.
"""

import django_filters
from django.db import models
from .models import Document, DocumentType, DocumentSource


class DocumentFilter(django_filters.FilterSet):
    """
    Advanced filter set for Document model.
    
    Provides comprehensive filtering options for documents
    including date ranges, text search, and status filtering.
    """
    
    # Text search filters
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        help_text='Search in document title'
    )
    
    description = django_filters.CharFilter(
        field_name='description',
        lookup_expr='icontains',
        help_text='Search in document description'
    )
    
    keywords = django_filters.CharFilter(
        field_name='keywords',
        lookup_expr='icontains',
        help_text='Search in document keywords'
    )
    
    document_number = django_filters.CharFilter(
        field_name='document_number',
        lookup_expr='icontains',
        help_text='Search in document number'
    )
    
    # Exact match filters
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Document.DOCUMENT_STATUS_CHOICES,
        help_text='Filter by document status'
    )
    
    priority = django_filters.ChoiceFilter(
        field_name='priority',
        choices=Document.PRIORITY_LEVELS,
        help_text='Filter by document priority'
    )
    
    document_type = django_filters.ModelChoiceFilter(
        field_name='document_type',
        queryset=DocumentType.objects.filter(is_active=True),
        help_text='Filter by document type'
    )
    
    document_source = django_filters.ModelChoiceFilter(
        field_name='document_source',
        queryset=DocumentSource.objects.filter(is_active=True),
        help_text='Filter by document source'
    )
    
    # User filters
    author = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='iexact',
        help_text='Filter by author username'
    )
    
    reviewer = django_filters.CharFilter(
        field_name='reviewer__username',
        lookup_expr='iexact',
        help_text='Filter by reviewer username'
    )
    
    approver = django_filters.CharFilter(
        field_name='approver__username',
        lookup_expr='iexact',
        help_text='Filter by approver username'
    )
    
    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter documents created after this date'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter documents created before this date'
    )
    
    effective_after = django_filters.DateFilter(
        field_name='effective_date',
        lookup_expr='gte',
        help_text='Filter documents effective after this date'
    )
    
    effective_before = django_filters.DateFilter(
        field_name='effective_date',
        lookup_expr='lte',
        help_text='Filter documents effective before this date'
    )
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        help_text='Filter documents updated after this date'
    )
    
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        help_text='Filter documents updated before this date'
    )
    
    # Version filters
    version_major = django_filters.NumberFilter(
        field_name='version_major',
        help_text='Filter by major version number'
    )
    
    version_minor = django_filters.NumberFilter(
        field_name='version_minor',
        help_text='Filter by minor version number'
    )
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        help_text='Filter by active status'
    )
    
    is_controlled = django_filters.BooleanFilter(
        field_name='is_controlled',
        help_text='Filter by controlled document status'
    )
    
    requires_training = django_filters.BooleanFilter(
        field_name='requires_training',
        help_text='Filter documents that require training'
    )
    
    is_encrypted = django_filters.BooleanFilter(
        field_name='is_encrypted',
        help_text='Filter encrypted documents'
    )
    
    # Advanced filters
    has_file = django_filters.BooleanFilter(
        method='filter_has_file',
        help_text='Filter documents that have files attached'
    )
    
    status_in = django_filters.MultipleChoiceFilter(
        field_name='status',
        choices=Document.DOCUMENT_STATUS_CHOICES,
        help_text='Filter by multiple statuses'
    )
    
    review_due_soon = django_filters.BooleanFilter(
        method='filter_review_due_soon',
        help_text='Filter documents with review due in next 30 days'
    )
    
    superseded_by_me = django_filters.BooleanFilter(
        method='filter_superseded_by_me',
        help_text='Filter documents superseded by current user'
    )
    
    my_documents = django_filters.BooleanFilter(
        method='filter_my_documents',
        help_text='Filter documents authored by current user'
    )
    
    pending_my_action = django_filters.BooleanFilter(
        method='filter_pending_my_action',
        help_text='Filter documents pending action by current user'
    )
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'keywords', 'document_number',
            'status', 'priority', 'document_type', 'document_source',
            'author', 'reviewer', 'approver',
            'created_after', 'created_before', 'effective_after', 'effective_before',
            'updated_after', 'updated_before',
            'version_major', 'version_minor',
            'is_active', 'is_controlled', 'requires_training', 'is_encrypted',
            'has_file', 'status_in', 'review_due_soon', 'superseded_by_me',
            'my_documents', 'pending_my_action'
        ]
    
    def filter_has_file(self, queryset, name, value):
        """Filter documents that have files attached."""
        if value:
            return queryset.exclude(file_path='').exclude(file_path__isnull=True)
        else:
            return queryset.filter(models.Q(file_path='') | models.Q(file_path__isnull=True))
    
    def filter_review_due_soon(self, queryset, name, value):
        """Filter documents with review due in next 30 days."""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            
            due_date = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                review_due_date__lte=due_date,
                status='EFFECTIVE'
            )
        return queryset
    
    def filter_superseded_by_me(self, queryset, name, value):
        """Filter documents that current user has superseded."""
        if value and self.request:
            user = self.request.user
            superseding_docs = Document.objects.filter(
                author=user,
                supersedes__isnull=False
            ).values_list('supersedes', flat=True)
            return queryset.filter(id__in=superseding_docs)
        return queryset
    
    def filter_my_documents(self, queryset, name, value):
        """Filter documents authored by current user."""
        if value and self.request:
            return queryset.filter(author=self.request.user)
        return queryset
    
    def filter_pending_my_action(self, queryset, name, value):
        """Filter documents pending action by current user."""
        if value and self.request:
            user = self.request.user
            return queryset.filter(
                models.Q(
                    reviewer=user,
                    status__in=['PENDING_REVIEW', 'UNDER_REVIEW']
                ) |
                models.Q(
                    approver=user,
                    status__in=['PENDING_APPROVAL', 'UNDER_APPROVAL']
                )
            )
        return queryset