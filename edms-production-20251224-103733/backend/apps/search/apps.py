"""
Search App Configuration.
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    verbose_name = 'Document Search'

    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import apps.search.signals  # noqa
        except ImportError:
            pass