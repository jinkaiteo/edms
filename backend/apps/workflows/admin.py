"""
Django admin configuration for workflow management.

This admin interface allows administrators to manage workflows, states, and transitions
through the Django admin interface, complementing the API-based workflow system.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WorkflowType, DocumentState, DocumentWorkflow, DocumentTransition,
    WorkflowInstance, WorkflowTask, WorkflowRule, WorkflowNotification, WorkflowTemplate
)


@admin.register(WorkflowType)
class WorkflowTypeAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowType management."""
    
    list_display = [
        'name', 'workflow_type', 'is_active', 'timeout_days', 
        'requires_approval', 'created_by'
    ]
    list_filter = ['is_active', 'requires_approval', 'workflow_type']
    search_fields = ['name', 'description', 'workflow_type']
    readonly_fields = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'workflow_type', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('timeout_days', 'requires_approval', 'auto_assign_reviewers', 'auto_assign_approvers')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentState)
class DocumentStateAdmin(admin.ModelAdmin):
    """Admin interface for DocumentState management."""
    
    list_display = ['code', 'name', 'is_initial', 'is_final', 'workflows_count']
    list_filter = ['is_initial', 'is_final']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    def workflows_count(self, obj):
        """Count workflows currently in this state."""
        try:
            from .models_simple import DocumentWorkflow
            count = DocumentWorkflow.objects.filter(current_state=obj).count()
            if count > 0:
                url = reverse('admin:workflows_documentworkflow_changelist') + f'?current_state__exact={obj.code}'
                return format_html('<a href="{}">{} workflows</a>', url, count)
            return '0 workflows'
        except Exception as e:
            # Handle any database or import errors gracefully
            return f'Error: {str(e)}'
    workflows_count.short_description = 'Current Workflows'


class DocumentTransitionInline(admin.TabularInline):
    """Inline for viewing workflow transitions."""
    
    model = DocumentTransition
    extra = 0
    readonly_fields = ['from_state', 'to_state', 'transitioned_by', 'transitioned_at', 'comment']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Transitions should be created through workflow logic, not admin


@admin.register(DocumentWorkflow)
class DocumentWorkflowAdmin(admin.ModelAdmin):
    """Admin interface for DocumentWorkflow management."""
    
    list_display = [
        'id', 'document_link', 'workflow_type', 'current_state', 
        'initiated_by', 'current_assignee', 'created_at', 'due_date'
    ]
    list_filter = [
        'workflow_type', 'current_state', 'created_at', 'is_terminated'
    ]
    search_fields = [
        'document__title', 'document__document_number', 
        'initiated_by__username', 'current_assignee__username'
    ]
    readonly_fields = [
        'uuid', 'created_at', 'updated_at', 'initiated_by', 
        'document_link', 'transitions_count'
    ]
    inlines = [DocumentTransitionInline]
    
    fieldsets = (
        ('Workflow Information', {
            'fields': ('uuid', 'document_link', 'workflow_type', 'current_state')
        }),
        ('Assignment', {
            'fields': ('initiated_by', 'current_assignee', 'selected_reviewer', 'selected_approver')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at', 'due_date', 'effective_date', 'obsoleting_date')
        }),
        ('Status', {
            'fields': ('is_terminated', 'last_approved_state')
        }),
        ('Workflow Data', {
            'fields': ('up_version_reason', 'obsoleting_reason', 'termination_reason', 'workflow_data'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('transitions_count',),
            'classes': ('collapse',)
        }),
    )
    
    def document_link(self, obj):
        """Create a link to the document."""
        if obj.document:
            url = reverse('admin:documents_document_change', args=[obj.document.id])
            return format_html('<a href="{}">{} ({})</a>', 
                             url, obj.document.title, obj.document.document_number)
        return 'No document'
    document_link.short_description = 'Document'
    
    def transitions_count(self, obj):
        """Count transitions for this workflow."""
        count = obj.transitions.count()
        if count > 0:
            return format_html('{} transitions', count)
        return 'No transitions'
    transitions_count.short_description = 'Transitions'
    
    def has_add_permission(self, request):
        """Workflows should be created through document upload, not admin."""
        return False


@admin.register(DocumentTransition)
class DocumentTransitionAdmin(admin.ModelAdmin):
    """Admin interface for viewing workflow transitions (read-only)."""
    
    list_display = [
        'workflow_link', 'from_state', 'to_state', 
        'transitioned_by', 'transitioned_at'
    ]
    list_filter = ['from_state', 'to_state', 'transitioned_at']
    search_fields = [
        'workflow__document__title', 'transitioned_by__username', 'comment'
    ]
    readonly_fields = [
        'uuid', 'workflow', 'from_state', 'to_state', 
        'transitioned_by', 'transitioned_at', 'comment', 'transition_data'
    ]
    
    def workflow_link(self, obj):
        """Create a link to the workflow."""
        if obj.workflow:
            url = reverse('admin:workflows_documentworkflow_change', args=[obj.workflow.id])
            return format_html('<a href="{}">Workflow #{}</a>', url, obj.workflow.id)
        return 'No workflow'
    workflow_link.short_description = 'Workflow'
    
    def has_add_permission(self, request):
        """Transitions should be created through workflow logic, not admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Transitions should be immutable once created."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Transitions should be permanent for audit trail."""
        return False


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowInstance management."""
    
    list_display = ['uuid', 'workflow_type', 'state', 'document_link']
    list_filter = ['workflow_type', 'state']
    search_fields = ['document__title', 'document__document_number']
    readonly_fields = ['uuid']
    
    def document_link(self, obj):
        """Create a link to the document."""
        if obj.document:
            url = reverse('admin:documents_document_change', args=[obj.document.id])
            return format_html('<a href="{}">{}</a>', url, obj.document.title)
        return 'No document'
    document_link.short_description = 'Document'


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowTask management."""
    
    list_display = ['workflow_instance', 'task_type', 'assigned_to', 'due_date']
    list_filter = ['task_type']
    search_fields = ['assigned_to__username', 'task_data']
    readonly_fields = ['uuid']


@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowRule management."""
    
    list_display = ['workflow_type', 'is_active']
    list_filter = ['workflow_type', 'is_active']
    search_fields = ['description']
    readonly_fields = []


@admin.register(WorkflowNotification)
class WorkflowNotificationAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowNotification management."""
    
    list_display = ['workflow_instance', 'notification_type', 'recipient', 'sent_at']
    list_filter = ['notification_type']
    search_fields = ['recipient__username', 'subject']
    readonly_fields = ['uuid', 'sent_at']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowTemplate management."""
    
    list_display = ['name', 'workflow_type', 'is_active', 'created_by']
    list_filter = ['workflow_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = []
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Custom admin site configuration for workflows
admin.site.site_header = 'EDMS Workflow Administration'
admin.site.site_title = 'EDMS Workflow Admin'
admin.site.index_title = 'Workflow Management Dashboard'