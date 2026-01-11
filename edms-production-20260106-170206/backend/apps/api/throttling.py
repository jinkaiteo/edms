"""
API Rate Limiting and Throttling for EDMS.

Custom throttling classes for API rate limiting with
different limits for different user types and endpoints.
"""

import time
from django.core.cache import cache
from django.conf import settings
from rest_framework.throttling import BaseThrottle, UserRateThrottle, AnonRateThrottle

from apps.audit.services import audit_service


class EDMSBaseThrottle(BaseThrottle):
    """
    Base throttle class with audit logging.
    
    Provides common functionality for EDMS throttling
    with audit trail integration.
    """
    
    def allow_request(self, request, view):
        """Check if request should be allowed."""
        if self.is_exempt_user(request.user if hasattr(request, 'user') else None):
            return True
        
        # Check rate limit
        allowed = self.check_rate_limit(request, view)
        
        # Log throttling events
        if not allowed:
            self.log_throttle_event(request, view)
        
        return allowed
    
    def check_rate_limit(self, request, view):
        """Check rate limit - implemented by subclasses."""
        raise NotImplementedError('Subclasses must implement check_rate_limit')
    
    def is_exempt_user(self, user):
        """Check if user is exempt from rate limiting."""
        if not user or not user.is_authenticated:
            return False
        
        # Exempt superusers and specific roles
        if user.is_superuser:
            return True
        
        # Check for API admin role
        if hasattr(user, 'user_roles'):
            admin_roles = user.user_roles.filter(
                role__name__in=['API Admin', 'System Admin'],
                is_active=True
            )
            return admin_roles.exists()
        
        return False
    
    def log_throttle_event(self, request, view):
        """Log throttling event for audit."""
        user = getattr(request, 'user', None)
        
        audit_data = {
            'endpoint': request.path,
            'method': request.method,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'throttle_class': self.__class__.__name__
        }
        
        if user and user.is_authenticated:
            audit_service.log_user_action(
                user=user,
                action='API_RATE_LIMITED',
                description='API request rate limited',
                additional_data=audit_data
            )
        else:
            audit_service.log_system_event(
                event_type='API_RATE_LIMITED_ANONYMOUS',
                description='Anonymous API request rate limited',
                additional_data=audit_data
            )
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_cache_key(self, request, view):
        """Generate cache key for rate limiting."""
        raise NotImplementedError('Subclasses must implement get_cache_key')


class EDMSUserRateThrottle(UserRateThrottle, EDMSBaseThrottle):
    """
    User-based rate throttling with audit logging.
    
    Rate limits based on authenticated user with
    different limits for different user types.
    """
    
    scope = 'user'
    
    def allow_request(self, request, view):
        """Check if request should be allowed."""
        if self.is_exempt_user(getattr(request, 'user', None)):
            return True
        
        # Use parent UserRateThrottle logic
        allowed = super(UserRateThrottle, self).allow_request(request, view)
        
        if not allowed:
            self.log_throttle_event(request, view)
        
        return allowed
    
    def get_rate(self):
        """Get rate limit based on user type."""
        if not hasattr(self.request, 'user') or not self.request.user.is_authenticated:
            return super().get_rate()
        
        user = self.request.user
        
        # Different rates for different user types
        if user.is_superuser:
            return getattr(settings, 'API_RATE_LIMIT_ADMIN', '10000/hour')
        
        # Check user roles for specific rates
        if hasattr(user, 'user_roles'):
            if user.user_roles.filter(role__permission_level='admin', is_active=True).exists():
                return getattr(settings, 'API_RATE_LIMIT_ADMIN', '10000/hour')
            elif user.user_roles.filter(role__permission_level__in=['approve', 'review'], is_active=True).exists():
                return getattr(settings, 'API_RATE_LIMIT_ELEVATED', '5000/hour')
        
        # Default user rate
        return getattr(settings, 'API_RATE_LIMIT_USER', '1000/hour')


class EDMSAnonRateThrottle(AnonRateThrottle, EDMSBaseThrottle):
    """
    Anonymous user rate throttling.
    
    Rate limits for unauthenticated requests.
    """
    
    scope = 'anon'
    
    def allow_request(self, request, view):
        """Check if request should be allowed."""
        # Use parent AnonRateThrottle logic
        allowed = super(AnonRateThrottle, self).allow_request(request, view)
        
        if not allowed:
            self.log_throttle_event(request, view)
        
        return allowed
    
    def get_rate(self):
        """Get rate limit for anonymous users."""
        return getattr(settings, 'API_RATE_LIMIT_ANON', '100/hour')


