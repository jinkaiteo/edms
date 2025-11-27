"""
Views for Document Management (O1).

Provides REST API views for document management, workflow operations,
and document lifecycle with proper permission controls and audit logging.
"""

import os
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.permissions import CanManageDocuments
from .models import (
    DocumentType, DocumentSource, Document, DocumentVersion,
    DocumentDependency, DocumentAccessLog, DocumentComment,
    DocumentAttachment
)
from .serializers import (
    DocumentTypeSerializer, DocumentSourceSerializer,
    DocumentListSerializer, DocumentDetailSerializer,
    DocumentCreateSerializer, DocumentUpdateSerializer,
    DocumentVersionSerializer, DocumentDependencySerializer,
    DocumentAccessLogSerializer, DocumentCommentSerializer,
    DocumentAttachmentSerializer, DocumentStatusChangeSerializer,
    DocumentVersionCreateSerializer
)
from .filters import DocumentFilter
from .utils import log_document_access, create_document_export


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document types.
    
    Provides CRUD operations for document types with
    appropriate permission checks.
    """
    
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'template_required', 'approval_required']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_superuser:
            return super().get_queryset()
        
        # Regular users see only active document types
        return super().get_queryset().filter(is_active=True)


class DocumentSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document sources.
    
    Provides CRUD operations for document sources with
    appropriate permission checks.
    """
    
    queryset = DocumentSource.objects.all()
    serializer_class = DocumentSourceSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'source_type', 'requires_verification']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'source_type', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_superuser:
            return super().get_queryset()
        
        # Regular users see only active document sources
        return super().get_queryset().filter(is_active=True)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents.
    
    Provides comprehensive document management with workflow
    operations, version control, and access logging.
    """
    
    queryset = Document.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DocumentFilter
    search_fields = ['document_number', 'title', 'description', 'keywords']
    ordering_fields = ['document_number', 'title', 'created_at', 'effective_date']
    ordering = ['-created_at']
    lookup_field = 'uuid'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        return DocumentDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset().select_related(
            'document_type', 'document_source', 'author', 'reviewer', 'approver'
        ).prefetch_related('dependencies', 'dependents')
        
        if user.is_superuser:
            return queryset
        
        # Check user's document permissions
        user_permissions = user.user_roles.filter(
            role__module='O1',
            is_active=True
        ).values_list('role__permission_level', flat=True)
        
        if 'admin' in user_permissions:
            return queryset
        
        # Filter based on user's role and document status
        q_filter = Q()
        
        # Authors can see their own documents
        q_filter |= Q(author=user)
        
        # Reviewers can see documents assigned to them for review
        if 'review' in user_permissions or 'approve' in user_permissions:
            q_filter |= Q(reviewer=user) | Q(approver=user)
        
        # Users with read permission can see effective documents
        if user_permissions:
            q_filter |= Q(status='EFFECTIVE', is_active=True)
        
        return queryset.filter(q_filter)
    
    def perform_create(self, serializer):
        """Set author and handle document creation."""
        document = serializer.save(author=self.request.user)
        
        # Log document creation
        log_document_access(
            document=document,
            user=self.request.user,
            access_type='EDIT',
            request=self.request,
            success=True
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Log document access when retrieving."""
        instance = self.get_object()
        
        # Log document access
        log_document_access(
            document=instance,
            user=request.user,
            access_type='VIEW',
            request=request,
            success=True
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, uuid=None):
        """Change document status with workflow validation."""
        document = self.get_object()
        serializer = DocumentStatusChangeSerializer(
            data=request.data,
            context={'document': document, 'request': request}
        )
        
        if serializer.is_valid():
            old_status = document.status
            new_status = serializer.validated_data['new_status']
            comment = serializer.validated_data.get('comment', '')
            effective_date = serializer.validated_data.get('effective_date')
            
            # Update document status
            document.status = new_status
            if effective_date:
                document.effective_date = effective_date
            if comment:
                document.change_summary = comment
            
            document.save()
            
            # Log status change
            log_document_access(
                document=document,
                user=request.user,
                access_type='EDIT',
                request=request,
                success=True,
                metadata={
                    'status_change': f'{old_status} -> {new_status}',
                    'comment': comment
                }
            )
            
            return Response(
                {'message': f'Status changed from {old_status} to {new_status}'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, uuid=None):
        """Create a new version of the document."""
        document = self.get_object()
        serializer = DocumentVersionCreateSerializer(
            data=request.data,
            context={'document': document, 'request': request}
        )
        
        if serializer.is_valid():
            major_increment = serializer.validated_data['major_increment']
            version_comment = serializer.validated_data.get('version_comment', '')
            change_summary = serializer.validated_data['change_summary']
            reason_for_change = serializer.validated_data['reason_for_change']
            
            # Calculate new version numbers
            if major_increment:
                new_major = document.version_major + 1
                new_minor = 0
            else:
                new_major = document.version_major
                new_minor = document.version_minor + 1
            
            # Create new document version
            new_document = Document.objects.create(
                title=document.title,
                description=document.description,
                keywords=document.keywords,
                version_major=new_major,
                version_minor=new_minor,
                document_type=document.document_type,
                document_source=document.document_source,
                author=request.user,
                reviewer=document.reviewer,
                approver=document.approver,
                status='DRAFT',
                priority=document.priority,
                supersedes=document,
                reason_for_change=reason_for_change,
                change_summary=change_summary,
                requires_training=document.requires_training,
                is_controlled=document.is_controlled,
            )
            
            # Log version creation
            log_document_access(
                document=new_document,
                user=request.user,
                access_type='EDIT',
                request=request,
                success=True,
                metadata={
                    'action': 'version_created',
                    'previous_version': document.version_string,
                    'new_version': new_document.version_string,
                    'major_increment': major_increment
                }
            )
            
            serializer = DocumentDetailSerializer(new_document, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='download/original')
    def download_original(self, request, uuid=None):
        """Download original document file."""
        document = self.get_object()
        return self._serve_document_file(document, request, 'original')
    
    @action(detail=True, methods=['get'], url_path='download/annotated')
    def download_annotated(self, request, uuid=None):
        """Download annotated document file with metadata."""
        document = self.get_object()
        return self._serve_document_file(document, request, 'annotated')
    
    @action(detail=True, methods=['get'], url_path='download/official')
    def download_official_pdf(self, request, uuid=None):
        """Download official PDF (only for approved and effective documents)."""
        document = self.get_object()
        
        # Access control: Only approved and effective documents can be downloaded as official PDF
        if document.status not in ['APPROVED_AND_EFFECTIVE']:
            return Response(
                {'error': 'Official PDF download is only available for approved and effective documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return self._serve_document_file(document, request, 'official_pdf')

    def _serve_document_file(self, document, request, download_type):
        """Common method to serve document files with proper validation."""
        
        if not document.file_path:
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason='No file attached to document'
            )
            return Response(
                {'error': 'No file attached to this document'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        file_path = document.full_file_path
        if not file_path or not os.path.exists(file_path):
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason='File not found'
            )
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify file integrity
        if not document.verify_file_integrity():
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason='File integrity check failed'
            )
            return Response(
                {'error': 'File integrity check failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log successful download
        log_document_access(
            document=document,
            user=request.user,
            access_type='DOWNLOAD',
            request=request,
            success=True,
            file_downloaded=True,
            metadata={'download_type': download_type}
        )
        
        # Serve file
        try:
            with open(file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type=document.mime_type or 'application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
                return response
        except Exception as e:
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason=str(e)
            )
            return Response(
                {'error': 'File could not be served'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, uuid=None):
        """Get document dependencies and dependents."""
        document = self.get_object()
        
        dependencies = DocumentDependencySerializer(
            document.dependencies.filter(is_active=True),
            many=True,
            context={'request': request}
        ).data
        
        dependents = DocumentDependencySerializer(
            document.dependents.filter(is_active=True),
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'dependencies': dependencies,
            'dependents': dependents
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, uuid=None):
        """Get document version history."""
        document = self.get_object()
        
        versions = DocumentVersionSerializer(
            document.versions.all(),
            many=True,
            context={'request': request}
        ).data
        
        return Response({'versions': versions})


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document versions.
    
    Provides read-only access to document version history
    for audit and compliance purposes.
    """
    
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document', 'version_major', 'status', 'created_by']
    ordering_fields = ['version_major', 'version_minor', 'created_at']
    ordering = ['-version_major', '-version_minor', '-created_at']


class DocumentDependencyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document dependencies.
    
    Provides CRUD operations for document dependencies
    with circular dependency prevention.
    """
    
    queryset = DocumentDependency.objects.all()
    serializer_class = DocumentDependencySerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document', 'depends_on', 'dependency_type', 'is_critical', 'is_active']
    ordering_fields = ['created_at', 'dependency_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter dependencies based on user's document access."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Filter based on documents user can access
        accessible_docs = Document.objects.filter(
            Q(author=user) | 
            Q(reviewer=user) | 
            Q(approver=user) |
            Q(status='EFFECTIVE', is_active=True)
        )
        
        return super().get_queryset().filter(
            Q(document__in=accessible_docs) | Q(depends_on__in=accessible_docs)
        )


class DocumentAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document access logs.
    
    Provides read-only access to document access logs
    for audit and compliance purposes.
    """
    
    queryset = DocumentAccessLog.objects.all()
    serializer_class = DocumentAccessLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document', 'user', 'access_type', 'success', 'access_timestamp']
    ordering_fields = ['access_timestamp']
    ordering = ['-access_timestamp']
    
    def get_queryset(self):
        """Filter access logs based on user permissions."""
        user = self.request.user
        
        # Only admin users or users with audit permissions can see all logs
        if user.is_superuser or user.user_roles.filter(
            role__module='S2',
            role__permission_level__in=['read', 'admin'],
            is_active=True
        ).exists():
            return super().get_queryset()
        
        # Regular users can only see their own access logs
        return super().get_queryset().filter(user=user)


class DocumentCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document comments.
    
    Provides CRUD operations for document comments
    with proper permission controls.
    """
    
    queryset = DocumentComment.objects.all()
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document', 'author', 'comment_type', 'is_resolved', 'requires_response']
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'comment_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter comments based on user's document access."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Filter based on documents user can access
        accessible_docs = Document.objects.filter(
            Q(author=user) | 
            Q(reviewer=user) | 
            Q(approver=user) |
            Q(status='EFFECTIVE', is_active=True)
        )
        
        return super().get_queryset().filter(document__in=accessible_docs)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark comment as resolved."""
        comment = self.get_object()
        comment.is_resolved = True
        comment.resolved_at = timezone.now()
        comment.resolved_by = request.user
        comment.save()
        
        return Response(
            {'message': 'Comment marked as resolved'},
            status=status.HTTP_200_OK
        )


class DocumentAttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document attachments.
    
    Provides CRUD operations for document attachments
    with file integrity checks.
    """
    
    queryset = DocumentAttachment.objects.all()
    serializer_class = DocumentAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document', 'attachment_type', 'is_active', 'is_public']
    search_fields = ['name', 'description', 'file_name']
    ordering_fields = ['name', 'uploaded_at', 'file_size']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter attachments based on user's document access."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Filter based on documents user can access and public attachments
        accessible_docs = Document.objects.filter(
            Q(author=user) | 
            Q(reviewer=user) | 
            Q(approver=user) |
            Q(status='EFFECTIVE', is_active=True)
        )
        
        return super().get_queryset().filter(
            Q(document__in=accessible_docs) & 
            (Q(is_public=True) | Q(document__author=user))
        )


class DocumentWorkflowView(APIView):
    """
    View for document workflow operations.
    
    Handles workflow transitions, approvals, and rejections
    with proper validation and audit logging.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def post(self, request, document_uuid):
        """Execute workflow action on document."""
        try:
            document = Document.objects.get(uuid=document_uuid)
        except Document.DoesNotExist:
            raise Http404("Document not found")
        
        action = request.data.get('action')
        comment = request.data.get('comment', '')
        
        if action == 'submit_for_review':
            return self._submit_for_review(document, request, comment)
        elif action == 'approve':
            return self._approve_document(document, request, comment)
        elif action == 'reject':
            return self._reject_document(document, request, comment)
        elif action == 'make_effective':
            return self._make_effective(document, request, comment)
        else:
            return Response(
                {'error': 'Invalid workflow action'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _submit_for_review(self, document, request, comment):
        """Submit document for review."""
        if document.status != 'DRAFT':
            return Response(
                {'error': 'Only draft documents can be submitted for review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not document.reviewer:
            return Response(
                {'error': 'Reviewer must be assigned before submission'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.status = 'PENDING_REVIEW'
        document.save()
        
        # Add comment if provided
        if comment:
            DocumentComment.objects.create(
                document=document,
                author=request.user,
                comment_type='GENERAL',
                subject='Submitted for review',
                content=comment
            )
        
        return Response(
            {'message': 'Document submitted for review'},
            status=status.HTTP_200_OK
        )
    
    def _approve_document(self, document, request, comment):
        """Approve document."""
        # Handle both review completion and document approval based on current status
        if document.status in ['PENDING_REVIEW', 'UNDER_REVIEW']:
            # This is review completion (reviewer completing review)
            if not document.can_review(request.user):
                return Response(
                    {'error': 'You do not have permission to review this document'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Complete review workflow
            document.status = 'REVIEW_COMPLETED' 
            document.review_date = timezone.now()
            document.save(update_fields=['status', 'review_date'])
            
        elif document.status == 'PENDING_APPROVAL':
            # This is final approval (approver signing off)
            if not document.can_approve(request.user):
                return Response(
                    {'error': 'You do not have permission to approve this document'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Complete approval workflow
            document.status = 'APPROVED'
            document.approval_date = timezone.now()
            document.save(update_fields=['status', 'approval_date'])
            
        else:
            return Response(
                {'error': f'Document cannot be approved in current status: {document.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add approval/review completion comment
        DocumentComment.objects.create(
            document=document,
            author=request.user,
            comment_type='APPROVAL',
            subject='Document approved',
            content=comment or 'Document approved'
        )
        
        return Response(
            {'message': 'Document approved'},
            status=status.HTTP_200_OK
        )
    
    def _reject_document(self, document, request, comment):
        """Reject document."""
        if not document.can_approve(request.user) and not document.can_review(request.user):
            return Response(
                {'error': 'You do not have permission to reject this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.status = 'DRAFT'
        document.save()
        
        # Add rejection comment
        DocumentComment.objects.create(
            document=document,
            author=request.user,
            comment_type='REJECTION',
            subject='Document rejected',
            content=comment or 'Document rejected',
            requires_response=True
        )
        
        return Response(
            {'message': 'Document rejected'},
            status=status.HTTP_200_OK
        )
    
    def _make_effective(self, document, request, comment):
        """Make document effective."""
        if document.status != 'APPROVED':
            return Response(
                {'error': 'Only approved documents can be made effective'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.status = 'EFFECTIVE'
        document.effective_date = timezone.now().date()
        document.save()
        
        # Supersede previous version if applicable
        if document.supersedes and document.supersedes.status == 'EFFECTIVE':
            document.supersedes.status = 'SUPERSEDED'
            document.supersedes.obsolete_date = timezone.now().date()
            document.supersedes.save()
        
        return Response(
            {'message': 'Document is now effective'},
            status=status.HTTP_200_OK
        )


class DocumentSearchView(APIView):
    """
    Advanced document search view.
    
    Provides full-text search capabilities with filters
    and relevance ranking.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Perform document search."""
        query = request.GET.get('q', '')
        document_type = request.GET.get('type')
        status = request.GET.get('status')
        author = request.GET.get('author')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Start with base queryset
        queryset = Document.objects.filter(is_active=True)
        
        # Apply access controls
        user = request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(author=user) | 
                Q(reviewer=user) | 
                Q(approver=user) |
                Q(status='EFFECTIVE')
            )
        
        # Apply filters
        if document_type:
            queryset = queryset.filter(document_type__code=document_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if author:
            queryset = queryset.filter(author__username=author)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Apply full-text search
        if query:
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                search=SearchVector('title', 'description', 'keywords', 'document_number')
            ).filter(search=search_query)
        
        # Serialize results
        serializer = DocumentListSerializer(
            queryset[:50],  # Limit to 50 results
            many=True,
            context={'request': request}
        )
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'query': query
        })


class DocumentExportView(APIView):
    """
    Document export view for compliance reporting.
    
    Provides document export functionality in various formats
    with audit logging.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def get(self, request, document_uuid):
        """Export document metadata and content."""
        try:
            document = Document.objects.get(uuid=document_uuid)
        except Document.DoesNotExist:
            raise Http404("Document not found")
        
        export_format = request.GET.get('format', 'json')
        include_content = request.GET.get('include_content', 'false').lower() == 'true'
        
        # Log export access
        log_document_access(
            document=document,
            user=request.user,
            access_type='EXPORT',
            request=request,
            success=True,
            metadata={
                'export_format': export_format,
                'include_content': include_content
            }
        )
        
        # Create export
        export_data = create_document_export(document, export_format, include_content)
        
        if export_format == 'json':
            return Response(export_data)
        else:
            # Return as file download
            response = HttpResponse(
                export_data,
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="document_{document.document_number}_export.{export_format}"'
            return response