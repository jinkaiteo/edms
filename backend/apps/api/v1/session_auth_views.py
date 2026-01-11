"""
Session-based authentication views for frontend integration.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
import json


@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """Get CSRF token for frontend."""
    return JsonResponse({
        'csrfToken': get_token(request),
        'sessionid': request.session.session_key
    })


@require_http_methods(["POST"])
def session_login(request):
    """Login endpoint for session-based authentication."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password required'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'uuid': str(user.uuid),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'is_active': user.is_active
                },
                'csrfToken': get_token(request),
                'sessionid': request.session.session_key
            })
        else:
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def current_user(request):
    """Get current user information."""
    if request.user.is_authenticated:
        return JsonResponse({
            'user': {
                'id': request.user.id,
                'uuid': str(request.user.uuid),
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'full_name': request.user.get_full_name(),
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'is_active': request.user.is_active
            },
            'csrfToken': get_token(request),
            'sessionid': request.session.session_key
        })
    else:
        return JsonResponse({
            'error': 'Not authenticated'
        }, status=401)


@require_http_methods(["POST"])
def session_logout(request):
    """Logout endpoint."""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({
            'error': 'Not authenticated'
        }, status=401)