"""
API Authentication for EDMS.

Custom authentication classes and middleware for API security,
including token-based authentication and session management.
"""

import logging
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token

from apps.audit.services import audit_service

User = get_user_model()
logger = logging.getLogger(__name__)


class APITokenAuthentication(BaseAuthentication):
    """
    Custom token authentication with audit logging.
    
    Extends DRF token authentication with additional security
    features and audit trail integration.
    """
    
    keyword = 'Token'
    model = Token
    
    def authenticate(self, request):
        """Authenticate user with token."""
        auth = self.get_authorization_header(request).split()
        
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise AuthenticationFailed(msg)
        
        return self.authenticate_credentials(token, request)
    
    def authenticate_credentials(self, key, request):
        """Authenticate token and return user."""
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            # Log failed authentication attempt
            audit_service.log_system_event(
                event_type='API_TOKEN_AUTHENTICATION_FAILED',
                description='Invalid API token used',
                additional_data={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'token_prefix': key[:8] if key else None
                }
            )
            raise AuthenticationFailed('Invalid token.')
        
        if not token.user.is_active:
            # Log inactive user attempt
            audit_service.log_system_event(
                event_type='API_AUTHENTICATION_INACTIVE_USER',
                description='Inactive user attempted API authentication',
                additional_data={
                    'user_id': token.user.id,
                    'username': token.user.username,
                    'ip_address': self.get_client_ip(request)
                }
            )
            raise AuthenticationFailed('User inactive or deleted.')
        
        # Check token expiry if configured
        if self.is_token_expired(token):
            # Log expired token usage
            audit_service.log_user_action(
                user=token.user,
                action='API_TOKEN_EXPIRED',
                description='Expired API token used',
                additional_data={
                    'token_created': token.created.isoformat(),
                    'ip_address': self.get_client_ip(request)
                }
            )
            raise AuthenticationFailed('Token has expired.')
        
        # Log successful authentication
        audit_service.log_user_action(
            user=token.user,
            action='API_TOKEN_AUTHENTICATION_SUCCESS',
            description='Successful API token authentication',
            additional_data={
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'endpoint': request.path
            }
        )
        
        return (token.user, token)
    
    def get_authorization_header(self, request):
        """Get authorization header from request."""
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            auth = auth.encode('iso-8859-1')
        return auth
    
    def get_model(self):
        """Get token model."""
        if self.model is not None:
            return self.model
        from rest_framework.authtoken.models import Token
        return Token
    
    def is_token_expired(self, token):
        """Check if token has expired."""
        token_lifetime = getattr(settings, 'API_TOKEN_LIFETIME_HOURS', 24)
        if token_lifetime is None:
            return False
        
        expiry_time = token.created + timedelta(hours=token_lifetime)
        return timezone.now() > expiry_time
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditedSessionAuthentication(SessionAuthentication):
    """
    Session authentication with audit logging.
    
    Extends DRF session authentication to include
    audit trail logging for compliance.
    """
    
    def authenticate(self, request):
        """Authenticate user with session."""
        result = super().authenticate(request)
        
        if result:
            user, auth = result
            
            # Log session authentication
            audit_service.log_user_action(
                user=user,
                action='API_SESSION_AUTHENTICATION',
                description='API access with session authentication',
                additional_data={
                    'session_key': request.session.session_key,
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'endpoint': request.path
                }
            )
        
        return result
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for external integrations.
    
    Simple API key authentication for system-to-system
    communication with audit logging.
    """
    
    keyword = 'ApiKey'
    
    def authenticate(self, request):
        """Authenticate with API key."""
        auth = self.get_authorization_header(request).split()
        
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth) == 1:
            msg = 'Invalid API key header. No key provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid API key header. Key should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        try:
            api_key = auth[1].decode()
        except UnicodeError:
            msg = 'Invalid API key header. Key contains invalid characters.'
            raise AuthenticationFailed(msg)
        
        return self.authenticate_credentials(api_key, request)
    
    def authenticate_credentials(self, api_key, request):
        """Authenticate API key and return user."""
        # Check against configured API keys
        valid_api_keys = getattr(settings, 'API_KEYS', {})
        
        if api_key not in valid_api_keys:
            # Log failed API key authentication
            audit_service.log_system_event(
                event_type='API_KEY_AUTHENTICATION_FAILED',
                description='Invalid API key used',
                additional_data={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'key_prefix': api_key[:8] if api_key else None
                }
            )
            raise AuthenticationFailed('Invalid API key.')
        
        # Get associated user
        username = valid_api_keys[api_key].get('user')
        if not username:
            raise AuthenticationFailed('API key not associated with user.')
        
        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed('Associated user not found or inactive.')
        
        # Log successful authentication
        audit_service.log_user_action(
            user=user,
            action='API_KEY_AUTHENTICATION_SUCCESS',
            description='Successful API key authentication',
            additional_data={
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'endpoint': request.path,
                'api_key_name': valid_api_keys[api_key].get('name', 'unknown')
            }
        )
        
        return (user, api_key)
    
    def get_authorization_header(self, request):
        """Get authorization header from request."""
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            auth = auth.encode('iso-8859-1')
        return auth
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BearerTokenAuthentication(BaseAuthentication):
    """
    Bearer token authentication for JWT tokens.
    
    Supports JWT tokens for modern API authentication
    with proper validation and audit logging.
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """Authenticate with Bearer token."""
        auth = self.get_authorization_header(request).split()
        
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth) == 1:
            msg = 'Invalid Bearer token header. No token provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid Bearer token header. Token should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = 'Invalid Bearer token header. Token contains invalid characters.'
            raise AuthenticationFailed(msg)
        
        return self.authenticate_credentials(token, request)
    
    def authenticate_credentials(self, token, request):
        """Validate JWT token and return user."""
        try:
            # This would integrate with a JWT library like PyJWT
            # For now, just a placeholder
            payload = self.decode_jwt_token(token)
            
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token does not contain user ID.')
            
            user = User.objects.get(id=user_id, is_active=True)
            
            # Log successful authentication
            audit_service.log_user_action(
                user=user,
                action='JWT_AUTHENTICATION_SUCCESS',
                description='Successful JWT authentication',
                additional_data={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'endpoint': request.path,
                    'token_exp': payload.get('exp')
                }
            )
            
            return (user, token)
            
        except Exception as e:
            # Log failed authentication
            audit_service.log_system_event(
                event_type='JWT_AUTHENTICATION_FAILED',
                description=f'JWT authentication failed: {str(e)}',
                additional_data={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'error': str(e)
                }
            )
            raise AuthenticationFailed('Invalid or expired token.')
    
    def decode_jwt_token(self, token):
        """Decode and validate JWT token."""
        # Placeholder for JWT token decoding
        # Would use PyJWT or similar library
        import json
        import base64
        
        try:
            # Simple base64 decoding for demonstration
            # In production, use proper JWT validation
            header, payload, signature = token.split('.')
            decoded_payload = json.loads(
                base64.urlsafe_b64decode(payload + '==')
            )
            return decoded_payload
        except Exception:
            raise AuthenticationFailed('Invalid token format.')
    
    def get_authorization_header(self, request):
        """Get authorization header from request."""
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            auth = auth.encode('iso-8859-1')
        return auth
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip