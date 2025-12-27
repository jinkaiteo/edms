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
from .rejection_api_views import get_rejection_history, get_assignment_recommendations, submit_for_review_enhanced
from .history_api_views import get_document_workflow_history
# user_task_api_views removed - using document filters instead
# task_views import removed - using document filters instead

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
    
    # Enhanced task API endpoints removed - using document filters instead
    
    # Workflow types endpoint
    path('types/', workflow_types, name='workflow_types'),
    
    # Enhanced rejection workflow endpoints
    path('documents/<uuid:document_id>/rejection-history/', 
         get_rejection_history, name='rejection-history'),
    path('documents/<uuid:document_id>/assignment-recommendations/', 
         get_assignment_recommendations, name='assignment-recommendations'),
    path('documents/<uuid:document_id>/submit-for-review-enhanced/', 
         submit_for_review_enhanced, name='submit-for-review-enhanced'),
    
    # Workflow history endpoint
    path('documents/<uuid:document_id>/history/', 
         get_document_workflow_history, name='workflow-history'),
    
    # Enhanced workflow user selection endpoints
    path('users/', include('apps.workflows.urls_enhanced')),
    
    # ViewSet URLs
    path('', include(router.urls)),
]