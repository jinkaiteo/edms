"""
Enhanced workflow URLs with user selection capabilities.
Adds routes for manual reviewer/approver assignment.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_enhanced import WorkflowUserSelectionViewSet, EnhancedDocumentWorkflowViewSet
from . import api_views_author_tasks

router = DefaultRouter()
router.register(r'users', WorkflowUserSelectionViewSet, basename='workflow-users')
router.register(r'workflows', EnhancedDocumentWorkflowViewSet, basename='workflows')

app_name = 'workflows_enhanced'

urlpatterns = [
    # Enhanced workflow endpoints
    path('', include(router.urls)),
    
    # Author task management
    path('tasks/author/', api_views_author_tasks.get_author_tasks, name='author-tasks'),
    path('tasks/summary/', api_views_author_tasks.get_task_summary, name='task-summary'),
    path('tasks/<uuid:task_id>/complete/', api_views_author_tasks.complete_task, name='complete-task'),
    
    # Additional workflow endpoints can be added here
]