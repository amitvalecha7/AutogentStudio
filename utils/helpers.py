import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import mimetypes
from urllib.parse import urlparse

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"ask_{secrets.token_urlsafe(32)}"

def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Hash password with salt"""
    if not salt:
        salt = secrets.token_hex(32)
    
    # Use PBKDF2 with SHA256
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return {
        'hash': password_hash.hex(),
        'salt': salt
    }

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash"""
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return password_hash.hex() == stored_hash

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_type_icon(filename: str) -> str:
    """Get icon class for file type"""
    if not filename:
        return 'fas fa-file'
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    icon_map = {
        # Documents
        'pdf': 'fas fa-file-pdf text-danger',
        'doc': 'fas fa-file-word text-primary',
        'docx': 'fas fa-file-word text-primary',
        'xls': 'fas fa-file-excel text-success',
        'xlsx': 'fas fa-file-excel text-success',
        'ppt': 'fas fa-file-powerpoint text-warning',
        'pptx': 'fas fa-file-powerpoint text-warning',
        'txt': 'fas fa-file-alt',
        'rtf': 'fas fa-file-alt',
        
        # Images
        'jpg': 'fas fa-file-image text-info',
        'jpeg': 'fas fa-file-image text-info',
        'png': 'fas fa-file-image text-info',
        'gif': 'fas fa-file-image text-info',
        'svg': 'fas fa-file-image text-info',
        'bmp': 'fas fa-file-image text-info',
        'webp': 'fas fa-file-image text-info',
        
        # Audio
        'mp3': 'fas fa-file-audio text-purple',
        'wav': 'fas fa-file-audio text-purple',
        'ogg': 'fas fa-file-audio text-purple',
        'm4a': 'fas fa-file-audio text-purple',
        'flac': 'fas fa-file-audio text-purple',
        
        # Video
        'mp4': 'fas fa-file-video text-dark',
        'avi': 'fas fa-file-video text-dark',
        'mkv': 'fas fa-file-video text-dark',
        'mov': 'fas fa-file-video text-dark',
        'webm': 'fas fa-file-video text-dark',
        
        # Archives
        'zip': 'fas fa-file-archive text-secondary',
        'rar': 'fas fa-file-archive text-secondary',
        '7z': 'fas fa-file-archive text-secondary',
        'tar': 'fas fa-file-archive text-secondary',
        'gz': 'fas fa-file-archive text-secondary',
        
        # Code
        'py': 'fas fa-file-code text-success',
        'js': 'fas fa-file-code text-warning',
        'html': 'fas fa-file-code text-danger',
        'css': 'fas fa-file-code text-primary',
        'json': 'fas fa-file-code text-info',
        'xml': 'fas fa-file-code text-secondary',
        'sql': 'fas fa-file-code text-info',
        'php': 'fas fa-file-code text-purple',
        'java': 'fas fa-file-code text-danger',
        'cpp': 'fas fa-file-code text-primary',
        'c': 'fas fa-file-code text-primary',
        'cs': 'fas fa-file-code text-success',
        'go': 'fas fa-file-code text-info',
        'rust': 'fas fa-file-code text-warning',
        'rb': 'fas fa-file-code text-danger',
        'swift': 'fas fa-file-code text-warning',
        'kt': 'fas fa-file-code text-purple',
        'ts': 'fas fa-file-code text-primary',
    }
    
    return icon_map.get(file_ext, 'fas fa-file')

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object"""
    if not dt:
        return ""
    
    return dt.strftime(format_str)

def time_ago(dt: datetime) -> str:
    """Get human readable time ago string"""
    if not dt:
        return ""
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""

def is_safe_url(url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
    """Check if URL is safe for redirects"""
    try:
        parsed = urlparse(url)
        
        # Must be HTTP or HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # If allowed hosts specified, check against them
        if allowed_hosts and parsed.netloc not in allowed_hosts:
            return False
        
        return True
    except:
        return False

def generate_filename(original_filename: str, prefix: str = "", suffix: str = "") -> str:
    """Generate safe filename with optional prefix and suffix"""
    if not original_filename:
        return f"{prefix}file{suffix}"
    
    # Remove dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    filename = ''.join(c for c in original_filename if c in safe_chars)
    
    # Add prefix and suffix
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        return f"{prefix}{name}{suffix}.{ext}"
    else:
        return f"{prefix}{filename}{suffix}"

def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """Calculate hash of file contents"""
    hash_algo = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_algo.update(chunk)
        return hash_algo.hexdigest()
    except Exception:
        return ""

def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Parse user agent string"""
    result = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop'
    }
    
    if not user_agent:
        return result
    
    ua = user_agent.lower()
    
    # Detect browser
    if 'chrome' in ua and 'safari' in ua:
        result['browser'] = 'Chrome'
    elif 'firefox' in ua:
        result['browser'] = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        result['browser'] = 'Safari'
    elif 'edge' in ua:
        result['browser'] = 'Edge'
    elif 'opera' in ua:
        result['browser'] = 'Opera'
    
    # Detect OS
    if 'windows' in ua:
        result['os'] = 'Windows'
    elif 'mac os' in ua or 'macos' in ua:
        result['os'] = 'macOS'
    elif 'linux' in ua:
        result['os'] = 'Linux'
    elif 'android' in ua:
        result['os'] = 'Android'
        result['device'] = 'Mobile'
    elif 'ios' in ua or 'iphone' in ua or 'ipad' in ua:
        result['os'] = 'iOS'
        result['device'] = 'Mobile' if 'iphone' in ua else 'Tablet'
    
    # Detect mobile
    mobile_indicators = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    if any(indicator in ua for indicator in mobile_indicators):
        result['device'] = 'Mobile'
    
    return result

def clean_html(html: str) -> str:
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    import re
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug

def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

def deep_get(dictionary: Dict[str, Any], keys: str, default: Any = None) -> Any:
    """Get nested dictionary value using dot notation"""
    keys_list = keys.split('.')
    for key in keys_list:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary

def format_currency(amount: float, currency: str = "USD", symbol: str = "$") -> str:
    """Format currency amount"""
    return f"{symbol}{amount:,.2f} {currency}"

def validate_json(json_string: str) -> Dict[str, Any]:
    """Validate and parse JSON string"""
    try:
        data = json.loads(json_string)
        return {'valid': True, 'data': data, 'error': None}
    except json.JSONDecodeError as e:
        return {'valid': False, 'data': None, 'error': str(e)}
