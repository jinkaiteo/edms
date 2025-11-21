from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit Trail (S2)'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.audit.signals  # noqa