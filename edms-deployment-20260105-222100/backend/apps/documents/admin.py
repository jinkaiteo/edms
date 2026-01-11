"""
Django Admin configuration for Document Management (O1).

Provides comprehensive admin interface for managing documents,
types, dependencies, and access logs with audit trail support.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from .models import (
    DocumentType, DocumentSource, Document, DocumentVersion,
    DocumentDependency, DocumentAccessLog, DocumentComment,
    DocumentAttachment
)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Admin for managing document types."""
    
    list_display = (
        'name', 'code', 'template_required', 'approval_required',
        'retention_years', 'document_count', 'is_active', 'created_at'
    )
    list_filter = ('template_required', 'approval_required', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'document_count')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        (_('Requirements'), {
            'fields': (
                'template_required', 'template_path',
                'approval_required', 'review_required'
            ),
        }),
        (_('Numbering'), {
            'fields': ('numbering_prefix', 'numbering_format'),
        }),
        (_('Compliance'), {
            'fields': ('retention_years',),
        }),
        (_('Status'), {
            'fields': ('is_active',),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_at', 'updated_at', 'created_by', 'metadata'),
        }),
    )
    
    def document_count(self, obj):
        """Return the number of documents of this type."""
        count = obj.documents.count()
        url = reverse('admin:documents_document_changelist') + f'?document_type__id__exact={obj.id}'
        return format_html('<a href="{}">{} documents</a>', url, count)
    document_count.short_description = _('Documents')
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new document type."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentSource)
class DocumentSourceAdmin(admin.ModelAdmin):
    """Admin for managing document sources."""
    
    list_display = (
        'name', 'source_type', 'requires_verification',
        'requires_signature', 'document_count', 'is_active'
    )
    list_filter = ('source_type', 'requires_verification', 'requires_signature', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'document_count')
    
    def document_count(self, obj):
        """Return the number of documents from this source."""
        count = obj.documents.count()
        url = reverse('admin:documents_document_changelist') + f'?document_source__id__exact={obj.id}'
        return format_html('<a href="{}">{} documents</a>', url, count)
    document_count.short_description = _('Documents')


class DocumentVersionInline(admin.TabularInline):
    """Inline for document versions."""
    model = DocumentVersion
    extra = 0
    readonly_fields = ('uuid', 'created_at', 'version_string', 'file_checksum')
    fields = (
        'version_major', 'version_minor', 'version_comment',
        'status', 'created_by', 'created_at'
    )
    
    def version_string(self, obj):
        return obj.version_string
    version_string.short_description = _('Version')


class DocumentDependencyInline(admin.TabularInline):
    """Inline for document dependencies."""
    model = DocumentDependency
    fk_name = 'document'
    extra = 0
    readonly_fields = ('uuid', 'created_at')
    fields = ('depends_on', 'dependency_type', 'is_critical', 'description')


