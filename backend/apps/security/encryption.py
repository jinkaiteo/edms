"""
EDMS File Encryption System

Provides encryption/decryption services for document files
with 21 CFR Part 11 compliance and integrity verification.
"""

import os
import hashlib
import hmac
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import secrets
import json


class DocumentEncryption:
    """
    Document encryption service using Fernet (symmetric encryption)
    with PBKDF2 key derivation for secure file encryption.
    """
    
    def __init__(self):
        """Initialize encryption service with master key."""
        self.master_key = self._get_master_key()
        
    def _get_master_key(self):
        """Get or generate master encryption key."""
        master_key = getattr(settings, 'EDMS_MASTER_KEY', None)
        
        if not master_key:
            # Generate a new master key for development
            if settings.DEBUG:
                master_key = Fernet.generate_key()
                print(f"⚠️  Generated temporary master key: {master_key.decode()}")
                print("⚠️  Set EDMS_MASTER_KEY in production settings!")
            else:
                raise ImproperlyConfigured(
                    "EDMS_MASTER_KEY must be set in production settings"
                )
        
        if isinstance(master_key, str):
            master_key = master_key.encode()
            
        return master_key
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )
        return b64encode(kdf.derive(password.encode()))
    
    def encrypt_file(self, file_path: str, metadata: dict = None) -> dict:
        """
        Encrypt a file and return encryption metadata.
        
        Args:
            file_path: Path to the file to encrypt
            metadata: Additional metadata to include
            
        Returns:
            Dict containing encryption metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate salt and derive key
        salt = os.urandom(16)
        key = self.derive_key(self.master_key.decode(), salt)
        cipher = Fernet(key)
        
        # Read and encrypt file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Calculate original file hash
        original_hash = hashlib.sha256(file_data).hexdigest()
        
        # Encrypt data
        encrypted_data = cipher.encrypt(file_data)
        
        # Create encrypted file
        encrypted_path = f"{file_path}.encrypted"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Generate HMAC for integrity
        hmac_key = self.master_key[:32]
        file_hmac = hmac.new(
            hmac_key, 
            encrypted_data, 
            hashlib.sha256
        ).hexdigest()
        
        # Create metadata
        encryption_metadata = {
            'encrypted_path': encrypted_path,
            'salt': b64encode(salt).decode(),
            'algorithm': 'Fernet-PBKDF2',
            'iterations': 100000,
            'original_hash': original_hash,
            'encrypted_hash': hashlib.sha256(encrypted_data).hexdigest(),
            'hmac': file_hmac,
            'key_derivation': 'PBKDF2-SHA256',
            'encrypted_size': len(encrypted_data),
            'original_size': len(file_data),
            'metadata': metadata or {}
        }
        
        return encryption_metadata
    
    def decrypt_file(self, encrypted_path: str, encryption_metadata: dict, 
                    output_path: str = None) -> str:
        """
        Decrypt a file using provided metadata.
        
        Args:
            encrypted_path: Path to encrypted file
            encryption_metadata: Encryption metadata from encrypt_file
            output_path: Optional output path for decrypted file
            
        Returns:
            Path to decrypted file
        """
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        # Read encrypted data
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Verify HMAC integrity
        hmac_key = self.master_key[:32]
        expected_hmac = encryption_metadata['hmac']
        calculated_hmac = hmac.new(
            hmac_key, 
            encrypted_data, 
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_hmac, calculated_hmac):
            raise ValueError("File integrity verification failed - HMAC mismatch")
        
        # Derive decryption key
        salt = b64decode(encryption_metadata['salt'])
        key = self.derive_key(self.master_key.decode(), salt)
        cipher = Fernet(key)
        
        # Decrypt data
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
        
        # Verify original file hash
        calculated_hash = hashlib.sha256(decrypted_data).hexdigest()
        if calculated_hash != encryption_metadata['original_hash']:
            raise ValueError("File integrity verification failed - hash mismatch")
        
        # Write decrypted file
        if not output_path:
            output_path = encrypted_path.replace('.encrypted', '.decrypted')
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return output_path
    
    def verify_file_integrity(self, encrypted_path: str, 
                             encryption_metadata: dict) -> bool:
        """
        Verify encrypted file integrity without decryption.
        
        Args:
            encrypted_path: Path to encrypted file
            encryption_metadata: Encryption metadata
            
        Returns:
            True if file integrity is verified
        """
        try:
            if not os.path.exists(encrypted_path):
                return False
            
            # Read encrypted data
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Verify HMAC
            hmac_key = self.master_key[:32]
            expected_hmac = encryption_metadata['hmac']
            calculated_hmac = hmac.new(
                hmac_key, 
                encrypted_data, 
                hashlib.sha256
            ).hexdigest()
            
            # Verify encrypted file hash
            calculated_encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
            expected_encrypted_hash = encryption_metadata['encrypted_hash']
            
            return (hmac.compare_digest(expected_hmac, calculated_hmac) and
                    calculated_encrypted_hash == expected_encrypted_hash)
            
        except Exception:
            return False


class DigitalSignature:
    """
    Digital signature service for document integrity and authentication.
    Provides RSA-based signatures for 21 CFR Part 11 compliance.
    """
    
    def __init__(self):
        """Initialize digital signature service."""
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        private_key_path = getattr(settings, 'EDMS_PRIVATE_KEY_PATH', None)
        public_key_path = getattr(settings, 'EDMS_PUBLIC_KEY_PATH', None)
        
        if private_key_path and public_key_path:
            self._load_keys(private_key_path, public_key_path)
        else:
            if settings.DEBUG:
                print("⚠️  Generating temporary RSA keys for development")
                print("⚠️  Use proper key management in production!")
                self._generate_keys()
            else:
                raise ImproperlyConfigured(
                    "RSA key paths must be configured in production"
                )
    
    def _generate_keys(self):
        """Generate new RSA key pair."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def _load_keys(self, private_key_path: str, public_key_path: str):
        """Load RSA keys from files."""
        try:
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            with open(public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(f.read())
                
        except Exception as e:
            raise ImproperlyConfigured(f"Failed to load RSA keys: {e}")
    
    def save_keys(self, private_key_path: str, public_key_path: str, 
                  password: bytes = None):
        """Save RSA keys to files."""
        if not self.private_key or not self.public_key:
            raise ValueError("No keys to save")
        
        # Save private key
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password) 
            if password else serialization.NoEncryption()
        )
        
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        
        # Save public key
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(public_key_path, 'wb') as f:
            f.write(public_pem)
    
    def sign_document(self, file_path: str, signer_info: dict = None) -> dict:
        """
        Create digital signature for a document.
        
        Args:
            file_path: Path to the document file
            signer_info: Information about the signer
            
        Returns:
            Dict containing signature and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Read document content
        with open(file_path, 'rb') as f:
            document_data = f.read()
        
        # Calculate document hash
        document_hash = hashlib.sha256(document_data).digest()
        
        # Create signature
        signature = self.private_key.sign(
            document_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Create signature metadata
        signature_metadata = {
            'signature': b64encode(signature).decode(),
            'algorithm': 'RSA-PSS-SHA256',
            'document_hash': document_hash.hex(),
            'document_size': len(document_data),
            'timestamp': secrets.token_hex(16),  # Replace with proper timestamp service
            'signer_info': signer_info or {},
            'public_key_fingerprint': self._get_public_key_fingerprint()
        }
        
        return signature_metadata
    
    def verify_signature(self, file_path: str, signature_metadata: dict) -> bool:
        """
        Verify document digital signature.
        
        Args:
            file_path: Path to the document file
            signature_metadata: Signature metadata from sign_document
            
        Returns:
            True if signature is valid
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Read document content
            with open(file_path, 'rb') as f:
                document_data = f.read()
            
            # Verify document hash
            document_hash = hashlib.sha256(document_data).digest()
            expected_hash = signature_metadata['document_hash']
            
            if document_hash.hex() != expected_hash:
                return False
            
            # Verify signature
            signature = b64decode(signature_metadata['signature'])
            
            self.public_key.verify(
                signature,
                document_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception:
            return False
    
    def _get_public_key_fingerprint(self) -> str:
        """Get public key fingerprint for identification."""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(public_pem).hexdigest()[:16]


# Initialize global instances
document_encryption = DocumentEncryption()
digital_signature = DigitalSignature()


def encrypt_document_file(file_path: str, metadata: dict = None) -> dict:
    """Convenience function to encrypt a document file."""
    return document_encryption.encrypt_file(file_path, metadata)


def decrypt_document_file(encrypted_path: str, encryption_metadata: dict, 
                         output_path: str = None) -> str:
    """Convenience function to decrypt a document file."""
    return document_encryption.decrypt_file(
        encrypted_path, encryption_metadata, output_path
    )


def sign_document_file(file_path: str, signer_info: dict = None) -> dict:
    """Convenience function to sign a document file."""
    return digital_signature.sign_document(file_path, signer_info)


def verify_document_signature(file_path: str, signature_metadata: dict) -> bool:
    """Convenience function to verify a document signature."""
    return digital_signature.verify_signature(file_path, signature_metadata)