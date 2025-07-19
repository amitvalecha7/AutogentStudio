from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from models import ChatSession, ChatMessage, db
from services.ai_service import AIService
import uuid
import json

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
@login_required
def index():
    # Get user's chat sessions
    sessions = ChatSession.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return render_template('chat/index.html', sessions=sessions)

@chat_bp.route('/<session_id>')
@login_required
def session_view(session_id):
    chat_session = ChatSession.query.filter_by(
        id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return render_template('chat/session.html', 
                         session=chat_session, 
                         messages=messages)

@chat_bp.route('/new', methods=['POST'])
@login_required
def new_session():
    data = request.get_json()
    
    session_id = str(uuid.uuid4())
    new_session = ChatSession(
        id=session_id,
        user_id=current_user.id,
        title=data.get('title', 'New Chat'),
        model_provider=data.get('model_provider', 'openai'),
        model_name=data.get('model_name', 'gpt-4o'),
        system_prompt=data.get('system_prompt', ''),
        settings=data.get('settings', {})
    )
    
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'redirect_url': f'/chat/{session_id}'
    })

@chat_bp.route('/<session_id>/messages', methods=['POST'])
@login_required
def send_message(session_id):
    chat_session = ChatSession.query.filter_by(
        id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Save user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role='user',
        content=user_message,
        metadata=data.get('metadata', {})
    )
    db.session.add(user_msg)
    
    try:
        # Get AI response
        ai_service = AIService()
        
        # Get conversation history
        messages = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        conversation_history = []
        if chat_session.system_prompt:
            conversation_history.append({
                'role': 'system',
                'content': chat_session.system_prompt
            })
        
        for msg in messages:
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Add current user message
        conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Get AI response
        response = ai_service.chat_completion(
            messages=conversation_history,
            provider=chat_session.model_provider,
            model=chat_session.model_name,
            settings=chat_session.settings
        )
        
        # Save AI response
        ai_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role='assistant',
            content=response['content'],
            metadata={
                'model': response.get('model'),
                'tokens_used': response.get('tokens_used', 0),
                'cost': response.get('cost', 0.0)
            },
            tokens_used=response.get('tokens_used', 0),
            cost=response.get('cost', 0.0)
        )
        db.session.add(ai_msg)
        
        # Update session
        chat_session.updated_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': {
                'id': ai_msg.id,
                'role': ai_msg.role,
                'content': ai_msg.content,
                'created_at': ai_msg.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/<session_id>/settings', methods=['GET', 'POST'])
@login_required
def session_settings(session_id):
    chat_session = ChatSession.query.filter_by(
        id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        data = request.get_json()
        
        chat_session.title = data.get('title', chat_session.title)
        chat_session.model_provider = data.get('model_provider', chat_session.model_provider)
        chat_session.model_name = data.get('model_name', chat_session.model_name)
        chat_session.system_prompt = data.get('system_prompt', chat_session.system_prompt)
        chat_session.settings = data.get('settings', chat_session.settings)
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    return render_template('chat/settings.html', session=chat_session)

@chat_bp.route('/<session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    chat_session = ChatSession.query.filter_by(
        id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    chat_session.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})

@chat_bp.route('/history')
@login_required
def chat_history():
    sessions = ChatSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return render_template('chat/history.html', sessions=sessions)

# WebSocket handlers for real-time chat
from app import socketio

@socketio.on('join_chat')
def on_join_chat(data):
    session_id = data['session_id']
    
    # Verify user has access to this session
    chat_session = ChatSession.query.filter_by(
        id=session_id,
        user_id=session.get('user_id')
    ).first()
    
    if chat_session:
        join_room(session_id)
        emit('joined_chat', {'session_id': session_id})

@socketio.on('leave_chat')
def on_leave_chat(data):
    session_id = data['session_id']
    leave_room(session_id)
    emit('left_chat', {'session_id': session_id})

@socketio.on('typing')
def on_typing(data):
    session_id = data['session_id']
    emit('user_typing', {
        'user_id': session.get('user_id'),
        'typing': data.get('typing', False)
    }, room=session_id, include_self=False)
