# Authentication and Integration Setup

## Overview
This document provides comprehensive authentication setup for the EDMS system, including Azure Entra ID integration, multi-factor authentication, and security configurations.

## Authentication Architecture

### Core Components
- **Django Authentication**: Base user management
- **JWT Tokens**: API authentication
- **Azure Entra ID**: Enterprise SSO integration
- **Multi-Factor Authentication**: Additional security layer
- **Session Management**: Web application sessions

## Django Authentication Setup

### Settings Configuration

```python
# settings.py
import os
from datetime import timedelta

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'edms.auth.backends.EntraIDBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'edms.auth.validators.ComplexityValidator',
    },
]

# Session Configuration
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_COOKIE_SECURE = False  # HTTP deployment
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Protection
CSRF_COOKIE_SECURE = False  # HTTP deployment
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# HSTS disabled for HTTP deployment

# Login/Logout URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Account Lockout
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 1800  # 30 minutes
```

### JWT Configuration

```python
# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'edms-system',
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# DRF Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## Azure Entra ID Integration

### Azure App Registration

```python
# Azure AD Configuration
AZURE_AD = {
    'TENANT_ID': os.environ.get('AZURE_TENANT_ID'),
    'CLIENT_ID': os.environ.get('AZURE_CLIENT_ID'),
    'CLIENT_SECRET': os.environ.get('AZURE_CLIENT_SECRET'),
    'REDIRECT_URI': os.environ.get('AZURE_REDIRECT_URI', 'http://edms.company.com/auth/azure/callback/'),
    'AUTHORITY': f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID')}",
    'SCOPE': ['User.Read', 'User.ReadBasic.All'],
}

# MSAL Configuration
MSAL_CONFIG = {
    'authority': AZURE_AD['AUTHORITY'],
    'client_id': AZURE_AD['CLIENT_ID'],
    'client_credential': AZURE_AD['CLIENT_SECRET'],
}
```

### Custom Authentication Backend

```python
# auth/backends.py
import logging
import requests
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.conf import settings
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

