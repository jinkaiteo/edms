"""
API Models for EDMS.

Models for API-specific functionality like API keys,
rate limiting, and API usage tracking.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class APIKey(models.Model):
    """
    API Key model for API authentication.
    
    Manages API keys for external integrations
    and system-to-system communication.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    key = models.CharField(max_length=64, unique=True)
    
    # Permissions and scope
    permissions = models.JSONField(
        default=list,
        help_text="List of permissions for this API key"
    )
    allowed_endpoints = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific endpoints this key can access"
    )
    
    # Usage and limits
    is_active = models.BooleanField(default=True)
    rate_limit = models.PositiveIntegerField(
        default=1000,
        help_text="Requests per hour limit"
    )
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Owner and metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_api_keys'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'api_keys'
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class APIUsageLog(models.Model):
    """
    API Usage Log model for tracking API usage.
    
    Logs API requests for monitoring, analytics,
    and rate limiting purposes.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Request details
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField()
    response_time = models.FloatField(help_text="Response time in seconds")
    
    # User and authentication
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='api_usage_logs'
    )
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usage_logs'
    )
    
    # Request context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=36, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_usage_logs'
        verbose_name = _('API Usage Log')
        verbose_name_plural = _('API Usage Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['endpoint', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['api_key', 'created_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"