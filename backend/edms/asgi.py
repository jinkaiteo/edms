"""
ASGI config for edms project - simplified without WebSocket complexity.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')

# Simplified ASGI - HTTP only, no WebSocket routing
application = get_asgi_application()
