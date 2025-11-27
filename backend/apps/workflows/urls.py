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

# Router for simple viewsets
router = DefaultRouter()
router.register(r'workflows', DocumentWorkflowViewSet)

app_name = 'workflows'

urlpatterns = [
    # Simple document workflow endpoints
    path('documents/<uuid:document_uuid>/', 
         SimpleDocumentWorkflowAPIView.as_view(), 
         name='simple_document_workflow'),
    
    path('documents/<uuid:document_uuid>/history/', 
         SimpleWorkflowHistoryAPIView.as_view(), 
         name='simple_document_workflow_history'),
    
    # Simple user tasks endpoint
    path('my-tasks/', 
         SimpleMyTasksAPIView.as_view(), 
         name='simple_my_tasks'),
    
    # ViewSet URLs
    path('', include(router.urls)),
]