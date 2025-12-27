"""
Search Services for EDMS Search Module.

Advanced search capabilities using PostgreSQL full-text search
with query optimization, faceting, and relevance scoring.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from django.db.models import Q, F, Count, Max, Avg
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline
)
from django.contrib.postgres.aggregates import StringAgg
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    SearchIndex, SearchQuery as SearchQueryLog, SearchResult, SavedSearch,
    SearchFacet, SearchSynonym, SearchConfiguration
)
from apps.documents.models import Document, DocumentType
from apps.audit.services import audit_service

User = get_user_model()
logger = logging.getLogger(__name__)


class SearchService:
    """
    Core search service for document full-text search.
    
    Provides advanced search capabilities with PostgreSQL full-text search,
    including faceting, ranking, and query optimization.
    """

    def __init__(self):
        self.cache_prefix = 'search_'
        self.default_language = 'english'
        self.max_results = 10000
        
    def search_documents(self, query: str, filters: Dict[str, Any] = None,
                        user: User = None, page: int = 1, page_size: int = 20,
                        sort_by: str = 'relevance') -> Dict[str, Any]:
        """
        Search documents with advanced filtering and ranking.
        
        Args:
            query: Search query text
            filters: Additional search filters
            user: User performing search
            page: Page number (1-based)
            page_size: Number of results per page
            sort_by: Sort criteria (relevance, date, title, etc.)
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = timezone.now()
        
        try:
            # Get search configuration
            config = self._get_active_search_configuration()
            
            # Process and validate query
            processed_query = self._process_search_query(query, config)
            if not processed_query:
                return self._empty_search_result()
            
            # Build base queryset with permissions
            queryset = self._build_base_queryset(user, filters or {})
            
            # Apply search query
            if query.strip():
                queryset = self._apply_search_query(queryset, processed_query, config)
            
            # Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            # Apply sorting
            queryset = self._apply_sorting(queryset, sort_by, bool(query.strip()))
            
            # Get total count for pagination
            total_count = queryset.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            paginated_queryset = queryset[offset:offset + page_size]
            
            # Execute query and get results
            documents = list(paginated_queryset)
            
            # Generate search highlights if text query
            if query.strip():
                documents = self._add_search_highlights(documents, processed_query)
            
            # Calculate response time
            response_time = (timezone.now() - start_time).total_seconds()
            
            # Log search query
            search_log = self._log_search_query(
                query=query,
                filters=filters or {},
                result_count=total_count,
                response_time=response_time,
                user=user
            )
            
            # Log search results
            self._log_search_results(search_log, documents)
            
            # Build response
            result = {
                'query': query,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'documents': [self._serialize_document_result(doc) for doc in documents],
                'facets': self._get_search_facets(filters or {}),
                'suggestions': self._get_search_suggestions(query),
                'response_time': response_time,
                'applied_filters': filters or {}
            }
            
            # Cache results if appropriate
            if self._should_cache_results(query, filters):
                self._cache_search_results(query, filters, result, config.cache_duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            # Log failed search
            self._log_search_query(
                query=query,
                filters=filters or {},
                result_count=0,
                response_time=(timezone.now() - start_time).total_seconds(),
                user=user,
                error=str(e)
            )
            
            return {
                'query': query,
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'documents': [],
                'facets': {},
                'suggestions': [],
                'error': str(e),
                'response_time': (timezone.now() - start_time).total_seconds()
            }

    def autocomplete_search(self, query: str, limit: int = 10, user: User = None) -> List[Dict[str, Any]]:
        """
        Provide autocomplete suggestions for search queries.
        
        Args:
            query: Partial search query
            limit: Maximum number of suggestions
            user: User requesting autocomplete
            
        Returns:
            List of autocomplete suggestions
        """
        if len(query.strip()) < 2:
            return []
        
        try:
            # Get base queryset with permissions
            queryset = self._build_base_queryset(user, {})
            
            # Build search vector for title and key fields
            search_vector = (
                SearchVector('title', weight='A') +
                SearchVector('document_number', weight='A') +
                SearchVector('metadata__description', weight='B')
            )
            
            # Create search query with prefix matching
            search_query = SearchQuery(query, search_type='websearch')
            
            # Execute search with ranking
            results = queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(
                search=search_query
            ).order_by('-rank')[:limit]
            
            suggestions = []
            for doc in results:
                suggestions.append({
                    'text': doc.title,
                    'document_number': doc.document_number,
                    'document_type': doc.document_type.name if doc.document_type else None,
                    'url': f'/documents/{doc.id}',
                    'rank': float(doc.rank) if hasattr(doc, 'rank') else 0
                })
            
            # Add query-based suggestions
            query_suggestions = self._get_query_autocomplete(query, user)
            suggestions.extend(query_suggestions[:limit - len(suggestions)])
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Autocomplete error: {str(e)}")
            return []

    def get_search_analytics(self, start_date: datetime = None, 
                           end_date: datetime = None, user: User = None) -> Dict[str, Any]:
        """
        Get search analytics and statistics.
        
        Args:
            start_date: Start date for analytics period
            end_date: End date for analytics period
            user: User to filter analytics (None for all users)
            
        Returns:
            Dictionary with search analytics data
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Base queryset
        queries = SearchQueryLog.objects.filter(
            executed_at__range=[start_date, end_date]
        )
        
        if user:
            queries = queries.filter(user=user)
        
        # Basic statistics
        total_searches = queries.count()
        unique_users = queries.values('user').distinct().count()
        avg_response_time = queries.aggregate(avg=Avg('response_time'))['avg'] or 0
        
        # Query analysis
        popular_queries = queries.values('query_text').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Zero result queries
        zero_result_queries = queries.filter(result_count=0).values('query_text').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Search types
        query_types = queries.values('query_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Daily search volume
        daily_volume = queries.extra(
            select={'day': 'date(executed_at)'}
        ).values('day').annotate(
            searches=Count('id')
        ).order_by('day')
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_searches': total_searches,
                'unique_users': unique_users,
                'average_response_time': round(avg_response_time, 3) if avg_response_time else 0,
                'zero_result_rate': (queries.filter(result_count=0).count() / total_searches * 100) if total_searches > 0 else 0
            },
            'popular_queries': list(popular_queries),
            'zero_result_queries': list(zero_result_queries),
            'query_types': list(query_types),
            'daily_volume': list(daily_volume)
        }

    def update_search_index(self, document: Document, force_update: bool = False) -> SearchIndex:
        """
        Update search index for a document.
        
        Args:
            document: Document to index
            force_update: Force update even if index is current
            
        Returns:
            Updated SearchIndex instance
        """
        try:
            # Get or create search index
            search_index, created = SearchIndex.objects.get_or_create(
                document=document,
                index_type='COMBINED',
                defaults={'language': self.default_language}
            )
            
            # Check if update is needed
            if not created and not force_update:
                if search_index.updated_at > document.updated_at:
                    return search_index
            
            # Update index status
            search_index.status = 'UPDATING'
            search_index.save()
            
            # Build search content
            content_parts = []
            
            # Document basic fields
            if document.title:
                content_parts.append(document.title)
            if document.document_number:
                content_parts.append(document.document_number)
            if document.description:
                content_parts.append(document.description)
            
            # Document type information
            if document.document_type:
                content_parts.append(document.document_type.name)
                if document.document_type.description:
                    content_parts.append(document.document_type.description)
            
            # Metadata content
            metadata_parts = []
            if document.metadata:
                for key, value in document.metadata.items():
                    if isinstance(value, str):
                        metadata_parts.append(f"{key}: {value}")
                    elif isinstance(value, (list, tuple)):
                        metadata_parts.append(f"{key}: {' '.join(map(str, value))}")
                    else:
                        metadata_parts.append(f"{key}: {str(value)}")
            
            # Keywords and tags
            if hasattr(document, 'keywords') and document.keywords:
                content_parts.extend(document.keywords.split(','))
            
            # Combine content
            indexed_content = ' '.join(content_parts)
            indexed_metadata = ' '.join(metadata_parts)
            
            # Create search vectors
            content_vector = SearchVector('title', weight='A')
            if indexed_content:
                content_vector += SearchVector('document_number', weight='A')
                content_vector += SearchVector('description', weight='B')
            
            metadata_vector = None
            if indexed_metadata:
                # Create a temporary field for metadata search
                metadata_vector = SearchVector(models.Value(indexed_metadata), weight='C')
            
            # Update search index
            search_index.indexed_content = indexed_content
            search_index.indexed_metadata = {'content': indexed_metadata}
            search_index.search_vector = content_vector
            search_index.metadata_vector = metadata_vector
            search_index.content_vector = content_vector
            search_index.index_size = len(indexed_content)
            search_index.status = 'ACTIVE'
            search_index.save()
            
            # Log index update
            audit_service.log_system_event(
                event_type='SEARCH_INDEX_UPDATED',
                object_type='Document',
                object_id=document.id,
                description=f"Search index updated for document {document.document_number}",
                additional_data={
                    'index_size': search_index.index_size,
                    'content_length': len(indexed_content),
                    'metadata_keys': list(document.metadata.keys()) if document.metadata else []
                }
            )
            
            return search_index
            
        except Exception as e:
            logger.error(f"Search indexing error for document {document.id}: {str(e)}")
            
            # Mark index as error
            if 'search_index' in locals():
                search_index.status = 'ERROR'
                search_index.save()
            
            raise

    def _process_search_query(self, query: str, config: SearchConfiguration) -> str:
        """Process and normalize search query."""
        if not query or not query.strip():
            return ''
        
        # Basic cleanup
        processed = query.strip()
        
        # Expand synonyms if enabled
        if config.synonym_expansion:
            processed = self._expand_synonyms(processed)
        
        # Handle special characters and operators
        processed = self._normalize_query_operators(processed, config)
        
        return processed

    def _build_base_queryset(self, user: User, filters: Dict[str, Any]):
        """Build base document queryset with permissions."""
        from apps.users.workflow_permissions import workflow_permission_manager
        
        # Start with all documents
        queryset = Document.objects.select_related(
            'document_type', 'created_by', 'approved_by'
        ).prefetch_related('dependencies')
        
        # Apply user permissions
        if user:
            accessible_docs = workflow_permission_manager.get_user_accessible_documents(user)
            queryset = queryset.filter(id__in=accessible_docs.values_list('id', flat=True))
        else:
            # Anonymous users only see public documents
            queryset = queryset.filter(is_public=True)
        
        return queryset

    def _apply_search_query(self, queryset, processed_query: str, config: SearchConfiguration):
        """Apply text search query to queryset."""
        # Create search vector combining different fields with weights
        search_vector = (
            SearchVector('title', weight='A', config=self.default_language) +
            SearchVector('document_number', weight='A', config=self.default_language) +
            SearchVector('description', weight='B', config=self.default_language)
        )
        
        # Add metadata search if available
        search_vector += SearchVector('metadata', weight='C', config=self.default_language)
        
        # Create search query
        search_type = 'websearch' if config.fuzzy_matching else 'plain'
        search_query = SearchQuery(processed_query, search_type=search_type, config=self.default_language)
        
        # Apply search with ranking
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)
        
        return queryset

    def _apply_filters(self, queryset, filters: Dict[str, Any]):
        """Apply additional search filters."""
        filter_conditions = Q()
        
        # Document type filter
        if 'document_type' in filters:
            doc_types = filters['document_type']
            if isinstance(doc_types, str):
                doc_types = [doc_types]
            filter_conditions &= Q(document_type__name__in=doc_types)
        
        # Status filter
        if 'status' in filters:
            statuses = filters['status']
            if isinstance(statuses, str):
                statuses = [statuses]
            filter_conditions &= Q(status__in=statuses)
        
        # Date range filters
        if 'created_after' in filters:
            filter_conditions &= Q(created_at__gte=filters['created_after'])
        
        if 'created_before' in filters:
            filter_conditions &= Q(created_at__lte=filters['created_before'])
        
        if 'effective_after' in filters:
            filter_conditions &= Q(effective_date__gte=filters['effective_after'])
        
        if 'effective_before' in filters:
            filter_conditions &= Q(effective_date__lte=filters['effective_before'])
        
        # Author filter
        if 'author' in filters:
            authors = filters['author']
            if isinstance(authors, str):
                authors = [authors]
            filter_conditions &= Q(created_by__username__in=authors)
        
        # Department filter (from metadata)
        if 'department' in filters:
            departments = filters['department']
            if isinstance(departments, str):
                departments = [departments]
            filter_conditions &= Q(metadata__department__in=departments)
        
        # Version filter
        if 'version' in filters:
            filter_conditions &= Q(version=filters['version'])
        
        # Keywords filter
        if 'keywords' in filters:
            keywords = filters['keywords']
            if isinstance(keywords, str):
                keywords = [keywords]
            for keyword in keywords:
                filter_conditions &= Q(metadata__keywords__icontains=keyword)
        
        return queryset.filter(filter_conditions)

    def _apply_sorting(self, queryset, sort_by: str, has_text_query: bool):
        """Apply sorting to search results."""
        if has_text_query and sort_by == 'relevance':
            return queryset.order_by('-rank', '-created_at')
        
        sort_mapping = {
            'title': 'title',
            'document_number': 'document_number',
            'created_date': '-created_at',
            'effective_date': '-effective_date',
            'author': 'created_by__username',
            'status': 'status',
            'type': 'document_type__name'
        }
        
        sort_field = sort_mapping.get(sort_by, '-created_at')
        return queryset.order_by(sort_field, '-created_at')

    def _add_search_highlights(self, documents: List[Document], query: str) -> List[Document]:
        """Add search result highlights to documents."""
        try:
            search_query = SearchQuery(query, config=self.default_language)
            
            for doc in documents:
                # Generate headlines for title and description
                if doc.title:
                    doc.title_highlight = SearchHeadline(
                        'title', search_query, max_words=10, min_words=5
                    )
                
                if doc.description:
                    doc.description_highlight = SearchHeadline(
                        'description', search_query, max_words=30, min_words=15
                    )
        
        except Exception as e:
            logger.warning(f"Error generating search highlights: {str(e)}")
        
        return documents

    def _get_search_facets(self, current_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get search facets for filtering."""
        facets = {}
        
        try:
            # Get active facets
            search_facets = SearchFacet.objects.filter(is_enabled=True).order_by('sort_order')
            
            for facet in search_facets:
                facet_values = self._calculate_facet_values(facet, current_filters)
                if facet_values:
                    facets[facet.name] = {
                        'display_name': facet.display_name,
                        'type': facet.facet_type,
                        'values': facet_values
                    }
        
        except Exception as e:
            logger.error(f"Error calculating facets: {str(e)}")
        
        return facets

    def _calculate_facet_values(self, facet: SearchFacet, current_filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate available values for a search facet."""
        # This is a simplified implementation
        # In a real system, you'd calculate actual facet counts based on current query and filters
        
        if facet.facet_type == 'CATEGORY':
            if facet.name == 'document_type':
                return [
                    {'value': dt.name, 'count': dt.documents.count(), 'selected': False}
                    for dt in DocumentType.objects.all()
                ]
            elif facet.name == 'status':
                from apps.documents.models import DOCUMENT_STATES
                return [
                    {'value': status[0], 'label': status[1], 'count': 0, 'selected': False}
                    for status in DOCUMENT_STATES
                ]
        
        return []

    def _get_search_suggestions(self, query: str) -> List[str]:
        """Get search query suggestions."""
        suggestions = []
        
        if len(query.strip()) < 3:
            return suggestions
        
        # Get popular related queries
        related_queries = SearchQueryLog.objects.filter(
            query_text__icontains=query,
            result_count__gt=0
        ).values('query_text').annotate(
            frequency=Count('id')
        ).order_by('-frequency')[:5]
        
        suggestions.extend([rq['query_text'] for rq in related_queries])
        
        return suggestions

    def _expand_synonyms(self, query: str) -> str:
        """Expand query with synonyms."""
        expanded_terms = []
        words = query.split()
        
        for word in words:
            synonyms = SearchSynonym.objects.filter(
                primary_term__iexact=word,
                is_active=True
            ).values_list('synonym_term', flat=True)
            
            if synonyms:
                # Add original word and synonyms with OR operator
                synonym_group = [word] + list(synonyms)
                expanded_terms.append(f"({' OR '.join(synonym_group)})")
            else:
                expanded_terms.append(word)
        
        return ' '.join(expanded_terms)

    def _normalize_query_operators(self, query: str, config: SearchConfiguration) -> str:
        """Normalize query operators based on configuration."""
        # Handle default operator
        if config.default_operator == 'AND':
            # Ensure AND between terms unless explicitly specified
            query = re.sub(r'\s+', ' AND ', query.strip())
        
        # Clean up extra spaces and operators
        query = re.sub(r'\s+', ' ', query)
        query = re.sub(r'\b(AND|OR)\s+(AND|OR)\b', r'\1', query)
        
        return query.strip()

    def _get_active_search_configuration(self) -> SearchConfiguration:
        """Get active search configuration."""
        try:
            return SearchConfiguration.objects.get(is_active=True)
        except SearchConfiguration.DoesNotExist:
            # Create default configuration
            return SearchConfiguration.objects.create(
                name='Default Search Configuration',
                description='Default search settings',
                is_active=True,
                created_by_id=1  # Assumes admin user exists
            )

    def _log_search_query(self, query: str, filters: Dict[str, Any], 
                         result_count: int, response_time: float, 
                         user: User = None, error: str = None) -> SearchQueryLog:
        """Log search query for analytics."""
        query_type = 'SIMPLE'
        if filters:
            query_type = 'FILTER' if len(filters) == 1 else 'ADVANCED'
        
        return SearchQueryLog.objects.create(
            query_type=query_type,
            query_text=query,
            processed_query=query,  # Would be different if query was expanded
            filters=filters,
            result_count=result_count,
            response_time=response_time,
            user=user
        )

    def _log_search_results(self, search_log: SearchQueryLog, documents: List[Document]):
        """Log individual search results."""
        for rank, document in enumerate(documents[:20], 1):  # Log top 20 results
            SearchResult.objects.create(
                query=search_log,
                document=document,
                rank=rank,
                relevance_score=getattr(document, 'rank', None)
            )

    def _serialize_document_result(self, document: Document) -> Dict[str, Any]:
        """Serialize document for search results."""
        return {
            'id': document.id,
            'document_number': document.document_number,
            'title': getattr(document, 'title_highlight', document.title),
            'description': getattr(document, 'description_highlight', document.description),
            'document_type': document.document_type.name if document.document_type else None,
            'status': document.status,
            'version': str(document.version),
            'created_by': document.created_by.get_full_name() if document.created_by else None,
            'created_at': document.created_at.isoformat(),
            'effective_date': document.effective_date.isoformat() if document.effective_date else None,
            'relevance_score': float(getattr(document, 'rank', 0)),
            'url': f'/documents/{document.id}',
            'metadata': document.metadata or {}
        }

    def _empty_search_result(self) -> Dict[str, Any]:
        """Return empty search result structure."""
        return {
            'query': '',
            'total_count': 0,
            'page': 1,
            'page_size': 20,
            'total_pages': 0,
            'documents': [],
            'facets': {},
            'suggestions': [],
            'response_time': 0,
            'applied_filters': {}
        }

    def _should_cache_results(self, query: str, filters: Dict[str, Any]) -> bool:
        """Determine if search results should be cached."""
        # Cache simple queries without user-specific filters
        return len(query.strip()) > 0 and not any(
            key in filters for key in ['user_specific', 'private']
        )

    def _cache_search_results(self, query: str, filters: Dict[str, Any], 
                             results: Dict[str, Any], duration: int):
        """Cache search results."""
        cache_key = f"{self.cache_prefix}query_{hash(query + str(sorted(filters.items())))}"
        cache.set(cache_key, results, duration)

    def _get_query_autocomplete(self, query: str, user: User = None) -> List[Dict[str, Any]]:
        """Get query-based autocomplete suggestions."""
        # Find popular queries that start with the input
        popular_queries = SearchQueryLog.objects.filter(
            query_text__istartswith=query,
            result_count__gt=0
        ).values('query_text').annotate(
            frequency=Count('id')
        ).order_by('-frequency')[:5]
        
        suggestions = []
        for pq in popular_queries:
            suggestions.append({
                'text': pq['query_text'],
                'type': 'query_suggestion',
                'frequency': pq['frequency']
            })
        
        return suggestions


# Global service instance
search_service = SearchService()