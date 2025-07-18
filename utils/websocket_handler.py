import logging
import json
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, rooms
from flask_login import current_user
from app import socketio, db
from models import Chat, Message, User
from services.ai_providers import AIProviders

# Global dictionary to track active connections
active_connections = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
            active_connections[user_id] = {
                'connected_at': datetime.utcnow().isoformat(),
                'rooms': []
            }
            
            # Join user's personal room
            join_room(f'user_{user_id}')
            active_connections[user_id]['rooms'].append(f'user_{user_id}')
            
            logging.info(f"User {user_id} connected via WebSocket")
            
            emit('connection_status', {
                'status': 'connected',
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            emit('connection_status', {
                'status': 'unauthorized',
                'message': 'Please log in to use Autogent Studio'
            })
    
    except Exception as e:
        logging.error(f"Error handling WebSocket connection: {str(e)}")
        emit('error', {'message': 'Connection error'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
            
            # Leave all rooms
            user_rooms = active_connections.get(user_id, {}).get('rooms', [])
            for room in user_rooms:
                leave_room(room)
            
            # Remove from active connections
            if user_id in active_connections:
                del active_connections[user_id]
            
            logging.info(f"User {user_id} disconnected from WebSocket")
    
    except Exception as e:
        logging.error(f"Error handling WebSocket disconnection: {str(e)}")

@socketio.on('join_chat')
def handle_join_chat(data):
    """Handle joining a chat room"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        chat_id = data.get('chat_id')
        if not chat_id:
            emit('error', {'message': 'Chat ID required'})
            return
        
        # Verify user has access to chat
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            emit('error', {'message': 'Chat not found or access denied'})
            return
        
        # Join chat room
        room_name = f'chat_{chat_id}'
        join_room(room_name)
        
        # Update active connections
        user_id = current_user.id
        if user_id in active_connections:
            active_connections[user_id]['rooms'].append(room_name)
        
        emit('chat_joined', {
            'chat_id': chat_id,
            'chat_title': chat.title,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logging.info(f"User {user_id} joined chat {chat_id}")
    
    except Exception as e:
        logging.error(f"Error joining chat: {str(e)}")
        emit('error', {'message': 'Failed to join chat'})

@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Handle leaving a chat room"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        chat_id = data.get('chat_id')
        if not chat_id:
            emit('error', {'message': 'Chat ID required'})
            return
        
        # Leave chat room
        room_name = f'chat_{chat_id}'
        leave_room(room_name)
        
        # Update active connections
        user_id = current_user.id
        if user_id in active_connections and room_name in active_connections[user_id]['rooms']:
            active_connections[user_id]['rooms'].remove(room_name)
        
        emit('chat_left', {
            'chat_id': chat_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logging.info(f"User {user_id} left chat {chat_id}")
    
    except Exception as e:
        logging.error(f"Error leaving chat: {str(e)}")
        emit('error', {'message': 'Failed to leave chat'})

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        chat_id = data.get('chat_id')
        message_content = data.get('message')
        model = data.get('model', 'gpt-4o')
        
        if not chat_id or not message_content:
            emit('error', {'message': 'Chat ID and message required'})
            return
        
        # Verify user has access to chat
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            emit('error', {'message': 'Chat not found or access denied'})
            return
        
        # Save user message
        user_message = Message(
            chat_id=chat_id,
            role='user',
            content=message_content
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Emit user message to chat room
        room_name = f'chat_{chat_id}'
        socketio.emit('new_message', {
            'message_id': user_message.id,
            'chat_id': chat_id,
            'role': 'user',
            'content': message_content,
            'timestamp': user_message.created_at.isoformat()
        }, room=room_name)
        
        # Generate AI response
        ai_providers = AIProviders()
        
        # Emit typing indicator
        socketio.emit('ai_typing', {
            'chat_id': chat_id,
            'status': 'typing'
        }, room=room_name)
        
        try:
            # Get conversation history for context
            recent_messages = Message.query.filter_by(chat_id=chat_id).order_by(
                Message.created_at.desc()
            ).limit(10).all()
            
            # Build conversation context
            conversation_context = []
            for msg in reversed(recent_messages):
                conversation_context.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # Generate response
            response = ai_providers.get_chat_response(
                message_content,
                model=model,
                temperature=chat.temperature,
                max_tokens=chat.max_tokens
            )
            
            # Save AI response
            ai_message = Message(
                chat_id=chat_id,
                role='assistant',
                content=response
            )
            db.session.add(ai_message)
            db.session.commit()
            
            # Stop typing indicator
            socketio.emit('ai_typing', {
                'chat_id': chat_id,
                'status': 'stopped'
            }, room=room_name)
            
            # Emit AI response
            socketio.emit('new_message', {
                'message_id': ai_message.id,
                'chat_id': chat_id,
                'role': 'assistant',
                'content': response,
                'model': model,
                'timestamp': ai_message.created_at.isoformat()
            }, room=room_name)
            
        except Exception as e:
            logging.error(f"Error generating AI response: {str(e)}")
            
            # Stop typing indicator
            socketio.emit('ai_typing', {
                'chat_id': chat_id,
                'status': 'stopped'
            }, room=room_name)
            
            # Send error message
            error_message = Message(
                chat_id=chat_id,
                role='assistant',
                content=f"I apologize, but I encountered an error: {str(e)}"
            )
            db.session.add(error_message)
            db.session.commit()
            
            socketio.emit('new_message', {
                'message_id': error_message.id,
                'chat_id': chat_id,
                'role': 'assistant',
                'content': error_message.content,
                'error': True,
                'timestamp': error_message.created_at.isoformat()
            }, room=room_name)
    
    except Exception as e:
        logging.error(f"Error handling send message: {str(e)}")
        emit('error', {'message': 'Failed to send message'})

@socketio.on('file_upload_progress')
def handle_file_upload_progress(data):
    """Handle file upload progress updates"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        file_id = data.get('file_id')
        progress = data.get('progress', 0)
        status = data.get('status', 'uploading')
        
        # Emit progress update to user
        user_id = current_user.id
        socketio.emit('file_upload_update', {
            'file_id': file_id,
            'progress': progress,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling file upload progress: {str(e)}")
        emit('error', {'message': 'Failed to update progress'})

@socketio.on('workflow_execution_update')
def handle_workflow_execution_update(data):
    """Handle workflow execution updates"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        workflow_id = data.get('workflow_id')
        node_id = data.get('node_id')
        status = data.get('status')
        result = data.get('result')
        
        # Emit update to user
        user_id = current_user.id
        socketio.emit('workflow_update', {
            'workflow_id': workflow_id,
            'node_id': node_id,
            'status': status,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling workflow execution update: {str(e)}")
        emit('error', {'message': 'Failed to update workflow'})

@socketio.on('quantum_job_update')
def handle_quantum_job_update(data):
    """Handle quantum job status updates"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        job_id = data.get('job_id')
        status = data.get('status')
        result = data.get('result')
        
        # Emit update to user
        user_id = current_user.id
        socketio.emit('quantum_job_update', {
            'job_id': job_id,
            'status': status,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling quantum job update: {str(e)}")
        emit('error', {'message': 'Failed to update quantum job'})

@socketio.on('federated_training_update')
def handle_federated_training_update(data):
    """Handle federated learning training updates"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        node_id = data.get('node_id')
        round_number = data.get('round_number')
        metrics = data.get('metrics')
        
        # Emit update to user
        user_id = current_user.id
        socketio.emit('federated_training_update', {
            'node_id': node_id,
            'round_number': round_number,
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling federated training update: {str(e)}")
        emit('error', {'message': 'Failed to update federated training'})

@socketio.on('research_progress_update')
def handle_research_progress_update(data):
    """Handle research progress updates"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        project_id = data.get('project_id')
        experiment_id = data.get('experiment_id')
        progress = data.get('progress')
        insights = data.get('insights')
        
        # Emit update to user
        user_id = current_user.id
        socketio.emit('research_progress_update', {
            'project_id': project_id,
            'experiment_id': experiment_id,
            'progress': progress,
            'insights': insights,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling research progress update: {str(e)}")
        emit('error', {'message': 'Failed to update research progress'})

@socketio.on('system_notification')
def handle_system_notification(data):
    """Handle system-wide notifications"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return
        
        notification_type = data.get('type')
        message = data.get('message')
        priority = data.get('priority', 'normal')
        
        # Emit notification to user
        user_id = current_user.id
        socketio.emit('system_notification', {
            'type': notification_type,
            'message': message,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error handling system notification: {str(e)}")
        emit('error', {'message': 'Failed to send notification'})

def send_user_notification(user_id, notification_type, message, priority='normal'):
    """Send notification to specific user"""
    try:
        socketio.emit('system_notification', {
            'type': notification_type,
            'message': message,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{user_id}')
    
    except Exception as e:
        logging.error(f"Error sending user notification: {str(e)}")

def broadcast_notification(notification_type, message, priority='normal'):
    """Broadcast notification to all connected users"""
    try:
        socketio.emit('system_notification', {
            'type': notification_type,
            'message': message,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)
    
    except Exception as e:
        logging.error(f"Error broadcasting notification: {str(e)}")

def get_active_users():
    """Get list of active users"""
    try:
        return list(active_connections.keys())
    
    except Exception as e:
        logging.error(f"Error getting active users: {str(e)}")
        return []

def is_user_online(user_id):
    """Check if user is online"""
    try:
        return user_id in active_connections
    
    except Exception as e:
        logging.error(f"Error checking user online status: {str(e)}")
        return False
