"""
Simple Workflow Views for EDMS.

Provides REST API views using the Simple Approach (DocumentWorkflow + DocumentLifecycleService)
for document lifecycle management with 21 CFR Part 11 compliance.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from apps.users.permissions import CanManageDocuments
from apps.documents.models import Document
from .models import DocumentWorkflow, DocumentState, DocumentTransition
from .document_lifecycle import get_document_lifecycle_service
from .serializers import DocumentWorkflowSerializer


class SimpleDocumentWorkflowAPIView(APIView):
    """
    Simple API view for document workflow operations.
    
    Uses the DocumentLifecycleService for straightforward workflow management.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def get(self, request, document_uuid):
        """Get workflow status for a document."""
        try:
            document = get_object_or_404(Document, uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get workflow status using simple approach
        lifecycle_service = get_document_lifecycle_service()
        workflow_status = lifecycle_service.get_document_workflow_status(document)
        
        return Response(workflow_status)
    
    def post(self, request, document_uuid):
        """Execute workflow action for a document."""
        try:
            document = get_object_or_404(Document, uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        action_type = request.data.get('action')
        comment = request.data.get('comment', '')
        
        if not action_type:
            return Response({
                'error': 'Action type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        lifecycle_service = get_document_lifecycle_service()
        
        try:
            # Execute workflow action based on type
            if action_type == 'submit_for_review':
                result = lifecycle_service.submit_for_review(document, request.user, comment)
            elif action_type == 'start_review':
                result = lifecycle_service.start_review(document, request.user, comment)
            elif action_type == 'complete_review':
                approved = request.data.get('approved', True)
                result = lifecycle_service.complete_review(document, request.user, approved, comment)
            elif action_type == 'approve_document':
                approved = request.data.get('approved', True)
                effective_date = request.data.get('effective_date')
                
                # APPROVAL REJECTION DEBUG LOGS
                print(f"🔥 APPROVAL DEBUG: action_type = {action_type}")
                print(f"🔥 APPROVAL DEBUG: raw request.data = {request.data}")
                print(f"🔥 APPROVAL DEBUG: approved = {approved} (type: {type(approved)})")
                print(f"🔥 APPROVAL DEBUG: effective_date = {effective_date}")
                print(f"🔥 APPROVAL DEBUG: comment = {comment}")
                print(f"🔥 APPROVAL DEBUG: user = {request.user.username}")
                print(f"🔥 APPROVAL DEBUG: document = {document.document_number}")
                print(f"🔥 APPROVAL DEBUG: document status = {document.status}")
                
                # Call the enhanced approve_document method
                print(f"🔥 APPROVAL DEBUG: Calling approve_document with approved={approved}")
                result = lifecycle_service.approve_document(document, request.user, effective_date, comment, approved)
                print(f"🔥 APPROVAL DEBUG: approve_document result = {result}")
            elif action_type == 'make_effective':
                result = lifecycle_service.make_effective(document, request.user, comment)
            elif action_type == 'terminate_workflow':
                reason = request.data.get('reason', comment)
                result = lifecycle_service.terminate_workflow(document, request.user, reason)
            elif action_type == 'start_version_workflow':
                version_data = {
                    'title': request.data.get('title'),
                    'description': request.data.get('description'), 
                    'reason_for_change': request.data.get('reason_for_change', ''),
                    'change_summary': request.data.get('change_summary', ''),
                    'major_increment': request.data.get('major_increment', False),
                    'reviewer': None,  # Will use existing reviewer
                    'approver': None   # Will use existing approver
                }
                
                if not version_data['reason_for_change']:
                    return Response({
                        'error': 'Reason for change is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not version_data['change_summary']:
                    return Response({
                        'error': 'Change summary is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = lifecycle_service.start_version_workflow(document, request.user, version_data)
                if result:
                    return Response({
                        'success': True,
                        'message': 'Version workflow started successfully',
                        'new_document_id': str(result['new_document'].uuid),
                        'new_document_number': result['new_document'].document_number,
                        'new_version': result['new_document'].version_string
                    })
            elif action_type == 'schedule_obsolescence':
                reason = request.data.get('reason')
                obsolescence_date = request.data.get('obsolescence_date')
                warning_days = request.data.get('warning_days', 30)
                replacement_document_id = request.data.get('replacement_document_id')
                
                if not reason:
                    return Response({
                        'error': 'Reason for obsolescence is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not obsolescence_date:
                    return Response({
                        'error': 'Obsolescence date is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Parse obsolescence_date
                from datetime import datetime, timezone
                try:
                    parsed_obsolescence_date = datetime.strptime(obsolescence_date, '%Y-%m-%d').date()
                    
                    # Validate future date
                    if parsed_obsolescence_date <= datetime.now().date():
                        return Response({
                            'error': 'Obsolescence date must be in the future'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
                except ValueError:
                    return Response({
                        'error': 'Invalid date format. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check user permissions
                if not (request.user.is_superuser or 
                       request.user.is_staff or
                       'approver' in request.user.username.lower() or
                       'admin' in request.user.username.lower()):
                    return Response({
                        'error': 'Insufficient permissions to schedule obsolescence'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Check for workflow conflicts
                validation = lifecycle_service.validate_obsolescence_eligibility(document)
                if not validation['can_obsolete']:
                    return Response({
                        'error': validation['reason'],
                        'conflicts': validation.get('conflicts', [])
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get replacement document if provided
                replacement_document = None
                if replacement_document_id:
                    try:
                        replacement_document = Document.objects.get(uuid=replacement_document_id)
                    except Document.DoesNotExist:
                        return Response({
                            'error': 'Replacement document not found'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    result = lifecycle_service.schedule_obsolescence(
                        document=document,
                        user=request.user,
                        reason=reason,
                        obsolescence_date=parsed_obsolescence_date,
                        warning_days=warning_days,
                        replacement_document=replacement_document
                    )
                except Exception as e:
                    return Response({
                        'error': f'Failed to schedule obsolescence: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                if result:
                    return Response({
                        'success': True,
                        'message': f'Document scheduled for obsolescence on {parsed_obsolescence_date.strftime("%B %d, %Y")}',
                        'obsolescence_date': obsolescence_date,
                        'warning_starts': result.get('warning_date'),
                        'replacement_document': replacement_document.document_number if replacement_document else None,
                        'status': 'scheduled_for_obsolescence'
                    })
            elif action_type == 'obsolete_document_directly':
                # OBSOLESCENCE DEBUG LOGGING
                print(f"🔥 OBSOLESCENCE DEBUG: Starting obsolescence process")
                print(f"🔥 OBSOLESCENCE DEBUG: Document = {document.document_number} (UUID: {document.uuid})")
                print(f"🔥 OBSOLESCENCE DEBUG: Document Status = {document.status}")
                print(f"🔥 OBSOLESCENCE DEBUG: User = {request.user.username}")
                print(f"🔥 OBSOLESCENCE DEBUG: Raw request data = {request.data}")
                
                reason = request.data.get('reason')
                obsolescence_date = request.data.get('obsolescence_date')  # Required
                
                print(f"🔥 OBSOLESCENCE DEBUG: Reason = {reason}")
                print(f"🔥 OBSOLESCENCE DEBUG: Obsolescence date = {obsolescence_date}")
                
                if not reason:
                    print(f"🔥 OBSOLESCENCE DEBUG: ERROR - No reason provided")
                    return Response({
                        'error': 'Reason for obsolescence is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not obsolescence_date:
                    return Response({
                        'error': 'Obsolescence date is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Parse and validate obsolescence date
                from datetime import datetime
                try:
                    obsolescence_date_obj = datetime.strptime(obsolescence_date, '%Y-%m-%d').date()
                    if obsolescence_date_obj < datetime.now().date():
                        return Response({
                            'error': 'Obsolescence date cannot be in the past'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({
                        'error': 'Invalid date format. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check user authority
                print(f"🔥 OBSOLESCENCE DEBUG: Checking user authority...")
                print(f"🔥 OBSOLESCENCE DEBUG: Document approver = {document.approver.username if document.approver else None}")
                print(f"🔥 OBSOLESCENCE DEBUG: User is approver = {request.user == document.approver}")
                print(f"🔥 OBSOLESCENCE DEBUG: User is staff = {request.user.is_staff}")
                print(f"🔥 OBSOLESCENCE DEBUG: User is superuser = {request.user.is_superuser}")
                
                has_authority = (
                    request.user == document.approver or  # Document approver
                    request.user.is_staff or  # System admin
                    request.user.is_superuser  # Superuser
                )
                
                print(f"🔥 OBSOLESCENCE DEBUG: Has authority = {has_authority}")
                
                if not has_authority:
                    print(f"🔥 OBSOLESCENCE DEBUG: ERROR - No authority")
                    return Response({
                        'error': 'You do not have authority to obsolete this document'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                try:
                    print(f"🔥 OBSOLESCENCE DEBUG: Calling obsolete_document_directly method...")
                    result = lifecycle_service.obsolete_document_directly(
                        document, request.user, reason, obsolescence_date_obj
                    )
                    print(f"🔥 OBSOLESCENCE DEBUG: Method result = {result}")
                    
                    if result:
                        print(f"🔥 OBSOLESCENCE DEBUG: SUCCESS - Obsolescence scheduled")
                        return Response({
                            'success': True,
                            'message': 'Document scheduled for obsolescence successfully',
                            'obsolescence_date': obsolescence_date,
                            'status': 'scheduled_for_obsolescence'
                        })
                    else:
                        print(f"🔥 OBSOLESCENCE DEBUG: ERROR - Method returned False")
                        
                except ValidationError as ve:
                    print(f"🔥 OBSOLESCENCE DEBUG: VALIDATION ERROR - {ve}")
                    return Response({
                        'error': str(ve)
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    print(f"🔥 OBSOLESCENCE DEBUG: UNEXPECTED ERROR - {e}")
                    import traceback
                    traceback.print_exc()
            elif action_type == 'approve_obsolescence':
                result = lifecycle_service.approve_obsolescence(document, request.user, comment)
                if result:
                    return Response({
                        'success': True,
                        'message': 'Document obsolescence approved successfully',
                        'status': 'obsolete'
                    })
            else:
                return Response({
                    'error': f'Unknown action: {action_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result:
                # Get updated workflow status
                workflow_status = lifecycle_service.get_document_workflow_status(document)
                return Response({
                    'success': True,
                    'message': f'Action {action_type} completed successfully',
                    'workflow_status': workflow_status
                })
            else:
                return Response({
                    'success': False,
                    'message': f'Action {action_type} failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Workflow action failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimpleWorkflowHistoryAPIView(APIView):
    """
    Simple API view for workflow history.
    
    Provides workflow history using the simple DocumentTransition model.
    """
    
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    
    def get(self, request, document_uuid):
        """Get workflow history for a document."""
        try:
            document = get_object_or_404(Document, uuid=document_uuid)
        except Document.DoesNotExist:
            return Response({
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get workflow history using simple approach
        workflow = DocumentWorkflow.objects.filter(document=document).first()
        if not workflow:
            return Response({
                'document_id': document_uuid,
                'document_number': document.document_number,
                'workflow_history': []
            })
        
        # Get all transitions for this workflow
        transitions = DocumentTransition.objects.filter(
            workflow=workflow
        ).select_related('from_state', 'to_state', 'transitioned_by').order_by('transitioned_at')
        
        history = []
        for transition in transitions:
            history.append({
                'from_state': transition.from_state.name,
                'to_state': transition.to_state.name,
                'transitioned_by': transition.transitioned_by.get_full_name(),
                'transitioned_at': transition.transitioned_at,
                'comment': transition.comment
            })
        
        return Response({
            'document_id': document_uuid,
            'document_number': document.document_number,
            'workflow_type': workflow.workflow_type,
            'workflow_history': history
        })


class SimpleMyTasksAPIView(APIView):
    """
    Simple API view for user's workflow tasks.
    
    Provides task management using the simple DocumentWorkflow approach.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get pending tasks for current user."""
        user = request.user
        
        # Get workflows where user is current assignee
        assigned_workflows = DocumentWorkflow.objects.filter(
            current_assignee=user,
            is_terminated=False
        ).select_related('document', 'current_state')
        
        # Build task list
        tasks = []
        for workflow in assigned_workflows:
            document = workflow.document
            task_info = {
                'document_id': str(document.uuid),
                'document_number': document.document_number,
                'document_title': document.title,
                'workflow_type': workflow.workflow_type,
                'current_state': workflow.current_state.name,
                'due_date': workflow.due_date,
                'created_at': workflow.created_at,
                'initiated_by': workflow.initiated_by.get_full_name(),
                'available_actions': workflow.get_valid_next_states()
            }
            tasks.append(task_info)
        
        return Response({
            'pending_tasks': tasks,
            'total_pending': len(tasks),
            'summary': {
                'review_tasks': len([t for t in tasks if 'REVIEW' in t['current_state']]),
                'approval_tasks': len([t for t in tasks if 'APPROVAL' in t['current_state']]),
            }
        })


class DocumentWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document workflows.
    
    Provides read-only access to DocumentWorkflow instances.
    """
    
    queryset = DocumentWorkflow.objects.all()
    serializer_class = DocumentWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocuments]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Filter workflows based on user permissions."""
        user = self.request.user
        
        if user.is_superuser:
            return super().get_queryset()
        
        # Users can see workflows for documents they have access to
        return super().get_queryset().filter(
            document__author=user
        ) | super().get_queryset().filter(
            document__reviewer=user
        ) | super().get_queryset().filter(
            document__approver=user
        )
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, uuid=None):
        """Submit document for review."""
        workflow = self.get_object()
        document = workflow.document
        comment = request.data.get('comment', '')
        
        lifecycle_service = get_document_lifecycle_service()
        
        try:
            result = lifecycle_service.submit_for_review(document, request.user, comment)
            
            if result:
                workflow.refresh_from_db()
                serializer = self.get_serializer(workflow)
                return Response({
                    'success': True,
                    'message': 'Document submitted for review successfully',
                    'workflow': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to submit document for review'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete_review(self, request, uuid=None):
        """Complete review of document."""
        workflow = self.get_object()
        document = workflow.document
        approved = request.data.get('approved', True)
        comment = request.data.get('comment', '')
        
        lifecycle_service = get_document_lifecycle_service()
        
        try:
            result = lifecycle_service.complete_review(document, request.user, approved, comment)
            
            if result:
                workflow.refresh_from_db()
                serializer = self.get_serializer(workflow)
                return Response({
                    'success': True,
                    'message': f'Review completed successfully ({"approved" if approved else "rejected"})',
                    'workflow': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to complete review'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)