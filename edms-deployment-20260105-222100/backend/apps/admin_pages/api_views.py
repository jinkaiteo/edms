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




