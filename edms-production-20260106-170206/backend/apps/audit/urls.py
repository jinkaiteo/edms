"""
URL Configuration for Audit App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AuditTrailViewSet, LoginAuditViewSet, ComplianceReportViewSet,
    UserSessionViewSet, CombinedAuditViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'trail', AuditTrailViewSet, basename='audit-trail')
router.register(r'login', LoginAuditViewSet, basename='login-audit')
router.register(r'compliance', ComplianceReportViewSet, basename='compliance-report')
router.register(r'sessions', UserSessionViewSet, basename='user-session')
router.register(r'combined', CombinedAuditViewSet, basename='combined-audit')

urlpatterns = [
    path('', include(router.urls)),
]