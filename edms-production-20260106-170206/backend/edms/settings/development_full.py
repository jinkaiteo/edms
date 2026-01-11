"""
Full development settings with all custom apps enabled.
"""

from .minimal import *

# Add our custom apps to the minimal setup
INSTALLED_APPS += [
    # EDMS Core Apps
    'apps.users',
    'apps.documents',
    # 'apps.audit',  # Temporarily disabled for auth testing
    'apps.security',
    'apps.placeholders',
    # 'apps.search',  # Temporarily disabled (depends on audit)
    # 'apps.backup',  # Removed
    'apps.settings',
    'apps.scheduler',
    'apps.api',
    'apps.workflows',  # Re-enabled for workflow activation
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Ensure CORS middleware is first
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
] + MIDDLEWARE + [
    # 'apps.audit.middleware.AuditMiddleware',  # Temporarily disabled for auth testing
    # 'apps.api.middleware.APIThrottleMiddleware',  # Disabled - middleware not implemented
]

# Update database name for full development
DATABASES['default']['NAME'] = BASE_DIR / 'edms_full_dev.sqlite3'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Simplified REST Framework settings for authentication testing
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# Document storage settings
DOCUMENT_STORAGE_ROOT = BASE_DIR / 'storage' / 'documents'
DOCUMENT_TEMP_ROOT = BASE_DIR / 'storage' / 'temp'

# Ensure storage directories exist
import os
os.makedirs(DOCUMENT_STORAGE_ROOT, exist_ok=True)
os.makedirs(DOCUMENT_TEMP_ROOT, exist_ok=True)

# CORS Configuration - Fix for credentials support  
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# CSRF Settings for CORS
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CSRF_COOKIE_HTTPONLY = False

# Session cookie settings for development (same domain)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_DOMAIN = None  # Allow both localhost and 127.0.0.1
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'X-Request-ID',  # Match the exact case from frontend
]