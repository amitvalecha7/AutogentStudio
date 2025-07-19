from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from models import User, Conversation, Message
from services.openai_service import OpenAIService
from services.anthropic_service import AnthropicService
import logging
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('chat/chat.html', 
                         user=user, 
                         conversations=conversations)

@chat_bp.route('/chat/<conversation_id>')
def chat_conversation(conversation_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    
    if not conversation:
        return redirect(url_for('chat.chat'))
    
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()
    
    return render_template('chat/chat.html', 
                         user=user, 
                         conversations=conversations,
                         current_conversation=conversation,
                         messages=messages)

@chat_bp.route('/chat/settings')
def chat_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('chat/settings.html', user=user)

@chat_bp.route('/api/chat/conversations', methods=['GET', 'POST'])
def conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            title = data.get('title', 'New Conversation')
            
            conversation = Conversation(
                user_id=user.id,
                title=title,
                system_prompt=data.get('system_prompt', 'You are a helpful AI assistant for Autogent Studio.'),
                model_provider=data.get('model_provider', 'openai'),
                model_name=data.get('model_name', 'gpt-4o')
            )
            
            db.session.add(conversation)
            db.session.commit()
            
            return jsonify({'success': True, 'conversation': conversation.to_dict()})
            
        except Exception as e:
            logging.error(f"Error creating conversation: {str(e)}")
            return jsonify({'error': 'Failed to create conversation'}), 500
    
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    return jsonify({'conversations': [conv.to_dict() for conv in conversations]})

@chat_bp.route('/api/chat/conversations/<conversation_id>/messages', methods=['GET', 'POST'])
def conversation_messages(conversation_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'error': 'Message content required'}), 400
            
            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role='user',
                content=content
            )
            db.session.add(user_message)
            db.session.commit()
            
            # Get AI response
            try:
                if conversation.model_provider == 'openai':
                    ai_service = OpenAIService()
                elif conversation.model_provider == 'anthropic':
                    ai_service = AnthropicService()
                else:
                    return jsonify({'error': 'Unsupported model provider'}), 400
                
                # Get conversation history
                messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()
                message_history = []
                
                if conversation.system_prompt:
                    message_history.append({'role': 'system', 'content': conversation.system_prompt})
                
                for msg in messages:
                    message_history.append({'role': msg.role, 'content': msg.content})
                
                # Generate AI response
                ai_response = ai_service.generate_response(
                    messages=message_history,
                    model=conversation.model_name,
                    temperature=conversation.temperature,
                    max_tokens=conversation.max_tokens
                )
                
                # Create assistant message
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role='assistant',
                    content=ai_response
                )
                db.session.add(assistant_message)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'user_message': user_message.to_dict(),
                    'assistant_message': assistant_message.to_dict()
                })
                
            except Exception as e:
                logging.error(f"Error generating AI response: {str(e)}")
                return jsonify({'error': 'Failed to generate AI response'}), 500
            
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return jsonify({'error': 'Failed to process message'}), 500
    
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()
    return jsonify({'messages': [msg.to_dict() for msg in messages]})

# WebSocket events
@socketio.on('join_conversation')
def on_join_conversation(data):
    conversation_id = data['conversation_id']
    join_room(conversation_id)
    emit('status', {'message': f'Joined conversation {conversation_id}'})

@socketio.on('leave_conversation')
def on_leave_conversation(data):
    conversation_id = data['conversation_id']
    leave_room(conversation_id)
    emit('status', {'message': f'Left conversation {conversation_id}'})

@socketio.on('send_message')
def handle_message(data):
    if 'user_id' not in session:
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        conversation_id = data['conversation_id']
        content = data['content']
        
        user = User.query.get(session['user_id'])
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
        
        if not conversation:
            emit('error', {'message': 'Conversation not found'})
            return
        
        # Create and save user message
        user_message = Message(
            conversation_id=conversation.id,
            role='user',
            content=content
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Emit user message to room
        emit('new_message', user_message.to_dict(), room=conversation_id)
        
        # Generate AI response (simplified for real-time)
        emit('typing', {'typing': True}, room=conversation_id)
        
        # Here you would integrate with your AI service
        # For now, we'll emit a simple response
        assistant_message = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=f"I received your message: {content}"
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        emit('typing', {'typing': False}, room=conversation_id)
        emit('new_message', assistant_message.to_dict(), room=conversation_id)
        
    except Exception as e:
        logging.error(f"WebSocket message error: {str(e)}")
        emit('error', {'message': 'Failed to process message'})
