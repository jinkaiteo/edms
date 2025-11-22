"""
Enhanced workflow URLs with user selection capabilities.
Adds routes for manual reviewer/approver assignment.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_enhanced import WorkflowUserSelectionViewSet, EnhancedDocumentWorkflowViewSet

router = DefaultRouter()
router.register(r'users', WorkflowUserSelectionViewSet, basename='workflow-users')
router.register(r'workflows', EnhancedDocumentWorkflowViewSet, basename='workflows')

app_name = 'workflows_enhanced'

urlpatterns = [
    # Enhanced workflow endpoints
    path('', include(router.urls)),
    
    # Additional workflow endpoints can be added here
]