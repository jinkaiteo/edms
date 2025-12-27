"""Development settings for EDMS project."""

from .base import *

# Enable all apps now that models are implemented
# INSTALLED_APPS will be inherited from base.py

# Re-enable custom User model
AUTH_USER_MODEL = 'users.User'

# Override middleware to remove problematic ones
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.backup.simple_auth_middleware.SimpleBackupAuthMiddleware',  # Added for backup API auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # REMOVED - causing template errors
]

# Temporarily disable cache and sessions that require Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Override logging to use console only for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver', '*']

# Development middleware already included above

# Debug Toolbar Configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Database - use PostgreSQL from base settings (no override needed)

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files serving
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Less strict security for development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# CORS Configuration - Enhanced for development
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
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
    'x-requested-id',
]

# Session Configuration for cross-origin development
SESSION_COOKIE_SAMESITE = 'None'  # Allow cross-origin session cookies
SESSION_COOKIE_SECURE = False  # Set to True only with HTTPS
SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript access for development
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration for development
CSRF_COOKIE_SAMESITE = 'None'  # Allow cross-origin CSRF cookies  
CSRF_COOKIE_SECURE = False  # Set to True only with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Celery settings for development
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# Logging configuration handled above

# Additional development settings
SHELL_PLUS_PRINT_SQL = True