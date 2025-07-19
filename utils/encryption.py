import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def get_encryption_key():
    """Get or generate encryption key for API keys"""
    password = os.environ.get('ENCRYPTION_KEY', 'autogent-studio-default-key').encode()
    salt = b'autogent_studio_salt'  # In production, use random salt per user
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage"""
    if not api_key:
        return ""
    
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_key = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted_key).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key for use"""
    if not encrypted_key:
        return ""
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_data = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted_key = f.decrypt(encrypted_data)
        return decrypted_key.decode()
    except Exception as e:
        print(f"Error decrypting API key: {e}")
        return ""
