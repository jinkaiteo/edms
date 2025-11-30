"""
ASGI config for EDMS project.

It exposes the ASGI callable as a module-level variable named ``application``.

Supports both HTTP and WebSocket connections for real-time features.
"""

import os
from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
django_asgi_app = get_asgi_application()

# Now import everything else that depends on Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})