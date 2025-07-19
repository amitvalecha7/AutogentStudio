import json
import logging
from typing import Dict, Any, List, Optional
from flask import session
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, db
from models import Chat, Message, User

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        """Initialize WebSocket service"""
        self.active_connections = {}
        self.chat_rooms = {}
        self.collaboration_sessions = {}
        
    def handle_connect(self, auth: Dict[str, Any]) -> bool:
        """Handle client connection"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                logger.warning("Unauthorized WebSocket connection attempt")
                return False
            
            # Store connection info
            self.active_connections[user_id] = {
                'connected_at': datetime.utcnow(),
                'user_id': user_id
            }
            
            logger.info(f"WebSocket connection established for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            return False
    
    def handle_disconnect(self):
        """Handle client disconnection"""
        try:
            user_id = session.get('user_id')
            if user_id and user_id in self.active_connections:
                del self.active_connections[user_id]
                logger.info(f"WebSocket disconnected for user {user_id}")
                
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {str(e)}")
    
    def join_chat_room(self, data: Dict[str, Any]):
        """Join a chat room"""
        try:
            chat_id = data.get('chat_id')
            user_id = session.get('user_id')
            
            if not chat_id or not user_id:
                emit('error', {'message': 'Invalid chat room data'})
                return
            
            # Verify user has access to chat
            chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
            if not chat:
                emit('error', {'message': 'Chat not found or access denied'})
                return
            
            room = f'chat_{chat_id}'
            join_room(room)
            
            # Track room membership
            if room not in self.chat_rooms:
                self.chat_rooms[room] = set()
            self.chat_rooms[room].add(user_id)
            
            emit('chat_joined', {
                'chat_id': chat_id,
                'room': room,
                'message': f'Joined chat: {chat.title}'
            })
            
            logger.info(f"User {user_id} joined chat room {room}")
            
        except Exception as e:
            logger.error(f"Error joining chat room: {str(e)}")
            emit('error', {'message': 'Failed to join chat room'})
    
    def leave_chat_room(self, data: Dict[str, Any]):
        """Leave a chat room"""
        try:
            chat_id = data.get('chat_id')
            user_id = session.get('user_id')
            
            if not chat_id or not user_id:
                return
            
            room = f'chat_{chat_id}'
            leave_room(room)
            
            # Update room membership
            if room in self.chat_rooms and user_id in self.chat_rooms[room]:
                self.chat_rooms[room].remove(user_id)
                if not self.chat_rooms[room]:
                    del self.chat_rooms[room]
            
            emit('chat_left', {
                'chat_id': chat_id,
                'room': room,
                'message': 'Left chat room'
            })
            
            logger.info(f"User {user_id} left chat room {room}")
            
        except Exception as e:
            logger.error(f"Error leaving chat room: {str(e)}")
    
    def handle_typing(self, data: Dict[str, Any]):
        """Handle typing indicators"""
        try:
            chat_id = data.get('chat_id')
            user_id = session.get('user_id')
            
            if not chat_id or not user_id:
                return
            
            user = User.query.get(user_id)
            if not user:
                return
            
            room = f'chat_{chat_id}'
            emit('user_typing', {
                'user_id': user_id,
                'username': user.username,
                'chat_id': chat_id
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling typing: {str(e)}")
    
    def handle_stop_typing(self, data: Dict[str, Any]):
        """Handle stop typing indicators"""
        try:
            chat_id = data.get('chat_id')
            user_id = session.get('user_id')
            
            if not chat_id or not user_id:
                return
            
            room = f'chat_{chat_id}'
            emit('user_stop_typing', {
                'user_id': user_id,
                'chat_id': chat_id
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling stop typing: {str(e)}")
    
    def broadcast_message(self, chat_id: int, message_data: Dict[str, Any]):
        """Broadcast new message to chat room"""
        try:
            room = f'chat_{chat_id}'
            emit('new_message', message_data, room=room)
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
    
    def handle_collaboration_join(self, data: Dict[str, Any]):
        """Handle joining collaboration session"""
        try:
            session_id = data.get('session_id')
            session_type = data.get('session_type')  # 'workflow', 'quantum', 'terminal'
            user_id = session.get('user_id')
            
            if not session_id or not session_type or not user_id:
                emit('error', {'message': 'Invalid collaboration data'})
                return
            
            room = f'collab_{session_type}_{session_id}'
            join_room(room)
            
            # Track collaboration session
            if room not in self.collaboration_sessions:
                self.collaboration_sessions[room] = {
                    'type': session_type,
                    'session_id': session_id,
                    'participants': set()
                }
            
            self.collaboration_sessions[room]['participants'].add(user_id)
            
            # Notify other participants
            user = User.query.get(user_id)
            emit('participant_joined', {
                'user_id': user_id,
                'username': user.username if user else 'Unknown',
                'session_id': session_id,
                'session_type': session_type
            }, room=room, include_self=False)
            
            emit('collaboration_joined', {
                'session_id': session_id,
                'session_type': session_type,
                'participants': len(self.collaboration_sessions[room]['participants'])
            })
            
            logger.info(f"User {user_id} joined collaboration session {room}")
            
        except Exception as e:
            logger.error(f"Error joining collaboration: {str(e)}")
            emit('error', {'message': 'Failed to join collaboration'})
    
    def handle_collaboration_leave(self, data: Dict[str, Any]):
        """Handle leaving collaboration session"""
        try:
            session_id = data.get('session_id')
            session_type = data.get('session_type')
            user_id = session.get('user_id')
            
            if not session_id or not session_type or not user_id:
                return
            
            room = f'collab_{session_type}_{session_id}'
            leave_room(room)
            
            # Update collaboration session
            if room in self.collaboration_sessions:
                self.collaboration_sessions[room]['participants'].discard(user_id)
                
                if not self.collaboration_sessions[room]['participants']:
                    del self.collaboration_sessions[room]
                else:
                    # Notify remaining participants
                    user = User.query.get(user_id)
                    emit('participant_left', {
                        'user_id': user_id,
                        'username': user.username if user else 'Unknown',
                        'session_id': session_id,
                        'session_type': session_type
                    }, room=room)
            
            logger.info(f"User {user_id} left collaboration session {room}")
            
        except Exception as e:
            logger.error(f"Error leaving collaboration: {str(e)}")
    
    def handle_workflow_update(self, data: Dict[str, Any]):
        """Handle workflow updates in collaboration"""
        try:
            session_id = data.get('session_id')
            workflow_data = data.get('workflow_data')
            user_id = session.get('user_id')
            
            if not session_id or not workflow_data:
                return
            
            room = f'collab_workflow_{session_id}'
            user = User.query.get(user_id)
            
            emit('workflow_updated', {
                'session_id': session_id,
                'workflow_data': workflow_data,
                'updated_by': user.username if user else 'Unknown',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling workflow update: {str(e)}")
    
    def handle_quantum_circuit_update(self, data: Dict[str, Any]):
        """Handle quantum circuit updates in collaboration"""
        try:
            session_id = data.get('session_id')
            circuit_data = data.get('circuit_data')
            user_id = session.get('user_id')
            
            if not session_id or not circuit_data:
                return
            
            room = f'collab_quantum_{session_id}'
            user = User.query.get(user_id)
            
            emit('quantum_circuit_updated', {
                'session_id': session_id,
                'circuit_data': circuit_data,
                'updated_by': user.username if user else 'Unknown',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling quantum circuit update: {str(e)}")
    
    def handle_terminal_command(self, data: Dict[str, Any]):
        """Handle shared terminal commands"""
        try:
            session_id = data.get('session_id')
            command = data.get('command')
            user_id = session.get('user_id')
            
            if not session_id or not command:
                return
            
            room = f'collab_terminal_{session_id}'
            user = User.query.get(user_id)
            
            emit('terminal_command', {
                'session_id': session_id,
                'command': command,
                'executed_by': user.username if user else 'Unknown',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling terminal command: {str(e)}")
    
    def handle_cursor_update(self, data: Dict[str, Any]):
        """Handle cursor position updates in collaboration"""
        try:
            session_id = data.get('session_id')
            session_type = data.get('session_type')
            cursor_data = data.get('cursor_data')
            user_id = session.get('user_id')
            
            if not session_id or not session_type or not cursor_data:
                return
            
            room = f'collab_{session_type}_{session_id}'
            user = User.query.get(user_id)
            
            emit('cursor_updated', {
                'user_id': user_id,
                'username': user.username if user else 'Unknown',
                'cursor_data': cursor_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling cursor update: {str(e)}")
    
    def get_active_participants(self, session_id: str, session_type: str) -> List[Dict[str, Any]]:
        """Get active participants in collaboration session"""
        try:
            room = f'collab_{session_type}_{session_id}'
            if room not in self.collaboration_sessions:
                return []
            
            participants = []
            for user_id in self.collaboration_sessions[room]['participants']:
                user = User.query.get(user_id)
                if user:
                    participants.append({
                        'user_id': user_id,
                        'username': user.username,
                        'email': user.email
                    })
            
            return participants
            
        except Exception as e:
            logger.error(f"Error getting active participants: {str(e)}")
            return []
    
    def broadcast_system_message(self, message: str, room: Optional[str] = None):
        """Broadcast system message to room or all connected clients"""
        try:
            message_data = {
                'type': 'system',
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if room:
                emit('system_message', message_data, room=room)
            else:
                emit('system_message', message_data, broadcast=True)
                
        except Exception as e:
            logger.error(f"Error broadcasting system message: {str(e)}")

# Initialize WebSocket service
ws_service = WebSocketService()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect(auth):
    return ws_service.handle_connect(auth)

@socketio.on('disconnect')
def handle_disconnect():
    ws_service.handle_disconnect()

@socketio.on('join_chat')
def handle_join_chat(data):
    ws_service.join_chat_room(data)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    ws_service.leave_chat_room(data)

@socketio.on('typing')
def handle_typing(data):
    ws_service.handle_typing(data)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    ws_service.handle_stop_typing(data)

@socketio.on('join_collaboration')
def handle_join_collaboration(data):
    ws_service.handle_collaboration_join(data)

@socketio.on('leave_collaboration')
def handle_leave_collaboration(data):
    ws_service.handle_collaboration_leave(data)

@socketio.on('workflow_update')
def handle_workflow_update(data):
    ws_service.handle_workflow_update(data)

@socketio.on('quantum_circuit_update')
def handle_quantum_circuit_update(data):
    ws_service.handle_quantum_circuit_update(data)

@socketio.on('terminal_command')
def handle_terminal_command(data):
    ws_service.handle_terminal_command(data)

@socketio.on('cursor_update')
def handle_cursor_update(data):
    ws_service.handle_cursor_update(data)

from datetime import datetime
