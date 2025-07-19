import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import str, bytes, Optional

class EncryptionService:
    """Service for handling encryption and decryption of sensitive data"""
    
    def __init__(self):
        self.master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            # Generate a master key if not provided (for development)
            self.master_key = Fernet.generate_key().decode()
            logging.warning("Using generated master key - set ENCRYPTION_MASTER_KEY in production")
        
        self.fernet = Fernet(self.master_key.encode() if isinstance(self.master_key, str) else self.master_key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logging.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
            
        except Exception as e:
            logging.error(f"Decryption error: {str(e)}")
            raise
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt bytes data"""
        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            logging.error(f"Bytes encryption error: {str(e)}")
            raise
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt bytes data"""
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            logging.error(f"Bytes decryption error: {str(e)}")
            raise
    
    def generate_key(self) -> str:
        """Generate a new encryption key"""
        try:
            key = Fernet.generate_key()
            return base64.b64encode(key).decode()
        except Exception as e:
            logging.error(f"Key generation error: {str(e)}")
            raise
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> str:
        """Derive encryption key from password"""
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
            return key.decode()
            
        except Exception as e:
            logging.error(f"Key derivation error: {str(e)}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password for storage"""
        try:
            from werkzeug.security import generate_password_hash
            return generate_password_hash(password)
        except Exception as e:
            logging.error(f"Password hashing error: {str(e)}")
            raise
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            from werkzeug.security import check_password_hash
            return check_password_hash(password_hash, password)
        except Exception as e:
            logging.error(f"Password verification error: {str(e)}")
            return False
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file"""
        try:
            if output_path is None:
                output_path = file_path + '.encrypted'
            
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.encrypt_bytes(file_data)
            
            with open(output_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            return output_path
            
        except Exception as e:
            logging.error(f"File encryption error: {str(e)}")
            raise
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        try:
            if output_path is None:
                output_path = encrypted_file_path.replace('.encrypted', '')
            
            with open(encrypted_file_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.decrypt_bytes(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            return output_path
            
        except Exception as e:
            logging.error(f"File decryption error: {str(e)}")
            raise
    
    def secure_delete(self, file_path: str):
        """Securely delete a file by overwriting it"""
        try:
            if not os.path.exists(file_path):
                return
            
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data multiple times
            with open(file_path, "r+b") as file:
                for _ in range(3):
                    file.seek(0)
                    file.write(os.urandom(file_size))
                    file.flush()
                    os.fsync(file.fileno())
            
            # Finally delete the file
            os.remove(file_path)
            
        except Exception as e:
            logging.error(f"Secure delete error: {str(e)}")
            raise
    
    def create_secure_token(self, length: int = 32) -> str:
        """Create a secure random token"""
        try:
            token = os.urandom(length)
            return base64.urlsafe_b64encode(token).decode()
        except Exception as e:
            logging.error(f"Token creation error: {str(e)}")
            raise
    
    def encrypt_json(self, data: dict) -> str:
        """Encrypt JSON data"""
        try:
            import json
            json_string = json.dumps(data)
            return self.encrypt(json_string)
        except Exception as e:
            logging.error(f"JSON encryption error: {str(e)}")
            raise
    
    def decrypt_json(self, encrypted_data: str) -> dict:
        """Decrypt JSON data"""
        try:
            import json
            json_string = self.decrypt(encrypted_data)
            return json.loads(json_string)
        except Exception as e:
            logging.error(f"JSON decryption error: {str(e)}")
            raise
    
    def rotate_key(self, new_key: Optional[str] = None) -> str:
        """Rotate the master encryption key"""
        try:
            if new_key is None:
                new_key = Fernet.generate_key().decode()
            
            # Store old key for migration
            old_fernet = self.fernet
            
            # Update to new key
            self.master_key = new_key
            self.fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
            
            logging.info("Encryption key rotated successfully")
            return new_key
            
        except Exception as e:
            logging.error(f"Key rotation error: {str(e)}")
            raise
    
    def migrate_encrypted_data(self, old_encrypted_data: str, old_key: str) -> str:
        """Migrate data from old key to current key"""
        try:
            # Create Fernet instance with old key
            old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
            
            # Decrypt with old key
            decoded_data = base64.b64decode(old_encrypted_data.encode())
            decrypted_data = old_fernet.decrypt(decoded_data)
            
            # Re-encrypt with current key
            new_encrypted_data = self.fernet.encrypt(decrypted_data)
            return base64.b64encode(new_encrypted_data).decode()
            
        except Exception as e:
            logging.error(f"Data migration error: {str(e)}")
            raise
    
    def verify_integrity(self, data: str, signature: str) -> bool:
        """Verify data integrity using signature"""
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.hmac import HMAC
            
            # Create HMAC signature for comparison
            h = HMAC(self.master_key.encode(), hashes.SHA256())
            h.update(data.encode())
            expected_signature = base64.b64encode(h.finalize()).decode()
            
            return expected_signature == signature
            
        except Exception as e:
            logging.error(f"Integrity verification error: {str(e)}")
            return False
    
    def create_signature(self, data: str) -> str:
        """Create HMAC signature for data"""
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.hmac import HMAC
            
            h = HMAC(self.master_key.encode(), hashes.SHA256())
            h.update(data.encode())
            signature = base64.b64encode(h.finalize()).decode()
            
            return signature
            
        except Exception as e:
            logging.error(f"Signature creation error: {str(e)}")
            raise
