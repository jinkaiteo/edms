"""
Simple Django Signals for Workflow Management.

Simplified signals for the DocumentWorkflow approach.
Handles basic audit logging without complex dependencies.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DocumentWorkflow, DocumentTransition


@receiver(post_save, sender=DocumentWorkflow)
def log_workflow_creation(sender, instance, created, **kwargs):
    """Simple logging for workflow creation."""
    if created:
        print(f"✓ Workflow created: {instance.document.document_number} - {instance.workflow_type}")


@receiver(post_save, sender=DocumentTransition)
def log_workflow_transition(sender, instance, created, **kwargs):
    """Simple logging for workflow transitions."""
    if created:
        print(f"✓ Transition: {instance.from_state.code} → {instance.to_state.code} by {instance.transitioned_by.username}")


# Note: Complex audit logging is temporarily disabled to avoid transaction conflicts
# In production, implement proper async audit logging using Celery tasks