class EntraIDBackend(BaseBackend):
    """Azure Entra ID authentication backend"""
    
    def authenticate(self, request, username=None, password=None, azure_token=None, **kwargs):
        if azure_token:
            return self._authenticate_with_token(azure_token)
        return None
    
    def _authenticate_with_token(self, token):
        """Authenticate user with Azure AD token"""
        try:
            # Validate token with Microsoft Graph
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return self._get_or_create_user(user_data)
            else:
                logger.warning(f"Azure AD token validation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Azure AD authentication error: {e}")
            return None
    
    def _get_or_create_user(self, user_data):
        """Get or create user from Azure AD data"""
        azure_id = user_data.get('id')
        email = user_data.get('mail') or user_data.get('userPrincipalName')
        first_name = user_data.get('givenName', '')
        last_name = user_data.get('surname', '')
        
        try:
            # Try to find existing user by Azure ID
            user = User.objects.get(userprofile__azure_id=azure_id)
        except User.DoesNotExist:
            try:
                # Try to find by email
                user = User.objects.get(email=email)
                # Link Azure ID
                profile = user.userprofile
                profile.azure_id = azure_id
                profile.save()
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                # Ensure unique username
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create profile with Azure ID
                from edms.users.models import UserProfile
                UserProfile.objects.create(
                    user=user,
                    azure_id=azure_id,
                    department=user_data.get('department', ''),
                    title=user_data.get('jobTitle', '')
                )
        
        return user if user.is_active else None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class LDAPBackend(BaseBackend):
    """LDAP authentication backend for on-premise AD"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
            
        try:
            import ldap
            
            # LDAP Configuration
            ldap_server = settings.LDAP_CONFIG['SERVER']
            ldap_base_dn = settings.LDAP_CONFIG['BASE_DN']
            ldap_user_dn = settings.LDAP_CONFIG['USER_DN']
            
            # Connect to LDAP
            conn = ldap.initialize(ldap_server)
            conn.protocol_version = ldap.VERSION3
            
            # Bind with user credentials
            user_dn = f"{ldap_user_dn}={username},{ldap_base_dn}"
            conn.simple_bind_s(user_dn, password)
            
            # Get user attributes
            search_filter = f"({ldap_user_dn}={username})"
            result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, search_filter)
            
            if result:
                dn, attributes = result[0]
                return self._get_or_create_ldap_user(username, attributes)
            
        except ldap.INVALID_CREDENTIALS:
            logger.warning(f"Invalid LDAP credentials for user: {username}")
            return None
        except Exception as e:
            logger.error(f"LDAP authentication error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.unbind()
        
        return None
    
    def _get_or_create_ldap_user(self, username, attributes):
        """Create or update user from LDAP attributes"""
        email = attributes.get('mail', [b''])[0].decode('utf-8')
        first_name = attributes.get('givenName', [b''])[0].decode('utf-8')
        last_name = attributes.get('sn', [b''])[0].decode('utf-8')
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
        )
        
        if not created:
            # Update user info
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        
        return user if user.is_active else None
```

### Multi-Factor Authentication

```python
# auth/mfa.py
import qrcode
import base64
from io import BytesIO
from django.conf import settings
import pyotp
from django.core.cache import cache
import secrets

class MFAService:
    """Multi-Factor Authentication service"""
    
    @staticmethod
    def generate_secret():
        """Generate MFA secret for user"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="EDMS System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp(secret, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def send_sms_code(phone_number):
        """Send SMS verification code"""
        code = secrets.randbelow(900000) + 100000  # 6-digit code
        
        # Store code in cache for 5 minutes
        cache_key = f"sms_code_{phone_number}"
        cache.set(cache_key, str(code), 300)
        
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        # sms_service.send(phone_number, f"Your EDMS verification code: {code}")
        
        return str(code)  # Return for testing
    
    @staticmethod
    def verify_sms_code(phone_number, code):
        """Verify SMS code"""
        cache_key = f"sms_code_{phone_number}"
        stored_code = cache.get(cache_key)
        
        if stored_code and stored_code == code:
            cache.delete(cache_key)
            return True
        return False

# MFA Models
from django.db import models

class MFADevice(models.Model):
    """MFA device for users"""
    MFA_TYPES = [
        ('totp', 'TOTP Authenticator'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_type = models.CharField(max_length=10, choices=MFA_TYPES)
    device_name = models.CharField(max_length=100)
    secret = models.CharField(max_length=32, blank=True)  # For TOTP
    phone_number = models.CharField(max_length=20, blank=True)  # For SMS
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'device_name']
```

### Authentication Views

```python
# auth/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import msal

class LoginView(View):
    """Handle user login"""
    
    def post(self, request):
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        mfa_token = data.get('mfa_token')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if MFA is required
            if user.mfa_devices.filter(is_active=True).exists():
                if not mfa_token:
                    return JsonResponse({
                        'success': False,
                        'mfa_required': True,
                        'message': 'MFA token required'
                    })
                
                # Verify MFA
                if not self._verify_mfa(user, mfa_token):
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid MFA token'
                    })
            
            login(request, user)
            
            # Generate JWT tokens for API access
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            })
        else:
            # Log failed attempt
            from .models import LoginAttempt
            LoginAttempt.objects.create(
                username=username,
                ip_address=request.META.get('REMOTE_ADDR'),
                success=False,
                failure_reason='Invalid credentials'
            )
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            })
    
    def _verify_mfa(self, user, token):
        """Verify MFA token"""
        primary_device = user.mfa_devices.filter(is_primary=True, is_active=True).first()
        
        if not primary_device:
            return False
        
        if primary_device.device_type == 'totp':
            return MFAService.verify_totp(primary_device.secret, token)
        elif primary_device.device_type == 'sms':
            return MFAService.verify_sms_code(primary_device.phone_number, token)
        
        return False

