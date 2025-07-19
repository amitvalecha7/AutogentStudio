from flask import render_template, session, redirect, url_for, request, flash
from app import app, db
from models import User, ChatSession, File, KnowledgeBase
from utils.ai_providers import ai_providers
import uuid

@app.route('/')
def index():
    """Main homepage - redirect to chat if authenticated, show landing page otherwise"""
    if 'user_id' in session:
        return redirect(url_for('chat.index'))
    return render_template('index.html')

@app.route('/image')
def image_generation():
    """AI Painting interface"""
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    return render_template('image/index.html')

@app.route('/signin')
def signin_redirect():
    """Redirect to auth signin"""
    return redirect(url_for('auth.signin'))

@app.route('/signup')
def signup_redirect():
    """Redirect to auth signup"""
    return redirect(url_for('auth.signup'))

@app.route('/me')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.signin'))
    
    return render_template('profile/index.html', user=user)

@app.route('/me/settings')
def profile_settings():
    """User profile settings"""
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    return render_template('profile/settings.html')

@app.errorhandler(404)
def page_not_found(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.context_processor
def inject_user():
    """Inject current user into all templates"""
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return {'current_user': user}

@app.context_processor
def inject_app_info():
    """Inject app information into templates"""
    return {
        'app_name': 'Autogent Studio',
        'app_version': '1.0.0',
        'app_description': 'The ultimate enterprise-grade AI development platform'
    }

