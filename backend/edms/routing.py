"""
Simplified ASGI routing - WebSocket notifications removed
Focus on simple HTTP-only communication
"""
from django.core.asgi import get_asgi_application

# No WebSocket routing needed for simplified notification system
application = get_asgi_application()
