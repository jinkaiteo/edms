"""
Certificate Management Service

Manages X.509 certificates for PDF digital signatures.
Handles certificate creation, validation, and storage.
"""

import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)


class CertificateManagerError(Exception):
    """Exception for certificate management errors."""
    pass


class CertificateManager:
    """Manage X.509 certificates for PDF signing."""
    
    def __init__(self):
        self.cert_storage = settings.OFFICIAL_PDF_CONFIG.get('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """Ensure certificate storage directory exists."""
        os.makedirs(self.cert_storage, exist_ok=True)
    
    def get_active_signing_certificate(self):
        """Get the currently active certificate for PDF signing."""
        from apps.security.models import PDFSigningCertificate
        
        cert = PDFSigningCertificate.objects.filter(
            is_active=True,
            is_default=True,
            valid_until__gt=timezone.now()
        ).first()
        
        if not cert:
            # Try to find any valid certificate
            cert = PDFSigningCertificate.objects.filter(
                is_active=True,
                valid_until__gt=timezone.now()
            ).first()
        
        if not cert:
            logger.warning("No valid signing certificate found, creating self-signed certificate")
            cert = self.create_self_signed_certificate()
        
        return cert
    
    def create_self_signed_certificate(self, common_name="EDMS PDF Signer"):
        """Generate self-signed certificate for development/testing."""
        logger.info(f"Creating self-signed certificate for: {common_name}")
        
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EDMS System"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # Build certificate
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)  # 1 year validity
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("edms.local"),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    key_cert_sign=True,
                    crl_sign=True,
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Convert to PEM format
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            # Save to database
            from apps.security.models import PDFSigningCertificate
            from django.contrib.auth import get_user_model
            
            # Get a system user (superuser)
            User = get_user_model()
            system_user = User.objects.filter(is_superuser=True).first()
            
            if not system_user:
                raise CertificateManagerError("No superuser found to assign certificate")
            
            # Create certificate record
            pdf_cert = PDFSigningCertificate.objects.create(
                name=f"Self-Signed Certificate - {common_name}",
                certificate_type='SELF_SIGNED',
                certificate_pem=cert_pem,
                private_key_pem=private_key_pem,
                public_key_pem=public_key_pem,
                subject_cn=common_name,
                issuer_name=common_name,  # Self-signed
                serial_number=str(cert.serial_number),
                valid_from=timezone.make_aware(datetime.utcnow()),
                valid_until=timezone.make_aware(datetime.utcnow() + timedelta(days=365)),
                is_active=True,
                is_default=True,
                created_by=system_user
            )
            
            logger.info(f"Created self-signed certificate: {pdf_cert.name} (ID: {pdf_cert.id})")
            return pdf_cert
            
        except Exception as e:
            logger.error(f"Failed to create self-signed certificate: {e}")
            raise CertificateManagerError(f"Certificate creation failed: {e}")
    
    def validate_certificate(self, pdf_certificate):
        """Validate certificate is still valid and usable."""
        try:
            # Check expiration
            if pdf_certificate.is_expired:
                raise CertificateManagerError("Certificate has expired")
            
            # Check if expires soon (within 30 days)
            if pdf_certificate.expires_soon:
                logger.warning(f"Certificate {pdf_certificate.name} expires soon: {pdf_certificate.valid_until}")
            
            # Try to load the certificate and private key
            cert_bytes = pdf_certificate.certificate_pem.encode('utf-8')
            key_bytes = pdf_certificate.private_key_pem.encode('utf-8')
            
            # Parse certificate
            cert = x509.load_pem_x509_certificate(cert_bytes)
            
            # Parse private key
            private_key = serialization.load_pem_private_key(key_bytes, password=None)
            
            # Verify they match
            public_key = cert.public_key()
            private_public_key = private_key.public_key()
            
            # Basic validation (in production, would do more thorough checks)
            if cert.serial_number != int(pdf_certificate.serial_number):
                raise CertificateManagerError("Certificate serial number mismatch")
            
            logger.info(f"Certificate validation successful: {pdf_certificate.name}")
            return True
            
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            raise CertificateManagerError(f"Certificate validation failed: {e}")
    
    def get_certificate_info(self, pdf_certificate):
        """Get detailed information about a certificate."""
        try:
            cert_bytes = pdf_certificate.certificate_pem.encode('utf-8')
            cert = x509.load_pem_x509_certificate(cert_bytes)
            
            return {
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'serial_number': str(cert.serial_number),
                'not_valid_before': cert.not_valid_before,
                'not_valid_after': cert.not_valid_after,
                'signature_algorithm': cert.signature_algorithm_oid._name,
                'public_key_size': cert.public_key().key_size,
                'fingerprint_sha256': cert.fingerprint(hashes.SHA256()).hex(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return {'error': str(e)}