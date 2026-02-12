"""
Document-Workflow Integration Views

Provides backward-compatible workflow endpoints under the documents app
to maintain frontend compatibility while using the simplified workflow system.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Document
from apps.workflows.services import get_simple_workflow_service
from apps.users.permissions import CanManageDocuments
from apps.scheduler.notification_service import notification_service


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanManageDocuments])
def document_workflow_endpoint(request, uuid):
    """
    Backward-compatible document workflow endpoint.
    
    Proxies requests to the new simplified workflow API while maintaining
    the old endpoint structure for frontend compatibility.
    
    GET: Returns workflow status for document
    POST: Executes workflow action on document
    """
    try:
        document = get_object_or_404(Document, uuid=uuid)
    except Document.DoesNotExist:
        return Response({
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    workflow_service = get_simple_workflow_service()
    
    if request.method == 'GET':
        # Get workflow status
        try:
            workflow_status = workflow_service.get_document_workflow_status(document)
            return Response(workflow_status)
        except Exception as e:
            return Response({
                'error': f'Failed to get workflow status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # Execute workflow action
        action = request.data.get('action')
        comment = request.data.get('comment', '')
        
        if not action:
            return Response({
                'error': 'Action is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Execute the action using simplified workflow service
            if action == 'submit_for_review':
                # For submit_for_review, first ensure workflow exists
                try:
                    result = workflow_service.submit_for_review(document, request.user, comment)
                except Exception as e:
                    error_msg = str(e)
                    if 'No active workflow found' in error_msg:
                        # Auto-start workflow and then submit
                        workflow_service.start_review_workflow(
                            document=document,
                            initiated_by=request.user,
                            reviewer=document.reviewer,
                            approver=document.approver
                        )
                        # Now try submit again
                        result = workflow_service.submit_for_review(document, request.user, comment)
                    else:
                        raise e
                
                # Send notification to reviewer after successful submission
                if result and document.reviewer:
                    notification_service.send_task_email(document.reviewer, 'Review', document)
            
            elif action == 'start_review':
                result = workflow_service.start_review(document, request.user, comment)
                # Send notification to reviewer
                if result and document.reviewer:
                    notification_service.send_task_email(document.reviewer, 'Review', document)
            elif action == 'complete_review':
                approved = request.data.get('approved', True)
                result = workflow_service.complete_review(document, request.user, approved, comment)
            elif action == 'route_for_approval':
                approver_id = request.data.get('approver_id')
                if not approver_id:
                    return Response({
                        'error': 'approver_id is required for route_for_approval action'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                from apps.users.models import User
                try:
                    approver = User.objects.get(id=approver_id)
                except User.DoesNotExist:
                    return Response({
                        'error': f'Approver with ID {approver_id} not found'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = workflow_service.route_for_approval(document, request.user, approver, comment)
                # Send notification to approver
                if result:
                    notification_service.send_task_email(approver, 'Approval', document)
            elif action == 'approve_document' or action == 'approve':
                effective_date = request.data.get('effective_date')
                if not effective_date:
                    return Response({
                        'error': 'effective_date is required for approval'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Parse effective_date if it's a string
                if isinstance(effective_date, str):
                    from datetime import datetime
                    try:
                        effective_date = datetime.fromisoformat(effective_date.replace('Z', '')).date()
                    except ValueError:
                        return Response({
                            'error': 'Invalid effective_date format. Use YYYY-MM-DD'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get approved flag, review_period_months, and sensitivity label for approval
                approved = request.data.get('approved', True)
                review_period_months = request.data.get('review_period_months')
                sensitivity_label = request.data.get('sensitivity_label')
                sensitivity_change_reason = request.data.get('sensitivity_change_reason', '')
                
                result = workflow_service.approve_document(
                    document, request.user, effective_date, comment, 
                    approved, review_period_months,
                    sensitivity_label, sensitivity_change_reason
                )
                # Send notification to document author about approval
                if result and document.author:
                    # Check if document is immediately effective or scheduled
                    from datetime import date
                    if document.effective_date and document.effective_date <= date.today():
                        notification_service.send_document_effective_notification(document)
                    else:
                        # Document approved but not yet effective
                        from django.core.mail import send_mail
                        from django.conf import settings
                        send_mail(
                            f'Document Approved: {document.document_number}',
                            f'''Your document has been approved and will become effective on {document.effective_date}.

Document: {document.document_number} - {document.title}
Approved by: {request.user.get_full_name()}
Effective Date: {document.effective_date}
{f"Next Review: {document.next_review_date}" if document.next_review_date else ""}

The document will automatically become effective on the scheduled date.

---
EDMS - Electronic Document Management System
''',
                            settings.DEFAULT_FROM_EMAIL,
                            [document.author.email],
                            fail_silently=True,
                        )
            # make_effective action removed - documents become effective automatically
            # via scheduler or immediately upon approval based on effective_date
            elif action == 'terminate_workflow':
                reason = request.data.get('reason', comment)
                result = workflow_service.terminate_workflow(document, request.user, reason)
            else:
                return Response({
                    'error': f'Unknown action: {action}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result:
                # Get updated workflow status
                workflow_status = workflow_service.get_document_workflow_status(document)
                return Response({
                    'success': True,
                    'message': f'Action {action} completed successfully',
                    'workflow_status': workflow_status
                })
            else:
                return Response({
                    'success': False,
                    'message': f'Action {action} failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Workflow action failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageDocuments])
def document_workflow_history(request, uuid):
    """
    Get workflow history for a document.
    
    Maintains backward compatibility for frontend history requests.
    """
    try:
        document = get_object_or_404(Document, uuid=uuid)
    except Document.DoesNotExist:
        return Response({
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        workflow_service = get_simple_workflow_service()
        history = workflow_service.get_workflow_history(document)
        
        return Response({
            'document_id': str(uuid),
            'document_number': document.document_number,
            'workflow_history': history
        })
    except Exception as e:
        return Response({
            'error': f'Failed to get workflow history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)