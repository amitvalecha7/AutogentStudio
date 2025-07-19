from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('auth/signin.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = str(user.id)
                session['username'] = user.username
                session['is_admin'] = user.is_admin
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
    
    return render_template('auth/signin.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
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
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return render_template('auth/signup.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
                return render_template('auth/signup.html')
            
            # Create new user
            user = User(
                username=username,
                email=email
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('auth.signin'))
            
        except Exception as e:
            logging.error(f"Signup error: {str(e)}")
            flash('An error occurred during signup', 'error')
            db.session.rollback()
    
    return render_template('auth/signup.html')

@auth_bp.route('/signout')
def signout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.signin'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            })
    
    return jsonify({'authenticated': False})
