"""
Admin Pages API Views
API endpoints for admin functionality including system reinit
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import authenticate
from django.utils import timezone
import json

from apps.audit.services import audit_service

logger = logging.getLogger(__name__)


@method_decorator([csrf_exempt, login_required, staff_member_required], name='dispatch')
class SystemReinitAPIView(View):
    """
    API endpoint for system reinit functionality
    Secure endpoint that requires authentication and staff privileges
    """
    
    def post(self, request):
        """Execute system reinit via API"""
        try:
            # Parse request data
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['confirmations', 'confirmation_text', 'admin_password']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Validate confirmations
            confirmations = data.get('confirmations', {})
            required_confirmations = [
                'understanding', 'dataLoss', 'irreversible', 
                'backupCreated', 'adminAccess'
            ]
            
            for confirmation in required_confirmations:
                if not confirmations.get(confirmation, False):
                    return JsonResponse({
                        'success': False,
                        'error': f'Required confirmation not checked: {confirmation}'
                    }, status=400)
            
            # Validate confirmation text
            confirmation_text = data.get('confirmation_text', '').strip()
            if confirmation_text != 'RESET SYSTEM NOW':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid confirmation text. Must be exactly: RESET SYSTEM NOW'
                }, status=400)
            
            # Validate admin password
            admin_password = data.get('admin_password', '')
            if not authenticate(username=request.user.username, password=admin_password):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid admin password'
                }, status=401)
            
            # Log the reinit attempt
            audit_service.log_user_action(
                user=request.user,
                action='SYSTEM_REINIT_INITIATED',
                object_type='System',
                description='System reinit initiated via API',
                additional_data={
                    'preserve_templates': data.get('preserve_templates', True),
                    'preserve_backups': data.get('preserve_backups', True),
                    'initiated_via': 'frontend_api'
                }
            )
            
            # Execute system reinit
            logger.info(f"Executing system reinit initiated by user {request.user.username}")
            
            # Call the management command programmatically
            call_command('system_reinit', '--confirm', verbosity=0)
            
            # Log successful completion
            audit_service.log_system_event(
                event_type='SYSTEM_REINIT_COMPLETED',
                object_type='System',
                description='System reinit completed successfully via API',
                additional_data={
                    'executed_by': request.user.username,
                    'completion_time': timezone.now().isoformat()
                }
            )
            
            # Return success response with new admin credentials
            return JsonResponse({
                'success': True,
                'message': 'System reinit completed successfully',
                'new_admin': {
                    'username': 'admin',
                    'password': 'test123', 
                    'email': 'admin@edms.local'
                },
                'completion_time': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
            
        except Exception as e:
            logger.error(f"System reinit API error: {str(e)}", exc_info=True)
            
            # Log the error
            audit_service.log_system_event(
                event_type='SYSTEM_REINIT_FAILED',
                object_type='System',
                description=f'System reinit failed via API: {str(e)}',
                additional_data={
                    'error_message': str(e),
                    'attempted_by': request.user.username if hasattr(request, 'user') else 'unknown'
                }
            )
            
            return JsonResponse({
                'success': False,
                'error': f'System reinit failed: {str(e)}'
            }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
@staff_member_required
def system_reinit_status(request):
    """Get current system status for reinit operations"""
    try:
        from apps.users.models import User
        from apps.documents.models import Document
        from apps.workflows.models import WorkflowInstance
        from apps.audit.models import AuditTrail
        from apps.backup.models import BackupJob
        
        status = {
            'system_status': {
                'users': User.objects.count(),
                'documents': Document.objects.count(),
                'workflows': WorkflowInstance.objects.count(),
                'audit_trails': AuditTrail.objects.count(),
                'backup_jobs': BackupJob.objects.count()
            },
            'ready_for_reinit': True,
            'current_time': timezone.now().isoformat(),
            'current_user': request.user.username
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Status check failed: {str(e)}'
        }, status=500)