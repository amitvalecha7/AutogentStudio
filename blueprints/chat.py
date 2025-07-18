from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room, rooms
from app import socketio, db
from models import Conversation, Message, User
from services.openai_service import OpenAIService
from services.anthropic_service import AnthropicService
from blueprints.auth import login_required, get_current_user
import logging
import json
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_index():
    user = get_current_user()
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    return render_template('chat/chat.html', conversations=conversations)

@chat_bp.route('/<int:conversation_id>')
@login_required
def chat_conversation(conversation_id):
    user = get_current_user()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first_or_404()
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('chat/chat.html', 
                         conversation=conversation, 
                         messages=messages, 
                         conversations=conversations)

@chat_bp.route('/new', methods=['POST'])
@login_required
def new_conversation():
    user = get_current_user()
    title = request.form.get('title', 'New Conversation')
    model_provider = request.form.get('model_provider', 'openai')
    model_name = request.form.get('model_name', 'gpt-4o')
    
    conversation = Conversation(
        user_id=user.id,
        title=title,
        model_provider=model_provider,
        model_name=model_name
    )
    
    try:
        db.session.add(conversation)
        db.session.commit()
        logging.info(f"New conversation created: {conversation.id}")
        return redirect(url_for('chat.chat_conversation', conversation_id=conversation.id))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating conversation: {str(e)}")
        return redirect(url_for('chat.chat_index'))

@chat_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    user = get_current_user()
    data = request.get_json()
    
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    
    if not conversation_id or not content:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=content
    )
    
    try:
        db.session.add(user_message)
        db.session.commit()
        
        # Get conversation history
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
        message_history = []
        
        for msg in messages:
            message_history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Generate AI response
        if conversation.model_provider == 'openai':
            ai_service = OpenAIService()
            response = ai_service.generate_response(message_history, conversation.model_name)
        elif conversation.model_provider == 'anthropic':
            ai_service = AnthropicService()
            response = ai_service.generate_response(message_history, conversation.model_name)
        else:
            response = "AI service not available"
        
        # Save AI response
        ai_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=response
        )
        
        db.session.add(ai_message)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update conversation title if it's the first exchange
        if len(message_history) <= 2 and conversation.title == 'New Conversation':
            title_prompt = f"Generate a short, descriptive title (max 50 chars) for this conversation: {content[:100]}"
            if conversation.model_provider == 'openai':
                title = ai_service.generate_title(title_prompt)
            else:
                title = content[:50] + "..."
            
            conversation.title = title
            db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.isoformat()
            },
            'conversation_title': conversation.title
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending message: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

@chat_bp.route('/settings')
@login_required
def chat_settings():
    user = get_current_user()
    return render_template('chat/settings.html', user=user)

@chat_bp.route('/delete/<int:conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    user = get_current_user()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    
    if conversation:
        try:
            db.session.delete(conversation)
            db.session.commit()
            logging.info(f"Conversation {conversation_id} deleted")
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting conversation: {str(e)}")
            return jsonify({'error': 'Failed to delete conversation'}), 500
    
    return jsonify({'error': 'Conversation not found'}), 404

# WebSocket events for real-time chat
@socketio.on('join_conversation')
def on_join_conversation(data):
    if 'user_id' not in session:
        return
    
    conversation_id = data.get('conversation_id')
    if conversation_id:
        join_room(f"conversation_{conversation_id}")
        emit('status', {'msg': f"Joined conversation {conversation_id}"})

@socketio.on('leave_conversation')
def on_leave_conversation(data):
    conversation_id = data.get('conversation_id')
    if conversation_id:
        leave_room(f"conversation_{conversation_id}")
        emit('status', {'msg': f"Left conversation {conversation_id}"})

@socketio.on('typing')
def on_typing(data):
    if 'user_id' not in session:
        return
    
    conversation_id = data.get('conversation_id')
    username = session.get('username', 'Anonymous')
    
    if conversation_id:
        emit('user_typing', {
            'username': username,
            'typing': data.get('typing', False)
        }, room=f"conversation_{conversation_id}", include_self=False)

@socketio.on('connect')
def on_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")
        emit('status', {'msg': 'Connected to Autogent Studio'})

@socketio.on('disconnect')
def on_disconnect():
    if 'user_id' in session:
        leave_room(f"user_{session['user_id']}")
