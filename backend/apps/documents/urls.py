"""
URL configuration for Document Management (O1).

Provides REST API endpoints for document CRUD operations,
workflow actions, and document lifecycle management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentTypeViewSet,
    DocumentSourceViewSet,
    DocumentViewSet,
    DocumentVersionViewSet,
    DocumentDependencyViewSet,
    DocumentAccessLogViewSet,
    DocumentCommentViewSet,
    DocumentAttachmentViewSet,
    DocumentWorkflowView,
    DocumentSearchView,
    DocumentExportView,
)
from .workflow_integration import document_workflow_endpoint, document_workflow_history

# Router for viewsets
router = DefaultRouter()
router.register(r'types', DocumentTypeViewSet)
router.register(r'sources', DocumentSourceViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'versions', DocumentVersionViewSet)
router.register(r'dependencies', DocumentDependencyViewSet)
router.register(r'access-logs', DocumentAccessLogViewSet)
router.register(r'comments', DocumentCommentViewSet)
router.register(r'attachments', DocumentAttachmentViewSet)

app_name = 'documents'

urlpatterns = [
    # Document workflow actions (backward compatible)
    path('documents/<uuid:uuid>/workflow/', 
         document_workflow_endpoint, 
         name='document_workflow_compatible'),
    
    # Document workflow history (backward compatible)
    path('documents/<uuid:uuid>/workflow/history/', 
         document_workflow_history, 
         name='document_workflow_history_compatible'),
    
    # Document search
    path('search/', 
         DocumentSearchView.as_view(), 
         name='document_search'),
    
    # Document export
    path('documents/<uuid:document_uuid>/export/', 
         DocumentExportView.as_view(), 
         name='document_export'),
    
    # ViewSet URLs
    path('', include(router.urls)),
]