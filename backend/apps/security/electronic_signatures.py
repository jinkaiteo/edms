"""
Electronic Signature Services for EDMS.

Implements electronic signature capabilities for 21 CFR Part 11 compliance,
including cryptographic signing, validation, and certificate management.
"""

import hashlib
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.storage import default_storage

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12

from .models import (
    ElectronicSignature, CertificateStore, SignatureValidation,
    UserCertificate
)
from apps.documents.models import Document
from apps.audit.services import audit_service

User = get_user_model()
logger = logging.getLogger(__name__)


class ElectronicSignatureService:
    """
    Core service for electronic signatures.
    
    Provides cryptographic signing capabilities for documents
    with 21 CFR Part 11 compliance features.
    """

    def __init__(self):
        self.algorithm = hashes.SHA256()
        self.key_size = 2048
        self.certificate_validity_days = 365

    def create_signature(self, document: Document, user: User, signature_reason: str,
                        signature_type: str = 'APPROVAL', password: str = None) -> ElectronicSignature:
        """
        Create an electronic signature for a document.
        
        Args:
            document: Document to sign
            user: User creating the signature
            signature_reason: Reason for signing
            signature_type: Type of signature (APPROVAL, REVIEW, AUTHOR, etc.)
            password: User's signing password
            
        Returns:
            ElectronicSignature: Created signature record
        """
        # Validate user can sign this document
        if not self._can_user_sign_document(user, document, signature_type):
            raise ValueError(f"User {user.username} cannot create {signature_type} signature for this document")

        # Get or create user certificate
        user_cert = self._get_or_create_user_certificate(user, password)
        
        # Generate document hash
        document_hash = self._calculate_document_hash(document)
        
        # Create cryptographic signature
        signature_data = self._create_cryptographic_signature(
            document_hash, user_cert, signature_reason
        )
        
        # Create signature record
        electronic_signature = ElectronicSignature.objects.create(
            document=document,
            user=user,
            signature_type=signature_type,
            reason=signature_reason,
            signature_timestamp=timezone.now(),
            document_hash=document_hash,
            signature_data=signature_data,
            certificate=user_cert,
            signature_method='PKI_DIGITAL',
            is_valid=True
        )
        
        # Log audit trail
        audit_service.log_user_action(
            user=user,
            action='ELECTRONIC_SIGNATURE_CREATED',
            object_type='Document',
            object_id=document.id,
            description=f"Electronic signature created: {signature_type}",
            additional_data={
                'signature_type': signature_type,
                'reason': signature_reason,
                'document_hash': document_hash,
                'signature_id': str(electronic_signature.uuid)
            }
        )
        
        return electronic_signature

    def validate_signature(self, signature: ElectronicSignature) -> SignatureValidation:
        """
        Validate an electronic signature.
        
        Args:
            signature: Electronic signature to validate
            
        Returns:
            SignatureValidation: Validation results
        """
        validation = SignatureValidation.objects.create(
            signature=signature,
            validated_at=timezone.now(),
            validation_method='CRYPTOGRAPHIC_VERIFICATION'
        )
        
        try:
            # Validate certificate
            cert_valid = self._validate_certificate(signature.certificate)
            
            # Validate signature integrity
            signature_valid = self._validate_signature_integrity(signature)
            
            # Validate document integrity
            document_valid = self._validate_document_integrity(signature)
            
            # Overall validation result
            is_valid = cert_valid and signature_valid and document_valid
            
            validation.is_valid = is_valid
            validation.certificate_valid = cert_valid
            validation.signature_valid = signature_valid
            validation.document_unchanged = document_valid
            validation.validation_details = {
                'certificate_check': cert_valid,
                'signature_check': signature_valid,
                'document_check': document_valid,
                'validation_timestamp': timezone.now().isoformat()
            }
            
            if not is_valid:
                validation.validation_errors = self._get_validation_errors(
                    cert_valid, signature_valid, document_valid
                )
            
            validation.save()
            
            # Log validation
            audit_service.log_system_event(
                event_type='SIGNATURE_VALIDATED',
                object_type='ElectronicSignature',
                object_id=signature.id,
                description=f"Signature validation result: {is_valid}",
                additional_data={
                    'signature_id': str(signature.uuid),
                    'validation_id': str(validation.uuid),
                    'is_valid': is_valid,
                    'validation_details': validation.validation_details
                }
            )
            
            return validation
            
        except Exception as e:
            validation.is_valid = False
            validation.validation_errors = {'exception': str(e)}
            validation.save()
            
            logger.error(f"Signature validation failed: {str(e)}")
            raise

    def verify_signature_chain(self, document: Document) -> Dict[str, Any]:
        """
        Verify the complete signature chain for a document.
        
        Args:
            document: Document to verify
            
        Returns:
            Dict containing verification results
        """
        signatures = ElectronicSignature.objects.filter(
            document=document
        ).order_by('signature_timestamp')
        
        verification_results = {
            'document_id': document.id,
            'total_signatures': signatures.count(),
            'valid_signatures': 0,
            'invalid_signatures': 0,
            'signature_details': [],
            'chain_valid': True,
            'verification_timestamp': timezone.now().isoformat()
        }
        
        for signature in signatures:
            validation = self.validate_signature(signature)
            
            signature_detail = {
                'signature_id': str(signature.uuid),
                'user': signature.user.username,
                'signature_type': signature.signature_type,
                'timestamp': signature.signature_timestamp.isoformat(),
                'is_valid': validation.is_valid,
                'validation_details': validation.validation_details
            }
            
            verification_results['signature_details'].append(signature_detail)
            
            if validation.is_valid:
                verification_results['valid_signatures'] += 1
            else:
                verification_results['invalid_signatures'] += 1
                verification_results['chain_valid'] = False
        
        # Log chain verification
        audit_service.log_system_event(
            event_type='SIGNATURE_CHAIN_VERIFIED',
            object_type='Document',
            object_id=document.id,
            description=f"Signature chain verification: {verification_results['chain_valid']}",
            additional_data=verification_results
        )
        
        return verification_results

    def _can_user_sign_document(self, user: User, document: Document, signature_type: str) -> bool:
        """Check if user can create a signature of specified type for document."""
        from apps.users.workflow_permissions import workflow_permission_manager
        
        # Check basic permissions
        signature_permissions = {
            'APPROVAL': ['approve', 'admin'],
            'REVIEW': ['review', 'approve', 'admin'],
            'AUTHOR': ['write', 'admin'],
            'WITNESS': ['review', 'approve', 'admin'],
            'VERIFICATION': ['approve', 'admin']
        }
        
        required_permissions = signature_permissions.get(signature_type, ['admin'])
        
        return workflow_permission_manager._has_permission_level(user, required_permissions)

    def _get_or_create_user_certificate(self, user: User, password: str = None) -> 'UserCertificate':
        """Get existing or create new user certificate."""
        try:
            # Try to get existing valid certificate
            user_cert = UserCertificate.objects.get(
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return user_cert
            
        except UserCertificate.DoesNotExist:
            # Create new certificate
            return self._create_user_certificate(user, password)

    def _create_user_certificate(self, user: User, password: str = None) -> 'UserCertificate':
        """Create a new user certificate for signing."""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        
        # Create certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EDMS System"),
            x509.NameAttribute(NameOID.COMMON_NAME, user.get_full_name() or user.username),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, user.email),
        ])
        
        # Self-signed certificate for now
        issuer = subject
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            timezone.now()
        ).not_valid_after(
            timezone.now() + timedelta(days=self.certificate_validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.RFC822Name(user.email),
            ]),
            critical=False,
        ).sign(private_key, self.algorithm)
        
        # Serialize certificate and private key
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        
        # Encrypt private key if password provided
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
        else:
            encryption_algorithm = serialization.NoEncryption()
        
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        
        # Create UserCertificate record
        user_cert = UserCertificate.objects.create(
            user=user,
            certificate_data=cert_pem.decode('utf-8'),
            private_key_data=private_key_pem.decode('utf-8'),
            serial_number=str(cert.serial_number),
            subject_dn=subject.rfc4514_string(),
            issuer_dn=issuer.rfc4514_string(),
            issued_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=self.certificate_validity_days),
            is_active=True
        )
        
        # Log certificate creation
        audit_service.log_user_action(
            user=user,
            action='USER_CERTIFICATE_CREATED',
            object_type='UserCertificate',
            object_id=user_cert.id,
            description=f"User certificate created for {user.username}",
            additional_data={
                'serial_number': user_cert.serial_number,
                'expires_at': user_cert.expires_at.isoformat()
            }
        )
        
        return user_cert

    def _calculate_document_hash(self, document: Document) -> str:
        """Calculate SHA-256 hash of document content."""
        if document.file_path and default_storage.exists(document.file_path):
            try:
                with default_storage.open(document.file_path, 'rb') as f:
                    file_content = f.read()
                return hashlib.sha256(file_content).hexdigest()
            except Exception as e:
                logger.error(f"Error calculating document hash: {str(e)}")
        
        # Fallback to metadata hash
        metadata = {
            'document_number': document.document_number,
            'title': document.title,
            'version': str(document.version),
            'content_hash': document.file_checksum or ''
        }
        metadata_str = json.dumps(metadata, sort_keys=True)
        return hashlib.sha256(metadata_str.encode()).hexdigest()

    def _create_cryptographic_signature(self, document_hash: str, user_cert: 'UserCertificate',
                                       reason: str) -> Dict[str, Any]:
        """Create cryptographic signature for document hash."""
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                user_cert.private_key_data.encode('utf-8'),
                password=None  # TODO: Handle encrypted private keys
            )
            
            # Create signature data
            signature_payload = {
                'document_hash': document_hash,
                'user_id': user_cert.user.id,
                'username': user_cert.user.username,
                'reason': reason,
                'timestamp': timezone.now().isoformat(),
                'certificate_serial': user_cert.serial_number
            }
            
            # Serialize and sign
            payload_bytes = json.dumps(signature_payload, sort_keys=True).encode('utf-8')
            payload_hash = hashlib.sha256(payload_bytes).digest()
            
            # Create digital signature
            digital_signature = private_key.sign(
                payload_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Encode signature
            signature_b64 = base64.b64encode(digital_signature).decode('utf-8')
            
            return {
                'signature_payload': signature_payload,
                'digital_signature': signature_b64,
                'signature_algorithm': 'RSA-PSS-SHA256',
                'created_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating cryptographic signature: {str(e)}")
            raise

    def _validate_certificate(self, user_cert: 'UserCertificate') -> bool:
        """Validate user certificate."""
        try:
            # Check if certificate is active and not expired
            if not user_cert.is_active:
                return False
            
            if user_cert.expires_at < timezone.now():
                return False
            
            # Load and validate certificate
            cert_bytes = user_cert.certificate_data.encode('utf-8')
            cert = x509.load_pem_x509_certificate(cert_bytes)
            
            # Check validity period
            now = timezone.now()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                return False
            
            # Additional certificate validation could be added here
            # (e.g., CRL checking, OCSP validation)
            
            return True
            
        except Exception as e:
            logger.error(f"Certificate validation error: {str(e)}")
            return False

    def _validate_signature_integrity(self, signature: ElectronicSignature) -> bool:
        """Validate cryptographic signature integrity."""
        try:
            signature_data = signature.signature_data
            if not signature_data or 'digital_signature' not in signature_data:
                return False
            
            # Load certificate public key
            user_cert = signature.certificate
            cert_bytes = user_cert.certificate_data.encode('utf-8')
            cert = x509.load_pem_x509_certificate(cert_bytes)
            public_key = cert.public_key()
            
            # Recreate signature payload
            signature_payload = signature_data['signature_payload']
            payload_bytes = json.dumps(signature_payload, sort_keys=True).encode('utf-8')
            payload_hash = hashlib.sha256(payload_bytes).digest()
            
            # Decode and verify signature
            digital_signature = base64.b64decode(signature_data['digital_signature'])
            
            public_key.verify(
                digital_signature,
                payload_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Signature integrity validation error: {str(e)}")
            return False

    def _validate_document_integrity(self, signature: ElectronicSignature) -> bool:
        """Validate that document hasn't changed since signing."""
        try:
            # Calculate current document hash
            current_hash = self._calculate_document_hash(signature.document)
            
            # Compare with stored hash
            return current_hash == signature.document_hash
            
        except Exception as e:
            logger.error(f"Document integrity validation error: {str(e)}")
            return False

    def _get_validation_errors(self, cert_valid: bool, signature_valid: bool, 
                             document_valid: bool) -> Dict[str, str]:
        """Generate validation error messages."""
        errors = {}
        
        if not cert_valid:
            errors['certificate'] = 'Certificate is invalid or expired'
        
        if not signature_valid:
            errors['signature'] = 'Digital signature verification failed'
        
        if not document_valid:
            errors['document'] = 'Document has been modified since signing'
        
        return errors


# Global service instance
electronic_signature_service = ElectronicSignatureService()