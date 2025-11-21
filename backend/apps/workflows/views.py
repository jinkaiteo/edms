"""
Views for Workflow Management.

Provides REST API views for workflow management, task handling,
and workflow operations with proper permission controls.
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.permissions import CanManageDocuments, CanManageWorkflows
from apps.documents.models import Document
from .models import (
    WorkflowType, WorkflowInstance, WorkflowTransition,
    WorkflowTask, WorkflowRule, WorkflowNotification,
    WorkflowTemplate
)
from .serializers import (
    WorkflowTypeSerializer, WorkflowInstanceSerializer,
    WorkflowTransitionSerializer, WorkflowTaskSerializer,
    WorkflowRuleSerializer, WorkflowNotificationSerializer,
    WorkflowTemplateSerializer, WorkflowTransitionActionSerializer,
    WorkflowInitiationSerializer, TaskCompletionSerializer,
    WorkflowStatusSerializer, WorkflowHistorySerializer,
    PendingTaskSummarySerializer, WorkflowMetricsSerializer
)
from .services import workflow_service, document_workflow_service


class WorkflowTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow types.
    
    Provides CRUD operations for workflow type configuration
    with proper permission controls.
    """
    
    queryset = WorkflowType.objects.all()
    serializer_class = WorkflowTypeSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageWorkflows]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workflow_type', 'is_active', 'requires_approval']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'workflow_type', 'created_at']
    ordering = ['name']


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow instances.
    
    Provides comprehensive workflow instance management
    with state transitions and task handling.
    """
    
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'workflow_type', 'state', 'is_active', 'is_completed',
        'initiated_by', 'current_assignee'
    ]
    search_fields = ['workflow_type__name']
    ordering_fields = ['started_at', 'due_date', 'completed_at']
    ordering = ['-started_at']
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Filter workflows based on user permissions."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Users can see workflows they initiated, are assigned to,
        # or have document access for
        return super().get_queryset().filter(
            Q(initiated_by=user) |
            Q(current_assignee=user) |
            Q(content_object__in=self._get_user_accessible_documents(user))
        ).distinct()
    
    def _get_user_accessible_documents(self, user):
        """Get documents user has access to."""
        return Document.objects.filter(
            Q(author=user) |
            Q(reviewer=user) |
            Q(approver=user) |
            Q(status='EFFECTIVE', is_active=True)
        )
    
    @action(detail=True, methods=['post'])
    def transition(self, request, uuid=None):
        """Execute workflow transition."""
        workflow_instance = self.get_object()
        serializer = WorkflowTransitionActionSerializer(data=request.data)
        
        if serializer.is_valid():
            transition_name = serializer.validated_data['transition_name']
            comment = serializer.validated_data.get('comment', '')
            transition_data = serializer.validated_data.get('transition_data', {})
            
            success = workflow_service.transition_workflow(
                workflow_instance,
                transition_name,
                request.user,
                comment,
                **transition_data
            )
            
            if success:
                # Return updated workflow instance
                updated_instance = WorkflowInstance.objects.get(uuid=uuid)
                response_serializer = self.get_serializer(updated_instance)
                return Response({
                    'success': True,
                    'message': f'Transition {transition_name} executed successfully',
                    'workflow': response_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': f'Failed to execute transition {transition_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, uuid=None):
        """Complete workflow instance."""
        workflow_instance = self.get_object()
        reason = request.data.get('reason', 'Manually completed')
        
        success = workflow_service.complete_workflow(workflow_instance, reason)
        
        if success:
            response_serializer = self.get_serializer(workflow_instance)
            return Response({
                'success': True,
                'message': 'Workflow completed successfully',
                'workflow': response_serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to complete workflow'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def history(self, request, uuid=None):
        """Get workflow transition history."""
        workflow_instance = self.get_object()
        transitions = WorkflowTransitionSerializer(
            workflow_instance.transitions.all(),
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'workflow_id': workflow_instance.uuid,
            'transitions': transitions
        })
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, uuid=None):
        """Get workflow tasks."""
        workflow_instance = self.get_object()
        tasks = WorkflowTaskSerializer(
            workflow_instance.tasks.all(),
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'workflow_id': workflow_instance.uuid,
            'tasks': tasks
        })


class WorkflowTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow tasks.
    
    Provides task management with assignment and completion
    tracking for workflow processes.
    """
    
    queryset = WorkflowTask.objects.all()
    serializer_class = WorkflowTaskSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'workflow_instance', 'task_type', 'priority', 'status',
        'assigned_to', 'assigned_by'
    ]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Filter tasks based on user permissions."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Users can see tasks assigned to them or tasks in workflows they have access to
        return super().get_queryset().filter(
            Q(assigned_to=user) |
            Q(workflow_instance__initiated_by=user) |
            Q(workflow_instance__current_assignee=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, uuid=None):
        """Complete a workflow task."""
        task = self.get_object()
        serializer = TaskCompletionSerializer(
            data=request.data,
            context={'task': task}
        )
        
        if serializer.is_valid():
            completion_note = serializer.validated_data.get('completion_note', '')
            result_data = serializer.validated_data.get('result_data', {})
            
            # Check if user can complete this task
            if task.assigned_to != request.user and not request.user.is_superuser:
                return Response({
                    'error': 'You can only complete tasks assigned to you'
                }, status=status.HTTP_403_FORBIDDEN)
            
            task.complete_task(completion_note, result_data)
            
            response_serializer = self.get_serializer(task)
            return Response({
                'success': True,
                'message': 'Task completed successfully',
                'task': response_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start(self, request, uuid=None):
        """Start working on a task."""
        task = self.get_object()
        
        if task.assigned_to != request.user and not request.user.is_superuser:
            return Response({
                'error': 'You can only start tasks assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != 'PENDING':
            return Response({
                'error': 'Task can only be started from pending status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'IN_PROGRESS'
        task.started_at = timezone.now()
        task.save()
        
        response_serializer = self.get_serializer(task)
        return Response({
            'success': True,
            'message': 'Task started successfully',
            'task': response_serializer.data
        })


class WorkflowTransitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing workflow transitions.
    
    Provides read-only access to workflow transition history
    for audit and tracking purposes.
    """
    
    queryset = WorkflowTransition.objects.all()
    serializer_class = WorkflowTransitionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        'workflow_instance', 'from_state', 'to_state',
        'transition_name', 'transitioned_by'
    ]
    ordering_fields = ['transitioned_at']
    ordering = ['-transitioned_at']
    
    def get_queryset(self):
        """Filter transitions based on user permissions."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Users can see transitions for workflows they have access to
        return super().get_queryset().filter(
            Q(workflow_instance__initiated_by=user) |
            Q(workflow_instance__current_assignee=user) |
            Q(transitioned_by=user)
        ).distinct()


class WorkflowRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow rules.
    
    Provides CRUD operations for workflow rule configuration
    with business logic validation.
    """
    
    queryset = WorkflowRule.objects.all()
    serializer_class = WorkflowRuleSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageWorkflows]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workflow_type', 'rule_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['execution_order', 'name', 'created_at']
    ordering = ['execution_order', 'name']


class WorkflowNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing workflow notifications.
    
    Provides read-only access to workflow notifications
    for tracking communication history.
    """
    
    queryset = WorkflowNotification.objects.all()
    serializer_class = WorkflowNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        'workflow_instance', 'notification_type', 'recipient', 'status'
    ]
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter notifications based on user permissions."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Users can see their own notifications
        return super().get_queryset().filter(recipient=user)


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow templates.
    
    Provides CRUD operations for workflow template configuration
    and template application.
    """
    
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageWorkflows]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workflow_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'version', 'created_at']
    ordering = ['name', '-version']
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply template to create a workflow type."""
        template = self.get_object()
        
        # Create workflow type from template
        workflow_type = WorkflowType.objects.create(
            name=f"{template.name} (from template)",
            workflow_type=template.workflow_type,
            description=template.description,
            is_active=True,
            created_by=request.user,
            metadata={
                'template_id': str(template.uuid),
                'template_version': template.version
            }
        )
        
        return Response({
            'success': True,
            'message': 'Template applied successfully',
            'workflow_type_id': workflow_type.id
        })


class DocumentWorkflowAPIView(APIView):
    """
    API view for document-specific workflow operations.
    
    Provides document-focused workflow management including
    initiation, status checking, and workflow actions.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def get(self, request, document_uuid):
        """Get workflow status for a document."""
        try:
            document = Document.objects.get(uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        workflow_status = document_workflow_service.get_document_workflow_status(document)
        
        # Add available actions based on current state and user permissions
        if workflow_status.get('has_active_workflow'):
            # TODO: Get available transitions from River
            workflow_status['available_actions'] = self._get_available_actions(
                document, request.user
            )
        
        serializer = WorkflowStatusSerializer(workflow_status)
        return Response(serializer.data)
    
    def post(self, request, document_uuid):
        """Initiate workflow for a document."""
        try:
            document = Document.objects.get(uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WorkflowInitiationSerializer(data=request.data)
        
        if serializer.is_valid():
            workflow_type = serializer.validated_data['workflow_type']
            due_date = serializer.validated_data.get('due_date')
            initial_data = serializer.validated_data.get('initial_data', {})
            
            # Initiate workflow based on type
            if workflow_type == 'REVIEW':
                workflow = document_workflow_service.start_review_workflow(
                    document, request.user, due_date=due_date
                )
            elif workflow_type == 'OBSOLETE':
                reason = initial_data.get('reason', '')
                workflow = document_workflow_service.start_obsolete_workflow(
                    document, request.user, reason
                )
            else:
                workflow = workflow_service.initiate_workflow(
                    document, workflow_type, request.user, **initial_data
                )
            
            workflow_serializer = WorkflowInstanceSerializer(workflow)
            return Response({
                'success': True,
                'message': f'{workflow_type} workflow initiated successfully',
                'workflow': workflow_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_available_actions(self, document, user):
        """Get available workflow actions for document and user."""
        actions = []
        
        # Check document permissions and current state
        if document.can_edit(user) and document.status == 'DRAFT':
            actions.append('submit_for_review')
        
        if document.can_review(user) and document.status in ['PENDING_REVIEW', 'UNDER_REVIEW']:
            actions.extend(['complete_review', 'reject'])
        
        if document.can_approve(user) and document.status in ['PENDING_APPROVAL', 'UNDER_APPROVAL']:
            actions.extend(['approve', 'reject'])
        
        if document.can_approve(user) and document.status == 'APPROVED':
            actions.append('make_effective')
        
        return actions


class WorkflowHistoryAPIView(APIView):
    """
    API view for workflow history.
    
    Provides comprehensive workflow history for documents
    with audit trail information.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def get(self, request, document_uuid):
        """Get workflow history for a document."""
        try:
            document = Document.objects.get(uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        history = workflow_service.get_workflow_history(document)
        serializer = WorkflowHistorySerializer(history, many=True)
        
        return Response({
            'document_id': document_uuid,
            'document_number': document.document_number,
            'workflow_history': serializer.data
        })


class MyTasksAPIView(APIView):
    """
    API view for user's workflow tasks.
    
    Provides personalized task management for users
    with filtering and prioritization.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get pending tasks for current user."""
        user = request.user
        
        # Get pending tasks
        pending_tasks = workflow_service.get_pending_tasks(user)
        overdue_tasks = workflow_service.get_overdue_tasks(user)
        
        # Serialize task data with document information
        task_data = []
        for task in pending_tasks:
            document = task.workflow_instance.content_object
            task_info = {
                'task_id': task.uuid,
                'workflow_type': task.workflow_instance.workflow_type.workflow_type,
                'document_number': document.document_number if document else 'N/A',
                'document_title': document.title if document else 'N/A',
                'task_name': task.name,
                'task_type': task.task_type,
                'priority': task.priority,
                'due_date': task.due_date,
                'days_remaining': task.days_remaining,
                'is_overdue': task.is_overdue,
                'assigned_at': task.assigned_at,
                'workflow_state': str(task.workflow_instance.state),
                'workflow_started': task.workflow_instance.started_at,
                'initiated_by': task.workflow_instance.initiated_by.get_full_name()
            }
            task_data.append(task_info)
        
        serializer = PendingTaskSummarySerializer(task_data, many=True)
        
        return Response({
            'pending_tasks': serializer.data,
            'total_pending': len(pending_tasks),
            'total_overdue': len(overdue_tasks),
            'summary': {
                'high_priority': len([t for t in pending_tasks if t.priority == 'HIGH']),
                'urgent': len([t for t in pending_tasks if t.priority == 'URGENT']),
                'due_today': len([t for t in pending_tasks if t.days_remaining == 0]),
                'due_this_week': len([t for t in pending_tasks if t.days_remaining and t.days_remaining <= 7])
            }
        })


class WorkflowMetricsAPIView(APIView):
    """
    API view for workflow metrics and analytics.
    
    Provides workflow performance metrics and statistics
    for management and reporting.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageWorkflows]
    
    def get(self, request):
        """Get workflow metrics and statistics."""
        # Basic workflow counts
        total_workflows = WorkflowInstance.objects.count()
        active_workflows = WorkflowInstance.objects.filter(is_active=True).count()
        completed_workflows = WorkflowInstance.objects.filter(is_completed=True).count()
        overdue_workflows = WorkflowInstance.objects.filter(
            due_date__lt=timezone.now(),
            is_active=True
        ).count()
        
        # Task metrics
        total_tasks = WorkflowTask.objects.count()
        pending_tasks = WorkflowTask.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        ).count()
        completed_tasks = WorkflowTask.objects.filter(status='COMPLETED').count()
        overdue_tasks = WorkflowTask.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['PENDING', 'IN_PROGRESS']
        ).count()
        
        # Performance metrics
        completed_workflow_times = WorkflowInstance.objects.filter(
            is_completed=True,
            completed_at__isnull=False
        ).extra(
            select={'duration': 'EXTRACT(epoch FROM completed_at - started_at)'}
        ).values_list('duration', flat=True)
        
        avg_completion_time = sum(completed_workflow_times) / len(completed_workflow_times) if completed_workflow_times else 0
        
        # Workflows by type
        workflows_by_type = dict(
            WorkflowInstance.objects.values('workflow_type__workflow_type')
            .annotate(count=Count('id'))
            .values_list('workflow_type__workflow_type', 'count')
        )
        
        # Tasks by type
        tasks_by_type = dict(
            WorkflowTask.objects.values('task_type')
            .annotate(count=Count('id'))
            .values_list('task_type', 'count')
        )
        
        # Recent activity (last 30 days)
        last_30_days = timezone.now() - timezone.timedelta(days=30)
        recent_completions = WorkflowInstance.objects.filter(
            completed_at__gte=last_30_days
        ).count()
        recent_initiations = WorkflowInstance.objects.filter(
            started_at__gte=last_30_days
        ).count()
        
        metrics_data = {
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'completed_workflows': completed_workflows,
            'overdue_workflows': overdue_workflows,
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'avg_completion_time': avg_completion_time / 3600 if avg_completion_time else 0,  # Convert to hours
            'avg_task_completion_time': 0,  # TODO: Calculate task completion time
            'workflows_by_type': workflows_by_type,
            'tasks_by_type': tasks_by_type,
            'recent_completions': recent_completions,
            'recent_initiations': recent_initiations
        }
        
        serializer = WorkflowMetricsSerializer(metrics_data)
        return Response(serializer.data)