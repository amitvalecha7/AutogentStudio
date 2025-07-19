import os
import uuid
import json
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import CodeProject, CodeGeneration, CodeReview
from app import db
import requests
import asyncio
import threading
from pathlib import Path
import zipfile
import time

class PlandexService:
    """Service for Plandex AI coding agent integration"""
    
    def __init__(self):
        self.plandex_path = self._find_plandex_binary()
        self.workspace_dir = 'plandex_workspace'
        self.active_sessions = {}
        self._ensure_workspace()
    
    def _find_plandex_binary(self) -> Optional[str]:
        """Find Plandex binary in system PATH"""
        try:
            result = subprocess.run(['which', 'plandex'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Try common installation paths
            common_paths = [
                '/usr/local/bin/plandex',
                '/usr/bin/plandex',
                '~/.local/bin/plandex',
                './plandex'
            ]
            
            for path in common_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path) and os.access(expanded_path, os.X_OK):
                    return expanded_path
            
            return None
            
        except Exception:
            return None
    
    def _ensure_workspace(self):
        """Ensure workspace directory exists"""
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
    
    def install_plandex(self) -> Dict[str, Any]:
        """Install Plandex from official GitHub repository"""
        if self.plandex_path:
            return {
                'success': True,
                'message': 'Plandex already installed',
                'path': self.plandex_path
            }
        
        try:
            # Clone the official Plandex repository
            plandex_repo = 'https://github.com/plandex-ai/plandex.git'
            temp_dir = tempfile.mkdtemp()
            
            # Clone repository
            clone_result = subprocess.run(
                ['git', 'clone', plandex_repo, temp_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Failed to clone repository: {clone_result.stderr}'
                }
            
            # Build and install Plandex
            build_dir = os.path.join(temp_dir, 'app', 'cli')
            
            # Build the CLI
            build_result = subprocess.run(
                ['go', 'build', '-o', 'plandex', '.'],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Build failed: {build_result.stderr}'
                }
            
            # Move binary to workspace
            source_binary = os.path.join(build_dir, 'plandex')
            target_binary = os.path.join(self.workspace_dir, 'plandex')
            
            shutil.move(source_binary, target_binary)
            os.chmod(target_binary, 0o755)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            self.plandex_path = target_binary
            
            return {
                'success': True,
                'message': 'Plandex installed successfully from GitHub',
                'path': self.plandex_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Installation error: {str(e)}'
            }
    
    def create_project(self, user_id: int, name: str, description: str, 
                      project_type: str = 'web', language: str = 'python') -> CodeProject:
        """Create a new code project"""
        try:
            project = CodeProject(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                description=description,
                project_type=project_type,
                language=language,
                status='active'
            )
            
            db.session.add(project)
            db.session.commit()
            
            # Create project workspace
            project_dir = os.path.join(self.workspace_dir, project.id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Initialize Plandex in project directory
            if self.plandex_path:
                self._run_plandex_command(['init'], project_dir)
            
            return project
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create project: {str(e)}")
    
    def generate_code(self, project_id: str, prompt: str, file_context: List[str] = None) -> CodeGeneration:
        """Generate code using Plandex"""
        try:
            project = CodeProject.query.get(project_id)
            if not project:
                raise ValueError("Project not found")
            
            generation = CodeGeneration(
                id=str(uuid.uuid4()),
                project_id=project_id,
                prompt=prompt,
                status='processing',
                file_context=file_context or []
            )
            
            db.session.add(generation)
            db.session.commit()
            
            # Run Plandex generation in background
            threading.Thread(
                target=self._generate_code_async,
                args=(generation.id, project_id, prompt, file_context)
            ).start()
            
            return generation
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to start code generation: {str(e)}")
    
    def _generate_code_async(self, generation_id: str, project_id: str, 
                           prompt: str, file_context: List[str]):
        """Generate code asynchronously using Plandex"""
        try:
            generation = CodeGeneration.query.get(generation_id)
            if not generation:
                return
            
            project_dir = os.path.join(self.workspace_dir, project_id)
            
            if not self.plandex_path:
                generation.status = 'failed'
                generation.error_message = 'Plandex not installed'
                db.session.commit()
                return
            
            # Add context files if provided
            if file_context:
                for file_path in file_context:
                    if os.path.exists(file_path):
                        self._run_plandex_command(['load', file_path], project_dir)
            
            # Generate code with Plandex
            result = self._run_plandex_command(['tell', prompt], project_dir)
            
            if result['success']:
                # Get the generated changes
                changes_result = self._run_plandex_command(['changes'], project_dir)
                
                if changes_result['success']:
                    generation.status = 'completed'
                    generation.generated_code = changes_result['stdout']
                    generation.output_files = self._get_project_files(project_dir)
                    generation.completed_at = datetime.now()
                else:
                    generation.status = 'failed'
                    generation.error_message = changes_result['stderr']
            else:
                generation.status = 'failed'
                generation.error_message = result['stderr']
            
            db.session.commit()
            
        except Exception as e:
            generation.status = 'failed'
            generation.error_message = str(e)
            db.session.commit()
    
    def _run_plandex_command(self, args: List[str], project_dir: str) -> Dict[str, Any]:
        """Run Plandex command in project directory"""
        try:
            if not self.plandex_path:
                return {
                    'success': False,
                    'stderr': 'Plandex binary not found'
                }
            
            cmd = [self.plandex_path] + args
            
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300,
                env=dict(os.environ, PLANDEX_API_KEY=os.environ.get('OPENAI_API_KEY', ''))
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stderr': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'stderr': str(e)
            }
    
    def _get_project_files(self, project_dir: str) -> List[Dict[str, str]]:
        """Get list of files in project directory"""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(project_dir):
                # Skip hidden directories and common build directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'dist', 'build']]
                
                for filename in filenames:
                    if not filename.startswith('.'):
                        file_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(file_path, project_dir)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            files.append({
                                'path': relative_path,
                                'content': content,
                                'size': os.path.getsize(file_path)
                            })
                        except (UnicodeDecodeError, PermissionError):
                            # Skip binary files or files we can't read
                            continue
        
        except Exception:
            pass
        
        return files
    
    def apply_changes(self, generation_id: str, approve_all: bool = False) -> Dict[str, Any]:
        """Apply Plandex generated changes"""
        try:
            generation = CodeGeneration.query.get(generation_id)
            if not generation:
                return {'success': False, 'message': 'Generation not found'}
            
            if generation.status != 'completed':
                return {'success': False, 'message': 'Generation not completed'}
            
            project_dir = os.path.join(self.workspace_dir, generation.project_id)
            
            if approve_all:
                result = self._run_plandex_command(['apply', '--all'], project_dir)
            else:
                result = self._run_plandex_command(['apply'], project_dir)
            
            if result['success']:
                generation.applied = True
                generation.applied_at = datetime.now()
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Changes applied successfully',
                    'output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to apply changes',
                    'error': result['stderr']
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error applying changes: {str(e)}'
            }
    
    def reject_changes(self, generation_id: str) -> Dict[str, Any]:
        """Reject Plandex generated changes"""
        try:
            generation = CodeGeneration.query.get(generation_id)
            if not generation:
                return {'success': False, 'message': 'Generation not found'}
            
            project_dir = os.path.join(self.workspace_dir, generation.project_id)
            result = self._run_plandex_command(['reject'], project_dir)
            
            if result['success']:
                generation.rejected = True
                generation.rejected_at = datetime.now()
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Changes rejected successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to reject changes',
                    'error': result['stderr']
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error rejecting changes: {str(e)}'
            }
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current status of Plandex project"""
        try:
            project = CodeProject.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}
            
            project_dir = os.path.join(self.workspace_dir, project_id)
            
            # Get Plandex status
            status_result = self._run_plandex_command(['status'], project_dir)
            plans_result = self._run_plandex_command(['plans'], project_dir)
            
            # Get recent generations
            recent_generations = CodeGeneration.query.filter_by(
                project_id=project_id
            ).order_by(CodeGeneration.created_at.desc()).limit(10).all()
            
            return {
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'language': project.language,
                    'status': project.status,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat()
                },
                'plandex_status': status_result['stdout'] if status_result['success'] else None,
                'plans': plans_result['stdout'] if plans_result['success'] else None,
                'recent_generations': [
                    {
                        'id': gen.id,
                        'prompt': gen.prompt[:100] + '...' if len(gen.prompt) > 100 else gen.prompt,
                        'status': gen.status,
                        'created_at': gen.created_at.isoformat(),
                        'completed_at': gen.completed_at.isoformat() if gen.completed_at else None,
                        'applied': gen.applied,
                        'rejected': gen.rejected
                    }
                    for gen in recent_generations
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def start_interactive_session(self, project_id: str) -> Dict[str, Any]:
        """Start interactive Plandex session"""
        try:
            project = CodeProject.query.get(project_id)
            if not project:
                return {'success': False, 'message': 'Project not found'}
            
            project_dir = os.path.join(self.workspace_dir, project_id)
            session_id = str(uuid.uuid4())
            
            # Create session info
            session_info = {
                'id': session_id,
                'project_id': project_id,
                'project_dir': project_dir,
                'started_at': datetime.now(),
                'active': True
            }
            
            self.active_sessions[session_id] = session_info
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Interactive session started'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to start session: {str(e)}'
            }
    
    def send_interactive_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Send command to interactive Plandex session"""
        try:
            if session_id not in self.active_sessions:
                return {'success': False, 'message': 'Session not found'}
            
            session = self.active_sessions[session_id]
            project_dir = session['project_dir']
            
            # Parse command
            if command.startswith('/'):
                # Special commands
                if command == '/status':
                    result = self._run_plandex_command(['status'], project_dir)
                elif command == '/plans':
                    result = self._run_plandex_command(['plans'], project_dir)
                elif command == '/changes':
                    result = self._run_plandex_command(['changes'], project_dir)
                elif command == '/apply':
                    result = self._run_plandex_command(['apply'], project_dir)
                elif command == '/reject':
                    result = self._run_plandex_command(['reject'], project_dir)
                elif command == '/help':
                    result = {
                        'success': True,
                        'stdout': '''Available commands:
/status - Show project status
/plans - List all plans
/changes - Show pending changes
/apply - Apply pending changes
/reject - Reject pending changes
/help - Show this help
Or just type your request naturally.'''
                    }
                else:
                    result = {'success': False, 'stderr': 'Unknown command'}
            else:
                # Regular prompt
                result = self._run_plandex_command(['tell', command], project_dir)
            
            return {
                'success': result['success'],
                'output': result['stdout'],
                'error': result['stderr'] if not result['success'] else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Command failed: {str(e)}'
            }
    
    def end_interactive_session(self, session_id: str) -> Dict[str, Any]:
        """End interactive Plandex session"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                return {'success': True, 'message': 'Session ended'}
            else:
                return {'success': False, 'message': 'Session not found'}
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error ending session: {str(e)}'
            }
    
    def export_project(self, project_id: str) -> Dict[str, Any]:
        """Export project as downloadable archive"""
        try:
            project = CodeProject.query.get(project_id)
            if not project:
                return {'success': False, 'message': 'Project not found'}
            
            project_dir = os.path.join(self.workspace_dir, project_id)
            
            # Create temporary zip file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(project_dir):
                        # Skip hidden directories
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        
                        for file in files:
                            if not file.startswith('.'):
                                file_path = os.path.join(root, file)
                                arc_path = os.path.relpath(file_path, project_dir)
                                zip_file.write(file_path, arc_path)
                
                return {
                    'success': True,
                    'zip_path': tmp_file.name,
                    'filename': f"{project.name.replace(' ', '_')}.zip"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Export failed: {str(e)}'
            }
    
    def import_project(self, user_id: int, name: str, zip_file) -> Dict[str, Any]:
        """Import project from uploaded archive"""
        try:
            # Create new project
            project = self.create_project(user_id, name, f"Imported project: {name}")
            project_dir = os.path.join(self.workspace_dir, project.id)
            
            # Extract zip file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(project_dir)
            
            # Initialize Plandex in the imported project
            if self.plandex_path:
                self._run_plandex_command(['init'], project_dir)
            
            return {
                'success': True,
                'project_id': project.id,
                'message': 'Project imported successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Import failed: {str(e)}'
            }
    
    def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        try:
            projects = CodeProject.query.filter_by(user_id=user_id).all()
            
            result = []
            for project in projects:
                # Get project statistics
                generations_count = CodeGeneration.query.filter_by(project_id=project.id).count()
                recent_generation = CodeGeneration.query.filter_by(
                    project_id=project.id
                ).order_by(CodeGeneration.created_at.desc()).first()
                
                result.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'language': project.language,
                    'project_type': project.project_type,
                    'status': project.status,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat(),
                    'generations_count': generations_count,
                    'last_generation': recent_generation.created_at.isoformat() if recent_generation else None
                })
            
            return result
            
        except Exception as e:
            return []
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete project and all associated data"""
        try:
            project = CodeProject.query.get(project_id)
            if not project:
                return {'success': False, 'message': 'Project not found'}
            
            # Delete project directory
            project_dir = os.path.join(self.workspace_dir, project_id)
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            # Delete from database (cascading will handle generations)
            db.session.delete(project)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Project deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Delete failed: {str(e)}'
            }
    
    def get_plandex_version(self) -> Dict[str, Any]:
        """Get Plandex version information"""
        if not self.plandex_path:
            return {
                'installed': False,
                'message': 'Plandex not installed'
            }
        
        try:
            result = subprocess.run(
                [self.plandex_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'installed': True,
                'version': result.stdout.strip(),
                'path': self.plandex_path
            }
            
        except Exception as e:
            return {
                'installed': False,
                'error': str(e)
            }