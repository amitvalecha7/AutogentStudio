import os
import uuid
import json
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import ChatSession, ChatMessage, Agent, User
from app import db
import requests
import asyncio
import threading
from pathlib import Path
import zipfile
import time
import yaml

class LobeChatService:
    """Service for LobeChat integration - Chat interface and AI agents"""
    
    def __init__(self):
        self.lobechat_path = None
        self.lobechat_dir = 'lobechat'
        self.agents_dir = 'agents'
        self.server_url = 'http://127.0.0.1:3210'
        self.is_running = False
        self.server_process = None
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure LobeChat directories exist"""
        for directory in [self.lobechat_dir, self.agents_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def install_lobechat(self) -> Dict[str, Any]:
        """Install LobeChat from official GitHub repository"""
        if self.lobechat_path and os.path.exists(self.lobechat_path):
            return {
                'success': True,
                'message': 'LobeChat already installed',
                'path': self.lobechat_path
            }
        
        try:
            # Clone the official LobeChat repository
            lobechat_repo = 'https://github.com/lobehub/lobe-chat.git'
            
            # Clone repository
            clone_result = subprocess.run(
                ['git', 'clone', lobechat_repo, self.lobechat_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Failed to clone repository: {clone_result.stderr}'
                }
            
            # Install Node.js dependencies
            npm_install_result = subprocess.run(
                ['npm', 'install'],
                cwd=self.lobechat_dir,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if npm_install_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Failed to install dependencies: {npm_install_result.stderr}'
                }
            
            # Build the project
            build_result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=self.lobechat_dir,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if build_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Build failed: {build_result.stderr}'
                }
            
            # Set LobeChat path
            self.lobechat_path = os.path.join(self.lobechat_dir, 'package.json')
            
            # Download official agent marketplace
            self._download_agent_marketplace()
            
            return {
                'success': True,
                'message': 'LobeChat installed successfully from GitHub',
                'path': self.lobechat_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Installation error: {str(e)}'
            }
    
    def _download_agent_marketplace(self):
        """Download official LobeChat agent marketplace"""
        try:
            # Clone the agents repository
            agents_repo = 'https://github.com/lobehub/lobe-chat-agents.git'
            agents_temp = tempfile.mkdtemp()
            
            clone_result = subprocess.run(
                ['git', 'clone', agents_repo, agents_temp],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode == 0:
                # Copy agent files to our agents directory
                agents_src = os.path.join(agents_temp, 'src')
                if os.path.exists(agents_src):
                    shutil.copytree(agents_src, self.agents_dir, dirs_exist_ok=True)
                
                # Clean up
                shutil.rmtree(agents_temp)
                
        except Exception as e:
            print(f"Error downloading agents: {str(e)}")
    
    def start_server(self) -> Dict[str, Any]:
        """Start LobeChat development server"""
        if self.is_running:
            return {
                'success': True,
                'message': 'LobeChat server already running',
                'url': self.server_url
            }
        
        try:
            if not self.lobechat_path or not os.path.exists(self.lobechat_path):
                return {
                    'success': False,
                    'message': 'LobeChat not installed'
                }
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'NEXT_PUBLIC_BASE_PATH': '',
                'PORT': '3210',
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
                'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', ''),
                'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', ''),
            })
            
            # Start development server
            self.server_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=self.lobechat_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Wait for server to start
            time.sleep(10)
            
            # Check if server is responding
            try:
                response = requests.get(f'{self.server_url}', timeout=10)
                if response.status_code == 200:
                    self.is_running = True
                    return {
                        'success': True,
                        'message': 'LobeChat server started successfully',
                        'url': self.server_url
                    }
            except:
                pass
            
            return {
                'success': False,
                'message': 'LobeChat server failed to start'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Server start error: {str(e)}'
            }
    
    def stop_server(self) -> Dict[str, Any]:
        """Stop LobeChat server"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.server_process = None
            
            self.is_running = False
            
            return {
                'success': True,
                'message': 'LobeChat server stopped'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error stopping server: {str(e)}'
            }
    
    def get_official_agents(self) -> List[Dict[str, Any]]:
        """Get official LobeChat agents from marketplace"""
        try:
            agents = []
            
            # Read agents from the downloaded marketplace
            if os.path.exists(self.agents_dir):
                for root, dirs, files in os.walk(self.agents_dir):
                    for file in files:
                        if file.endswith('.json'):
                            agent_path = os.path.join(root, file)
                            try:
                                with open(agent_path, 'r', encoding='utf-8') as f:
                                    agent_data = json.load(f)
                                    
                                    # Normalize agent data
                                    agent = {
                                        'id': agent_data.get('identifier', file.replace('.json', '')),
                                        'name': agent_data.get('meta', {}).get('title', 'Unknown'),
                                        'description': agent_data.get('meta', {}).get('description', ''),
                                        'avatar': agent_data.get('meta', {}).get('avatar', ''),
                                        'tags': agent_data.get('meta', {}).get('tags', []),
                                        'author': agent_data.get('author', 'LobeHub'),
                                        'config': agent_data.get('config', {}),
                                        'systemRole': agent_data.get('systemRole', ''),
                                        'category': agent_data.get('meta', {}).get('category', 'assistant'),
                                        'source': 'official'
                                    }
                                    
                                    agents.append(agent)
                                    
                            except Exception as e:
                                print(f"Error reading agent {agent_path}: {str(e)}")
                                continue
            
            return agents
            
        except Exception as e:
            return []
    
    def create_custom_agent(self, user_id: int, name: str, description: str, 
                          system_role: str, config: Dict = None) -> Agent:
        """Create a custom agent"""
        try:
            agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                description=description,
                system_role=system_role,
                config=config or {},
                is_active=True,
                agent_type='custom'
            )
            
            db.session.add(agent)
            db.session.commit()
            
            return agent
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create agent: {str(e)}")
    
    def import_official_agent(self, user_id: int, agent_id: str) -> Agent:
        """Import an official agent for a user"""
        try:
            # Get the official agent data
            official_agents = self.get_official_agents()
            official_agent = None
            
            for agent in official_agents:
                if agent['id'] == agent_id:
                    official_agent = agent
                    break
            
            if not official_agent:
                raise ValueError("Official agent not found")
            
            # Create user's copy of the agent
            user_agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=official_agent['name'],
                description=official_agent['description'],
                system_role=official_agent['systemRole'],
                config=official_agent['config'],
                avatar_url=official_agent['avatar'],
                tags=official_agent['tags'],
                is_active=True,
                agent_type='imported',
                source_id=agent_id
            )
            
            db.session.add(user_agent)
            db.session.commit()
            
            return user_agent
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to import agent: {str(e)}")
    
    def get_user_agents(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's agents"""
        try:
            agents = Agent.query.filter_by(user_id=user_id, is_active=True).all()
            
            result = []
            for agent in agents:
                # Get usage statistics
                sessions_count = ChatSession.query.filter_by(agent_id=agent.id).count()
                messages_count = db.session.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.agent_id == agent.id
                ).count()
                
                result.append({
                    'id': agent.id,
                    'name': agent.name,
                    'description': agent.description,
                    'avatar_url': agent.avatar_url,
                    'tags': agent.tags,
                    'agent_type': agent.agent_type,
                    'created_at': agent.created_at.isoformat(),
                    'updated_at': agent.updated_at.isoformat(),
                    'stats': {
                        'sessions_count': sessions_count,
                        'messages_count': messages_count
                    }
                })
            
            return result
            
        except Exception as e:
            return []
    
    def create_chat_session(self, user_id: int, agent_id: str = None, 
                          title: str = None) -> ChatSession:
        """Create a new chat session"""
        try:
            session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                agent_id=agent_id,
                title=title or 'New Chat',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(session)
            db.session.commit()
            
            return session
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create chat session: {str(e)}")
    
    def send_message(self, session_id: str, content: str, role: str = 'user') -> ChatMessage:
        """Send a message in a chat session"""
        try:
            session = ChatSession.query.get(session_id)
            if not session:
                raise ValueError("Chat session not found")
            
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=role,
                content=content,
                created_at=datetime.now()
            )
            
            db.session.add(message)
            
            # Update session
            session.updated_at = datetime.now()
            
            db.session.commit()
            
            return message
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to send message: {str(e)}")
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get messages from a chat session"""
        try:
            messages = ChatMessage.query.filter_by(session_id=session_id).order_by(
                ChatMessage.created_at.asc()
            ).all()
            
            result = []
            for message in messages:
                result.append({
                    'id': message.id,
                    'role': message.role,
                    'content': message.content,
                    'metadata': message.metadata,
                    'created_at': message.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            return []
    
    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        try:
            sessions = ChatSession.query.filter_by(user_id=user_id).order_by(
                ChatSession.updated_at.desc()
            ).all()
            
            result = []
            for session in sessions:
                # Get last message
                last_message = ChatMessage.query.filter_by(session_id=session.id).order_by(
                    ChatMessage.created_at.desc()
                ).first()
                
                # Get agent info
                agent = None
                if session.agent_id:
                    agent = Agent.query.get(session.agent_id)
                
                result.append({
                    'id': session.id,
                    'title': session.title,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat(),
                    'agent': {
                        'id': agent.id,
                        'name': agent.name,
                        'avatar_url': agent.avatar_url
                    } if agent else None,
                    'last_message': {
                        'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                        'created_at': last_message.created_at.isoformat()
                    } if last_message else None
                })
            
            return result
            
        except Exception as e:
            return []
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a chat session"""
        try:
            session = ChatSession.query.get(session_id)
            if not session:
                return {'success': False, 'message': 'Session not found'}
            
            # Delete all messages (cascade should handle this)
            ChatMessage.query.filter_by(session_id=session_id).delete()
            
            # Delete session
            db.session.delete(session)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Session deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Delete failed: {str(e)}'
            }
    
    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export chat session as JSON"""
        try:
            session = ChatSession.query.get(session_id)
            if not session:
                return {'success': False, 'message': 'Session not found'}
            
            messages = self.get_session_messages(session_id)
            
            # Get agent info
            agent = None
            if session.agent_id:
                agent = Agent.query.get(session.agent_id)
            
            export_data = {
                'session': {
                    'id': session.id,
                    'title': session.title,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                },
                'agent': {
                    'id': agent.id,
                    'name': agent.name,
                    'system_role': agent.system_role
                } if agent else None,
                'messages': messages,
                'exported_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'data': export_data,
                'filename': f"chat_session_{session.id}.json"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Export failed: {str(e)}'
            }
    
    def import_session(self, user_id: int, session_data: Dict) -> Dict[str, Any]:
        """Import chat session from JSON"""
        try:
            # Create new session
            session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=session_data.get('session', {}).get('title', 'Imported Chat'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(session)
            db.session.flush()  # Get the ID
            
            # Import messages
            messages = session_data.get('messages', [])
            for msg_data in messages:
                message = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    role=msg_data.get('role', 'user'),
                    content=msg_data.get('content', ''),
                    metadata=msg_data.get('metadata'),
                    created_at=datetime.now()
                )
                db.session.add(message)
            
            db.session.commit()
            
            return {
                'success': True,
                'session_id': session.id,
                'message': 'Session imported successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Import failed: {str(e)}'
            }
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get LobeChat server status"""
        try:
            if not self.is_running:
                return {
                    'running': False,
                    'message': 'Server not running'
                }
            
            # Check server health
            response = requests.get(f'{self.server_url}', timeout=5)
            if response.status_code == 200:
                return {
                    'running': True,
                    'url': self.server_url,
                    'status': 'healthy'
                }
            else:
                return {
                    'running': False,
                    'message': 'Server not responding'
                }
                
        except Exception as e:
            return {
                'running': False,
                'message': str(e)
            }
    
    def get_agent_categories(self) -> List[Dict[str, Any]]:
        """Get available agent categories"""
        categories = [
            {
                'id': 'assistant',
                'name': 'Assistant',
                'description': 'General purpose assistants',
                'icon': 'user'
            },
            {
                'id': 'programming',
                'name': 'Programming',
                'description': 'Code and development assistants',
                'icon': 'code'
            },
            {
                'id': 'writing',
                'name': 'Writing',
                'description': 'Content creation and writing',
                'icon': 'edit'
            },
            {
                'id': 'academic',
                'name': 'Academic',
                'description': 'Research and academic assistance',
                'icon': 'book'
            },
            {
                'id': 'business',
                'name': 'Business',
                'description': 'Business and productivity',
                'icon': 'briefcase'
            },
            {
                'id': 'creative',
                'name': 'Creative',
                'description': 'Creative and artistic assistance',
                'icon': 'palette'
            },
            {
                'id': 'language',
                'name': 'Language',
                'description': 'Translation and language learning',
                'icon': 'globe'
            },
            {
                'id': 'entertainment',
                'name': 'Entertainment',
                'description': 'Games and entertainment',
                'icon': 'gamepad'
            }
        ]
        
        return categories
    
    def update_agent_config(self, agent_id: str, config: Dict) -> Dict[str, Any]:
        """Update agent configuration"""
        try:
            agent = Agent.query.get(agent_id)
            if not agent:
                return {'success': False, 'message': 'Agent not found'}
            
            agent.config = config
            agent.updated_at = datetime.now()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Agent configuration updated'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Update failed: {str(e)}'
            }
    
    def get_lobechat_version(self) -> Dict[str, Any]:
        """Get LobeChat version information"""
        if not self.lobechat_path:
            return {
                'installed': False,
                'message': 'LobeChat not installed'
            }
        
        try:
            with open(self.lobechat_path, 'r') as f:
                package_data = json.load(f)
            
            return {
                'installed': True,
                'version': package_data.get('version', 'unknown'),
                'name': package_data.get('name', 'lobe-chat'),
                'path': self.lobechat_path
            }
            
        except Exception as e:
            return {
                'installed': False,
                'error': str(e)
            }