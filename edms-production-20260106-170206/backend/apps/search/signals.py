"""
Search Signals for automatic index management.

Django signals to automatically update search indices
when documents are created, updated, or deleted.
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from apps.documents.models import Document
from .services import search_service
from .models import SearchIndex

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def update_document_search_index(sender, instance, created, **kwargs):
    """Update search index when document is created or modified."""
    try:
        # Update search index for the document
        search_service.update_search_index(instance, force_update=True)
        
        logger.info(f"Search index updated for document {instance.document_number}")
        
    except Exception as e:
        logger.error(f"Failed to update search index for document {instance.id}: {str(e)}")


@receiver(pre_delete, sender=Document)
def cleanup_document_search_index(sender, instance, **kwargs):
    """Clean up search index when document is deleted."""
    try:
        # Delete associated search indices
        SearchIndex.objects.filter(document=instance).delete()
        
        logger.info(f"Search index cleaned up for document {instance.document_number}")
        
    except Exception as e:
        logger.error(f"Failed to cleanup search index for document {instance.id}: {str(e)}")