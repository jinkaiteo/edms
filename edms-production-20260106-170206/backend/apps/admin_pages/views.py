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