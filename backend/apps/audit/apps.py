from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit Trail (S2)'
    
    def ready(self):
        """Import signals and tasks when the app is ready."""
        import apps.audit.signals  # noqa
        # Import integrity tasks to register with Celery
        try:
            import apps.audit.integrity_tasks  # noqa
        except ImportError:
            pass