"""
API Middleware for EDMS.

Custom middleware for API request processing, security headers,
and request/response logging.
"""

import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

from apps.audit.services import audit_service

logger = logging.getLogger(__name__)


class APIRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging API requests and responses.
    
    Logs all API requests for audit and monitoring purposes
    with configurable detail levels.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_body = getattr(settings, 'API_LOG_REQUEST_BODY', False)
        self.log_sensitive_data = getattr(settings, 'API_LOG_SENSITIVE_DATA', False)
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming API request."""
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Add timestamp for response time calculation
        request._api_start_time = time.time()
        
        # Log request if enabled
        if getattr(settings, 'API_REQUEST_LOGGING', True):
            self._log_request(request)
        
        return None
    
    def process_response(self, request, response):
        """Process API response."""
        # Only process API responses
        if not request.path.startswith('/api/'):
            return response
        
        # Calculate response time
        if hasattr(request, '_api_start_time'):
            response_time = time.time() - request._api_start_time
            response['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Log response if enabled
        if getattr(settings, 'API_RESPONSE_LOGGING', True):
            self._log_response(request, response)
        
        return response
    
    def _log_request(self, request):
        """Log API request details."""
        try:
            log_data = {
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'content_type': request.META.get('CONTENT_TYPE', ''),
                'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            }
            
            # Log request body if enabled and not sensitive
            if self.log_body and request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    if hasattr(request, 'body'):
                        body = request.body.decode('utf-8')
                        if self._is_sensitive_endpoint(request.path):
                            log_data['body'] = '[SENSITIVE DATA REDACTED]'
                        elif len(body) < 10000:  # Limit body size in logs
                            log_data['body'] = body[:1000] + ('...' if len(body) > 1000 else '')
                except Exception:
                    log_data['body'] = '[COULD NOT DECODE BODY]'
            
            # Log to audit system if user is authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                audit_service.log_user_action(
                    user=request.user,
                    action='API_REQUEST',
                    description=f"API {request.method} request to {request.path}",
                    additional_data=log_data
                )
            else:
                audit_service.log_system_event(
                    event_type='API_REQUEST_ANONYMOUS',
                    description=f"Anonymous API {request.method} request to {request.path}",
                    additional_data=log_data
                )
            
        except Exception as e:
            logger.error(f"Error logging API request: {str(e)}")
    
    def _log_response(self, request, response):
        """Log API response details."""
        try:
            response_time = time.time() - request._api_start_time if hasattr(request, '_api_start_time') else 0
            
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'response_time': response_time,
                'content_type': response.get('Content-Type', ''),
                'content_length': response.get('Content-Length', 0)
            }
            
            # Log response body for errors
            if response.status_code >= 400:
                try:
                    if hasattr(response, 'content'):
                        content = response.content.decode('utf-8')
                        if len(content) < 1000:
                            log_data['error_response'] = content
                except Exception:
                    pass
            
            # Log to audit system
            if hasattr(request, 'user') and request.user.is_authenticated:
                audit_service.log_user_action(
                    user=request.user,
                    action='API_RESPONSE',
                    description=f"API response {response.status_code} for {request.method} {request.path}",
                    additional_data=log_data
                )
            
        except Exception as e:
            logger.error(f"Error logging API response: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_sensitive_endpoint(self, path):
        """Check if endpoint handles sensitive data."""
        sensitive_patterns = [
            '/auth/', '/login/', '/password/', '/token/',
            '/certificates/', '/keys/', '/signatures/'
        ]
        return any(pattern in path.lower() for pattern in sensitive_patterns)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware for adding security headers to API responses.
    
    Adds security headers to protect against common attacks
    and ensure secure API communication.
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        # Only add headers to API responses
        if not request.path.startswith('/api/'):
            return response
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # API-specific headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # CORS headers for API (if enabled)
        if getattr(settings, 'API_CORS_ENABLED', True):
            allowed_origins = getattr(settings, 'API_CORS_ALLOWED_ORIGINS', ['*'])
            if '*' in allowed_origins:
                response['Access-Control-Allow-Origin'] = '*'
            else:
                origin = request.META.get('HTTP_ORIGIN')
                if origin in allowed_origins:
                    response['Access-Control-Allow-Origin'] = origin
            
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Accept, Authorization, Content-Type, X-Requested-With'
            response['Access-Control-Max-Age'] = '3600'
        
        # Custom API headers
        response['X-API-Version'] = getattr(settings, 'API_VERSION', '1.0')
        response['X-Powered-By'] = 'EDMS API'
        
        return response


class APIExceptionMiddleware(MiddlewareMixin):
    """
    Middleware for handling API exceptions.
    
    Provides consistent error responses and logging
    for unhandled exceptions in API endpoints.
    """
    
    def process_exception(self, request, exception):
        """Handle unhandled exceptions in API endpoints."""
        # Only handle API exceptions
        if not request.path.startswith('/api/'):
            return None
        
        # Log the exception
        logger.error(f"Unhandled API exception: {str(exception)}", exc_info=True)
        
        # Log to audit system
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        audit_service.log_system_event(
            event_type='API_EXCEPTION',
            description=f"Unhandled exception in API: {str(exception)}",
            additional_data={
                'path': request.path,
                'method': request.method,
                'user': user.username if user else 'anonymous',
                'ip_address': self._get_client_ip(request),
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception)
            }
        )
        
        # Return standardized error response
        error_response = {
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An internal server error occurred',
                'timestamp': time.time()
            }
        }
        
        # Add debug info in development
        if getattr(settings, 'DEBUG', False):
            error_response['error']['debug'] = {
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception)
            }
        
        return JsonResponse(error_response, status=500)
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APIVersioningMiddleware(MiddlewareMixin):
    """
    Middleware for API versioning support.
    
    Handles API version detection and routing
    for backward compatibility.
    """
    
    def process_request(self, request):
        """Process API version from request."""
        # Only process API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Extract version from URL path
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[2].startswith('v'):
            version = path_parts[2]
        else:
            version = 'v1'  # Default version
        
        # Check version from header
        header_version = request.META.get('HTTP_API_VERSION')
        if header_version:
            version = f"v{header_version}"
        
        # Validate version
        supported_versions = getattr(settings, 'API_SUPPORTED_VERSIONS', ['v1'])
        if version not in supported_versions:
            error_response = {
                'error': {
                    'code': 'UNSUPPORTED_API_VERSION',
                    'message': f'API version {version} is not supported',
                    'supported_versions': supported_versions
                }
            }
            return JsonResponse(error_response, status=400)
        
        # Add version to request
        request.api_version = version
        
        return None


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware for adding unique request IDs.
    
    Adds unique request IDs for tracking and debugging
    API requests across services.
    """
    
    def process_request(self, request):
        """Add unique request ID to request."""
        # Only for API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Generate unique request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        # Add to request
        request.request_id = request_id
        
        return None
    
    def process_response(self, request, response):
        """Add request ID to response header."""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        
        return response