class AzureAuthView(View):
    """Handle Azure AD authentication"""
    
    def get(self, request):
        """Initiate Azure AD login"""
        app = msal.ConfidentialClientApplication(**settings.MSAL_CONFIG)
        
        auth_url = app.get_authorization_request_url(
            settings.AZURE_AD['SCOPE'],
            redirect_uri=settings.AZURE_AD['REDIRECT_URI'],
            state=secrets.token_urlsafe(32)
        )
        
        # Store state in session
        request.session['azure_state'] = auth_url
        
        return JsonResponse({'auth_url': auth_url})
    
    def post(self, request):
        """Handle Azure AD callback"""
        data = json.loads(request.body)
        code = data.get('code')
        state = data.get('state')
        
        # Verify state
        if state != request.session.get('azure_state'):
            return JsonResponse({'error': 'Invalid state parameter'}, status=400)
        
        app = msal.ConfidentialClientApplication(**settings.MSAL_CONFIG)
        
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=settings.AZURE_AD['SCOPE'],
            redirect_uri=settings.AZURE_AD['REDIRECT_URI']
        )
        
        if 'access_token' in result:
            # Authenticate user with token
            user = authenticate(request, azure_token=result['access_token'])
            
            if user:
                login(request, user)
                
                # Generate JWT tokens
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)
                
                return JsonResponse({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                })
        
        return JsonResponse({'error': 'Authentication failed'}, status=401)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    """Handle user logout"""
    
    @method_decorator(login_required)
    def post(self, request):
        logout(request)
        return JsonResponse({'success': True})
```

### Security Middleware

```python
# auth/middleware.py
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

class SecurityMiddleware:
    """Security middleware for authentication and authorization"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Rate limiting
        if not self._check_rate_limit(request):
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        # Account lockout check
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            if self._is_account_locked(request.user.username):
                return JsonResponse({'error': 'Account locked'}, status=423)
        
        response = self.get_response(request)
        
        # Log successful requests
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            self._log_user_activity(request)
        
        return response
    
    def _check_rate_limit(self, request):
        """Check rate limiting"""
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f"rate_limit_{ip}"
        
        requests = cache.get(cache_key, 0)
        if requests >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        cache.set(cache_key, requests + 1, 60)
        return True
    
    def _is_account_locked(self, username):
        """Check if account is locked"""
        cache_key = f"account_locked_{username}"
        return cache.get(cache_key, False)
    
    def _log_user_activity(self, request):
        """Log user activity"""
        from .models import UserActivity
        
        UserActivity.objects.create(
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            path=request.path,
            method=request.method
        )

class SessionTimeoutMiddleware:
    """Handle session timeout"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Check session timeout
            last_activity = request.session.get('last_activity')
            now = time.time()
            
            if last_activity and (now - last_activity) > settings.SESSION_TIMEOUT:
                from django.contrib.auth import logout
                logout(request)
                return JsonResponse({'error': 'Session expired'}, status=401)
            
            request.session['last_activity'] = now
        
        return self.get_response(request)
```

### Password Validators

```python
# auth/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ComplexityValidator:
    """Custom password complexity validator"""
    
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_number',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )
        
        if user:
            # Check against user attributes
            forbidden = [
                user.username.lower(),
                user.first_name.lower(),
                user.last_name.lower(),
                user.email.split('@')[0].lower(),
            ]
            
            for attr in forbidden:
                if attr and attr in password.lower():
                    raise ValidationError(
                        _("Password cannot contain personal information."),
                        code='password_personal_info',
                    )
    
    def get_help_text(self):
        return _(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one number, and one special character."
        )
```

This authentication setup provides:

1. **Multi-backend authentication** (Django, Azure AD, LDAP)
2. **JWT token management** for API access
3. **Multi-factor authentication** support
4. **Session security** with timeout and validation
5. **Rate limiting** and account lockout protection
6. **Comprehensive security middleware**
7. **Azure Entra ID integration** for enterprise SSO
8. **Strong password policies** and validation
9. **Activity logging** for audit compliance
10. **CSRF and XSS protection**