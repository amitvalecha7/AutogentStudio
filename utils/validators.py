import re
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email or len(email) > 254:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    if not password:
        return {'valid': False, 'message': 'Password is required'}
    
    if len(password) < 8:
        return {'valid': False, 'message': 'Password must be at least 8 characters long'}
    
    if len(password) > 128:
        return {'valid': False, 'message': 'Password is too long'}
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return {'valid': False, 'message': 'Password must contain at least one lowercase letter'}
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return {'valid': False, 'message': 'Password must contain at least one uppercase letter'}
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return {'valid': False, 'message': 'Password must contain at least one number'}
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return {'valid': False, 'message': 'Password must contain at least one special character'}
    
    return {'valid': True, 'message': 'Password is valid'}

def validate_username(username: str) -> Dict[str, Any]:
    """Validate username format"""
    if not username:
        return {'valid': False, 'message': 'Username is required'}
    
    if len(username) < 3:
        return {'valid': False, 'message': 'Username must be at least 3 characters long'}
    
    if len(username) > 32:
        return {'valid': False, 'message': 'Username is too long'}
    
    # Allow alphanumeric characters, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return {'valid': False, 'message': 'Username can only contain letters, numbers, underscores, and hyphens'}
    
    # Username cannot start or end with underscore or hyphen
    if username.startswith(('_', '-')) or username.endswith(('_', '-')):
        return {'valid': False, 'message': 'Username cannot start or end with underscore or hyphen'}
    
    return {'valid': True, 'message': 'Username is valid'}

def validate_api_key(api_key: str, provider: str) -> Dict[str, Any]:
    """Validate API key format for different providers"""
    if not api_key:
        return {'valid': False, 'message': 'API key is required'}
    
    if provider.lower() == 'openai':
        if not api_key.startswith('sk-'):
            return {'valid': False, 'message': 'OpenAI API key must start with "sk-"'}
        if len(api_key) < 40:
            return {'valid': False, 'message': 'OpenAI API key is too short'}
    
    elif provider.lower() == 'anthropic':
        if not api_key.startswith('sk-ant-'):
            return {'valid': False, 'message': 'Anthropic API key must start with "sk-ant-"'}
        if len(api_key) < 40:
            return {'valid': False, 'message': 'Anthropic API key is too short'}
    
    elif provider.lower() == 'google':
        if len(api_key) < 32:
            return {'valid': False, 'message': 'Google API key is too short'}
    
    return {'valid': True, 'message': 'API key format is valid'}

def validate_url(url: str) -> Dict[str, Any]:
    """Validate URL format"""
    if not url:
        return {'valid': False, 'message': 'URL is required'}
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return {'valid': False, 'message': 'Invalid URL format'}
        
        if result.scheme not in ['http', 'https']:
            return {'valid': False, 'message': 'URL must use HTTP or HTTPS protocol'}
        
        return {'valid': True, 'message': 'URL is valid'}
    
    except Exception:
        return {'valid': False, 'message': 'Invalid URL format'}

def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def validate_file_upload(filename: str, file_size: int, allowed_extensions: List[str], max_size_mb: int = 10) -> Dict[str, Any]:
    """Validate file upload"""
    if not filename:
        return {'valid': False, 'message': 'Filename is required'}
    
    # Check file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if allowed_extensions and file_ext not in allowed_extensions:
        return {'valid': False, 'message': f'File type .{file_ext} not allowed. Allowed types: {", ".join(allowed_extensions)}'}
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return {'valid': False, 'message': f'File size exceeds maximum of {max_size_mb}MB'}
    
    # Check for potentially dangerous filenames
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return {'valid': False, 'message': 'Filename contains invalid characters'}
    
    return {'valid': True, 'message': 'File is valid'}

def validate_model_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate AI model configuration"""
    required_fields = ['model_name', 'provider']
    
    for field in required_fields:
        if field not in config:
            return {'valid': False, 'message': f'Missing required field: {field}'}
    
    # Validate temperature
    if 'temperature' in config:
        temp = config['temperature']
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
            return {'valid': False, 'message': 'Temperature must be between 0 and 2'}
    
    # Validate max_tokens
    if 'max_tokens' in config:
        max_tokens = config['max_tokens']
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 32768:
            return {'valid': False, 'message': 'Max tokens must be between 1 and 32768'}
    
    # Validate provider
    valid_providers = ['openai', 'anthropic', 'google', 'ollama', 'deepseek', 'qwen']
    if config['provider'].lower() not in valid_providers:
        return {'valid': False, 'message': f'Invalid provider. Must be one of: {", ".join(valid_providers)}'}
    
    return {'valid': True, 'message': 'Model configuration is valid'}

def validate_knowledge_base_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate knowledge base configuration"""
    required_fields = ['name', 'embedding_model']
    
    for field in required_fields:
        if field not in config:
            return {'valid': False, 'message': f'Missing required field: {field}'}
    
    # Validate chunk_size
    if 'chunk_size' in config:
        chunk_size = config['chunk_size']
        if not isinstance(chunk_size, int) or chunk_size < 100 or chunk_size > 8192:
            return {'valid': False, 'message': 'Chunk size must be between 100 and 8192'}
    
    # Validate chunk_overlap
    if 'chunk_overlap' in config:
        overlap = config['chunk_overlap']
        if not isinstance(overlap, int) or overlap < 0 or overlap > 1000:
            return {'valid': False, 'message': 'Chunk overlap must be between 0 and 1000'}
    
    # Validate embedding model
    valid_embedding_models = [
        'text-embedding-3-small', 'text-embedding-3-large',
        'text-embedding-ada-002', 'sentence-transformers'
    ]
    if config['embedding_model'] not in valid_embedding_models:
        return {'valid': False, 'message': f'Invalid embedding model. Must be one of: {", ".join(valid_embedding_models)}'}
    
    return {'valid': True, 'message': 'Knowledge base configuration is valid'}

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ''
    
    # Remove potential HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potential script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove potential SQL injection patterns
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bUNION\b.*\bSELECT\b)'
    ]
    
    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Limit length
    text = text[:10000]  # Prevent extremely long inputs
    
    return text.strip()
