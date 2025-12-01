"""
URL configuration for Workflow Management (Simple Approach).

Provides REST API endpoints using the Simple Workflow approach
for document lifecycle management with 21 CFR Part 11 compliance.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SimpleDocumentWorkflowAPIView,
    SimpleWorkflowHistoryAPIView,
    SimpleMyTasksAPIView,
    DocumentWorkflowViewSet,
)
from .api_views import workflow_types
from .task_api_views import author_tasks, task_summary, complete_task
from .user_task_api_views import user_task_summary, complete_user_task
from apps.api.v1 import task_views

# Router for simple viewsets
router = DefaultRouter()
router.register(r'workflows', DocumentWorkflowViewSet)

app_name = 'workflows'

urlpatterns = [
    # Simple document workflow endpoints
    path('documents/<uuid:document_uuid>/', 
         SimpleDocumentWorkflowAPIView.as_view(), 
         name='simple_document_workflow'),
    
    path('documents/<uuid:document_uuid>/status/', 
         SimpleDocumentWorkflowAPIView.as_view(), 
         name='simple_document_workflow_status'),
    
    path('documents/<uuid:document_uuid>/history/', 
         SimpleWorkflowHistoryAPIView.as_view(), 
         name='simple_document_workflow_history'),
    
    # Simple user tasks endpoint
    path('my-tasks/', 
         SimpleMyTasksAPIView.as_view(), 
         name='simple_my_tasks'),
    
    # Task API endpoints (matching frontend expectations)
    path('tasks/author/', author_tasks, name='author_tasks'),
    path('tasks/summary/', task_summary, name='task_summary'),
    path('tasks/<uuid:task_uuid>/complete/', complete_task, name='complete_task'),
    
    # Enhanced task API endpoints (using new implementation)
    path('tasks/user-tasks/', task_views.user_tasks, name='user_tasks'),
    path('tasks/user-summary/', user_task_summary, name='user_task_summary'),
    path('tasks/<uuid:task_uuid>/user-complete/', complete_user_task, name='complete_user_task'),
    
    # Workflow types endpoint
    path('types/', workflow_types, name='workflow_types'),
    
    # Enhanced workflow user selection endpoints
    path('users/', include('apps.workflows.urls_enhanced')),
    
    # ViewSet URLs
    path('', include(router.urls)),
]