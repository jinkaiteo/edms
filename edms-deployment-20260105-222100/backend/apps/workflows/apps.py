from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflows'
    verbose_name = 'Workflow Engine'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.workflows.signals  # noqa