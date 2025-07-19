import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import str as String

class EncryptionService:
    """Encryption service for Autogent Studio API keys and sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with master key."""
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get existing master key or create a new one."""
        # In production, this should be stored securely (e.g., AWS KMS, Azure Key Vault)
        master_key_env = os.environ.get("ENCRYPTION_MASTER_KEY")
        
        if master_key_env:
            try:
                return base64.urlsafe_b64decode(master_key_env)
            except Exception:
                pass
        
        # Generate new key if none exists
        return Fernet.generate_key()
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: String data to encrypt
        
        Returns:
            Base64 encoded encrypted data
        """
        try:
            if not isinstance(data, str):
                data = str(data)
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
        
        Returns:
            Decrypted string data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")
    
    def encrypt_api_key(self, api_key: str, service_name: str) -> str:
        """
        Encrypt API key with additional service context.
        
        Args:
            api_key: API key to encrypt
            service_name: Name of the service (for additional entropy)
        
        Returns:
            Encrypted API key
        """
        try:
            # Add service name as prefix for additional security
            prefixed_key = f"{service_name}:{api_key}"
            return self.encrypt(prefixed_key)
        except Exception as e:
            raise Exception(f"API key encryption failed: {str(e)}")
    
    def decrypt_api_key(self, encrypted_api_key: str, service_name: str) -> str:
        """
        Decrypt API key and verify service context.
        
        Args:
            encrypted_api_key: Encrypted API key
            service_name: Expected service name
        
        Returns:
            Decrypted API key
        """
        try:
            decrypted_data = self.decrypt(encrypted_api_key)
            
            # Verify service name prefix
            if not decrypted_data.startswith(f"{service_name}:"):
                raise ValueError("Service name mismatch in encrypted data")
            
            # Extract actual API key
            api_key = decrypted_data[len(service_name) + 1:]
            return api_key
        except Exception as e:
            raise Exception(f"API key decryption failed: {str(e)}")
    
    def encrypt_with_password(self, data: str, password: str) -> dict:
        """
        Encrypt data using password-based encryption.
        
        Args:
            data: Data to encrypt
            password: Password for encryption
        
        Returns:
            Dictionary containing encrypted data and salt
        """
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Derive key from password
            key = self._derive_key_from_password(password, salt)
            fernet = Fernet(key)
            
            # Encrypt data
            encrypted_data = fernet.encrypt(data.encode())
            
            return {
                "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
                "salt": base64.urlsafe_b64encode(salt).decode()
            }
        except Exception as e:
            raise Exception(f"Password-based encryption failed: {str(e)}")
    
    def decrypt_with_password(self, encrypted_data: str, salt: str, password: str) -> str:
        """
        Decrypt data using password-based encryption.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            salt: Base64 encoded salt
            password: Password for decryption
        
        Returns:
            Decrypted data
        """
        try:
            # Decode salt and encrypted data
            salt_bytes = base64.urlsafe_b64decode(salt.encode())
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Derive key from password
            key = self._derive_key_from_password(password, salt_bytes)
            fernet = Fernet(key)
            
            # Decrypt data
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            raise Exception(f"Password-based decryption failed: {str(e)}")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: Length of token in bytes
        
        Returns:
            Base64 encoded secure token
        """
        try:
            token = os.urandom(length)
            return base64.urlsafe_b64encode(token).decode()
        except Exception as e:
            raise Exception(f"Token generation failed: {str(e)}")
    
    def hash_password(self, password: str) -> dict:
        """
        Hash password using PBKDF2.
        
        Args:
            password: Password to hash
        
        Returns:
            Dictionary containing hashed password and salt
        """
        try:
            salt = os.urandom(32)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            hashed_password = kdf.derive(password.encode())
            
            return {
                "hashed_password": base64.urlsafe_b64encode(hashed_password).decode(),
                "salt": base64.urlsafe_b64encode(salt).decode()
            }
        except Exception as e:
            raise Exception(f"Password hashing failed: {str(e)}")
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Password to verify
            hashed_password: Base64 encoded hashed password
            salt: Base64 encoded salt
        
        Returns:
            True if password is correct
        """
        try:
            salt_bytes = base64.urlsafe_b64decode(salt.encode())
            stored_hash = base64.urlsafe_b64decode(hashed_password.encode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )
            
            # This will raise an exception if the password is wrong
            kdf.verify(password.encode(), stored_hash)
            return True
        except Exception:
            return False
    
    def encrypt_json_data(self, data: dict) -> str:
        """
        Encrypt JSON-serializable data.
        
        Args:
            data: Dictionary to encrypt
        
        Returns:
            Encrypted JSON string
        """
        try:
            import json
            json_string = json.dumps(data, sort_keys=True)
            return self.encrypt(json_string)
        except Exception as e:
            raise Exception(f"JSON encryption failed: {str(e)}")
    
    def decrypt_json_data(self, encrypted_data: str) -> dict:
        """
        Decrypt JSON data.
        
        Args:
            encrypted_data: Encrypted JSON string
        
        Returns:
            Decrypted dictionary
        """
        try:
            import json
            decrypted_string = self.decrypt(encrypted_data)
            return json.loads(decrypted_string)
        except Exception as e:
            raise Exception(f"JSON decryption failed: {str(e)}")
