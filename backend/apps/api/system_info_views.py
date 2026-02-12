"""
System Information API Views
Provides system version, environment, and health information
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import connection
import django
import sys
import platform
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_info_view(request):
    """
    Returns comprehensive system information including versions and environment details.
    
    Response includes:
    - Application version
    - Backend framework version (Django)
    - Database information
    - Python version
    - Server platform
    - Build date
    """
    
    # Get Django version
    django_version = django.get_version()
    
    # Get Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.release}"
    
    # Get database info
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version_full = cursor.fetchone()[0]
            # Extract just "PostgreSQL X.Y" from full version string
            db_version = db_version_full.split(',')[0] if ',' in db_version_full else db_version_full.split()[0:2]
            db_version = ' '.join(db_version) if isinstance(db_version, list) else db_version
    except Exception:
        db_version = "Unknown"
    
    # Application version (read from environment or use default)
    # This will be set by deployment script from package.json
    import os
    app_version = os.getenv('APP_VERSION', getattr(settings, 'APP_VERSION', '1.3.3'))
    
    # Build date (auto-generated during deployment)
    build_date = os.getenv('BUILD_DATE', getattr(settings, 'BUILD_DATE', datetime.now().strftime('%Y-%m-%d')))
    
    # Environment
    environment = 'production' if not settings.DEBUG else 'development'
    
    # Platform info
    platform_info = platform.platform()
    
    return Response({
        'application': {
            'version': app_version,
            'build_date': build_date,
            'environment': environment,
        },
        'backend': {
            'framework': 'Django',
            'version': django_version,
            'python_version': python_version,
        },
        'database': {
            'type': 'PostgreSQL',
            'version': db_version,
            'status': 'connected',  # If we got here, DB is connected
        },
        'server': {
            'platform': platform_info,
        },
        'timestamp': datetime.now().isoformat(),
    })
