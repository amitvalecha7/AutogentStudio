from flask_socketio import emit, join_room, leave_room, disconnect
from flask import session, request
import logging
import json
from datetime import datetime

def handle_websocket_authentication():
    """Handle WebSocket authentication"""
    if 'user_id' not in session:
        logging.warning("Unauthenticated WebSocket connection attempt")
        disconnect()
        return False
    return True

def emit_to_user(user_id: str, event: str, data: dict):
    """Emit event to specific user"""
    try:
        emit(event, data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error emitting to user {user_id}: {str(e)}")

def emit_to_chat(chat_id: str, event: str, data: dict):
    """Emit event to specific chat room"""
    try:
        emit(event, data, room=f'chat_{chat_id}')
    except Exception as e:
        logging.error(f"Error emitting to chat {chat_id}: {str(e)}")

def join_user_room(user_id: str):
    """Join user-specific room"""
    try:
        join_room(f'user_{user_id}')
        logging.info(f"User {user_id} joined personal room")
    except Exception as e:
        logging.error(f"Error joining user room for {user_id}: {str(e)}")

def leave_user_room(user_id: str):
    """Leave user-specific room"""
    try:
        leave_room(f'user_{user_id}')
        logging.info(f"User {user_id} left personal room")
    except Exception as e:
        logging.error(f"Error leaving user room for {user_id}: {str(e)}")

def broadcast_system_message(message: str, message_type: str = 'info'):
    """Broadcast system message to all connected users"""
    try:
        data = {
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat()
        }
        emit('system_message', data, broadcast=True)
        logging.info(f"System message broadcasted: {message}")
    except Exception as e:
        logging.error(f"Error broadcasting system message: {str(e)}")

def log_websocket_event(event_type: str, user_id: str = None, data: dict = None):
    """Log WebSocket events for debugging and analytics"""
    try:
        log_data = {
            'event_type': event_type,
            'user_id': user_id or session.get('user_id'),
            'timestamp': datetime.now().isoformat(),
            'client_ip': request.environ.get('REMOTE_ADDR'),
            'user_agent': request.environ.get('HTTP_USER_AGENT'),
            'data': data
        }
        logging.info(f"WebSocket event: {json.dumps(log_data)}")
    except Exception as e:
        logging.error(f"Error logging WebSocket event: {str(e)}")

def handle_websocket_error(error):
    """Handle WebSocket errors"""
    logging.error(f"WebSocket error: {str(error)}")
    emit('error', {
        'message': 'A connection error occurred. Please refresh the page.',
        'timestamp': datetime.now().isoformat()
    })

def validate_websocket_data(data: dict, required_fields: list) -> bool:
    """Validate WebSocket message data"""
    try:
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                logging.warning(f"Missing required field in WebSocket data: {field}")
                return False
        
        return True
    except Exception as e:
        logging.error(f"Error validating WebSocket data: {str(e)}")
        return False

def send_typing_indicator(chat_id: str, user_id: str, is_typing: bool):
    """Send typing indicator to chat room"""
    try:
        data = {
            'user_id': user_id,
            'is_typing': is_typing,
            'timestamp': datetime.now().isoformat()
        }
        emit('typing_indicator', data, room=f'chat_{chat_id}', include_self=False)
    except Exception as e:
        logging.error(f"Error sending typing indicator: {str(e)}")

def send_chat_status_update(chat_id: str, status: str, additional_data: dict = None):
    """Send chat status update to room"""
    try:
        data = {
            'chat_id': chat_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        if additional_data:
            data.update(additional_data)
        
        emit('chat_status_update', data, room=f'chat_{chat_id}')
    except Exception as e:
        logging.error(f"Error sending chat status update: {str(e)}")

def send_file_processing_update(user_id: str, file_id: str, progress: int, status: str):
    """Send file processing progress update"""
    try:
        data = {
            'file_id': file_id,
            'progress': progress,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        emit('file_processing_update', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending file processing update: {str(e)}")

def send_quantum_job_update(user_id: str, job_id: str, status: str, result: dict = None):
    """Send quantum computing job update"""
    try:
        data = {
            'job_id': job_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        if result:
            data['result'] = result
        
        emit('quantum_job_update', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending quantum job update: {str(e)}")

def send_federated_learning_update(user_id: str, job_id: str, round_number: int, metrics: dict):
    """Send federated learning progress update"""
    try:
        data = {
            'job_id': job_id,
            'round_number': round_number,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        emit('federated_learning_update', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending federated learning update: {str(e)}")

def send_neuromorphic_simulation_update(user_id: str, simulation_id: str, progress: int, metrics: dict):
    """Send neuromorphic simulation progress update"""
    try:
        data = {
            'simulation_id': simulation_id,
            'progress': progress,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        emit('neuromorphic_simulation_update', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending neuromorphic simulation update: {str(e)}")

def send_safety_alert(user_id: str, alert_type: str, message: str, severity: str = 'medium'):
    """Send AI safety alert"""
    try:
        data = {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        emit('safety_alert', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending safety alert: {str(e)}")

def send_research_progress_update(user_id: str, project_id: str, phase: str, progress: int):
    """Send self-improving AI research progress update"""
    try:
        data = {
            'project_id': project_id,
            'phase': phase,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        emit('research_progress_update', data, room=f'user_{user_id}')
    except Exception as e:
        logging.error(f"Error sending research progress update: {str(e)}")
