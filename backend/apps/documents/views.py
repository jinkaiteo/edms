"""
Views for Document Management (O1).

Provides REST API views for document management, workflow operations,
and document lifecycle with proper permission controls and audit logging.
"""

import os
import logging
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

logger = logging.getLogger(__name__)

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
    
    def create(self, request, *args, **kwargs):
        """Enhanced document creation with better error handling."""
        # Ensure user has proper permissions
        user = request.user
        if user.is_anonymous:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user has document creation permissions
        has_permission = (
            user.is_superuser or
            user.user_roles.filter(
                role__module='O1',
                role__permission_level__in=['write', 'admin'],
                is_active=True
            ).exists()
        )
        
        if not has_permission:
            return Response(
                {'error': 'Insufficient permissions to create documents'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
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
        
        # Authors can see ALL their own documents (including DRAFT)
        q_filter |= Q(author=user)
        
        # Reviewers can see documents assigned to them ONLY after submitted for review
        if 'review' in user_permissions:
            q_filter |= Q(reviewer=user, status__in=['PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL', 'APPROVED_AND_EFFECTIVE'])
        
        # Approvers can see documents assigned to them ONLY after reviewed
        if 'approve' in user_permissions:
            q_filter |= Q(approver=user, status__in=['PENDING_APPROVAL', 'APPROVED_AND_EFFECTIVE'])
            # Also allow approvers to see documents assigned to them as reviewers (flexible workflow routing)
            q_filter |= Q(reviewer=user, status__in=['PENDING_REVIEW', 'UNDER_REVIEW'])
        
        # Users with read permission can see effective documents and approved pending effective documents
        if user_permissions:
            q_filter |= Q(status__in=['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE'], is_active=True)
        
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
        """Download annotated document file with metadata overlay."""
        document = self.get_object()
        return self._serve_annotated_document(document, request)
    
    def _serve_annotated_document(self, document, request):
        """Generate and serve annotated document with metadata overlay or processed .docx template."""
        from .annotation_processor import annotation_processor
        from .docx_processor import docx_processor
        from django.http import HttpResponse
        import tempfile
        import os
        
        try:
            # Check if document has a .docx file for template processing
            if document.file_name and document.file_name.lower().endswith('.docx') and docx_processor.is_available():
                # Process .docx template with placeholder replacement
                try:
                    processed_file_path = docx_processor.process_docx_template(document, request.user)
                    
                    # Read the processed file
                    with open(processed_file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Clean up temporary file
                    os.unlink(processed_file_path)
                    
                    # Create response for processed .docx
                    response = HttpResponse(
                        file_content,
                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    
                    filename = f"{document.document_number}_annotated.docx"
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    response['Content-Length'] = str(len(file_content))
                    
                    # Log successful download
                    log_document_access(
                        document=document,
                        user=request.user,
                        access_type='DOWNLOAD',
                        request=request,
                        success=True,
                        file_downloaded=True,
                        metadata={'download_type': 'annotated_docx_processed'}
                    )
                    
                    return response
                    
                except Exception as docx_error:
                    # Fall back to text annotation if .docx processing fails
                    print(f"DOCX processing failed, falling back to text annotation: {docx_error}")
            
            # Generate text annotation content (default behavior or fallback)
            annotation_content = annotation_processor.generate_annotated_document_content(document, request.user)
            
            # Create temporary file with annotation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(annotation_content)
                temp_file_path = temp_file.name
            
            # Read the file and serve it
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Create response
            response = HttpResponse(
                file_content,
                content_type='text/plain; charset=utf-8'
            )
            
            filename = f"{document.document_number}_annotated.txt"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = str(len(file_content))
            
            # Log successful download
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=True,
                file_downloaded=True,
                metadata={'download_type': 'annotated_text'}
            )
            
            return response
            
        except Exception as e:
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason=f'Annotation generation failed: {str(e)}'
            )
            return Response(
                {'error': f'Failed to generate annotated document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _serve_processed_docx(self, document, request):
        """Generate and serve processed .docx document with placeholder replacement."""
        from .docx_processor import docx_processor
        from django.http import HttpResponse
        import os
        
        try:
            # Check if document has a .docx file
            if not document.file_name or not document.file_name.lower().endswith('.docx'):
                return Response(
                    {'error': 'Document must have a .docx file for template processing'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if docx processing is available
            if not docx_processor.is_available():
                return Response(
                    {'error': 'DOCX template processing is not available. Missing python-docx-template package.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Process the document
            processed_file_path = docx_processor.process_docx_template(document, request.user)
            
            # Read the processed file
            with open(processed_file_path, 'rb') as f:
                file_content = f.read()
            
            # Clean up temporary file
            os.unlink(processed_file_path)
            
            # Create response
            response = HttpResponse(
                file_content,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            filename = f"{document.document_number}_processed.docx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = str(len(file_content))
            
            # Log successful download
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=True,
                file_downloaded=True,
                metadata={'download_type': 'processed_docx'}
            )
            
            return response
            
        except Exception as e:
            log_document_access(
                document=document,
                user=request.user,
                access_type='DOWNLOAD',
                request=request,
                success=False,
                failure_reason=f'DOCX processing failed: {str(e)}'
            )
            return Response(
                {'error': f'Failed to process .docx document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='download/official')
    def download_official_pdf(self, request, uuid=None):
        """Download official PDF (only for approved and effective documents)."""
        document = self.get_object()
        
        # Access control: Only approved and effective documents can be downloaded as official PDF
        if document.status not in ['APPROVED_AND_EFFECTIVE', 'EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE']:
            return Response(
                {'error': 'Official PDF download is only available for approved and effective documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Generate official PDF with digital signature (Phase 2 implementation)
            from apps.documents.services.pdf_generator import OfficialPDFGenerator
            generator = OfficialPDFGenerator()
            
            signed_pdf_content = generator.generate_official_pdf(document, request.user)
            
            # Serve PDF with proper headers
            response = HttpResponse(signed_pdf_content, content_type='application/pdf')
            filename = f"{document.document_number}_official_v{getattr(document, 'version_string', '1.0')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(signed_pdf_content)
            
            # Log successful download
            logger.info(f"Official PDF download successful: {filename} by {request.user.username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Official PDF generation failed for document {document.uuid}: {e}")
            
            # Fallback to annotated document with clear messaging
            if settings.OFFICIAL_PDF_CONFIG.get('FALLBACK_TO_ANNOTATED', True):
                logger.info(f"Falling back to annotated document for {document.uuid}")
                return self._serve_document_file(document, request, 'annotated')
            else:
                return Response({
                    'error': 'PDF generation temporarily unavailable',
                    'details': str(e),
                    'fallback_available': f'/api/v1/documents/documents/{document.uuid}/download/annotated/'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=True, methods=['get'], url_path='download/processed')
    def download_processed_docx(self, request, uuid=None):
        """Download .docx document with placeholders replaced by actual metadata."""
        document = self.get_object()
        return self._serve_processed_docx(document, request)
    
    @action(detail=True, methods=['patch'], url_path='upload')
    def upload_file(self, request, uuid=None):
        """Upload file to a document in DRAFT status."""
        document = self.get_object()
        
        # Check permissions
        if not document.can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to edit this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check document status
        if document.status != 'DRAFT':
            return Response(
                {'error': 'Files can only be uploaded to documents in DRAFT status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if file is provided
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Save file
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        import mimetypes
        
        # Generate file path
        file_path = f"documents/{document.uuid}/{uploaded_file.name}"
        
        # Save file using default storage
        saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        
        # Update document with file information
        document.file_name = uploaded_file.name
        document.file_path = saved_path
        document.file_size = uploaded_file.size
        document.mime_type = mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
        
        # Calculate checksum
        document.file_checksum = document.calculate_file_checksum()
        
        document.save()
        
        # Log file upload
        log_document_access(
            document=document,
            user=request.user,
            access_type='EDIT',
            request=request,
            success=True,
            metadata={
                'action': 'file_uploaded',
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size
            }
        )
        
        # Return updated document
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Enhanced update method to handle document type changes and number regeneration."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user can edit this document
        if not instance.can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to edit this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow core field changes in DRAFT status
        if instance.status != 'DRAFT':
            # Remove protected fields from the request data for non-DRAFT documents
            protected_fields = ['title', 'document_type', 'document_source']
            for field in protected_fields:
                if field in request.data:
                    return Response(
                        {'error': f'Field "{field}" cannot be changed after document leaves DRAFT status'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        # Handle document type changes
        document_type_changed = request.data.get('document_type_changed') == 'true'
        old_document_type_id = request.data.get('old_document_type')
        new_document_type_id = request.data.get('document_type')
        
        old_document_number = None
        if document_type_changed and old_document_type_id and new_document_type_id:
            from apps.documents.models import DocumentType
            
            try:
                old_type = DocumentType.objects.get(id=old_document_type_id)
                new_type = DocumentType.objects.get(id=new_document_type_id)
                
                if old_type != new_type:
                    # Store old number for audit logging
                    old_document_number = instance.document_number
                    
                    # Generate new document number based on new type
                    instance.document_number = instance.generate_document_number(new_type)
                    
                    # Log the document number change
                    from apps.audit.models import DatabaseChangeLog
                    import json
                    
                    # Create change log with correct field structure
                    DatabaseChangeLog.objects.create(
                        content_type=ContentType.objects.get_for_model(instance),
                        object_id=instance.id,
                        action='UPDATE',
                        user=request.user,
                        table_name='documents_document',
                        operation='UPDATE', 
                        record_id=str(instance.id),
                        old_values={
                            'document_number': old_document_number,
                            'document_type': old_type.name
                        },
                        new_values={
                            'document_number': instance.document_number,
                            'document_type': new_type.name
                        }
                    )
                    
            except DocumentType.DoesNotExist:
                return Response(
                    {'error': 'Invalid document type provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle document_source, dependencies, and file upload manually since they need special processing
        document_source_id = request.data.get('document_source')
        dependencies_data = []
        uploaded_file = request.FILES.get('file') if hasattr(request, 'FILES') else None
        
        # Extract dependencies from form data
        for key, value in request.data.items():
            if key.startswith('dependencies[') and key.endswith(']'):
                dependencies_data.append(value)
                
        print(f"Debug: File upload detected: {uploaded_file.name if uploaded_file else 'None'}")
        print(f"Debug: File size: {uploaded_file.size if uploaded_file else 'None'}")
        
        # Update document_source if provided
        if document_source_id:
            try:
                from apps.documents.models import DocumentSource
                new_source = DocumentSource.objects.get(id=document_source_id)
                instance.document_source = new_source
                print(f"Updated document source to: {new_source.name} (ID: {new_source.id})")
            except DocumentSource.DoesNotExist:
                return Response(
                    {'error': f'Document source with ID {document_source_id} not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update dependencies if provided
        if dependencies_data:
            try:
                from apps.documents.models import DocumentDependency
                # Validate all dependency documents exist first
                valid_dependencies = []
                invalid_dependencies = []
                
                for dep_doc_id in dependencies_data:
                    try:
                        depends_on_doc = Document.objects.get(id=dep_doc_id)
                        # Don't allow self-dependency
                        if depends_on_doc.id != instance.id:
                            valid_dependencies.append(depends_on_doc)
                        else:
                            print(f"Skipped self-dependency: {dep_doc_id}")
                    except Document.DoesNotExist:
                        invalid_dependencies.append(dep_doc_id)
                
                if invalid_dependencies:
                    return Response(
                        {'error': f'Dependency documents not found: {invalid_dependencies}. Available document IDs: {[doc.id for doc in Document.objects.exclude(id=instance.id)[:10]]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Clear existing dependencies
                DocumentDependency.objects.filter(document=instance, is_active=True).update(is_active=False)
                
                # Create new dependencies (use get_or_create to avoid duplicates)
                for depends_on_doc in valid_dependencies:
                    dependency, created = DocumentDependency.objects.get_or_create(
                        document=instance,
                        depends_on=depends_on_doc,
                        dependency_type='required',
                        defaults={
                            'created_by': request.user,
                            'is_active': True
                        }
                    )
                    
                    # If dependency already exists but was inactive, reactivate it
                    if not created and not dependency.is_active:
                        dependency.is_active = True
                        dependency.save()
                        print(f"Reactivated existing dependency: {instance.id} → {depends_on_doc.id}")
                    elif created:
                        print(f"Created new dependency: {instance.id} → {depends_on_doc.id}")
                    else:
                        print(f"Dependency already active: {instance.id} → {depends_on_doc.id}")
                
                print(f"Updated dependencies to: {[doc.id for doc in valid_dependencies]}")
                
            except Exception as e:
                return Response(
                    {'error': f'Error updating dependencies: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle file upload if provided
        if uploaded_file:
            try:
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                import os
                import mimetypes
                
                print(f"Processing file upload: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                # Generate file path
                file_path = f"documents/{instance.uuid}/{uploaded_file.name}"
                
                # Save file using default storage
                saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
                
                # Update document with file information
                instance.file_name = uploaded_file.name
                instance.file_path = saved_path
                instance.file_size = uploaded_file.size
                instance.mime_type = mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
                
                # Calculate checksum
                instance.file_checksum = instance.calculate_file_checksum()
                
                print(f"File saved successfully: {saved_path}")
                print(f"File info updated: name={instance.file_name}, size={instance.file_size}")
                
                # Log file upload
                from .utils import log_document_access
                log_document_access(
                    document=instance,
                    user=request.user,
                    access_type='EDIT',
                    request=request,
                    success=True,
                    metadata={
                        'action': 'file_uploaded',
                        'file_name': uploaded_file.name,
                        'file_size': uploaded_file.size,
                        'via': 'edit_modal'
                    }
                )
                
            except Exception as e:
                print(f"Error processing file upload: {e}")
                return Response(
                    {'error': f'File upload failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Continue with normal update process for other fields
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)

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
                status=status.HTTP_400_BAD_REQUEST
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
        
        # Verify file integrity (temporarily disabled for debugging)
        # TODO: Re-enable after implementing verify_file_integrity method
        # if not document.verify_file_integrity():
        #     log_document_access(
        #         document=document,
        #         user=request.user,
        #         access_type='DOWNLOAD',
        #         request=request,
        #         success=False,
        #         failure_reason='File integrity check failed'
        #     )
        #     return Response(
        #         {'error': 'File integrity check failed'},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
        
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
    
    @action(detail=True, methods=['post'])
    def workflow(self, request, uuid=None):
        """Handle workflow actions (submit review, route for approval, etc.)."""
        document = self.get_object()
        action_type = request.data.get('action')
        
        if not action_type:
            return Response(
                {'error': 'Action type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if action_type == 'submit_review':
                return self._handle_submit_review(document, request)
            elif action_type == 'route_for_approval':
                return self._handle_route_for_approval(document, request)
            elif action_type == 'approve':
                return self._handle_approve(document, request)
            else:
                return Response(
                    {'error': f'Unknown workflow action: {action_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # Log the error for debugging
            print(f"Workflow error for {action_type}: {e}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {'error': f'Workflow action failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_submit_review(self, document, request):
        """Handle review submission."""
        # Validate that user can submit review
        if document.reviewer != request.user:
            return Response(
                {'error': 'Only the assigned reviewer can submit a review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate document status
        if document.status not in ['PENDING_REVIEW', 'UNDER_REVIEW']:
            return Response(
                {'error': f'Cannot submit review for document in {document.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get review data
        recommendation = request.data.get('recommendation')
        comments = request.data.get('comments', '')
        
        if not recommendation:
            return Response(
                {'error': 'Review recommendation is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update document status
        old_status = document.status
        if recommendation == 'approve':
            document.status = 'REVIEWED'
        elif recommendation == 'reject':
            document.status = 'DRAFT'  # Send back to author
        else:
            return Response(
                {'error': 'Invalid recommendation. Must be "approve" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.save()
        
        # Create comment for review
        if comments:
            from .models import DocumentComment
            DocumentComment.objects.create(
                document=document,
                author=request.user,
                content=comments,
                comment_type='review',
                subject=f'Review {recommendation.title()}: {document.document_number}'
            )
        
        # Log workflow action
        log_document_access(
            document=document,
            user=request.user,
            access_type='WORKFLOW',
            request=request,
            success=True,
            metadata={
                'action': 'submit_review',
                'recommendation': recommendation,
                'old_status': old_status,
                'new_status': document.status
            }
        )
        
        return Response({
            'message': f'Review {recommendation}ed successfully',
            'status': document.status,
            'recommendation': recommendation
        })
    
    def _handle_route_for_approval(self, document, request):
        """Handle routing for approval."""
        # Validate that user is document author
        if document.author != request.user:
            return Response(
                {'error': 'Only the document author can route for approval'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate document status
        if document.status != 'REVIEWED':
            return Response(
                {'error': f'Document must be in REVIEWED status to route for approval. Current status: {document.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get approver
        approver_id = request.data.get('approver_id')
        if not approver_id:
            return Response(
                {'error': 'Approver ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            approver = User.objects.get(id=approver_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid approver ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update document
        old_status = document.status
        document.status = 'PENDING_APPROVAL'
        document.approver = approver
        document.save()
        
        # Log workflow action
        log_document_access(
            document=document,
            user=request.user,
            access_type='WORKFLOW',
            request=request,
            success=True,
            metadata={
                'action': 'route_for_approval',
                'approver': approver.username,
                'old_status': old_status,
                'new_status': document.status
            }
        )
        
        return Response({
            'message': 'Document routed for approval successfully',
            'status': document.status,
            'approver': approver.username
        })
    
    def _handle_approve(self, document, request):
        """Handle document approval."""
        # Validate that user is assigned approver
        if document.approver != request.user:
            return Response(
                {'error': 'Only the assigned approver can approve this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate document status
        if document.status != 'PENDING_APPROVAL':
            return Response(
                {'error': f'Document must be in PENDING_APPROVAL status. Current status: {document.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get approval data
        decision = request.data.get('decision')
        comments = request.data.get('comments', '')
        effective_date = request.data.get('effective_date')
        
        if not decision:
            return Response(
                {'error': 'Approval decision is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update document status
        old_status = document.status
        if decision == 'approve':
            document.status = 'APPROVED_AND_EFFECTIVE'
            if effective_date:
                from django.utils.dateparse import parse_date
                document.effective_date = parse_date(effective_date) or timezone.now().date()
            else:
                document.effective_date = timezone.now().date()
        elif decision == 'reject':
            document.status = 'DRAFT'  # Send back to author
        else:
            return Response(
                {'error': 'Invalid decision. Must be "approve" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.save()
        
        # Create comment for approval
        if comments:
            from .models import DocumentComment
            DocumentComment.objects.create(
                document=document,
                author=request.user,
                content=comments,
                comment_type='approval',
                subject=f'Approval {decision.title()}: {document.document_number}'
            )
        
        # Log workflow action
        log_document_access(
            document=document,
            user=request.user,
            access_type='WORKFLOW',
            request=request,
            success=True,
            metadata={
                'action': 'approve',
                'decision': decision,
                'old_status': old_status,
                'new_status': document.status,
                'effective_date': str(document.effective_date) if document.effective_date else None
            }
        )
        
        return Response({
            'message': f'Document {decision}ed successfully',
            'status': document.status,
            'decision': decision,
            'effective_date': document.effective_date
        })


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