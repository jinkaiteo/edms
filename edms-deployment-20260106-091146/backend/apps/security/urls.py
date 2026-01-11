"""
Security URL Configuration

Provides API endpoints for security-related operations including
digital signatures, certificates, and security events.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DigitalSignatureViewSet,
    SecurityEventViewSet,
    EncryptionKeyViewSet,
    CertificateAuthorityViewSet
)

router = DefaultRouter()
router.register(r'signatures', DigitalSignatureViewSet, basename='signature')
router.register(r'events', SecurityEventViewSet, basename='security-event')
router.register(r'keys', EncryptionKeyViewSet, basename='encryption-key')
router.register(r'certificates', CertificateAuthorityViewSet, basename='certificate-authority')

urlpatterns = [
    path('', include(router.urls)),
]