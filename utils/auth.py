from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify
from models import User
import logging

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.signin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or current_user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin privileges required'}), 403
            flash('Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def researcher_required(f):
    """Decorator to require researcher privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or current_user.role not in ['admin', 'researcher']:
            if request.is_json:
                return jsonify({'error': 'Researcher privileges required'}), 403
            flash('Researcher privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get the current logged-in user"""
    user_id = session.get('user_id')
    if user_id:
        try:
            return User.query.get(user_id)
        except Exception as e:
            logging.error(f"Error getting current user: {e}")
            session.pop('user_id', None)
    return None

def login_user(user):
    """Log in a user"""
    session['user_id'] = user.id
    session['username'] = user.username
    session['user_role'] = user.role
    session.permanent = True
    logging.info(f"User {user.username} logged in")

def logout_user():
    """Log out the current user"""
    username = session.get('username', 'Unknown')
    session.clear()
    logging.info(f"User {username} logged out")

def check_user_permissions(user, required_permissions):
    """Check if user has required permissions"""
    if not user:
        return False
    
    if user.role == 'admin':
        return True
    
    user_permissions = get_user_permissions(user)
    return all(perm in user_permissions for perm in required_permissions)

def get_user_permissions(user):
    """Get list of permissions for a user based on role"""
    if not user:
        return []
    
    base_permissions = [
        'chat.create', 'chat.read', 'chat.update', 'chat.delete',
        'files.upload', 'files.read', 'files.delete',
        'knowledge_base.create', 'knowledge_base.read', 'knowledge_base.update', 'knowledge_base.delete',
        'settings.read', 'settings.update'
    ]
    
    researcher_permissions = base_permissions + [
        'quantum.access', 'federated.access', 'neuromorphic.access',
        'safety.read', 'research.create', 'research.read', 'research.update',
        'analytics.read', 'workspace.create', 'workspace.manage'
    ]
    
    admin_permissions = researcher_permissions + [
        'admin.access', 'users.manage', 'system.configure',
        'safety.manage', 'security.manage', 'blockchain.manage',
        'analytics.full_access', 'research.admin', 'self_improving.admin'
    ]
    
    if user.role == 'admin':
        return admin_permissions
    elif user.role == 'researcher':
        return researcher_permissions
    else:
        return base_permissions

def validate_api_key(api_key_header):
    """Validate API key for API access"""
    if not api_key_header:
        return None
    
    try:
        # Extract user from API key
        # In a real implementation, you'd look up the API key in the database
        if api_key_header.startswith('ak-'):
            # For demo purposes, extract user_id from a pattern
            # In production, store API keys in database with user association
            return None
    except Exception as e:
        logging.error(f"API key validation error: {e}")
    
    return None

def rate_limit_check(user_id, endpoint, limit_per_minute=60):
    """Check rate limiting for user endpoints"""
    try:
        import time
        from collections import defaultdict
        
        # Simple in-memory rate limiting (use Redis in production)
        if not hasattr(rate_limit_check, 'requests'):
            rate_limit_check.requests = defaultdict(list)
        
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        rate_limit_check.requests[f"{user_id}:{endpoint}"] = [
            req_time for req_time in rate_limit_check.requests[f"{user_id}:{endpoint}"]
            if req_time > minute_ago
        ]
        
        # Check current count
        current_requests = len(rate_limit_check.requests[f"{user_id}:{endpoint}"])
        
        if current_requests >= limit_per_minute:
            return False
        
        # Add current request
        rate_limit_check.requests[f"{user_id}:{endpoint}"].append(now)
        return True
        
    except Exception as e:
        logging.error(f"Rate limit check error: {e}")
        return True  # Allow request if rate limiting fails

def log_user_activity(user_id, action, details=None):
    """Log user activity for auditing"""
    try:
        # In production, log to a proper audit system
        logging.info(f"User {user_id} performed action: {action} - {details}")
    except Exception as e:
        logging.error(f"Activity logging error: {e}")

def generate_session_token():
    """Generate a secure session token"""
    from utils.encryption import generate_secure_token
    return generate_secure_token(64)

def validate_session_token(token):
    """Validate a session token"""
    # In production, implement proper session token validation
    return len(token) == 64 if token else False
