"""
Test-specific settings for EDMS
Excludes problematic apps that cause test database setup issues
"""
from .base import *

# Remove scheduler from installed apps for testing
# Scheduler migrations have cursor issues during test database setup
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'scheduler' not in app]

# Use test-specific URLs that exclude scheduler
ROOT_URLCONF = 'edms.urls_test'

# Remove whitenoise middleware for tests (not needed, causes import errors)
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m.lower()]

# Use simpler database for faster tests
DATABASES['default']['TEST'] = {
    'NAME': 'test_edms_db',
    'SERIALIZE': False,  # Disable serialization (causes cursor issues)
}

# Disable migrations for faster test setup (use schema from models)
# Uncomment if you want even faster tests:
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests (cleaner output)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Faster tests
DEBUG = False

print("✅ Using test settings (scheduler disabled, test URLs, fast password hashing)")
