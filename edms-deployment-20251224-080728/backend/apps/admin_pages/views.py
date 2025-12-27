"""
Admin Dashboard Views for EDMS Frontend Integration

Provides simple HTML views for admin functions that can be accessed
through the frontend navigation submenu.
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.management import call_command
from django.utils import timezone
import json
import os
from apps.users.models import Role, UserRole
from apps.workflows.models import DocumentWorkflow
from apps.audit.models import AuditTrail
from apps.documents.models import Document
from apps.backup.models import BackupJob, RestoreJob

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with navigation links."""
    context = {
        'user_count': User.objects.count(),
        'document_count': Document.objects.count(),
        'workflow_count': DocumentWorkflow.objects.count(),
        'audit_count': AuditTrail.objects.count(),
    }
    return render(request, 'admin_pages/dashboard.html', context)


@staff_member_required
def user_management(request):
    """User management interface."""
    users = User.objects.all().select_related().order_by('username')
    roles = Role.objects.all()
    
    context = {
        'users': users,
        'roles': roles,
        'page_title': 'User Management',
        'api_endpoint': '/api/v1/users/',
    }
    return render(request, 'admin_pages/user_management.html', context)


@staff_member_required
def system_settings(request):
    """System settings interface."""
    context = {
        'page_title': 'System Settings',
        'api_endpoint': '/api/v1/settings/',
    }
    return render(request, 'admin_pages/system_settings.html', context)


@staff_member_required
def audit_trail(request):
    """Audit trail viewer interface."""
    recent_audits = AuditTrail.objects.select_related('user').order_by('-timestamp')[:50]
    
    context = {
        'recent_audits': recent_audits,
        'page_title': 'Audit Trail',
        'api_endpoint': '/api/v1/audit/',
    }
    return render(request, 'admin_pages/audit_trail.html', context)


@staff_member_required
def system_reinit_dashboard(request):
    """System reinit interface with comprehensive warnings."""
    
    # Get current system state for display
    current_state = {
        'users': User.objects.count(),
        'documents': Document.objects.count(),
        'workflows': DocumentWorkflow.objects.count(),
        'audit_trails': AuditTrail.objects.count(),
        'backup_jobs': BackupJob.objects.count(),
        'restore_jobs': RestoreJob.objects.count(),
    }
    
    # Check file storage
    storage_info = {}
    storage_paths = [
        ('/app/storage/documents', 'Documents'),
        ('/app/storage/media', 'Media Files'),
        ('/storage/backups', 'Backups'),
        ('/opt/edms/backups', 'Archive Backups')
    ]
    
    total_files = 0
    for path, label in storage_paths:
        if os.path.exists(path) and os.path.isdir(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            storage_info[label] = len(files)
            total_files += len(files)
        else:
            storage_info[label] = 0
    
    storage_info['total_files'] = total_files
    
    context = {
        'page_title': 'System Reinit',
        'current_state': current_state,
        'storage_info': storage_info,
        'admin_user': request.user,
    }
    return render(request, 'admin_pages/system_reinit.html', context)


@staff_member_required
@require_POST
@csrf_exempt
def system_reinit_execute(request):
    """Execute system reinit with safety checks."""
    
    try:
        data = json.loads(request.body)
        
        # Verify all safety confirmations
        confirmations = data.get('confirmations', {})
        required_confirmations = [
            'understand_destructive',
            'data_loss_acknowledged', 
            'no_rollback_understood',
            'testing_environment_confirmed',
            'backup_not_needed'
        ]
        
        # Check all confirmations
        for confirmation in required_confirmations:
            if not confirmations.get(confirmation, False):
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required confirmation: {confirmation}'
                }, status=400)
        
        # Verify confirmation text
        confirmation_text = data.get('confirmation_text', '').strip()
        if confirmation_text != 'RESET SYSTEM NOW':
            return JsonResponse({
                'success': False,
                'error': 'Confirmation text must be exactly: RESET SYSTEM NOW'
            }, status=400)
        
        # Verify admin password
        admin_password = data.get('admin_password', '')
        if not request.user.check_password(admin_password):
            return JsonResponse({
                'success': False,
                'error': 'Invalid admin password'
            }, status=403)
        
        # Get options
        preserve_templates = data.get('preserve_templates', True)
        preserve_backups = data.get('preserve_backups', True)
        
        # Log the reinit attempt
        from apps.audit.services import audit_service
        audit_service.log_user_action(
            user=request.user,
            action='SYSTEM_REINIT_INITIATED',
            object_type='System',
            object_id=None,
            description=f'System reinit initiated by {request.user.username}',
            additional_data={
                'preserve_templates': preserve_templates,
                'preserve_backups': preserve_backups,
                'initiated_from': 'admin_dashboard'
            }
        )
        
        # Execute the reinit command
        try:
            # Use StringIO to capture command output
            from io import StringIO
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Execute reinit command
            call_command(
                'system_reinit',
                confirm=True,
                preserve_templates=preserve_templates,
                preserve_backups=preserve_backups,
                verbosity=1
            )
            
            sys.stdout = old_stdout
            command_output = captured_output.getvalue()
            
            # Log successful completion
            audit_service.log_user_action(
                user=request.user,
                action='SYSTEM_REINIT_COMPLETED',
                object_type='System',
                object_id=None,
                description='System reinit completed successfully',
                additional_data={
                    'preserve_templates': preserve_templates,
                    'preserve_backups': preserve_backups,
                    'execution_time': timezone.now().isoformat()
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'System reset completed successfully',
                'output': command_output,
                'new_admin': {
                    'username': 'admin',
                    'password': 'test123',
                    'email': 'admin@edms.local'
                }
            })
            
        except Exception as cmd_error:
            # Log the failure
            audit_service.log_user_action(
                user=request.user,
                action='SYSTEM_REINIT_FAILED',
                object_type='System',
                object_id=None,
                description=f'System reinit failed: {str(cmd_error)}',
                additional_data={
                    'error': str(cmd_error),
                    'preserve_templates': preserve_templates,
                    'preserve_backups': preserve_backups
                }
            )
            
            return JsonResponse({
                'success': False,
                'error': f'System reinit failed: {str(cmd_error)}'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@staff_member_required
def redirect_to_scheduler(request):
    """Redirect to the scheduler monitoring dashboard."""
    return HttpResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to Scheduler Dashboard...</title>
        <meta http-equiv="refresh" content="0; url='/admin/scheduler/monitoring/dashboard/'">
    </head>
    <body>
        <p>Redirecting to <a href="/admin/scheduler/monitoring/dashboard/">Scheduler Dashboard</a>...</p>
        <script>window.location.href = '/admin/scheduler/monitoring/dashboard/';</script>
    </body>
    </html>
    """)