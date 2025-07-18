import os
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EncryptionService:
    def __init__(self):
        self.master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            logging.warning("ENCRYPTION_MASTER_KEY not found, generating temporary key")
            self.master_key = Fernet.generate_key().decode()
        
        self.fernet = Fernet(self.master_key.encode() if isinstance(self.master_key, str) else self.master_key)
    
    def encrypt_api_key(self, api_key):
        """Encrypt API key for secure storage"""
        try:
            if not api_key:
                return None
            
            encrypted_key = self.fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted_key).decode()
        except Exception as e:
            logging.error(f"Error encrypting API key: {str(e)}")
            raise
    
    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key for use"""
        try:
            if not encrypted_key:
                return None
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_key = self.fernet.decrypt(encrypted_bytes)
            return decrypted_key.decode()
        except Exception as e:
            logging.error(f"Error decrypting API key: {str(e)}")
            raise
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data"""
        try:
            if not data:
                return None
            
            data_str = str(data)
            encrypted_data = self.fernet.encrypt(data_str.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logging.error(f"Error encrypting sensitive data: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            if not encrypted_data:
                return None
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logging.error(f"Error decrypting sensitive data: {str(e)}")
            raise
    
    def generate_key_from_password(self, password, salt=None):
        """Generate encryption key from password"""
        try:
            if salt is None:
                salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key, salt
        except Exception as e:
            logging.error(f"Error generating key from password: {str(e)}")
            raise
    
    def hash_password(self, password):
        """Hash password for storage"""
        try:
            # Generate salt and hash password
            salt = os.urandom(32)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return salt + key
        except Exception as e:
            logging.error(f"Error hashing password: {str(e)}")
            raise
    
    def verify_password(self, stored_password, provided_password):
        """Verify password against stored hash"""
        try:
            # Extract salt and hash from stored password
            salt = stored_password[:32]
            stored_key = stored_password[32:]
            
            # Hash provided password with same salt
            new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            
            # Compare hashes
            return new_key == stored_key
        except Exception as e:
            logging.error(f"Error verifying password: {str(e)}")
            return False

# Global encryption service instance
encryption_service = EncryptionService()
