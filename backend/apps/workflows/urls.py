"""
URL configuration for Workflow Management.

Provides REST API endpoints for workflow operations,
task management, and workflow automation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WorkflowTypeViewSet,
    WorkflowInstanceViewSet,
    WorkflowTaskViewSet,
    WorkflowTransitionViewSet,
    WorkflowRuleViewSet,
    WorkflowNotificationViewSet,
    WorkflowTemplateViewSet,
    DocumentWorkflowAPIView,
    WorkflowHistoryAPIView,
    MyTasksAPIView,
    WorkflowMetricsAPIView,
)

# Router for viewsets
router = DefaultRouter()
router.register(r'types', WorkflowTypeViewSet)
router.register(r'instances', WorkflowInstanceViewSet)
router.register(r'tasks', WorkflowTaskViewSet)
router.register(r'transitions', WorkflowTransitionViewSet)
router.register(r'rules', WorkflowRuleViewSet)
router.register(r'notifications', WorkflowNotificationViewSet)
router.register(r'templates', WorkflowTemplateViewSet)

app_name = 'workflows'

urlpatterns = [
    # Document-specific workflow endpoints
    path('documents/<uuid:document_uuid>/', 
         DocumentWorkflowAPIView.as_view(), 
         name='document_workflow'),
    
    path('documents/<uuid:document_uuid>/history/', 
         WorkflowHistoryAPIView.as_view(), 
         name='document_workflow_history'),
    
    # User-specific endpoints
    path('my-tasks/', 
         MyTasksAPIView.as_view(), 
         name='my_tasks'),
    
    # Metrics and reporting
    path('metrics/', 
         WorkflowMetricsAPIView.as_view(), 
         name='workflow_metrics'),
    
    # ViewSet URLs
    path('', include(router.urls)),
]