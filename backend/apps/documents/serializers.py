"""
Serializers for Document Management (O1).

Provides REST API serialization for documents, types, dependencies,
and related models with validation and security considerations.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    DocumentType, DocumentSource, Document, DocumentVersion,
    DocumentDependency, DocumentAccessLog, DocumentComment,
    DocumentAttachment
)


User = get_user_model()


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for Document Type model."""
    
    document_count = serializers.SerializerMethodField()
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentType
        fields = [
            'id', 'uuid', 'name', 'code', 'description',
            'template_required', 'template_path', 'approval_required', 'review_required',
            'retention_years', 'numbering_prefix', 'numbering_format',
            'is_active', 'created_at', 'updated_at', 'created_by_display',
            'document_count', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at', 'document_count']
    
    def get_document_count(self, obj):
        """Return the number of documents of this type."""
        return obj.documents.filter(is_active=True).count()
    
    def create(self, validated_data):
        """Set created_by when creating new document type."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentSourceSerializer(serializers.ModelSerializer):
    """Serializer for Document Source model."""
    
    document_count = serializers.SerializerMethodField()
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    
    class Meta:
        model = DocumentSource
        fields = [
            'id', 'uuid', 'name', 'source_type', 'source_type_display',
            'description', 'requires_verification', 'requires_signature',
            'is_active', 'created_at', 'document_count'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'document_count']
    
    def get_document_count(self, obj):
        """Return the number of documents from this source."""
        return obj.documents.filter(is_active=True).count()


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for Document Version model."""
    
    version_string = serializers.CharField(read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'uuid', 'document', 'version_major', 'version_minor',
            'version_string', 'version_comment', 'file_name', 'file_path',
            'file_size', 'file_checksum', 'created_at', 'created_by',
            'created_by_display', 'status', 'status_display',
            'change_summary', 'reason_for_change', 'metadata'
        ]
        read_only_fields = [
            'id', 'uuid', 'created_at', 'version_string', 
            'created_by', 'created_by_display'
        ]


class DocumentDependencySerializer(serializers.ModelSerializer):
    """Serializer for Document Dependency model."""
    
    document_display = serializers.CharField(source='document.document_number', read_only=True)
    depends_on_display = serializers.CharField(source='depends_on.document_number', read_only=True)
    dependency_type_display = serializers.CharField(source='get_dependency_type_display', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentDependency
        fields = [
            'id', 'uuid', 'document', 'document_display',
            'depends_on', 'depends_on_display', 'dependency_type',
            'dependency_type_display', 'description', 'is_critical',
            'created_at', 'created_by', 'created_by_display',
            'is_active', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'created_by', 'created_by_display']
    
    def validate(self, data):
        """Validate dependency to prevent circular references."""
        if data['document'] == data['depends_on']:
            raise serializers.ValidationError("Document cannot depend on itself")
        
        # Create a temporary dependency object to test comprehensive validation
        temp_dependency = DocumentDependency(
            document=data['document'],
            depends_on=data['depends_on'],
            dependency_type=data.get('dependency_type', 'REFERENCE'),
            is_active=True
        )
        
        # Use the comprehensive circular dependency check
        if temp_dependency._would_create_circular_dependency():
            # Get detailed information about the potential circular dependency
            try:
                chain = DocumentDependency.get_dependency_chain(data['depends_on'].id, max_depth=5)
                dependency_info = chain.get('dependencies', [])
                
                error_detail = (
                    f"Circular dependency detected: Adding dependency from "
                    f"{data['document'].document_number} to {data['depends_on'].document_number} "
                    f"would create a dependency loop."
                )
                
                if dependency_info:
                    error_detail += f" Existing dependency chain: {len(dependency_info)} levels deep."
                
                raise serializers.ValidationError({
                    'non_field_errors': [error_detail],
                    'dependency_chain_preview': dependency_info[:3] if dependency_info else []
                })
            except Exception as e:
                # Fallback to simple error message if dependency chain analysis fails
                raise serializers.ValidationError(
                    f"Circular dependency detected: Adding dependency from "
                    f"{data['document'].document_number} to {data['depends_on'].document_number} "
                    f"would create a dependency loop."
                )
        
        return data
    
    def create(self, validated_data):
        """Set created_by when creating new dependency."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentCommentSerializer(serializers.ModelSerializer):
    """Serializer for Document Comment model."""
    
    author_display = serializers.CharField(source='author.get_full_name', read_only=True)
    comment_type_display = serializers.CharField(source='get_comment_type_display', read_only=True)
    resolved_by_display = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentComment
        fields = [
            'id', 'uuid', 'document', 'author', 'author_display',
            'comment_type', 'comment_type_display', 'subject', 'content',
            'page_number', 'section', 'line_reference',
            'created_at', 'updated_at', 'is_resolved', 'resolved_at',
            'resolved_by', 'resolved_by_display', 'parent_comment',
            'is_internal', 'requires_response', 'replies_count', 'metadata'
        ]
    
        read_only_fields = [
            'id', 'uuid', 'created_at', 'updated_at', 
            'author', 'author_display', 'replies_count'
        ]
    
    def get_replies_count(self, obj):
        """Return the number of replies to this comment."""
        return obj.replies.count()
    
    def create(self, validated_data):
        """Set author when creating new comment."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class DocumentAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Document Attachment model."""
    
    uploaded_by_display = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    attachment_type_display = serializers.CharField(source='get_attachment_type_display', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentAttachment
        fields = [
            'id', 'uuid', 'document', 'name', 'description',
            'attachment_type', 'attachment_type_display',
            'file_name', 'file_path', 'file_size', 'file_size_display',
            'file_checksum', 'mime_type', 'uploaded_at', 'uploaded_by',
            'uploaded_by_display', 'is_active', 'is_public',
            'requires_signature', 'version', 'metadata'
        ]
        read_only_fields = [
            'id', 'uuid', 'uploaded_at', 'uploaded_by', 
            'uploaded_by_display', 'file_size_display', 'file_checksum'
        ]
    
    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        if not obj.file_size:
            return '0 B'
        
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def create(self, validated_data):
        """Set uploaded_by when creating new attachment."""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for document lists."""
    
    version_string = serializers.CharField(read_only=True)
    document_type_display = serializers.CharField(source='document_type.name', read_only=True)
    author_display = serializers.CharField(source='author.get_full_name', read_only=True)
    reviewer_display = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    approver_display = serializers.CharField(source='approver.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Add username fields for frontend compatibility
    author_username = serializers.CharField(source='author.username', read_only=True)
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)
    approver_username = serializers.CharField(source='approver.username', read_only=True)
    
    # Add obsolescence user display name
    obsoleted_by_display = serializers.SerializerMethodField()
    
    # Add dependency information
    dependencies = serializers.SerializerMethodField()
    dependents = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'uuid', 'document_number', 'title', 'version_string',
            'status', 'status_display', 'document_type_display',
            'author', 'author_display', 'author_username',
            'reviewer', 'reviewer_display', 'reviewer_username',
            'approver', 'approver_display', 'approver_username',
            'created_at', 'effective_date', 'is_controlled', 'requires_training',
            # Add file information for workflow button logic
            'file_name', 'file_path', 'file_size',
            # Add obsolescence information
            'obsolescence_date', 'obsolescence_reason', 'obsoleted_by', 'obsoleted_by_display',
            # Add dependency information
            'dependencies', 'dependents'
        ]
    
    def get_obsoleted_by_display(self, obj):
        """Return the full name of the user who initiated obsolescence."""
        if obj.obsoleted_by:
            return obj.obsoleted_by.get_full_name() or obj.obsoleted_by.username
        return None
    
    def get_dependencies(self, obj):
        """Get active dependencies where target documents are approved/effective."""
        active_dependencies = obj.dependencies.filter(
            is_active=True,
            depends_on__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
        )
        return DocumentDependencySerializer(active_dependencies, many=True, context=self.context).data
    
    def get_dependents(self, obj):
        """Get active dependents where source documents are approved/effective."""
        active_dependents = obj.dependents.filter(
            is_active=True,
            document__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
        )
        return DocumentDependencySerializer(active_dependents, many=True, context=self.context).data


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for document details."""
    
    version_string = serializers.CharField(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    document_source = DocumentSourceSerializer(read_only=True)
    author_display = serializers.CharField(source='author.get_full_name', read_only=True)
    reviewer_display = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    approver_display = serializers.CharField(source='approver.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    # Add username fields for frontend compatibility
    author_username = serializers.CharField(source='author.username', read_only=True)
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)
    approver_username = serializers.CharField(source='approver.username', read_only=True)
    
    # Related objects (custom methods to filter active only)
    dependencies = serializers.SerializerMethodField()
    dependents = serializers.SerializerMethodField()
    comments = DocumentCommentSerializer(many=True, read_only=True)
    attachments = DocumentAttachmentSerializer(many=True, read_only=True)
    versions = DocumentVersionSerializer(many=True, read_only=True)
    
    # Permissions
    can_edit = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'uuid', 'document_number', 'title', 'description', 'keywords',
            'version_major', 'version_minor', 'version_string',
            'document_type', 'document_source', 'status', 'status_display',
            'priority', 'priority_display', 'author', 'author_display', 'author_username',
            'reviewer', 'reviewer_display', 'reviewer_username',
            'approver', 'approver_display', 'approver_username',
            'file_name', 'file_path', 'file_size', 'file_checksum', 'mime_type',
            'is_encrypted', 'created_at', 'updated_at', 'review_date',
            'approval_date', 'effective_date', 'review_due_date', 'obsolete_date',
            'reason_for_change', 'change_summary', 'supersedes',
            # Add obsolescence information
            'obsolescence_date', 'obsolescence_reason', 'obsoleted_by',
            'is_active', 'requires_training', 'is_controlled',
            'dependencies', 'dependents', 'comments', 'attachments', 'versions',
            'can_edit', 'can_review', 'can_approve', 'metadata'
        ]
        read_only_fields = [
            'uuid', 'document_number', 'created_at', 'updated_at',
            'file_checksum', 'file_size', 'version_string',
            'dependencies', 'dependents', 'comments', 'attachments', 'versions',
            'can_edit', 'can_review', 'can_approve'
        ]
    
    def get_can_edit(self, obj):
        """Check if current user can edit this document."""
        user = self.context['request'].user
        return obj.can_edit(user)
    
    def get_can_review(self, obj):
        """Check if current user can review this document."""
        user = self.context['request'].user
        return obj.can_review(user)
    
    def get_can_approve(self, obj):
        """Check if current user can approve this document."""
        user = self.context['request'].user
        return obj.can_approve(user)
    
    def get_dependencies(self, obj):
        """Get only active dependencies where target documents are approved/effective."""
        active_dependencies = obj.dependencies.filter(
            is_active=True,
            depends_on__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
        )
        return DocumentDependencySerializer(active_dependencies, many=True, context=self.context).data
    
    def get_dependents(self, obj):
        """Get only active dependents where source documents are approved/effective."""
        active_dependents = obj.dependents.filter(
            is_active=True,
            document__status__in=['APPROVED_PENDING_EFFECTIVE', 'EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE']
        )
        return DocumentDependencySerializer(active_dependents, many=True, context=self.context).data
    
    def get_obsoleted_by_display(self, obj):
        """Return the full name of the user who initiated obsolescence."""
        if obj.obsoleted_by:
            return obj.obsoleted_by.get_full_name() or obj.obsoleted_by.username
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new documents."""
    
    file = serializers.FileField(write_only=True, required=False, allow_empty_file=False)
    version_string = serializers.CharField(read_only=True)
    document_type_display = serializers.CharField(source='document_type.name', read_only=True)
    author_display = serializers.CharField(source='author.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'uuid', 'document_number', 'title', 'description', 'keywords', 
            'document_type', 'document_type_display', 'document_source', 'priority', 
            'reviewer', 'approver', 'file', 'effective_date', 'reason_for_change', 
            'requires_training', 'is_controlled', 'version_string', 'status', 
            'status_display', 'author', 'author_display', 'created_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'document_number', 'version_string', 'status', 
            'status_display', 'author', 'author_display', 'created_at'
        ]
    
    def validate(self, data):
        """Validate document creation data."""
        document_type = data.get('document_type')
        
        # Check if template is required
        if document_type and document_type.template_required and not data.get('file_path'):
            raise serializers.ValidationError(
                f"Template is required for document type: {document_type.name}"
            )
        
        # Check if review is required - EDMS Step 2 compliance
        # Per EDMS specification lines 4-6: reviewer selection happens in Step 2, not Step 1
        # Only require reviewer if document is moving to review stage
        status = data.get('status', 'DRAFT')
        if (document_type and document_type.review_required and 
            status in ['PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEW_COMPLETED'] and 
            not data.get('reviewer')):
            raise serializers.ValidationError(
                f"Reviewer is required when moving to review stage for document type: {document_type.name}"
            )
        
        # Check if approval is required
        # Note: Per EDMS workflow specification (lines 6 & 11), approver is assigned 
        # AFTER review completion, not at document creation
        # Only require approver if document is moving to approval stage
        status = data.get('status', 'DRAFT')
        if (document_type and document_type.approval_required and 
            status in ['PENDING_APPROVAL', 'UNDER_APPROVAL', 'APPROVED'] and 
            not data.get('approver')):
            raise serializers.ValidationError(
                f"Approver is required when moving to approval stage for document type: {document_type.name}"
            )
        
        return data
    
    def create(self, validated_data):
        """Create new document with proper defaults and file handling."""
        import os
        import hashlib
        import mimetypes
        from django.conf import settings
        
        # Get user from context with fallback
        user = self.context['request'].user
        if user.is_anonymous:
            raise ValidationError({'detail': 'Authentication required to create documents'})
        
        validated_data['author'] = user
        
        # Handle file upload if present
        uploaded_file = validated_data.pop('file', None)
        
        # Create document first
        document = super().create(validated_data)
        
        if uploaded_file:
            # Create storage directory if it doesn't exist
            storage_dir = os.path.join(settings.BASE_DIR, 'storage', 'documents')
            os.makedirs(storage_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"{document.uuid}{file_extension}"
            file_path = os.path.join(storage_dir, filename)
            
            # Save file to disk
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # Calculate file metadata
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(uploaded_file.name)
            
            # Calculate checksum
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                checksum = file_hash.hexdigest()
            
            # Update document with file information
            document.file_name = uploaded_file.name
            document.file_path = os.path.relpath(file_path, settings.BASE_DIR)
            document.file_size = file_size
            document.file_checksum = checksum
            document.mime_type = mime_type or 'application/octet-stream'
            document.save()
        
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing documents."""
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'keywords', 'priority',
            'reviewer', 'approver', 'effective_date', 'review_due_date',
            'reason_for_change', 'change_summary', 'requires_training'
        ]
    
    def validate(self, data):
        """Validate document update data."""
        instance = self.instance
        
        # Only allow updates if document is in editable state
        if instance and not instance.can_edit(self.context['request'].user):
            raise serializers.ValidationError(
                "Document cannot be edited in current state or by current user"
            )
        
        return data


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for Document Access Log (read-only)."""
    
    document_display = serializers.CharField(source='document.document_number', read_only=True)
    user_display = serializers.CharField(source='user.get_full_name', read_only=True)
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)
    
    class Meta:
        model = DocumentAccessLog
        fields = [
            'id', 'uuid', 'document', 'document_display', 'user', 'user_display',
            'access_type', 'access_type_display', 'access_timestamp',
            'ip_address', 'user_agent', 'success', 'failure_reason',
            'document_version', 'file_downloaded', 'access_duration'
        ]
        read_only_fields = '__all__'


# Action serializers for workflow operations
class DocumentStatusChangeSerializer(serializers.Serializer):
    """Serializer for document status change operations."""
    
    new_status = serializers.ChoiceField(choices=Document.DOCUMENT_STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False)
    
    def validate_new_status(self, value):
        """Validate status transition."""
        current_status = self.context['document'].status
        user = self.context['request'].user
        
        # Define valid transitions (simplified)
        valid_transitions = {
            'DRAFT': ['PENDING_REVIEW', 'TERMINATED'],
            'PENDING_REVIEW': ['UNDER_REVIEW', 'DRAFT'],
            'UNDER_REVIEW': ['REVIEW_COMPLETED', 'DRAFT'],
            'REVIEW_COMPLETED': ['PENDING_APPROVAL', 'DRAFT'],
            'PENDING_APPROVAL': ['UNDER_APPROVAL', 'REVIEW_COMPLETED'],
            'UNDER_APPROVAL': ['APPROVED', 'REVIEW_COMPLETED'],
            'APPROVED': ['EFFECTIVE'],
            'EFFECTIVE': ['SUPERSEDED', 'OBSOLETE'],
        }
        
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Invalid status transition from {current_status} to {value}"
            )
        
        return value


class DocumentVersionCreateSerializer(serializers.Serializer):
    """Serializer for creating new document versions."""
    
    major_increment = serializers.BooleanField(default=False)
    version_comment = serializers.CharField(required=False, allow_blank=True)
    change_summary = serializers.CharField(required=True)
    reason_for_change = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate version creation."""
        document = self.context['document']
        user = self.context['request'].user
        
        # Check if user can create new version
        if not document.can_edit(user):
            raise serializers.ValidationError(
                "You don't have permission to create a new version of this document"
            )
        
        # Check if document is in a state that allows versioning
        if document.status not in ['DRAFT', 'EFFECTIVE']:
            raise serializers.ValidationError(
                "New versions can only be created from DRAFT or EFFECTIVE documents"
            )
        
        return data