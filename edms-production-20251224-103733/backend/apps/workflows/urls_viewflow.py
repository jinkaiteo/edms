"""
Viewflow URLs for EDMS document workflows.
Integrates Viewflow workflow URLs with EDMS routing.
"""

from django.urls import path, include
from viewflow.workflow.urls import application
from . import flows
from .views import WorkflowDashboardView, workflow_tasks_api, workflow_processes_api

app_name = 'workflows'

# Register Viewflow flows
application.register('document_review', flows.DocumentReviewFlow)
application.register('document_upversion', flows.DocumentUpVersionFlow)
application.register('document_obsolete', flows.DocumentObsoleteFlow)

urlpatterns = [
    # Workflow dashboard
    path('dashboard/', WorkflowDashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/tasks/', workflow_tasks_api, name='tasks_api'),
    path('api/processes/', workflow_processes_api, name='processes_api'),
    
    # Viewflow URLs
    path('', include(application.urls)),
]