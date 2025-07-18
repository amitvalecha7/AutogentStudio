from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from app import db
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/signin.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            logging.info(f"User {user.email} signed in successfully")
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
            logging.warning(f"Failed sign in attempt for {email}")
    
    return render_template('auth/signin.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('auth/signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/signup.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('auth/signup.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            session['username'] = user.username
            
            flash('Account created successfully!', 'success')
            logging.info(f"New user registered: {user.email}")
            return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'error')
            logging.error(f"Registration error: {str(e)}")
    
    return render_template('auth/signup.html')

@auth_bp.route('/signout')
def signout():
    user_id = session.get('user_id')
    session.clear()
    flash('You have been signed out successfully', 'info')
    logging.info(f"User {user_id} signed out")
    return redirect(url_for('auth.signin'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real application, you would send a password reset email
            flash('Password reset instructions have been sent to your email', 'info')
            logging.info(f"Password reset requested for {email}")
        else:
            flash('Email not found', 'error')
    
    return render_template('auth/forgot_password.html')

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.signin'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None
