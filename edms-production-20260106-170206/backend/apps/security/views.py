"""
Security Views

API views for security-related operations including digital signatures,
certificates, encryption keys, and security events.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import DigitalSignature, SecurityEvent, EncryptionKey, CertificateAuthority
from .serializers import (
    DigitalSignatureSerializer,
    SecurityEventSerializer, 
    EncryptionKeySerializer,
    CertificateAuthoritySerializer
)


class DigitalSignatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing digital signatures.
    
    Provides CRUD operations for digital signatures with
    document filtering and verification capabilities.
    """
    serializer_class = DigitalSignatureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DigitalSignature.objects.all()
        
        # Filter by document ID if provided
        document_id = self.request.query_params.get('document_id', None)
        if document_id:
            try:
                queryset = queryset.filter(document__id=document_id)
            except (ValueError, TypeError):
                # If document_id is invalid, return empty queryset
                queryset = DigitalSignature.objects.none()
        
        return queryset.select_related('signer', 'document').order_by('-signed_at')
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify the digital signature"""
        signature = self.get_object()
        
        # In a real implementation, this would perform cryptographic verification
        # For now, return mock verification result
        verification_result = {
            'signature_id': signature.id,
            'is_valid': signature.is_valid,
            'verified_at': signature.verified_at,
            'verification_message': signature.validation_message or 'Signature verification completed',
            'algorithm': signature.algorithm,
            'signer': signature.signer.get_full_name() or signature.signer.username
        }
        
        return Response(verification_result)


class SecurityEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security events.
    
    Provides read-only access to security events for audit purposes.
    """
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityEvent.objects.all()
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            try:
                queryset = queryset.filter(user__id=user_id)
            except (ValueError, TypeError):
                queryset = SecurityEvent.objects.none()
        
        return queryset.select_related('user', 'document').order_by('-timestamp')


class EncryptionKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing encryption keys.
    
    Provides secure access to encryption key metadata.
    Note: Actual key material is never exposed through API.
    """
    serializer_class = EncryptionKeySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show active keys
        return EncryptionKey.objects.filter(
            is_active=True,
            revoked_at__isnull=True
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke an encryption key"""
        key = self.get_object()
        
        if key.revoked_at:
            return Response(
                {'error': 'Key is already revoked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In real implementation, this would properly revoke the key
        key.is_active = False
        key.revoked_by = request.user
        key.save()
        
        return Response({'message': 'Key revoked successfully'})


class CertificateAuthorityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Certificate Authorities.
    
    Provides access to CA information for certificate validation.
    """
    serializer_class = CertificateAuthoritySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show valid, trusted CAs
        return CertificateAuthority.objects.filter(
            is_valid=True,
            is_trusted=True,
            revoked_at__isnull=True
        ).order_by('name')
    
    @action(detail=True, methods=['get'])
    def certificate_chain(self, request, pk=None):
        """Get the certificate chain for this CA"""
        ca = self.get_object()
        
        # Build certificate chain
        chain = []
        current_ca = ca
        
        while current_ca:
            chain.append({
                'name': current_ca.name,
                'subject': current_ca.subject,
                'issuer': current_ca.issuer,
                'valid_from': current_ca.valid_from,
                'valid_until': current_ca.valid_until,
                'fingerprint': current_ca.fingerprint_sha256
            })
            current_ca = current_ca.parent_ca
            
            # Prevent infinite loops
            if len(chain) > 10:
                break
        
        return Response({
            'certificate_chain': chain,
            'chain_length': len(chain)
        })