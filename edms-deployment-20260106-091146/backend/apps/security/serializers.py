"""
Security Serializers

API serializers for security-related models including digital signatures,
certificates, encryption keys, and security events.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DigitalSignature, SecurityEvent, EncryptionKey, CertificateAuthority

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for security context"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']


class DigitalSignatureSerializer(serializers.ModelSerializer):
    """Serializer for digital signatures"""
    signer = UserBasicSerializer(read_only=True)
    verified_by = UserBasicSerializer(read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    document_number = serializers.CharField(source='document.document_number', read_only=True)
    
    class Meta:
        model = DigitalSignature
        fields = [
            'id', 'uuid', 'document', 'document_title', 'document_number',
            'signature_data', 'algorithm', 'document_hash',
            'signer', 'signer_certificate', 'signer_role',
            'signed_at', 'verified_at', 'verified_by',
            'status', 'is_valid', 'validation_message',
            'timestamp_token', 'timestamp_authority',
            'signature_purpose', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'signed_at']
    
    def to_representation(self, instance):
        """Custom representation to match frontend expectations"""
        data = super().to_representation(instance)
        
        # Transform to match frontend ElectronicSignature interface
        return {
            'id': data['id'],
            'uuid': data['uuid'],
            'document': data['document'],
            'user': data['signer'],
            'signature_type': data['signer_role'] or 'DIGITAL',
            'reason': data['signature_purpose'] or 'Digital signature applied',
            'signature_timestamp': data['signed_at'],
            'document_hash': data['document_hash'],
            'signature_data': {
                'algorithm': data['algorithm'],
                'signature': data['signature_data'][:50] + '...' if data['signature_data'] else '',  # Truncate for security
                'metadata': data['metadata']
            },
            'certificate': {
                'id': 1,  # Mock certificate data
                'uuid': 'cert-uuid',
                'user': data['signer']['id'] if data['signer'] else None,
                'certificate_type': 'SIGNING',
                'serial_number': f"CERT-{data['id']:03d}-2024",
                'subject_dn': f"CN={data['signer']['full_name']},O=EDMS,C=US" if data['signer'] else '',
                'issuer_dn': 'CN=EDMS CA,O=EDMS,C=US',
                'issued_at': '2024-01-01T00:00:00Z',
                'expires_at': '2025-01-01T00:00:00Z',
                'is_active': True,
                'revoked_at': None,
                'revocation_reason': ''
            },
            'signature_method': 'PKI_DIGITAL',
            'is_valid': data['is_valid'],
            'invalidated_at': None,
            'invalidation_reason': ''
        }


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for security events"""
    user = UserBasicSerializer(read_only=True)
    resolved_by = UserBasicSerializer(read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'uuid', 'event_type', 'severity',
            'title', 'description', 'timestamp',
            'user', 'ip_address', 'user_agent',
            'document', 'document_title',
            'is_resolved', 'resolved_at', 'resolved_by',
            'resolution_notes', 'event_data', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'timestamp']


class EncryptionKeySerializer(serializers.ModelSerializer):
    """Serializer for encryption keys (metadata only)"""
    created_by = UserBasicSerializer(read_only=True)
    revoked_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = EncryptionKey
        fields = [
            'id', 'uuid', 'name', 'key_type', 'algorithm',
            'key_id', 'fingerprint', 'key_size',
            'created_at', 'created_by', 'expires_at',
            'is_active', 'revoked_at', 'revoked_by',
            'last_used_at', 'usage_count', 'metadata'
        ]
        read_only_fields = [
            'id', 'uuid', 'key_id', 'fingerprint', 
            'created_at', 'last_used_at', 'usage_count'
        ]
    
    def to_representation(self, instance):
        """Hide sensitive key material"""
        data = super().to_representation(instance)
        
        # Never expose actual key material through API
        if 'key_material' in data.get('metadata', {}):
            data['metadata'] = {k: v for k, v in data['metadata'].items() if k != 'key_material'}
        
        return data


class CertificateAuthoritySerializer(serializers.ModelSerializer):
    """Serializer for Certificate Authorities"""
    created_by = UserBasicSerializer(read_only=True)
    parent_ca_name = serializers.CharField(source='parent_ca.name', read_only=True)
    
    class Meta:
        model = CertificateAuthority
        fields = [
            'id', 'uuid', 'name', 'ca_type',
            'subject', 'issuer', 'serial_number',
            'fingerprint_sha256', 'valid_from', 'valid_until',
            'is_valid', 'parent_ca', 'parent_ca_name',
            'created_at', 'created_by', 'is_trusted',
            'revoked_at', 'metadata'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'fingerprint_sha256']
    
    def to_representation(self, instance):
        """Secure representation of CA data"""
        data = super().to_representation(instance)
        
        # Don't expose full certificate PEM data in list views
        if self.context.get('request') and self.context['request'].method == 'GET':
            # Only show certificate in detail view
            if 'certificate_pem' in data:
                data['has_certificate'] = bool(instance.certificate_pem)
                data.pop('certificate_pem', None)
            if 'public_key_pem' in data:
                data['has_public_key'] = bool(instance.public_key_pem)
                data.pop('public_key_pem', None)
        
        return data