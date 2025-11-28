"""
News Feed API Views

Quick implementation of missing endpoints for the news feed.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from django.utils import timezone
from datetime import timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_documents(request):
    """Get user's documents for news feed."""
    try:
        from apps.documents.models import Document
        user = request.user
        
        # Get user's documents with basic filtering
        docs = Document.objects.filter(
            models.Q(author=user) | 
            models.Q(reviewer=user) | 
            models.Q(approver=user)
        ).distinct()
        
        # Convert to list format expected by news feed
        doc_list = []
        for doc in docs:
            doc_list.append({
                'id': doc.id,
                'document_number': doc.document_number,
                'title': doc.title,
                'status': doc.status,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'effective_date': doc.effective_date.isoformat() if doc.effective_date else None,
                'author': {'id': doc.author.id, 'username': doc.author.username} if doc.author else None,
                'reviewer': {'id': doc.reviewer.id, 'username': doc.reviewer.username} if doc.reviewer else None,
                'approver': {'id': doc.approver.id, 'username': doc.approver.username} if doc.approver else None
            })
        
        return Response(doc_list)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tasks(request):
    """Get user's workflow tasks for news feed."""
    try:
        from apps.workflows.models import DocumentWorkflow
        user = request.user
        
        # Get workflows related to user
        workflows = DocumentWorkflow.objects.filter(
            models.Q(current_assignee=user) | 
            models.Q(document__author=user) |
            models.Q(document__reviewer=user) |
            models.Q(document__approver=user),
            is_terminated=False
        ).distinct().select_related('document', 'current_state')
        
        # Convert to list format
        workflow_list = []
        for workflow in workflows:
            workflow_list.append({
                'id': workflow.id,
                'document': {
                    'document_number': workflow.document.document_number,
                    'title': workflow.document.title
                },
                'current_state': {
                    'name': workflow.current_state.name if workflow.current_state else 'Unknown'
                },
                'due_date': workflow.due_date.isoformat() if workflow.due_date else None,
                'created_at': workflow.created_at.isoformat() if workflow.created_at else None
            })
        
        return Response(workflow_list)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_notifications(request):
    """Get recent notifications for news feed."""
    try:
        from apps.scheduler.models import NotificationQueue
        user = request.user
        
        # Get recent notifications for user
        recent_date = timezone.now() - timedelta(days=7)
        notifications = NotificationQueue.objects.filter(
            models.Q(recipients=user) | models.Q(created_by=user),
            created_at__gte=recent_date
        ).distinct().order_by('-created_at')[:10]
        
        # Convert to list format
        notif_list = []
        for notif in notifications:
            notif_list.append({
                'id': notif.id,
                'subject': notif.subject,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'priority': notif.priority,
                'status': notif.status,
                'created_at': notif.created_at.isoformat(),
                'scheduled_at': notif.scheduled_at.isoformat() if notif.scheduled_at else None,
                'sent_at': notif.sent_at.isoformat() if notif.sent_at else None
            })
        
        return Response(notif_list)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Get system status for news feed."""
    try:
        from apps.documents.models import Document
        from apps.workflows.models import DocumentWorkflow
        from apps.scheduler.models import ScheduledTask
        
        # Basic system statistics
        stats = {
            'overall_status': 'HEALTHY',
            'timestamp': timezone.now().isoformat(),
            'system_statistics': {
                'documents': {
                    'total': Document.objects.count(),
                    'active': Document.objects.filter(is_active=True).count(),
                    'effective': Document.objects.filter(status='EFFECTIVE').count()
                },
                'workflows': {
                    'active': DocumentWorkflow.objects.filter(is_terminated=False).count()
                },
                'scheduler': {
                    'active_tasks': ScheduledTask.objects.filter(status='ACTIVE').count()
                }
            },
            'recommendations': []
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response({
            'overall_status': 'ERROR',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)