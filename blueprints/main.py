from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import current_user
from models import ChatSession, Assistant, Plugin
from services.ai_providers import get_available_models
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Autogent Studio Homepage - Main chat interface"""
    if not current_user.is_authenticated:
        # Show landing page for logged out users
        return render_template('index.html', page_type='landing')
    
    # Get user's recent chat sessions
    recent_sessions = ChatSession.query.filter_by(user_id=current_user.id)\
        .order_by(ChatSession.updated_at.desc()).limit(5).all()
    
    # Get featured assistants for recommendations
    featured_assistants = Assistant.query.filter_by(is_public=True)\
        .order_by(Assistant.usage_count.desc()).limit(4).all()
    
    # Get available models
    available_models = get_available_models()
    
    context = {
        'page_type': 'chat',
        'recent_sessions': recent_sessions,
        'featured_assistants': featured_assistants,
        'available_models': available_models,
        'user': current_user
    }
    
    return render_template('index.html', **context)

@main_bp.route('/about')
def about():
    """About Autogent Studio"""
    return render_template('about.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@main_bp.route('/docs')
def documentation():
    """Documentation hub"""
    return render_template('docs/index.html')

@main_bp.route('/enterprise')
def enterprise():
    """Enterprise features overview"""
    return render_template('enterprise.html')
