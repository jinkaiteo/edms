"""
Enhanced workflow views with user selection capabilities.
Adds API endpoints for manual reviewer/approver assignment.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import DocumentWorkflow, DocumentState, WorkflowType
from .serializers import DocumentWorkflowSerializer
from apps.users.serializers import UserSerializer
from apps.documents.models import Document

User = get_user_model()


class WorkflowUserSelectionViewSet(viewsets.ViewSet):
    """
    ViewSet for user selection in workflows.
    Provides endpoints to get available reviewers and approvers.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def reviewers(self, request):
        """
        Get available users for document review.
        Filters users with review permissions.
        """
        document_type = request.query_params.get('document_type')
        department = request.query_params.get('department')
        
        # Base query for users with review permissions
        reviewers = User.objects.filter(
            Q(groups__name__icontains='reviewer') |
            Q(user_permissions__codename='can_review_document') |
            Q(is_staff=True)
        ).filter(is_active=True).distinct()
        
        # Filter by document type if specified
        if document_type:
            # Add document type specific filtering logic here
            reviewers = reviewers.filter(
                Q(groups__name__icontains=document_type.lower()) |
                Q(groups__name__icontains='reviewer')
            )
        
        # Add workload information
        reviewer_data = []
        for user in reviewers:
            # Count active review tasks
            active_reviews = DocumentWorkflow.objects.filter(
                current_assignee=user,
                current_state__code__in=['UNDER_REVIEW', 'PENDING_REVIEW']
            ).count()
            
            reviewer_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'active_reviews': active_reviews,
                'workload_status': 'high' if active_reviews > 5 else 'normal' if active_reviews > 2 else 'low',
                'department': getattr(user, 'department', 'Unknown'),
                'is_available': active_reviews < 10  # Simple availability check
            })
        
        return Response({
            'reviewers': reviewer_data,
            'total_count': len(reviewer_data)
        })

    @action(detail=False, methods=['get'])
    def approvers(self, request):
        """
        Get available users for document approval.
        Filters users with approval permissions.
        """
        document_type = request.query_params.get('document_type')
        criticality = request.query_params.get('criticality', 'normal')
        
        # Base query for users with approval permissions
        approvers = User.objects.filter(
            Q(groups__name__icontains='approver') |
            Q(groups__name__icontains='manager') |
            Q(user_permissions__codename='can_approve_document') |
            Q(is_superuser=True)
        ).filter(is_active=True).distinct()
        
        # Filter by criticality level
        if criticality == 'high':
            approvers = approvers.filter(
                Q(groups__name__icontains='senior') |
                Q(groups__name__icontains='manager') |
                Q(is_superuser=True)
            )
        
        # Add workload information
        approver_data = []
        for user in approvers:
            # Count active approval tasks
            active_approvals = DocumentWorkflow.objects.filter(
                current_assignee=user,
                current_state__code__in=['UNDER_APPROVAL', 'PENDING_APPROVAL']
            ).count()
            
            approver_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'active_approvals': active_approvals,
                'workload_status': 'high' if active_approvals > 3 else 'normal' if active_approvals > 1 else 'low',
                'approval_level': 'senior' if user.groups.filter(name__icontains='senior').exists() else 'standard',
                'department': getattr(user, 'department', 'Unknown'),
                'is_available': active_approvals < 5  # Simple availability check
            })
        
        return Response({
            'approvers': approver_data,
            'total_count': len(approver_data)
        })

    @action(detail=False, methods=['get'])
    def user_workload(self, request):
        """
        Get detailed workload information for a specific user.
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter required'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        # Get user's active workflows
        active_workflows = DocumentWorkflow.objects.filter(
            current_assignee=user,
            current_state__is_final=False
        ).select_related('document', 'current_state')
        
        workload_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'email': user.email
            },
            'active_tasks': [],
            'summary': {
                'total_active': 0,
                'pending_review': 0,
                'pending_approval': 0,
                'overdue': 0
            }
        }
        
        for workflow in active_workflows:
            task_data = {
                'workflow_id': workflow.id,
                'document_title': workflow.document.title,
                'current_state': workflow.current_state.name,
                'due_date': workflow.due_date.isoformat() if workflow.due_date else None,
                'is_overdue': workflow.due_date < timezone.now() if workflow.due_date else False,
                'days_remaining': (workflow.due_date - timezone.now()).days if workflow.due_date else None
            }
            workload_data['active_tasks'].append(task_data)
            
            # Update summary
            workload_data['summary']['total_active'] += 1
            if 'REVIEW' in workflow.current_state.code:
                workload_data['summary']['pending_review'] += 1
            elif 'APPROVAL' in workflow.current_state.code:
                workload_data['summary']['pending_approval'] += 1
            if task_data['is_overdue']:
                workload_data['summary']['overdue'] += 1
        
        return Response(workload_data)


class EnhancedDocumentWorkflowViewSet(viewsets.ModelViewSet):
    """
    Enhanced workflow viewset with manual user assignment capabilities.
    """
    queryset = DocumentWorkflow.objects.all()
    serializer_class = DocumentWorkflowSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_with_assignments(self, request):
        """
        Create a new workflow with manual reviewer/approver assignment.
        """
        data = request.data
        
        # Validate required fields
        document_id = data.get('document_id')
        selected_reviewer_id = data.get('reviewer_id')
        selected_approver_id = data.get('approver_id')
        review_due_date = data.get('review_due_date')
        approval_due_date = data.get('approval_due_date')
        assignment_comment = data.get('comment', '')
        
        if not document_id:
            return Response({'error': 'document_id is required'}, status=400)
        
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found'}, status=404)
        
        # Validate selected users
        selected_reviewer = None
        selected_approver = None
        
        if selected_reviewer_id:
            try:
                selected_reviewer = User.objects.get(id=selected_reviewer_id, is_active=True)
                # TODO: Add permission validation for reviewer
            except User.DoesNotExist:
                return Response({'error': 'Selected reviewer not found'}, status=400)
        
        if selected_approver_id:
            try:
                selected_approver = User.objects.get(id=selected_approver_id, is_active=True)
                # TODO: Add permission validation for approver
            except User.DoesNotExist:
                return Response({'error': 'Selected approver not found'}, status=400)
        
        # Create workflow
        draft_state = DocumentState.objects.get(code='DRAFT')
        workflow = DocumentWorkflow.objects.create(
            document=document,
            current_state=draft_state,
            initiated_by=request.user,
            workflow_data={
                'selected_reviewer_id': selected_reviewer_id,
                'selected_approver_id': selected_approver_id,
                'assignment_method': 'manual',
                'assignment_comment': assignment_comment
            }
        )
        
        # Immediately transition to review if reviewer is selected
        if selected_reviewer:
            due_date = None
            if review_due_date:
                try:
                    due_date = timezone.datetime.fromisoformat(review_due_date.replace('Z', '+00:00'))
                except:
                    due_date = timezone.now() + timedelta(days=5)  # Default 5 days
            
            workflow.transition_to(
                'PENDING_REVIEW',
                user=request.user,
                assignee=selected_reviewer,
                comment=f'Manual assignment: {assignment_comment}',
                due_date=due_date
            )
        
        serializer = self.get_serializer(workflow)
        return Response({
            'workflow': serializer.data,
            'message': 'Workflow created with manual assignments',
            'assignments': {
                'reviewer': {
                    'id': selected_reviewer.id,
                    'username': selected_reviewer.username
                } if selected_reviewer else None,
                'approver': {
                    'id': selected_approver.id,
                    'username': selected_approver.username
                } if selected_approver else None
            }
        }, status=201)

    @action(detail=True, methods=['post'])
    def reassign(self, request, pk=None):
        """
        Reassign a workflow to a different user.
        """
        workflow = self.get_object()
        new_assignee_id = request.data.get('assignee_id')
        reason = request.data.get('reason', '')
        
        if not new_assignee_id:
            return Response({'error': 'assignee_id is required'}, status=400)
        
        try:
            new_assignee = User.objects.get(id=new_assignee_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'New assignee not found'}, status=400)
        
        # Validate permissions (TODO: Add proper permission checking)
        
        # Update assignment
        old_assignee = workflow.current_assignee
        workflow.current_assignee = new_assignee
        workflow.save()
        
        # Log the reassignment in workflow data
        if 'reassignment_history' not in workflow.workflow_data:
            workflow.workflow_data['reassignment_history'] = []
        
        workflow.workflow_data['reassignment_history'].append({
            'timestamp': timezone.now().isoformat(),
            'from_user': old_assignee.username if old_assignee else None,
            'to_user': new_assignee.username,
            'reassigned_by': request.user.username,
            'reason': reason
        })
        workflow.save()
        
        return Response({
            'message': 'Workflow reassigned successfully',
            'old_assignee': old_assignee.username if old_assignee else None,
            'new_assignee': new_assignee.username,
            'reason': reason
        })

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """
        Get workflows assigned to the current user.
        """
        user_workflows = DocumentWorkflow.objects.filter(
            current_assignee=request.user,
            current_state__is_final=False
        ).select_related('document', 'current_state', 'initiated_by')
        
        tasks = []
        for workflow in user_workflows:
            task_data = {
                'workflow_id': workflow.id,
                'document': {
                    'id': workflow.document.id,
                    'title': workflow.document.title,
                    'document_type': workflow.document.document_type.name if hasattr(workflow.document, 'document_type') else 'Unknown'
                },
                'current_state': {
                    'code': workflow.current_state.code,
                    'name': workflow.current_state.name
                },
                'initiated_by': workflow.initiated_by.username,
                'created_at': workflow.created_at.isoformat(),
                'due_date': workflow.due_date.isoformat() if workflow.due_date else None,
                'is_overdue': workflow.due_date < timezone.now() if workflow.due_date else False,
                'priority': 'high' if workflow.due_date and workflow.due_date < timezone.now() + timedelta(days=2) else 'normal'
            }
            tasks.append(task_data)
        
        # Sort by due date and priority
        tasks.sort(key=lambda x: (x['is_overdue'], x['due_date'] or '9999-12-31'))
        
        return Response({
            'tasks': tasks,
            'total_count': len(tasks),
            'overdue_count': sum(1 for task in tasks if task['is_overdue'])
        })