class SearchRateThrottle(EDMSBaseThrottle):
    """
    Search-specific rate throttling.
    
    Higher rate limits for search endpoints due to
    their interactive nature.
    """
    
    scope = 'search'
    
    def check_rate_limit(self, request, view):
        """Check search-specific rate limit."""
        ident = self.get_ident(request)
        if ident is None:
            return True
        
        cache_key = f'throttle_search_{ident}'
        
        # Get current count and timestamp
        history = cache.get(cache_key, [])
        now = time.time()
        
        # Remove old entries outside the time window
        window_start = now - 3600  # 1 hour window
        history = [timestamp for timestamp in history if timestamp > window_start]
        
        # Check if limit exceeded
        limit = self.get_search_rate_limit(request)
        if len(history) >= limit:
            return False
        
        # Add current request
        history.append(now)
        cache.set(cache_key, history, timeout=3600)
        
        return True
    
    def get_search_rate_limit(self, request):
        """Get search rate limit based on user."""
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            if self.is_exempt_user(user):
                return 10000  # Very high limit for exempt users
            elif user.is_superuser:
                return 1000   # High limit for admin users
            else:
                return 500    # Standard limit for authenticated users
        else:
            return 50         # Low limit for anonymous users
    
    def get_ident(self, request):
        """Get identifier for rate limiting."""
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            return f'user_{user.id}'
        else:
            return self.get_client_ip(request)
    
    def get_cache_key(self, request, view):
        """Generate cache key for search throttling."""
        ident = self.get_ident(request)
        return f'throttle_search_{ident}'


class BulkOperationThrottle(EDMSBaseThrottle):
    """
    Bulk operation throttling.
    
    Stricter rate limits for bulk operations like
    document uploads, bulk updates, etc.
    """
    
    scope = 'bulk'
    
    def check_rate_limit(self, request, view):
        """Check bulk operation rate limit."""
        ident = self.get_ident(request)
        if ident is None:
            return True
        
        cache_key = f'throttle_bulk_{ident}'
        
        # Get current count
        history = cache.get(cache_key, [])
        now = time.time()
        
        # Remove old entries (24 hour window for bulk operations)
        window_start = now - 86400  # 24 hours
        history = [timestamp for timestamp in history if timestamp > window_start]
        
        # Check if limit exceeded
        limit = self.get_bulk_rate_limit(request)
        if len(history) >= limit:
            return False
        
        # Add current request
        history.append(now)
        cache.set(cache_key, history, timeout=86400)
        
        return True
    
    def get_bulk_rate_limit(self, request):
        """Get bulk operation rate limit."""
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            if self.is_exempt_user(user):
                return 1000  # High limit for exempt users
            elif user.is_superuser:
                return 100   # Moderate limit for admin users
            else:
                return 50    # Standard limit for authenticated users
        else:
            return 5         # Very low limit for anonymous users
    
    def get_ident(self, request):
        """Get identifier for rate limiting."""
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            return f'user_{user.id}'
        else:
            return self.get_client_ip(request)
    
    def get_cache_key(self, request, view):
        """Generate cache key for bulk throttling."""
        ident = self.get_ident(request)
        return f'throttle_bulk_{ident}'


class IPBasedThrottle(EDMSBaseThrottle):
    """
    IP-based throttling for additional security.
    
    Rate limits based on IP address regardless of
    authentication status.
    """
    
    scope = 'ip'
    
    def check_rate_limit(self, request, view):
        """Check IP-based rate limit."""
        ip = self.get_client_ip(request)
        if not ip:
            return True
        
        # Check if IP is whitelisted
        whitelisted_ips = getattr(settings, 'API_WHITELISTED_IPS', [])
        if ip in whitelisted_ips:
            return True
        
        cache_key = f'throttle_ip_{ip}'
        
        # Get current count
        history = cache.get(cache_key, [])
        now = time.time()
        
        # Remove old entries (1 hour window)
        window_start = now - 3600
        history = [timestamp for timestamp in history if timestamp > window_start]
        
        # Check if limit exceeded
        limit = getattr(settings, 'API_RATE_LIMIT_IP', 2000)
        if len(history) >= limit:
            # Log potential abuse
            audit_service.log_system_event(
                event_type='API_IP_RATE_LIMITED',
                description=f'IP {ip} exceeded rate limit',
                additional_data={
                    'ip_address': ip,
                    'request_count': len(history),
                    'limit': limit,
                    'endpoint': request.path
                }
            )
            return False
        
        # Add current request
        history.append(now)
        cache.set(cache_key, history, timeout=3600)
        
        return True
    
    def get_ident(self, request):
        """Get IP address for rate limiting."""
        return self.get_client_ip(request)
    
    def get_cache_key(self, request, view):
        """Generate cache key for IP throttling."""
        ip = self.get_client_ip(request)
        return f'throttle_ip_{ip}'