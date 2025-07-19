import json
import uuid
from datetime import datetime
from flask import current_app
from models import ChatSession, ChatMessage, User
from app import db
from utils.ai_providers import ai_providers

class ChatService:
    def __init__(self):
        self.ai_providers = ai_providers
    
    def create_session(self, user_id: str, title: str = None, model: str = 'gpt-4o') -> str:
        """Create a new chat session"""
        try:
            if not title:
                title = f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            session = ChatSession(
                user_id=user_id,
                title=title,
                model=model
            )
            
            db.session.add(session)
            db.session.commit()
            
            return str(session.id)
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create session: {str(e)}")
    
    def get_session(self, session_id: str, user_id: str) -> dict:
        """Get chat session with messages"""
        try:
            session = ChatSession.query.filter_by(
                id=session_id, 
                user_id=user_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            messages = ChatMessage.query.filter_by(
                session_id=session_id
            ).order_by(ChatMessage.created_at).all()
            
            return {
                'session': {
                    'id': str(session.id),
                    'title': session.title,
                    'model': session.model,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                },
                'messages': [
                    {
                        'id': str(msg.id),
                        'role': msg.role,
                        'content': msg.content,
                        'model_used': msg.model_used,
                        'tokens_used': msg.tokens_used,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            raise Exception(f"Failed to get session: {str(e)}")
    
    def add_message(self, session_id: str, role: str, content: str, model_used: str = None, tokens_used: int = None) -> str:
        """Add a message to a chat session"""
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                model_used=model_used,
                tokens_used=tokens_used
            )
            
            db.session.add(message)
            db.session.commit()
            
            return str(message.id)
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to add message: {str(e)}")
    
    def chat_completion(self, session_id: str, user_message: str, model: str = 'gpt-4o', provider: str = 'openai') -> dict:
        """Generate chat completion and save to session"""
        try:
            # Get session
            session = ChatSession.query.get(session_id)
            if not session:
                raise ValueError("Session not found")
            
            # Add user message
            user_msg_id = self.add_message(session_id, 'user', user_message)
            
            # Get conversation history
            messages = ChatMessage.query.filter_by(
                session_id=session_id
            ).order_by(ChatMessage.created_at).all()
            
            # Prepare messages for API
            api_messages = []
            if session.system_prompt:
                api_messages.append({
                    'role': 'system',
                    'content': session.system_prompt
                })
            
            for msg in messages:
                if msg.role in ['user', 'assistant']:
                    api_messages.append({
                        'role': msg.role,
                        'content': msg.content
                    })
            
            # Generate response
            if provider == 'openai':
                response = self.ai_providers.chat_with_openai(
                    messages=api_messages,
                    model=model,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                assistant_message = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
                
            elif provider == 'anthropic':
                response = self.ai_providers.chat_with_anthropic(
                    messages=api_messages,
                    model=model,
                    max_tokens=4000
                )
                
                assistant_message = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else None
                
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Add assistant message
            assistant_msg_id = self.add_message(
                session_id, 
                'assistant', 
                assistant_message, 
                model_used=model,
                tokens_used=tokens_used
            )
            
            # Update session timestamp
            session.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'message_id': assistant_msg_id,
                'content': assistant_message,
                'model_used': model,
                'tokens_used': tokens_used
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Chat completion failed: {str(e)}")
    
    def get_user_sessions(self, user_id: str) -> list:
        """Get all chat sessions for a user"""
        try:
            sessions = ChatSession.query.filter_by(
                user_id=user_id
            ).order_by(ChatSession.updated_at.desc()).all()
            
            return [
                {
                    'id': str(session.id),
                    'title': session.title,
                    'model': session.model,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                }
                for session in sessions
            ]
        except Exception as e:
            raise Exception(f"Failed to get user sessions: {str(e)}")
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            session = ChatSession.query.filter_by(
                id=session_id,
                user_id=user_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            db.session.delete(session)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete session: {str(e)}")

# Global instance
chat_service = ChatService()
