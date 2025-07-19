import logging
import json
from typing import Dict, Any, List, Optional
from flask_socketio import emit, join_room, leave_room, rooms
from flask_login import current_user
from datetime import datetime

class WebSocketService:
    """Service for handling WebSocket communications"""
    
    def __init__(self):
        self.active_connections = {}
        self.room_members = {}
    
    def emit_message(self, room: str, message: Dict[str, Any], include_self: bool = True):
        """Emit message to a specific room"""
        try:
            emit('new_message', message, room=room, include_self=include_self)
            logging.debug(f"Message emitted to room {room}: {message}")
        except Exception as e:
            logging.error(f"Error emitting message to room {room}: {str(e)}")
    
    def emit_to_user(self, user_id: str, event: str, data: Dict[str, Any]):
        """Emit event to specific user"""
        try:
            user_room = f"user_{user_id}"
            emit(event, data, room=user_room)
            logging.debug(f"Event {event} emitted to user {user_id}")
        except Exception as e:
            logging.error(f"Error emitting to user {user_id}: {str(e)}")
    
    def broadcast_to_all(self, event: str, data: Dict[str, Any]):
        """Broadcast event to all connected users"""
        try:
            emit(event, data, broadcast=True)
            logging.debug(f"Event {event} broadcasted to all users")
        except Exception as e:
            logging.error(f"Error broadcasting event: {str(e)}")
    
    def join_chat_room(self, chat_id: str, user_id: str):
        """Join user to chat room"""
        try:
            room_name = f"chat_{chat_id}"
            join_room(room_name)
            
            if room_name not in self.room_members:
                self.room_members[room_name] = set()
            self.room_members[room_name].add(user_id)
            
            # Notify others in room
            emit('user_joined', {
                'user_id': user_id,
                'username': current_user.username if current_user.is_authenticated else 'Anonymous',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, include_self=False)
            
            logging.debug(f"User {user_id} joined chat room {chat_id}")
            
        except Exception as e:
            logging.error(f"Error joining chat room: {str(e)}")
    
    def leave_chat_room(self, chat_id: str, user_id: str):
        """Remove user from chat room"""
        try:
            room_name = f"chat_{chat_id}"
            leave_room(room_name)
            
            if room_name in self.room_members:
                self.room_members[room_name].discard(user_id)
            
            # Notify others in room
            emit('user_left', {
                'user_id': user_id,
                'username': current_user.username if current_user.is_authenticated else 'Anonymous',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
            
            logging.debug(f"User {user_id} left chat room {chat_id}")
            
        except Exception as e:
            logging.error(f"Error leaving chat room: {str(e)}")
    
    def emit_typing_indicator(self, chat_id: str, user_id: str, is_typing: bool):
        """Emit typing indicator"""
        try:
            room_name = f"chat_{chat_id}"
            
            event = 'user_typing' if is_typing else 'user_stopped_typing'
            emit(event, {
                'user_id': user_id,
                'username': current_user.username if current_user.is_authenticated else 'Anonymous',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, include_self=False)
            
        except Exception as e:
            logging.error(f"Error emitting typing indicator: {str(e)}")
    
    def emit_ai_response_chunk(self, chat_id: str, chunk: str, is_complete: bool = False):
        """Emit AI response chunk for streaming"""
        try:
            room_name = f"chat_{chat_id}"
            
            emit('ai_response_chunk', {
                'chunk': chunk,
                'is_complete': is_complete,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
            
        except Exception as e:
            logging.error(f"Error emitting AI response chunk: {str(e)}")
    
    def emit_file_upload_progress(self, user_id: str, file_id: str, progress: int):
        """Emit file upload progress"""
        try:
            self.emit_to_user(user_id, 'file_upload_progress', {
                'file_id': file_id,
                'progress': progress,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting upload progress: {str(e)}")
    
    def emit_file_processing_status(self, user_id: str, file_id: str, status: str, message: str = ""):
        """Emit file processing status update"""
        try:
            self.emit_to_user(user_id, 'file_processing_status', {
                'file_id': file_id,
                'status': status,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting processing status: {str(e)}")
    
    def emit_knowledge_base_update(self, user_id: str, kb_id: str, event_type: str, data: Dict[str, Any]):
        """Emit knowledge base update"""
        try:
            self.emit_to_user(user_id, 'knowledge_base_update', {
                'kb_id': kb_id,
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting knowledge base update: {str(e)}")
    
    def emit_system_notification(self, user_id: str, notification_type: str, title: str, message: str, 
                                level: str = 'info'):
        """Emit system notification to user"""
        try:
            self.emit_to_user(user_id, 'system_notification', {
                'type': notification_type,
                'title': title,
                'message': message,
                'level': level,  # info, success, warning, error
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting system notification: {str(e)}")
    
    def emit_workspace_activity(self, workspace_id: str, user_id: str, activity_type: str, data: Dict[str, Any]):
        """Emit workspace activity update"""
        try:
            room_name = f"workspace_{workspace_id}"
            
            emit('workspace_activity', {
                'user_id': user_id,
                'activity_type': activity_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, include_self=False)
            
        except Exception as e:
            logging.error(f"Error emitting workspace activity: {str(e)}")
    
    def emit_collaboration_cursor(self, workspace_id: str, user_id: str, cursor_data: Dict[str, Any]):
        """Emit real-time cursor position for collaboration"""
        try:
            room_name = f"workspace_{workspace_id}"
            
            emit('collaboration_cursor', {
                'user_id': user_id,
                'cursor_data': cursor_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, include_self=False)
            
        except Exception as e:
            logging.error(f"Error emitting collaboration cursor: {str(e)}")
    
    def emit_workflow_status(self, user_id: str, workflow_id: str, status: str, progress: int = 0, 
                           message: str = ""):
        """Emit workflow execution status"""
        try:
            self.emit_to_user(user_id, 'workflow_status', {
                'workflow_id': workflow_id,
                'status': status,
                'progress': progress,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting workflow status: {str(e)}")
    
    def emit_quantum_job_update(self, user_id: str, job_id: str, status: str, results: Optional[Dict] = None):
        """Emit quantum job status update"""
        try:
            self.emit_to_user(user_id, 'quantum_job_update', {
                'job_id': job_id,
                'status': status,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting quantum job update: {str(e)}")
    
    def emit_federated_training_update(self, user_id: str, session_id: str, round_num: int, 
                                     metrics: Dict[str, Any]):
        """Emit federated learning training update"""
        try:
            self.emit_to_user(user_id, 'federated_training_update', {
                'session_id': session_id,
                'round': round_num,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting federated training update: {str(e)}")
    
    def emit_safety_alert(self, user_id: str, alert_type: str, severity: str, message: str, 
                         context: Dict[str, Any]):
        """Emit AI safety alert"""
        try:
            self.emit_to_user(user_id, 'safety_alert', {
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'context': context,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting safety alert: {str(e)}")
    
    def emit_research_discovery(self, user_id: str, discovery_type: str, title: str, data: Dict[str, Any]):
        """Emit automated research discovery"""
        try:
            self.emit_to_user(user_id, 'research_discovery', {
                'discovery_type': discovery_type,
                'title': title,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting research discovery: {str(e)}")
    
    def emit_blockchain_transaction(self, user_id: str, transaction_hash: str, status: str, 
                                  transaction_type: str):
        """Emit blockchain transaction update"""
        try:
            self.emit_to_user(user_id, 'blockchain_transaction', {
                'transaction_hash': transaction_hash,
                'status': status,
                'transaction_type': transaction_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logging.error(f"Error emitting blockchain transaction: {str(e)}")
    
    def get_room_members(self, room: str) -> List[str]:
        """Get list of members in a room"""
        try:
            return list(self.room_members.get(room, set()))
        except Exception as e:
            logging.error(f"Error getting room members: {str(e)}")
            return []
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get list of rooms a user is in"""
        try:
            user_rooms = []
            for room, members in self.room_members.items():
                if user_id in members:
                    user_rooms.append(room)
            return user_rooms
        except Exception as e:
            logging.error(f"Error getting user rooms: {str(e)}")
            return []
    
    def cleanup_user_connections(self, user_id: str):
        """Clean up user connections when they disconnect"""
        try:
            # Remove user from all rooms
            for room in list(self.room_members.keys()):
                if user_id in self.room_members[room]:
                    self.room_members[room].discard(user_id)
                    
                    # Remove empty rooms
                    if not self.room_members[room]:
                        del self.room_members[room]
            
            # Remove from active connections
            if user_id in self.active_connections:
                del self.active_connections[user_id]
                
            logging.debug(f"Cleaned up connections for user {user_id}")
            
        except Exception as e:
            logging.error(f"Error cleaning up user connections: {str(e)}")
    
    def handle_connection(self, user_id: str, session_id: str):
        """Handle new user connection"""
        try:
            self.active_connections[user_id] = {
                'session_id': session_id,
                'connected_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
            
            # Join user to their personal room
            join_room(f"user_{user_id}")
            
            logging.debug(f"User {user_id} connected with session {session_id}")
            
        except Exception as e:
            logging.error(f"Error handling connection: {str(e)}")
    
    def handle_disconnection(self, user_id: str):
        """Handle user disconnection"""
        try:
            # Leave personal room
            leave_room(f"user_{user_id}")
            
            # Clean up connections
            self.cleanup_user_connections(user_id)
            
            logging.debug(f"User {user_id} disconnected")
            
        except Exception as e:
            logging.error(f"Error handling disconnection: {str(e)}")
    
    def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        try:
            if user_id in self.active_connections:
                self.active_connections[user_id]['last_activity'] = datetime.utcnow()
        except Exception as e:
            logging.error(f"Error updating user activity: {str(e)}")
    
    def get_active_users_count(self) -> int:
        """Get count of currently active users"""
        try:
            return len(self.active_connections)
        except Exception as e:
            logging.error(f"Error getting active users count: {str(e)}")
            return 0
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is currently online"""
        try:
            return user_id in self.active_connections
        except Exception as e:
            logging.error(f"Error checking user online status: {str(e)}")
            return False
