"""
Serializers for Workflow Management.

Provides REST API serialization for workflow models
with validation and proper data formatting.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    DocumentState, DocumentWorkflow, DocumentTransition,
    WorkflowType, WorkflowInstance, WorkflowTransition,
    WorkflowTask, WorkflowRule, WorkflowNotification,
    WorkflowTemplate
)

User = get_user_model()


class WorkflowTypeSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowType model."""
    
    workflow_type_display = serializers.CharField(source='get_workflow_type_display', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    active_instances_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowType
        fields = [
            'id', 'uuid', 'name', 'workflow_type', 'workflow_type_display',
            'description', 'is_active', 'requires_approval', 'allows_parallel',
            'auto_transition', 'timeout_days', 'reminder_days',
            'created_at', 'created_by', 'created_by_display',
            'active_instances_count', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'created_by', 'active_instances_count']
    
    def get_active_instances_count(self, obj):
        """Return count of active workflow instances."""
        return obj.instances.filter(is_active=True).count()
    
    def create(self, validated_data):
        """Set created_by when creating new workflow type."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowInstance model."""
    
    workflow_type_display = serializers.CharField(source='workflow_type.name', read_only=True)
    initiated_by_display = serializers.CharField(source='initiated_by.get_full_name', read_only=True)
    current_assignee_display = serializers.CharField(source='current_assignee.get_full_name', read_only=True)
    content_object_display = serializers.SerializerMethodField()
    days_remaining = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    active_tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowInstance
        fields = [
            'id', 'uuid', 'workflow_type', 'workflow_type_display',
            'state', 'content_type', 'object_id', 'content_object_display',
            'initiated_by', 'initiated_by_display', 'current_assignee',
            'current_assignee_display', 'started_at', 'completed_at',
            'due_date', 'is_active', 'is_completed', 'completion_reason',
            'days_remaining', 'is_overdue', 'active_tasks_count',
            'workflow_data', 'metadata'
        ]
        read_only_fields = [
            'id', 'uuid', 'started_at', 'completed_at', 'is_completed',
            'completion_reason', 'days_remaining', 'is_overdue',
            'active_tasks_count', 'content_object_display'
        ]
    
    def get_content_object_display(self, obj):
        """Return display representation of content object."""
        if obj.content_object:
            return str(obj.content_object)
        return f"{obj.content_type.name} ({obj.object_id})"
    
    def get_active_tasks_count(self, obj):
        """Return count of active tasks."""
        return obj.tasks.filter(status__in=['PENDING', 'IN_PROGRESS']).count()


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTransition model."""
    
    workflow_instance_display = serializers.CharField(
        source='workflow_instance.workflow_type.name', 
        read_only=True
    )
    transitioned_by_display = serializers.CharField(
        source='transitioned_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = WorkflowTransition
        fields = [
            'id', 'uuid', 'workflow_instance', 'workflow_instance_display',
            'from_state', 'to_state', 'transition_name',
            'transitioned_by', 'transitioned_by_display', 'transitioned_at',
            'ip_address', 'comment', 'transition_data', 'metadata'
        ]
        read_only_fields = '__all__'


class WorkflowTaskSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTask model."""
    
    workflow_instance_display = serializers.CharField(
        source='workflow_instance.workflow_type.name', 
        read_only=True
    )
    assigned_to_display = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    assigned_by_display = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkflowTask
        fields = [
            'id', 'uuid', 'workflow_instance', 'workflow_instance_display',
            'name', 'description', 'task_type', 'task_type_display',
            'priority', 'priority_display', 'assigned_to', 'assigned_to_display',
            'assigned_by', 'assigned_by_display', 'created_at', 'assigned_at',
            'started_at', 'completed_at', 'due_date', 'status', 'status_display',
            'completion_note', 'is_overdue', 'task_data', 'result_data', 'metadata'
        ]
        read_only_fields = [
            'id', 'uuid', 'created_at', 'assigned_at', 'started_at', 'completed_at',
            'assigned_by', 'is_overdue'
        ]


class WorkflowRuleSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowRule model."""
    
    workflow_type_display = serializers.CharField(source='workflow_type.name', read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowRule
        fields = [
            'id', 'uuid', 'workflow_type', 'workflow_type_display',
            'name', 'description', 'rule_type', 'rule_type_display',
            'conditions', 'actions', 'is_active', 'execution_order',
            'created_at', 'created_by', 'created_by_display', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'created_by']
    
    def create(self, validated_data):
        """Set created_by when creating new rule."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowNotificationSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowNotification model."""
    
    workflow_instance_display = serializers.CharField(
        source='workflow_instance.workflow_type.name', 
        read_only=True
    )
    recipient_display = serializers.CharField(source='recipient.get_full_name', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = WorkflowNotification
        fields = [
            'id', 'uuid', 'workflow_instance', 'workflow_instance_display',
            'notification_type', 'notification_type_display', 'recipient',
            'recipient_display', 'subject', 'message', 'notification_data',
            'created_at', 'sent_at', 'status', 'status_display',
            'error_message', 'channels', 'metadata'
        ]
        read_only_fields = '__all__'


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTemplate model."""
    
    workflow_type_display = serializers.CharField(source='get_workflow_type_display', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    document_types_display = serializers.StringRelatedField(
        source='document_types', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'uuid', 'name', 'description', 'workflow_type',
            'workflow_type_display', 'states_config', 'transitions_config',
            'tasks_config', 'rules_config', 'document_types',
            'document_types_display', 'is_active', 'is_default',
            'version', 'created_at', 'created_by', 'created_by_display',
            'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'created_by', 'version']
    
    def create(self, validated_data):
        """Set created_by and handle version when creating template."""
        validated_data['created_by'] = self.context['request'].user
        
        # Auto-increment version if template with same name exists
        existing_template = WorkflowTemplate.objects.filter(
            name=validated_data['name']
        ).order_by('-version').first()
        
        if existing_template:
            validated_data['version'] = existing_template.version + 1
        
        return super().create(validated_data)


# Action serializers for workflow operations
class WorkflowTransitionActionSerializer(serializers.Serializer):
    """Serializer for workflow transition actions."""
    
    transition_name = serializers.CharField(max_length=100)
    comment = serializers.CharField(required=False, allow_blank=True)
    transition_data = serializers.DictField(required=False, default=dict)
    
    def validate_transition_name(self, value):
        """Validate transition name."""
        valid_transitions = [
            'submit_for_review', 'start_review', 'complete_review',
            'approve', 'reject', 'make_effective', 'obsolete', 'terminate'
        ]
        
        if value not in valid_transitions:
            raise serializers.ValidationError(f"Invalid transition: {value}")
        
        return value


class WorkflowInitiationSerializer(serializers.Serializer):
    """Serializer for workflow initiation."""
    
    workflow_type = serializers.CharField(max_length=20)
    document_id = serializers.UUIDField()
    due_date = serializers.DateTimeField(required=False)
    assignee = serializers.CharField(required=False, allow_blank=True)
    initial_data = serializers.DictField(required=False, default=dict)
    
    def validate_workflow_type(self, value):
        """Validate workflow type."""
        valid_types = ['REVIEW', 'UP_VERSION', 'OBSOLETE', 'TERMINATE']
        
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid workflow type: {value}")
        
        # Check if workflow type is active
        if not WorkflowType.objects.filter(workflow_type=value, is_active=True).exists():
            raise serializers.ValidationError(f"Workflow type {value} is not active")
        
        return value
    
    def validate_document_id(self, value):
        """Validate document exists."""
        from apps.documents.models import Document
        
        try:
            Document.objects.get(uuid=value)
        except Document.DoesNotExist:
            raise serializers.ValidationError("Document not found")
        
        return value


class TaskCompletionSerializer(serializers.Serializer):
    """Serializer for task completion."""
    
    completion_note = serializers.CharField(required=False, allow_blank=True)
    result_data = serializers.DictField(required=False, default=dict)
    
    def validate(self, data):
        """Validate task completion data."""
        task = self.context.get('task')
        if not task:
            raise serializers.ValidationError("Task context not provided")
        
        if task.status not in ['PENDING', 'IN_PROGRESS']:
            raise serializers.ValidationError("Task cannot be completed in current status")
        
        return data


class WorkflowStatusSerializer(serializers.Serializer):
    """Serializer for workflow status information."""
    
    has_active_workflow = serializers.BooleanField(read_only=True)
    workflow_type = serializers.CharField(read_only=True, required=False)
    current_state = serializers.CharField(read_only=True, required=False)
    current_assignee = serializers.CharField(read_only=True, required=False)
    started_at = serializers.DateTimeField(read_only=True, required=False)
    due_date = serializers.DateTimeField(read_only=True, required=False)
    is_overdue = serializers.BooleanField(read_only=True, required=False)
    pending_tasks = serializers.IntegerField(read_only=True, required=False)
    
    # Available actions for current state
    available_transitions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        required=False
    )
    
    # User permissions for workflow actions
    can_transition = serializers.BooleanField(read_only=True, required=False)
    can_complete_tasks = serializers.BooleanField(read_only=True, required=False)


class WorkflowHistorySerializer(serializers.Serializer):
    """Serializer for workflow history information."""
    
    workflow_type = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, required=False)
    initiated_by = serializers.CharField(read_only=True)
    current_state = serializers.CharField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    # Nested transitions and tasks
    transitions = serializers.ListField(read_only=True)
    tasks = serializers.ListField(read_only=True)


class PendingTaskSummarySerializer(serializers.Serializer):
    """Serializer for pending task summary."""
    
    task_id = serializers.UUIDField(read_only=True)
    workflow_type = serializers.CharField(read_only=True)
    document_number = serializers.CharField(read_only=True)
    document_title = serializers.CharField(read_only=True)
    task_name = serializers.CharField(read_only=True)
    task_type = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    due_date = serializers.DateTimeField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True)
    
    # Workflow context
    workflow_state = serializers.CharField(read_only=True)
    workflow_started = serializers.DateTimeField(read_only=True)
    initiated_by = serializers.CharField(read_only=True)



class WorkflowMetricsSerializer(serializers.Serializer):
    """Serializer for workflow metrics and statistics."""
    
    total_workflows = serializers.IntegerField(read_only=True)
    active_workflows = serializers.IntegerField(read_only=True)
    completed_workflows = serializers.IntegerField(read_only=True)
    overdue_workflows = serializers.IntegerField(read_only=True)
    
    # Task metrics
    total_tasks = serializers.IntegerField(read_only=True)
    pending_tasks = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    overdue_tasks = serializers.IntegerField(read_only=True)
    
    # Performance metrics
    avg_completion_time = serializers.FloatField(read_only=True)
    avg_task_completion_time = serializers.FloatField(read_only=True)
    
    # By workflow type
    workflows_by_type = serializers.DictField(read_only=True)
    tasks_by_type = serializers.DictField(read_only=True)
    
    # Recent activity
    recent_completions = serializers.IntegerField(read_only=True)
    recent_initiations = serializers.IntegerField(read_only=True)
class DocumentStateSerializer(serializers.ModelSerializer):
    """Serializer for DocumentState model."""
    
    class Meta:
        model = DocumentState
        fields = [
            'code', 'name', 'description', 
            'is_initial', 'is_final'
        ]
        read_only_fields = ['code']


class DocumentWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for DocumentWorkflow model."""
    
    current_state = DocumentStateSerializer(read_only=True)
    initiated_by = serializers.StringRelatedField(read_only=True)
    current_assignee = serializers.StringRelatedField(read_only=True)
    selected_reviewer = serializers.StringRelatedField(read_only=True)
    selected_approver = serializers.StringRelatedField(read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    document_number = serializers.CharField(source='document.document_number', read_only=True)
    
    class Meta:
        model = DocumentWorkflow
        fields = [
            'uuid', 'document', 'document_title', 'document_number',
            'workflow_type', 'current_state', 'initiated_by', 
            'current_assignee', 'selected_reviewer', 'selected_approver',
            'created_at', 'updated_at', 'due_date', 'effective_date',
            'obsoleting_date', 'workflow_data', 'up_version_reason',
            'obsoleting_reason', 'termination_reason', 'is_terminated',
            'last_approved_state'
        ]


class DocumentTransitionSerializer(serializers.ModelSerializer):
    """Serializer for DocumentTransition model."""
    
    workflow = DocumentWorkflowSerializer(read_only=True)
    from_state = DocumentStateSerializer(read_only=True)
    to_state = DocumentStateSerializer(read_only=True)
    transitioned_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = DocumentTransition
        fields = [
            'uuid', 'workflow', 'from_state', 'to_state',
            'transitioned_by', 'transitioned_at', 'comment',
            'transition_data'
        ]
        read_only_fields = '__all__'
