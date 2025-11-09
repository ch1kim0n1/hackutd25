"""
Credential encryption service for APEX.
Encrypts and decrypts sensitive credentials (API keys, access tokens) using Fernet symmetric encryption.
"""
import os
import base64
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)


class CredentialEncryptionService:
    """
    Handles encryption/decryption of user credentials.
    Each user has a unique encryption key stored in the database.
    """
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a new Fernet encryption key for a user.
        Returns base64-encoded key string.
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')  # Decode to store as string
    
    @staticmethod
    def encrypt_credential(plaintext: str, encryption_key: str) -> bytes:
        """
        Encrypt a credential string using the user's encryption key.
        
        Args:
            plaintext: The plaintext credential (API key, token, etc.)
            encryption_key: Base64-encoded Fernet key from user.encryption_key
        
        Returns:
            Encrypted bytes suitable for LargeBinary column
        
        Raises:
            ValueError: If encryption key is invalid
        """
        if not plaintext:
            return None
        
        try:
            # Decode the base64-encoded key
            key_bytes = encryption_key.encode('utf-8') if isinstance(encryption_key, str) else encryption_key
            fernet = Fernet(key_bytes)
            
            # Encrypt the plaintext
            plaintext_bytes = plaintext.encode('utf-8') if isinstance(plaintext, str) else plaintext
            ciphertext = fernet.encrypt(plaintext_bytes)
            
            return ciphertext
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt credential: {str(e)}")
    
    @staticmethod
    def decrypt_credential(ciphertext: bytes, encryption_key: str) -> str:
        """
        Decrypt a credential using the user's encryption key.
        
        Args:
            ciphertext: Encrypted bytes from LargeBinary column
            encryption_key: Base64-encoded Fernet key from user.encryption_key
        
        Returns:
            Decrypted plaintext string
        
        Raises:
            ValueError: If decryption fails (invalid key, corrupted data)
        """
        if not ciphertext:
            return None
        
        try:
            # Decode the base64-encoded key
            key_bytes = encryption_key.encode('utf-8') if isinstance(encryption_key, str) else encryption_key
            fernet = Fernet(key_bytes)
            
            # Decrypt the ciphertext
            plaintext = fernet.decrypt(ciphertext)
            
            return plaintext.decode('utf-8')
        except InvalidToken as e:
            logger.error(f"Decryption failed - invalid token or corrupted data")
            raise ValueError("Failed to decrypt credential - invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt credential: {str(e)}")
    
    @staticmethod
    def rotate_encryption_key(old_ciphertext_dict: dict, old_key: str, new_key: str) -> dict:
        """
        Re-encrypt all encrypted credentials with a new encryption key.
        Useful for key rotation.
        
        Args:
            old_ciphertext_dict: Dict of {field_name: ciphertext_bytes}
            old_key: Base64-encoded old Fernet key
            new_key: Base64-encoded new Fernet key
        
        Returns:
            Dict of {field_name: newly_encrypted_bytes}
        """
        new_ciphertext_dict = {}
        
        for field_name, ciphertext in old_ciphertext_dict.items():
            if not ciphertext:
                new_ciphertext_dict[field_name] = None
                continue
            
            try:
                # Decrypt with old key
                plaintext = CredentialEncryptionService.decrypt_credential(ciphertext, old_key)
                
                # Encrypt with new key
                new_ciphertext = CredentialEncryptionService.encrypt_credential(plaintext, new_key)
                
                new_ciphertext_dict[field_name] = new_ciphertext
            except Exception as e:
                logger.error(f"Failed to rotate key for {field_name}: {str(e)}")
                raise ValueError(f"Failed to rotate encryption key for {field_name}: {str(e)}")
        
        return new_ciphertext_dict
    
    @staticmethod
    def audit_encryption_status(user) -> dict:
        """
        Audit which credentials are encrypted for a user.
        Returns status of encryption for all credential fields.
        
        Args:
            user: User model instance
        
        Returns:
            Dict with encryption status for each field
        """
        return {
            "encryption_key_present": bool(user.encryption_key),
            "plaid_access_token_encrypted": bool(user.plaid_access_token),
            "alpaca_api_key_encrypted": bool(user.alpaca_api_key),
            "alpaca_secret_key_encrypted": bool(user.alpaca_secret_key),
            "total_encrypted_fields": sum([
                bool(user.plaid_access_token),
                bool(user.alpaca_api_key),
                bool(user.alpaca_secret_key),
            ])
        }
