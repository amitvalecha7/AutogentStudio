from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import ChatSession, ChatMessage, File, KnowledgeBase, db
from services.ai_service import AIService
from services.vector_service import VectorService
from services.file_service import FileService
import uuid

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Chat API endpoints
@api_bp.route('/chat/sessions', methods=['GET'])
@login_required
def get_chat_sessions():
    sessions = ChatSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return jsonify({
        'sessions': [{
            'id': session.id,
            'title': session.title,
            'model_provider': session.model_provider,
            'model_name': session.model_name,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        } for session in sessions]
    })

@api_bp.route('/chat/<session_id>/messages', methods=['GET'])
@login_required
def get_chat_messages(session_id):
    session = ChatSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()
    
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'messages': [{
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'metadata': message.metadata,
            'created_at': message.created_at.isoformat()
        } for message in messages]
    })

@api_bp.route('/chat/stream', methods=['POST'])
@login_required
def stream_chat():
    data = request.get_json()
    
    session_id = data.get('session_id')
    message = data.get('message')
    
    if not session_id or not message:
        return jsonify({'error': 'session_id and message are required'}), 400
    
    session = ChatSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        ai_service = AIService()
        
        # Get conversation history
        messages = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        conversation_history = []
        if session.system_prompt:
            conversation_history.append({
                'role': 'system',
                'content': session.system_prompt
            })
        
        for msg in messages:
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        conversation_history.append({
            'role': 'user',
            'content': message
        })
        
        # Stream response
        response_generator = ai_service.stream_chat_completion(
            messages=conversation_history,
            provider=session.model_provider,
            model=session.model_name,
            settings=session.settings
        )
        
        def generate():
            full_response = ""
            for chunk in response_generator:
                full_response += chunk.get('content', '')
                yield f"data: {jsonify(chunk).get_data(as_text=True)}\n\n"
            
            # Save messages to database
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role='user',
                content=message
            )
            
            ai_msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role='assistant',
                content=full_response
            )
            
            db.session.add(user_msg)
            db.session.add(ai_msg)
            db.session.commit()
        
        return generate(), 200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache'
        }
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Files API endpoints
@api_bp.route('/files', methods=['GET'])
@login_required
def get_files():
    files = File.query.filter_by(
        user_id=current_user.id
    ).order_by(File.created_at.desc()).all()
    
    return jsonify({
        'files': [{
            'id': file.id,
            'filename': file.original_filename,
            'file_type': file.file_type,
            'file_size': file.file_size,
            'is_processed': file.is_processed,
            'processing_status': file.processing_status,
            'created_at': file.created_at.isoformat()
        } for file in files]
    })

@api_bp.route('/files/<file_id>/process', methods=['POST'])
@login_required
def process_file(file_id):
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        file_service = FileService()
        result = file_service.process_file(file_id)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Knowledge Base API endpoints
@api_bp.route('/knowledge-base', methods=['GET'])
@login_required
def get_knowledge_bases():
    kbs = KnowledgeBase.query.filter_by(
        user_id=current_user.id
    ).order_by(KnowledgeBase.updated_at.desc()).all()
    
    return jsonify({
        'knowledge_bases': [{
            'id': kb.id,
            'name': kb.name,
            'description': kb.description,
            'file_count': kb.file_count,
            'total_chunks': kb.total_chunks,
            'created_at': kb.created_at.isoformat(),
            'updated_at': kb.updated_at.isoformat()
        } for kb in kbs]
    })

@api_bp.route('/knowledge-base/<kb_id>/query', methods=['POST'])
@login_required
def query_knowledge_base(kb_id):
    kb = KnowledgeBase.query.filter_by(
        id=kb_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        vector_service = VectorService()
        results = vector_service.search_knowledge_base(kb, query)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Settings API endpoints
@api_bp.route('/settings', methods=['GET'])
@login_required
def get_settings():
    return jsonify({
        'user_id': current_user.id,
        'preferences': current_user.preferences or {},
        'subscription_tier': current_user.subscription_tier
    })

@api_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    
    if 'preferences' in data:
        current_user.preferences = data['preferences']
    
    db.session.commit()
    
    return jsonify({'success': True})

# Model provider API endpoints
@api_bp.route('/models', methods=['GET'])
@login_required
def get_models():
    from models import AIModel
    
    models = AIModel.query.filter_by(is_active=True).all()
    
    models_by_provider = {}
    for model in models:
        if model.provider not in models_by_provider:
            models_by_provider[model.provider] = []
        models_by_provider[model.provider].append({
            'id': model.id,
            'name': model.name,
            'model_type': model.model_type,
            'capabilities': model.capabilities,
            'max_tokens': model.max_tokens,
            'cost_per_token_input': model.cost_per_token_input,
            'cost_per_token_output': model.cost_per_token_output
        })
    
    return jsonify({
        'models_by_provider': models_by_provider
    })

# Analytics API endpoints
@api_bp.route('/analytics/usage', methods=['GET'])
@login_required
def get_usage_analytics():
    # Get user's usage statistics
    from models import UsageMetrics
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Total messages
    total_messages = ChatMessage.query.join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).count()
    
    # Total tokens used
    total_tokens = db.session.query(func.sum(ChatMessage.tokens_used)).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).scalar() or 0
    
    # Total cost
    total_cost = db.session.query(func.sum(ChatMessage.cost)).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).scalar() or 0.0
    
    # Files uploaded
    files_uploaded = File.query.filter(
        File.user_id == current_user.id,
        File.created_at >= start_date
    ).count()
    
    return jsonify({
        'period': '30_days',
        'total_messages': total_messages,
        'total_tokens': int(total_tokens),
        'total_cost': float(total_cost),
        'files_uploaded': files_uploaded
    })

# Plugin development API endpoints
@api_bp.route('/plugins', methods=['GET'])
@login_required
def get_plugins():
    from models import Plugin
    
    plugins = Plugin.query.filter_by(is_featured=True).all()
    
    return jsonify({
        'plugins': [{
            'id': plugin.id,
            'name': plugin.name,
            'description': plugin.description,
            'category': plugin.category,
            'version': plugin.version,
            'author': plugin.author,
            'installation_type': plugin.installation_type,
            'download_count': plugin.download_count,
            'rating': plugin.rating
        } for plugin in plugins]
    })

# Mobile API endpoints
@api_bp.route('/mobile/sync', methods=['POST'])
@login_required
def mobile_sync():
    # Sync data for mobile app
    data = request.get_json()
    last_sync = data.get('last_sync')
    
    # Get updated data since last sync
    # This would include sessions, messages, files, etc.
    
    return jsonify({
        'success': True,
        'sync_timestamp': datetime.utcnow().isoformat(),
        'updated_sessions': [],
        'updated_messages': [],
        'updated_files': []
    })

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
