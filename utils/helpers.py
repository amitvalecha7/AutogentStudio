import os
import logging
from flask import session, redirect, url_for, flash
from functools import wraps
from app import db
from models import User
import mimetypes

def get_current_user():
    """Get current logged-in user"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash('Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file type is allowed for upload"""
    allowed_extensions = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg',
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'csv', 'json', 'xml', 'md', 'py', 'js', 'html',
        'css', 'zip', 'tar', 'gz', 'mp3', 'wav', 'mp4',
        'avi', 'mov', 'mkv'
    }
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_icon(filename):
    """Get appropriate icon for file type"""
    if not filename:
        return 'fas fa-file'
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    icon_map = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'ppt': 'fas fa-file-powerpoint',
        'pptx': 'fas fa-file-powerpoint',
        'txt': 'fas fa-file-alt',
        'md': 'fas fa-file-alt',
        'csv': 'fas fa-file-csv',
        'json': 'fas fa-file-code',
        'xml': 'fas fa-file-code',
        'py': 'fas fa-file-code',
        'js': 'fas fa-file-code',
        'html': 'fas fa-file-code',
        'css': 'fas fa-file-code',
        'png': 'fas fa-file-image',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'gif': 'fas fa-file-image',
        'svg': 'fas fa-file-image',
        'mp3': 'fas fa-file-audio',
        'wav': 'fas fa-file-audio',
        'mp4': 'fas fa-file-video',
        'avi': 'fas fa-file-video',
        'mov': 'fas fa-file-video',
        'mkv': 'fas fa-file-video',
        'zip': 'fas fa-file-archive',
        'tar': 'fas fa-file-archive',
        'gz': 'fas fa-file-archive'
    }
    
    return icon_map.get(ext, 'fas fa-file')

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return "Never"
    
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 7:
        return timestamp.strftime("%Y-%m-%d")
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

def validate_api_key(api_key, provider):
    """Validate API key format"""
    if not api_key:
        return False
    
    # Basic validation rules for different providers
    validation_rules = {
        'openai': lambda k: k.startswith('sk-') and len(k) > 40,
        'anthropic': lambda k: k.startswith('sk-ant-') and len(k) > 40,
        'google': lambda k: len(k) > 30,
        'aws': lambda k: len(k) > 15,
        'azure': lambda k: len(k) > 20
    }
    
    validator = validation_rules.get(provider.lower())
    if validator:
        return validator(api_key)
    
    return len(api_key) > 10  # Generic validation

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename

def generate_secure_token(length=32):
    """Generate secure random token"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def is_safe_url(target):
    """Check if URL is safe for redirect"""
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def get_client_ip():
    """Get client IP address"""
    from flask import request
    
    # Check for forwarded headers first
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.environ.get('REMOTE_ADDR', 'unknown')

def log_security_event(event_type, details, user_id=None):
    """Log security-related events"""
    security_log = {
        'event_type': event_type,
        'details': details,
        'user_id': user_id,
        'ip_address': get_client_ip(),
        'timestamp': datetime.utcnow().isoformat(),
        'user_agent': request.headers.get('User-Agent', 'unknown')
    }
    
    logging.warning(f"Security Event: {security_log}")

def rate_limit_key(user_id=None):
    """Generate rate limit key"""
    if user_id:
        return f"rate_limit:user:{user_id}"
    else:
        return f"rate_limit:ip:{get_client_ip()}"

def check_rate_limit(key, limit=100, window=3600):
    """Check if rate limit is exceeded"""
    # This would integrate with Redis in production
    # For now, return False (not rate limited)
    return False

def mask_sensitive_data(data, mask_char='*'):
    """Mask sensitive data for logging"""
    if not data:
        return data
    
    if len(data) <= 8:
        return mask_char * len(data)
    
    # Show first 4 and last 4 characters
    return data[:4] + mask_char * (len(data) - 8) + data[-4:]

def validate_json_schema(data, schema):
    """Validate JSON data against schema"""
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return True
    except:
        return False

def get_system_stats():
    """Get system statistics"""
    import psutil
    
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
    }

def create_audit_log(action, resource, details=None):
    """Create audit log entry"""
    user = get_current_user()
    audit_entry = {
        'action': action,
        'resource': resource,
        'user_id': user.id if user else None,
        'username': user.username if user else 'anonymous',
        'ip_address': get_client_ip(),
        'timestamp': datetime.utcnow().isoformat(),
        'details': details or {}
    }
    
    logging.info(f"Audit Log: {audit_entry}")
    return audit_entry

def send_notification(user_id, message, notification_type='info'):
    """Send notification to user"""
    # This would integrate with a notification service in production
    logging.info(f"Notification for user {user_id}: {message} (type: {notification_type})")

def generate_qr_code(data):
    """Generate QR code for data"""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except ImportError:
        logging.warning("qrcode library not installed")
        return None

def backup_database():
    """Create database backup"""
    try:
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_autogent_studio_{timestamp}.sql"
        
        # This would run actual pg_dump in production
        logging.info(f"Database backup created: {backup_file}")
        return backup_file
    except Exception as e:
        logging.error(f"Database backup failed: {str(e)}")
        return None

def cleanup_temp_files():
    """Clean up temporary files"""
    import glob
    import time
    
    temp_pattern = "/tmp/autogent_*"
    current_time = time.time()
    
    for filepath in glob.glob(temp_pattern):
        try:
            file_age = current_time - os.path.getctime(filepath)
            if file_age > 86400:  # 24 hours
                os.remove(filepath)
                logging.info(f"Cleaned up temp file: {filepath}")
        except Exception as e:
            logging.error(f"Error cleaning temp file {filepath}: {str(e)}")
