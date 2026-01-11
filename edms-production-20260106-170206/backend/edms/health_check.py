"""
Simple health check view for EDMS.
Provides unauthenticated health status endpoint for monitoring.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
import datetime


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint.
    Returns 200 OK if the application is running and database is accessible.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return JsonResponse({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": db_status,
        "service": "edms-backend"
    })


@csrf_exempt  
@require_http_methods(["GET"])
def simple_health_check(request):
    """Ultra simple health check that just returns OK."""
    return JsonResponse({"status": "ok"})