"""
Security Signals for EDMS

Handles security-related events and automatic audit logging
for encryption, decryption, and signature operations.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EncryptionKey, DigitalSignature, SecurityEvent


@receiver(post_save, sender=EncryptionKey)
def log_encryption_key_event(sender, instance, created, **kwargs):
    """Log encryption key creation and updates."""
    action = 'key_generation' if created else 'key_update'
    
    SecurityEvent.objects.create(
        event_type=action,
        title=f"Encryption Key {'Created' if created else 'Updated'}",
        description=f"Encryption key '{instance.name}' was {'created' if created else 'updated'}",
        severity='info',
        encryption_key=instance,
        user=getattr(instance, '_current_user', None),
        ip_address=getattr(instance, '_current_ip', None),
        metadata={
            'key_type': instance.key_type,
            'algorithm': instance.algorithm,
            'key_size': instance.key_size,
        }
    )


@receiver(post_save, sender=DigitalSignature)
def log_signature_event(sender, instance, created, **kwargs):
    """Log digital signature creation and verification."""
    if created:
        SecurityEvent.objects.create(
            event_type='signature_creation',
            title="Digital Signature Applied",
            description=f"Digital signature applied to document by {instance.signer.username}",
            severity='info',
            document=instance.document,
            signature=instance,
            user=instance.signer,
            metadata={
                'algorithm': instance.algorithm,
                'signature_purpose': instance.signature_purpose,
                'document_hash': instance.document_hash,
            }
        )


@receiver(post_delete, sender=EncryptionKey)
def log_key_deletion(sender, instance, **kwargs):
    """Log encryption key deletion."""
    SecurityEvent.objects.create(
        event_type='key_revocation',
        title="Encryption Key Deleted",
        description=f"Encryption key '{instance.name}' was deleted",
        severity='warning',
        user=getattr(instance, '_deleted_by', None),
        metadata={
            'key_type': instance.key_type,
            'key_id': instance.key_id,
            'was_active': instance.is_active,
        }
    )