class DocumentAttachmentInline(admin.TabularInline):
    """Inline for document attachments."""
    model = DocumentAttachment
    extra = 0
    readonly_fields = ('uuid', 'uploaded_at', 'file_size', 'file_checksum')
    fields = ('name', 'attachment_type', 'file_name', 'is_active')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Comprehensive admin for managing documents."""
    
    list_display = (
        'document_number', 'title', 'version_display', 'status',
        'document_type', 'author', 'created_at', 'effective_date'
    )
    list_filter = (
        'status', 'document_type', 'document_source', 'priority',
        'is_active', 'is_controlled', 'requires_training',
        'created_at', 'effective_date'
    )
    search_fields = (
        'document_number', 'title', 'description', 'keywords',
        'author__username', 'author__first_name', 'author__last_name'
    )
    readonly_fields = (
        'uuid', 'document_number', 'created_at', 'updated_at',
        'file_checksum', 'file_size', 'version_display',
        'dependency_count', 'access_count'
    )
    
    fieldsets = (
        (None, {
            'fields': (
                'document_number', 'title', 'description', 'keywords'
            )
        }),
        (_('Version Control'), {
            'fields': (
                'version_major', 'version_minor', 'supersedes',
                'reason_for_change', 'change_summary'
            ),
        }),
        (_('Classification'), {
            'fields': (
                'document_type', 'document_source', 'priority', 'status'
            ),
        }),
        (_('People & Roles'), {
            'fields': ('author', 'reviewer', 'approver'),
        }),
        (_('File Information'), {
            'fields': (
                'file_name', 'file_path', 'file_size',
                'file_checksum', 'mime_type', 'is_encrypted'
            ),
        }),
        (_('Important Dates'), {
            'fields': (
                'review_date', 'approval_date', 'effective_date',
                'review_due_date', 'obsolete_date'
            ),
        }),
        (_('Settings'), {
            'fields': (
                'is_active', 'is_controlled', 'requires_training'
            ),
        }),
        (_('System Information'), {
            'fields': (
                'uuid', 'created_at', 'updated_at',
                'dependency_count', 'access_count', 'metadata'
            ),
        }),
    )
    
    inlines = [DocumentVersionInline, DocumentDependencyInline, DocumentAttachmentInline]
    
    def version_display(self, obj):
        """Display version in a formatted way."""
        return f"v{obj.version_major:02d}.{obj.version_minor:02d}"
    version_display.short_description = _('Version')
    version_display.admin_order_field = 'version_major'
    
    def dependency_count(self, obj):
        """Return the number of dependencies."""
        count = obj.dependencies.count()
        if count > 0:
            url = reverse('admin:documents_documentdependency_changelist') + f'?document__id__exact={obj.uuid}'
            return format_html('<a href="{}">{} dependencies</a>', url, count)
        return '0'
    dependency_count.short_description = _('Dependencies')
    
    def access_count(self, obj):
        """Return the number of access logs."""
        count = obj.access_logs.count()
        if count > 0:
            url = reverse('admin:documents_documentaccesslog_changelist') + f'?document__id__exact={obj.uuid}'
            return format_html('<a href="{}">{} accesses</a>', url, count)
        return '0'
    access_count.short_description = _('Access Logs')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'document_type', 'document_source', 'author', 'reviewer', 'approver'
        ).prefetch_related('dependencies', 'access_logs')


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin for document versions."""
    
    list_display = (
        'document', 'version_string', 'status',
        'created_by', 'created_at', 'file_checksum'
    )
    list_filter = ('status', 'created_at', 'version_major')
    search_fields = (
        'document__document_number', 'document__title',
        'change_summary', 'reason_for_change'
    )
    readonly_fields = ('uuid', 'created_at', 'version_string')
    
    fieldsets = (
        (None, {
            'fields': ('document', 'version_major', 'version_minor', 'status')
        }),
        (_('File Information'), {
            'fields': ('file_name', 'file_path', 'file_size', 'file_checksum'),
        }),
        (_('Change Information'), {
            'fields': ('version_comment', 'change_summary', 'reason_for_change'),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_at', 'created_by', 'metadata'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'created_by')


@admin.register(DocumentDependency)
class DocumentDependencyAdmin(admin.ModelAdmin):
    """Admin for document dependencies."""
    
    list_display = (
        'document', 'depends_on', 'dependency_type',
        'is_critical', 'created_by', 'created_at', 'is_active'
    )
    list_filter = ('dependency_type', 'is_critical', 'is_active', 'created_at')
    search_fields = (
        'document__document_number', 'document__title',
        'depends_on__document_number', 'depends_on__title'
    )
    readonly_fields = ('uuid', 'created_at')
    
    fieldsets = (
        (None, {
            'fields': ('document', 'depends_on', 'dependency_type')
        }),
        (_('Details'), {
            'fields': ('description', 'is_critical', 'is_active'),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_at', 'created_by', 'metadata'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new dependency."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    """Admin for document access logs (read-only for audit)."""
    
    list_display = (
        'document', 'user', 'access_type', 'success',
        'access_timestamp', 'ip_address', 'document_version'
    )
    list_filter = (
        'access_type', 'success', 'access_timestamp',
        'file_downloaded', 'document__document_type'
    )
    search_fields = (
        'document__document_number', 'user__username',
        'ip_address', 'failure_reason'
    )
    readonly_fields = (
        'uuid', 'document', 'user', 'access_type', 'access_timestamp',
        'ip_address', 'user_agent', 'success', 'failure_reason',
        'document_version', 'file_downloaded', 'access_duration'
    )
    
    fieldsets = (
        (None, {
            'fields': ('document', 'user', 'access_type', 'access_timestamp')
        }),
        (_('Context'), {
            'fields': ('ip_address', 'user_agent', 'session_id'),
        }),
        (_('Result'), {
            'fields': ('success', 'failure_reason', 'document_version'),
        }),
        (_('Additional Information'), {
            'fields': ('file_downloaded', 'access_duration', 'metadata'),
        }),
    )
    
    def has_add_permission(self, request):
        """Access logs are created automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Access logs are read-only for audit purposes."""
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'user')


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    """Admin for document comments."""
    
    list_display = (
        'document', 'author', 'comment_type', 'subject',
        'is_resolved', 'requires_response', 'created_at'
    )
    list_filter = (
        'comment_type', 'is_resolved', 'requires_response',
        'is_internal', 'created_at'
    )
    search_fields = (
        'document__document_number', 'author__username',
        'subject', 'content'
    )
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('document', 'author', 'comment_type', 'subject')
        }),
        (_('Content'), {
            'fields': ('content',),
        }),
        (_('Location'), {
            'fields': ('page_number', 'section', 'line_reference'),
        }),
        (_('Status'), {
            'fields': (
                'is_resolved', 'resolved_at', 'resolved_by',
                'requires_response', 'is_internal'
            ),
        }),
        (_('Threading'), {
            'fields': ('parent_comment',),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_at', 'updated_at', 'metadata'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'document', 'author', 'resolved_by', 'parent_comment'
        )


@admin.register(DocumentAttachment)
class DocumentAttachmentAdmin(admin.ModelAdmin):
    """Admin for document attachments."""
    
    list_display = (
        'name', 'document', 'attachment_type', 'file_name',
        'file_size_display', 'uploaded_by', 'uploaded_at', 'is_active'
    )
    list_filter = ('attachment_type', 'is_active', 'is_public', 'uploaded_at')
    search_fields = (
        'name', 'document__document_number', 'file_name',
        'description'
    )
    readonly_fields = ('uuid', 'uploaded_at', 'file_checksum', 'file_size_display')
    
    fieldsets = (
        (None, {
            'fields': ('document', 'name', 'description', 'attachment_type')
        }),
        (_('File Information'), {
            'fields': (
                'file_name', 'file_path', 'file_size_display',
                'file_checksum', 'mime_type'
            ),
        }),
        (_('Settings'), {
            'fields': (
                'is_active', 'is_public', 'requires_signature', 'version'
            ),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'uploaded_at', 'uploaded_by', 'metadata'),
        }),
    )
    
    def file_size_display(self, obj):
        """Display file size in human readable format."""
        if not obj.file_size:
            return '-'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"
    file_size_display.short_description = _('File Size')
    
    def save_model(self, request, obj, form, change):
        """Set uploaded_by when creating new attachment."""
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)