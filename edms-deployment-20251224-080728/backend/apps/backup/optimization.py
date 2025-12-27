"""
Performance optimization utilities for natural key operations
Day 4: Database indexing, caching, and bulk operations optimization
"""

from django.db import models
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NaturalKeyOptimizer:
    """Optimization utilities for natural key operations"""
    
    CACHE_PREFIX = 'nk_cache_'
    CACHE_TIMEOUT = 300  # 5 minutes default
    
    @classmethod
    def get_cache_key(cls, model_name: str, natural_key_values: tuple) -> str:
        """Generate cache key for natural key lookup"""
        key_str = '_'.join(str(v) for v in natural_key_values)
        return f"{cls.CACHE_PREFIX}{model_name}_{key_str}"
    
    @classmethod
    def cache_natural_key_lookup(cls, model_class, natural_key_values: tuple, obj):
        """Cache natural key lookup result"""
        try:
            cache_key = cls.get_cache_key(model_class.__name__, natural_key_values)
            cache.set(cache_key, obj.pk, cls.CACHE_TIMEOUT)
            logger.debug(f"Cached natural key lookup: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache natural key lookup: {e}")
    
    @classmethod
    def get_cached_natural_key_lookup(cls, model_class, natural_key_values: tuple):
        """Get cached natural key lookup result"""
        try:
            cache_key = cls.get_cache_key(model_class.__name__, natural_key_values)
            cached_pk = cache.get(cache_key)
            if cached_pk:
                try:
                    return model_class.objects.get(pk=cached_pk)
                except model_class.DoesNotExist:
                    # Object was deleted, remove from cache
                    cache.delete(cache_key)
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached natural key lookup: {e}")
            return None
    
    @classmethod
    def clear_model_cache(cls, model_class):
        """Clear all cached lookups for a model"""
        # Note: This is a simplified implementation
        # In production, you'd want a more sophisticated cache invalidation strategy
        pass

class OptimizedNaturalKeyMixin:
    """Mixin to add optimized natural key lookups to models"""
    
    @classmethod
    def get_by_natural_key_optimized(cls, *natural_key_values):
        """Optimized natural key lookup with caching"""
        # Try cache first
        cached_obj = NaturalKeyOptimizer.get_cached_natural_key_lookup(cls, natural_key_values)
        if cached_obj:
            logger.debug(f"Natural key cache hit: {cls.__name__}")
            return cached_obj
        
        # Cache miss - do database lookup
        logger.debug(f"Natural key cache miss: {cls.__name__}")
        try:
            obj = cls.get_by_natural_key(*natural_key_values)
            # Cache the result
            NaturalKeyOptimizer.cache_natural_key_lookup(cls, natural_key_values, obj)
            return obj
        except cls.DoesNotExist:
            # Cache negative results briefly to prevent repeated DB hits
            cache_key = NaturalKeyOptimizer.get_cache_key(cls.__name__, natural_key_values)
            cache.set(f"{cache_key}_notfound", True, 60)  # 1 minute for negative cache
            raise

def add_natural_key_indexes():
    """
    SQL statements to add indexes for natural key fields
    These should be run as migrations for production deployment
    """
    
    index_statements = [
        # User model - username is already indexed by Django
        
        # Document model - document_number
        "CREATE INDEX IF NOT EXISTS documents_document_number_idx ON documents_document (document_number);",
        
        # DocumentType model - code
        "CREATE INDEX IF NOT EXISTS documents_documenttype_code_idx ON documents_documenttype (code);",
        
        # DocumentSource model - name  
        "CREATE INDEX IF NOT EXISTS documents_documentsource_name_idx ON documents_documentsource (name);",
        
        # DocumentState model - code
        "CREATE INDEX IF NOT EXISTS workflows_documentstate_code_idx ON workflows_documentstate (code);",
        
        # PlaceholderDefinition model - name
        "CREATE INDEX IF NOT EXISTS placeholders_placeholderdefinition_name_idx ON placeholders_placeholderdefinition (name);",
        
        # BackupConfiguration model - name
        "CREATE INDEX IF NOT EXISTS backup_backupconfiguration_name_idx ON backup_backupconfiguration (name);",
        
        # Composite indexes for complex natural keys
        # DocumentVersion - document + version_major + version_minor
        "CREATE INDEX IF NOT EXISTS documents_documentversion_composite_idx ON documents_documentversion (document_id, version_major, version_minor);",
        
        # DocumentDependency - document + depends_on + dependency_type  
        "CREATE INDEX IF NOT EXISTS documents_documentdependency_composite_idx ON documents_documentdependency (document_id, depends_on_id, dependency_type);",
        
        # UserRole - user + role
        "CREATE INDEX IF NOT EXISTS users_userrole_composite_idx ON users_userrole (user_id, role_id);",
        
        # DocumentWorkflow - document + workflow_type
        "CREATE INDEX IF NOT EXISTS workflows_documentworkflow_composite_idx ON workflows_documentworkflow (document_id, workflow_type);"
    ]
    
    return index_statements

class BulkNaturalKeyOperations:
    """Optimized bulk operations for natural key models"""
    
    @classmethod
    def bulk_get_by_natural_keys(cls, model_class, natural_key_list):
        """
        Efficiently get multiple objects by natural keys
        Returns dict mapping natural_key_tuple → object
        """
        results = {}
        cache_misses = []
        
        # Check cache for all keys first
        for natural_key_values in natural_key_list:
            cached_obj = NaturalKeyOptimizer.get_cached_natural_key_lookup(
                model_class, natural_key_values
            )
            if cached_obj:
                results[natural_key_values] = cached_obj
            else:
                cache_misses.append(natural_key_values)
        
        # Bulk fetch cache misses
        if cache_misses:
            # This would need to be customized per model based on natural key fields
            # For example, for User model:
            if model_class.__name__ == 'User':
                usernames = [nk[0] for nk in cache_misses]
                objects = model_class.objects.filter(username__in=usernames)
                for obj in objects:
                    natural_key = obj.natural_key()
                    results[natural_key] = obj
                    # Cache the result
                    NaturalKeyOptimizer.cache_natural_key_lookup(
                        model_class, natural_key, obj
                    )
        
        return results

# Performance monitoring decorator
def monitor_natural_key_performance(func):
    """Decorator to monitor natural key lookup performance"""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 0.01:  # Log slow lookups (>10ms)
                logger.warning(f"Slow natural key lookup: {func.__name__} took {duration*1000:.2f}ms")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Natural key lookup failed: {func.__name__} after {duration*1000:.2f}ms - {e}")
            raise
    return wrapper