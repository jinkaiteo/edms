"""
Security Models for EDMS

Manages encryption keys, digital signatures, and security events
for 21 CFR Part 11 compliance.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class EncryptionKey(models.Model):
    """
    Manages encryption keys used for document encryption.
    
    Stores metadata about encryption keys while keeping
    the actual key material secure.
    """
    
    KEY_TYPES = [
        ('master', 'Master Key'),
        ('document', 'Document Key'),
        ('backup', 'Backup Key'),
        ('temp', 'Temporary Key'),
    ]
    
    KEY_ALGORITHMS = [
        ('AES-256', 'AES 256-bit'),
        ('Fernet', 'Fernet (AES 128-bit)'),
        ('RSA-2048', 'RSA 2048-bit'),
        ('RSA-4096', 'RSA 4096-bit'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    key_type = models.CharField(max_length=20, choices=KEY_TYPES)
    algorithm = models.CharField(max_length=20, choices=KEY_ALGORITHMS)
    
    # Key metadata (not the actual key)
    key_id = models.CharField(max_length=64, unique=True)
    fingerprint = models.CharField(max_length=64)
    key_size = models.IntegerField()
    
    # Lifecycle management
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        null=True, blank=True,
        related_name='revoked_keys'
    )
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "security"
        db_table = 'security_encryption_keys'
        verbose_name = _('Encryption Key')
        verbose_name_plural = _('Encryption Keys')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key_type', 'is_active']),
            models.Index(fields=['key_id']),
            models.Index(fields=['fingerprint']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key_type})"


class PDFSigningCertificate(models.Model):
    """X.509 certificates for PDF digital signatures."""
    CERT_TYPE_CHOICES = [
        ('SELF_SIGNED', 'Self-Signed'),
        ('CA_ISSUED', 'Certificate Authority Issued'),
        ('DEVELOPMENT', 'Development Only'),
    ]
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200, help_text="Certificate friendly name")
    certificate_type = models.CharField(max_length=20, choices=CERT_TYPE_CHOICES, default='SELF_SIGNED')
    
    # Certificate data
    certificate_pem = models.TextField(help_text="PEM encoded certificate")
    private_key_pem = models.TextField(help_text="PEM encoded private key")
    public_key_pem = models.TextField(help_text="PEM encoded public key")
    
    # Certificate metadata
    subject_cn = models.CharField(max_length=200, help_text="Certificate Common Name")
    issuer_name = models.CharField(max_length=200, help_text="Certificate Issuer")
    serial_number = models.CharField(max_length=100, unique=True)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Management
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default certificate for PDF signing")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "PDF Signing Certificate"
        verbose_name_plural = "PDF Signing Certificates"
    
    def natural_key(self):
        """Return the natural key for this PDF signing certificate"""
        return (self.serial_number,)

    @classmethod
    def get_by_natural_key(cls, serial_number):
        """Get PDF signing certificate by natural key (serial_number)"""
        return cls.objects.get(serial_number=serial_number)

    def __str__(self):
        return f"{self.name} ({self.subject_cn})"
    
    @property
    def is_expired(self):
        """Check if certificate is expired."""
        from django.utils import timezone
        return timezone.now() > self.valid_until
    
    @property
    def expires_soon(self):
        """Check if certificate expires within 30 days."""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() + timedelta(days=30) > self.valid_until


class PDFGenerationLog(models.Model):
    """Log of PDF generation attempts for audit and monitoring."""
    GENERATION_TYPE_CHOICES = [
        ('DOCX_TO_PDF', 'DOCX to PDF'),
        ('FILE_TO_PDF', 'File to PDF'),
        ('PDF_PASSTHROUGH', 'PDF Passthrough'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('TIMEOUT', 'Timeout'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Related objects
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.PROTECT)
    certificate = models.ForeignKey(PDFSigningCertificate, on_delete=models.PROTECT, null=True, blank=True)
    
    # Generation details
    generation_type = models.CharField(max_length=20, choices=GENERATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Performance metrics
    processing_time_ms = models.PositiveIntegerField(default=0, help_text="Processing time in milliseconds")
    input_file_size = models.PositiveIntegerField(default=0, help_text="Input file size in bytes")
    output_file_size = models.PositiveIntegerField(default=0, help_text="Generated PDF size in bytes")
    
    # Status details
    error_message = models.TextField(blank=True)
    signature_applied = models.BooleanField(default=False)
    metadata_embedded = models.BooleanField(default=False)
    watermark_applied = models.BooleanField(default=False)
    qr_code_added = models.BooleanField(default=False)
    
    # Audit fields
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "PDF Generation Log"
        verbose_name_plural = "PDF Generation Logs"
    
    def __str__(self):
        return f"PDF Generation {self.status} - {self.document.document_number} by {self.user}"
    
    @property
    def processing_time_seconds(self):
        """Get processing time in seconds."""
        return self.processing_time_ms / 1000.0


class DigitalSignature(models.Model):
    """
    Stores digital signature metadata for documents.
    
    Tracks digital signatures applied to documents for
    compliance and audit purposes.
    """
    
    SIGNATURE_ALGORITHMS = [
        ('RSA-PSS-SHA256', 'RSA-PSS with SHA-256'),
        ('RSA-PKCS1-SHA256', 'RSA-PKCS1 with SHA-256'),
        ('ECDSA-SHA256', 'ECDSA with SHA-256'),
        ('EdDSA', 'Edwards-curve Digital Signature Algorithm'),
    ]
    
    SIGNATURE_STATUS = [
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
        ('pending', 'Pending Verification'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        'documents.Document', 
        on_delete=models.PROTECT,
        related_name='signatures'
    )
    
    # Signature metadata
    signature_data = models.TextField()  # Base64 encoded signature
    algorithm = models.CharField(max_length=30, choices=SIGNATURE_ALGORITHMS)
    document_hash = models.CharField(max_length=64)  # SHA-256 hash
    
    # Signer information
    signer = models.ForeignKey(User, on_delete=models.PROTECT)
    signer_certificate = models.TextField(null=True, blank=True)
    signer_role = models.CharField(max_length=100, null=True, blank=True)
    
    # Signature lifecycle
    signed_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='verified_signatures'
    )
    
    # Status and validity
    status = models.CharField(max_length=20, choices=SIGNATURE_STATUS, default='pending')
    is_valid = models.BooleanField(null=True, blank=True)
    validation_message = models.TextField(blank=True)
    
    # Timestamping (for advanced compliance)
    timestamp_token = models.TextField(null=True, blank=True)
    timestamp_authority = models.CharField(max_length=200, null=True, blank=True)
    
    # Additional metadata
    signature_purpose = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "security"
        db_table = 'security_digital_signatures'
        verbose_name = _('Digital Signature')
        verbose_name_plural = _('Digital Signatures')
        ordering = ['-signed_at']
        indexes = [
            models.Index(fields=['document', 'signer']),
            models.Index(fields=['status', 'is_valid']),
            models.Index(fields=['signed_at']),
            models.Index(fields=['document_hash']),
        ]
    
    def __str__(self):
        return f"Signature by {self.signer.username} on {self.document}"


class SecurityEvent(models.Model):
    """
    Logs security-related events for audit and compliance.
    
    Tracks security events such as encryption/decryption,
    signature verification, key usage, etc.
    """
    
    EVENT_TYPES = [
        ('encryption', 'File Encryption'),
        ('decryption', 'File Decryption'),
        ('signature_creation', 'Signature Creation'),
        ('signature_verification', 'Signature Verification'),
        ('key_generation', 'Key Generation'),
        ('key_revocation', 'Key Revocation'),
        ('access_granted', 'Access Granted'),
        ('access_denied', 'Access Denied'),
        ('integrity_check', 'Integrity Check'),
        ('security_violation', 'Security Violation'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    # Event details
    title = models.CharField(max_length=200)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Actor information
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Related objects
    document = models.ForeignKey(
        'documents.Document', 
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    encryption_key = models.ForeignKey(
        EncryptionKey,
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    signature = models.ForeignKey(
        DigitalSignature,
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    
    # Event status and resolution
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='resolved_security_events'
    )
    resolution_notes = models.TextField(blank=True)
    
    # Additional context
    event_data = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "security"
        db_table = 'security_events'
        verbose_name = _('Security Event')
        verbose_name_plural = _('Security Events')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['document', 'event_type']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title}"


class CertificateAuthority(models.Model):
    """
    Manages Certificate Authority information for digital signatures.
    
    Stores CA certificates and metadata for signature verification
    and certificate chain validation.
    """
    
    CA_TYPES = [
        ('root', 'Root CA'),
        ('intermediate', 'Intermediate CA'),
        ('issuing', 'Issuing CA'),
        ('self_signed', 'Self-Signed'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    ca_type = models.CharField(max_length=20, choices=CA_TYPES)
    
    # Certificate data
    certificate_pem = models.TextField()
    public_key_pem = models.TextField()
    subject = models.CharField(max_length=500)
    issuer = models.CharField(max_length=500)
    serial_number = models.CharField(max_length=100)
    fingerprint_sha256 = models.CharField(max_length=64)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_valid = models.BooleanField(default=True)
    
    # CA hierarchy
    parent_ca = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='child_cas'
    )
    
    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    is_trusted = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "security"
        db_table = 'security_certificate_authorities'
        verbose_name = _('Certificate Authority')
        verbose_name_plural = _('Certificate Authorities')
        ordering = ['name']
        indexes = [
            models.Index(fields=['ca_type', 'is_valid']),
            models.Index(fields=['fingerprint_sha256']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['valid_until']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.ca_type})"