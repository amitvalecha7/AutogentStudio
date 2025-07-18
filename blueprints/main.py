from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import Conversation, Assistant, Plugin, User
from app import db
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main homepage with chat interface"""
    if current_user.is_authenticated:
        # Get recent conversations
        recent_conversations = Conversation.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(Conversation.updated_at.desc()).limit(10).all()
        
        # Get featured assistants
        featured_assistants = Assistant.query.filter_by(
            is_public=True
        ).order_by(Assistant.usage_count.desc()).limit(8).all()
        
        return render_template('index.html',
                             conversations=recent_conversations,
                             assistants=featured_assistants)
    else:
        return render_template('index.html', show_signin=True)

@main_bp.route('/image')
def image_generation():
    """AI Painting/Image Generation page"""
    return render_template('image_generation.html')

@main_bp.route('/me')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@main_bp.route('/me/settings')
@login_required
def profile_settings():
    """User profile settings"""
    return render_template('profile_settings.html', user=current_user)

@main_bp.route('/workspace/<int:workspace_id>')
@login_required
def workspace(workspace_id):
    """Collaborative workspace"""
    from models import Workspace
    workspace = Workspace.query.get_or_404(workspace_id)
    
    # Check permissions
    if workspace.owner_id != current_user.id:
        # Check if user is member of workspace
        pass  # TODO: Implement workspace membership
    
    return render_template('workspace.html', workspace=workspace)

@main_bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Autogent Studio',
        'version': '1.0.0'
    })

@main_bp.route('/api/user/stats')
@login_required
def user_stats():
    """Get user statistics"""
    try:
        conversations_count = Conversation.query.filter_by(
            user_id=current_user.id
        ).count()
        
        messages_count = db.session.query(
            db.func.count(Message.id)
        ).join(Conversation).filter(
            Conversation.user_id == current_user.id
        ).scalar()
        
        files_count = File.query.filter_by(
            user_id=current_user.id
        ).count()
        
        return jsonify({
            'conversations': conversations_count,
            'messages': messages_count,
            'files': files_count
        })
    except Exception as e:
        logging.error(f"Error getting user stats: {str(e)}")
        return jsonify({'error': 'Failed to get user statistics'}), 500

@main_bp.route('/api/search')
@login_required
def global_search():
    """Global search across conversations, files, and knowledge bases"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    try:
        results = []
        
        # Search conversations
        conversations = Conversation.query.filter(
            Conversation.user_id == current_user.id,
            Conversation.title.ilike(f'%{query}%')
        ).limit(5).all()
        
        for conv in conversations:
            results.append({
                'type': 'conversation',
                'id': conv.id,
                'title': conv.title,
                'url': f'/chat/{conv.id}'
            })
        
        # Search files
        files = File.query.filter(
            File.user_id == current_user.id,
            File.original_filename.ilike(f'%{query}%')
        ).limit(5).all()
        
        for file in files:
            results.append({
                'type': 'file',
                'id': file.id,
                'title': file.original_filename,
                'url': f'/files/{file.id}'
            })
        
        return jsonify({'results': results})
    except Exception as e:
        logging.error(f"Error in global search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@main_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
