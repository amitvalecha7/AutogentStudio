from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('auth/signin.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/signin.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('auth/signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('auth/signup.html')
        
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        session['user_id'] = user.id
        flash('Account created successfully!', 'success')
        return redirect(url_for('chat.index'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real application, send email with reset link
            flash('Password reset instructions sent to your email', 'info')
        else:
            flash('Email not found', 'error')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/me')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/me/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '')
        current_user.last_name = request.form.get('last_name', '')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
    
    return render_template('auth/profile_settings.html', user=current_user)
