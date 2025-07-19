import os
import uuid
import json
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import ImageGeneration, ComfyUIWorkflow, ComfyUIModel
from app import db
import requests
import asyncio
import threading
from pathlib import Path
import zipfile
import time
import websocket
import base64
from PIL import Image
import io

class ComfyUIService:
    """Service for ComfyUI integration - Advanced node-based image generation"""
    
    def __init__(self):
        self.comfyui_path = None
        self.comfyui_dir = 'comfyui'
        self.server_url = 'http://127.0.0.1:8188'
        self.ws_url = 'ws://127.0.0.1:8188/ws'
        self.is_running = False
        self.server_process = None
        self.active_generations = {}
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure ComfyUI directory exists"""
        if not os.path.exists(self.comfyui_dir):
            os.makedirs(self.comfyui_dir)
    
    def install_comfyui(self) -> Dict[str, Any]:
        """Install ComfyUI from official GitHub repository"""
        if self.comfyui_path and os.path.exists(self.comfyui_path):
            return {
                'success': True,
                'message': 'ComfyUI already installed',
                'path': self.comfyui_path
            }
        
        try:
            # Clone the official ComfyUI repository
            comfyui_repo = 'https://github.com/comfyanonymous/ComfyUI.git'
            
            # Clone repository
            clone_result = subprocess.run(
                ['git', 'clone', comfyui_repo, self.comfyui_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Failed to clone repository: {clone_result.stderr}'
                }
            
            # Install Python dependencies
            requirements_path = os.path.join(self.comfyui_dir, 'requirements.txt')
            if os.path.exists(requirements_path):
                pip_result = subprocess.run(
                    ['pip', 'install', '-r', requirements_path],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if pip_result.returncode != 0:
                    return {
                        'success': False,
                        'message': f'Failed to install dependencies: {pip_result.stderr}'
                    }
            
            # Set ComfyUI path
            self.comfyui_path = os.path.join(self.comfyui_dir, 'main.py')
            
            # Download essential models
            self._download_essential_models()
            
            return {
                'success': True,
                'message': 'ComfyUI installed successfully from GitHub',
                'path': self.comfyui_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Installation error: {str(e)}'
            }
    
    def _download_essential_models(self):
        """Download essential models for ComfyUI"""
        try:
            models_dir = os.path.join(self.comfyui_dir, 'models')
            checkpoints_dir = os.path.join(models_dir, 'checkpoints')
            vae_dir = os.path.join(models_dir, 'vae')
            
            # Create model directories
            os.makedirs(checkpoints_dir, exist_ok=True)
            os.makedirs(vae_dir, exist_ok=True)
            
            # Essential models to download (using Hugging Face)
            essential_models = [
                {
                    'name': 'SD 1.5',
                    'url': 'https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt',
                    'path': os.path.join(checkpoints_dir, 'v1-5-pruned-emaonly.ckpt')
                },
                {
                    'name': 'SD VAE',
                    'url': 'https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.ckpt',
                    'path': os.path.join(vae_dir, 'vae-ft-mse-840000-ema-pruned.ckpt')
                }
            ]
            
            for model in essential_models:
                if not os.path.exists(model['path']):
                    print(f"Downloading {model['name']}...")
                    # Note: In production, you'd want to implement proper download progress
                    # This is a placeholder for model download logic
                    
        except Exception as e:
            print(f"Error downloading models: {str(e)}")
    
    def start_server(self) -> Dict[str, Any]:
        """Start ComfyUI server"""
        if self.is_running:
            return {
                'success': True,
                'message': 'ComfyUI server already running',
                'url': self.server_url
            }
        
        try:
            if not self.comfyui_path or not os.path.exists(self.comfyui_path):
                return {
                    'success': False,
                    'message': 'ComfyUI not installed'
                }
            
            # Start ComfyUI server
            self.server_process = subprocess.Popen(
                ['python', self.comfyui_path, '--listen', '0.0.0.0', '--port', '8188'],
                cwd=self.comfyui_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(5)
            
            # Check if server is responding
            try:
                response = requests.get(f'{self.server_url}/system_stats', timeout=10)
                if response.status_code == 200:
                    self.is_running = True
                    return {
                        'success': True,
                        'message': 'ComfyUI server started successfully',
                        'url': self.server_url
                    }
            except:
                pass
            
            return {
                'success': False,
                'message': 'ComfyUI server failed to start'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Server start error: {str(e)}'
            }
    
    def stop_server(self) -> Dict[str, Any]:
        """Stop ComfyUI server"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.server_process = None
            
            self.is_running = False
            
            return {
                'success': True,
                'message': 'ComfyUI server stopped'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error stopping server: {str(e)}'
            }
    
    def create_workflow(self, user_id: int, name: str, description: str, 
                       workflow_json: Dict) -> ComfyUIWorkflow:
        """Create a new ComfyUI workflow"""
        try:
            workflow = ComfyUIWorkflow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                description=description,
                workflow_json=workflow_json,
                version=1,
                is_active=True
            )
            
            db.session.add(workflow)
            db.session.commit()
            
            return workflow
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create workflow: {str(e)}")
    
    def execute_workflow(self, workflow_id: str, input_data: Dict = None) -> ImageGeneration:
        """Execute a ComfyUI workflow"""
        try:
            workflow = ComfyUIWorkflow.query.get(workflow_id)
            if not workflow:
                raise ValueError("Workflow not found")
            
            generation = ImageGeneration(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                status='queued',
                input_data=input_data or {},
                created_at=datetime.now()
            )
            
            db.session.add(generation)
            db.session.commit()
            
            # Execute workflow in background
            self.active_generations[generation.id] = generation
            threading.Thread(
                target=self._execute_workflow_async,
                args=(generation.id, workflow.workflow_json, input_data)
            ).start()
            
            return generation
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to start workflow execution: {str(e)}")
    
    def _execute_workflow_async(self, generation_id: str, workflow_json: Dict, input_data: Dict):
        """Execute workflow asynchronously"""
        try:
            generation = ImageGeneration.query.get(generation_id)
            if not generation:
                return
            
            # Ensure server is running
            if not self.is_running:
                self.start_server()
                time.sleep(5)
            
            # Prepare workflow with input data
            prepared_workflow = self._prepare_workflow(workflow_json, input_data)
            
            # Submit to ComfyUI
            client_id = str(uuid.uuid4())
            
            # Queue prompt
            response = requests.post(
                f'{self.server_url}/prompt',
                json={
                    'prompt': prepared_workflow,
                    'client_id': client_id
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to queue prompt: {response.text}")
            
            prompt_id = response.json()['prompt_id']
            
            # Update generation status
            generation.status = 'processing'
            generation.prompt_id = prompt_id
            generation.started_at = datetime.now()
            db.session.commit()
            
            # Wait for completion
            result = self._wait_for_completion(prompt_id, client_id)
            
            if result['success']:
                generation.status = 'completed'
                generation.output_images = result['images']
                generation.completed_at = datetime.now()
            else:
                generation.status = 'failed'
                generation.error_message = result['error']
            
            db.session.commit()
            
        except Exception as e:
            generation.status = 'failed'
            generation.error_message = str(e)
            db.session.commit()
        
        finally:
            # Remove from active generations
            if generation_id in self.active_generations:
                del self.active_generations[generation_id]
    
    def _prepare_workflow(self, workflow_json: Dict, input_data: Dict) -> Dict:
        """Prepare workflow with input data"""
        prepared = workflow_json.copy()
        
        # Replace input placeholders with actual data
        for node_id, node in prepared.items():
            if isinstance(node, dict) and 'inputs' in node:
                for input_key, input_value in node['inputs'].items():
                    # Replace placeholders like {{prompt}} with actual values
                    if isinstance(input_value, str) and input_value.startswith('{{') and input_value.endswith('}}'):
                        placeholder = input_value[2:-2]
                        if placeholder in input_data:
                            node['inputs'][input_key] = input_data[placeholder]
        
        return prepared
    
    def _wait_for_completion(self, prompt_id: str, client_id: str) -> Dict[str, Any]:
        """Wait for workflow completion and get results"""
        try:
            # Connect to WebSocket for real-time updates
            ws = websocket.WebSocket()
            ws.connect(f'{self.ws_url}?clientId={client_id}')
            
            images = []
            
            while True:
                try:
                    message = ws.recv()
                    data = json.loads(message)
                    
                    if data['type'] == 'executing':
                        if data['data']['node'] is None:
                            # Execution finished
                            break
                    
                    elif data['type'] == 'executed':
                        # Node execution completed
                        if 'images' in data['data']['output']:
                            for image_data in data['data']['output']['images']:
                                image_url = f"{self.server_url}/view?filename={image_data['filename']}&subfolder={image_data['subfolder']}&type={image_data['type']}"
                                images.append({
                                    'filename': image_data['filename'],
                                    'url': image_url,
                                    'subfolder': image_data['subfolder'],
                                    'type': image_data['type']
                                })
                    
                    elif data['type'] == 'execution_error':
                        ws.close()
                        return {
                            'success': False,
                            'error': data['data']['error']
                        }
                    
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    ws.close()
                    return {
                        'success': False,
                        'error': str(e)
                    }
            
            ws.close()
            
            return {
                'success': True,
                'images': images
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models"""
        try:
            if not self.is_running:
                return {'error': 'ComfyUI server not running'}
            
            response = requests.get(f'{self.server_url}/object_info')
            if response.status_code != 200:
                return {'error': 'Failed to get model info'}
            
            object_info = response.json()
            
            models = {
                'checkpoints': [],
                'vae': [],
                'loras': [],
                'controlnet': [],
                'upscale_models': []
            }
            
            # Extract model lists from object info
            for node_class, node_info in object_info.items():
                if 'input' in node_info:
                    for input_name, input_info in node_info['input']['required'].items():
                        if isinstance(input_info, list) and len(input_info) > 0:
                            if 'ckpt_name' in input_name.lower():
                                models['checkpoints'].extend(input_info[0])
                            elif 'vae_name' in input_name.lower():
                                models['vae'].extend(input_info[0])
                            elif 'lora_name' in input_name.lower():
                                models['loras'].extend(input_info[0])
                            elif 'control_net_name' in input_name.lower():
                                models['controlnet'].extend(input_info[0])
                            elif 'model_name' in input_name.lower():
                                models['upscale_models'].extend(input_info[0])
            
            # Remove duplicates
            for key in models:
                models[key] = list(set(models[key]))
            
            return models
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_node_definitions(self) -> Dict[str, Any]:
        """Get available node definitions"""
        try:
            if not self.is_running:
                return {'error': 'ComfyUI server not running'}
            
            response = requests.get(f'{self.server_url}/object_info')
            if response.status_code != 200:
                return {'error': 'Failed to get node definitions'}
            
            return response.json()
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get status of image generation"""
        try:
            generation = ImageGeneration.query.get(generation_id)
            if not generation:
                return {'error': 'Generation not found'}
            
            result = {
                'id': generation.id,
                'status': generation.status,
                'created_at': generation.created_at.isoformat(),
                'started_at': generation.started_at.isoformat() if generation.started_at else None,
                'completed_at': generation.completed_at.isoformat() if generation.completed_at else None,
                'error_message': generation.error_message,
                'input_data': generation.input_data,
                'output_images': generation.output_images
            }
            
            # Get queue position if still queued
            if generation.status == 'queued' and generation.prompt_id:
                try:
                    queue_response = requests.get(f'{self.server_url}/queue')
                    if queue_response.status_code == 200:
                        queue_data = queue_response.json()
                        for i, item in enumerate(queue_data['queue_running'] + queue_data['queue_pending']):
                            if item[1] == generation.prompt_id:
                                result['queue_position'] = i + 1
                                break
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def cancel_generation(self, generation_id: str) -> Dict[str, Any]:
        """Cancel a running generation"""
        try:
            generation = ImageGeneration.query.get(generation_id)
            if not generation:
                return {'success': False, 'message': 'Generation not found'}
            
            if generation.status not in ['queued', 'processing']:
                return {'success': False, 'message': 'Generation cannot be cancelled'}
            
            # Cancel in ComfyUI
            if generation.prompt_id:
                try:
                    requests.post(f'{self.server_url}/interrupt')
                    requests.delete(f'{self.server_url}/queue', json={'delete': [generation.prompt_id]})
                except:
                    pass
            
            # Update status
            generation.status = 'cancelled'
            generation.completed_at = datetime.now()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Generation cancelled'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_workflow_templates(self) -> List[Dict[str, Any]]:
        """Get built-in workflow templates"""
        templates = [
            {
                'id': 'txt2img_basic',
                'name': 'Text to Image (Basic)',
                'description': 'Basic text-to-image generation',
                'category': 'generation',
                'workflow': {
                    '1': {
                        'inputs': {
                            'ckpt_name': 'v1-5-pruned-emaonly.ckpt'
                        },
                        'class_type': 'CheckpointLoaderSimple'
                    },
                    '2': {
                        'inputs': {
                            'text': '{{prompt}}',
                            'clip': ['1', 1]
                        },
                        'class_type': 'CLIPTextEncode'
                    },
                    '3': {
                        'inputs': {
                            'text': '{{negative_prompt}}',
                            'clip': ['1', 1]
                        },
                        'class_type': 'CLIPTextEncode'
                    },
                    '4': {
                        'inputs': {
                            'width': 512,
                            'height': 512,
                            'batch_size': 1
                        },
                        'class_type': 'EmptyLatentImage'
                    },
                    '5': {
                        'inputs': {
                            'seed': 0,
                            'steps': 20,
                            'cfg': 7,
                            'sampler_name': 'euler',
                            'scheduler': 'normal',
                            'denoise': 1,
                            'model': ['1', 0],
                            'positive': ['2', 0],
                            'negative': ['3', 0],
                            'latent_image': ['4', 0]
                        },
                        'class_type': 'KSampler'
                    },
                    '6': {
                        'inputs': {
                            'samples': ['5', 0],
                            'vae': ['1', 2]
                        },
                        'class_type': 'VAEDecode'
                    },
                    '7': {
                        'inputs': {
                            'filename_prefix': 'ComfyUI',
                            'images': ['6', 0]
                        },
                        'class_type': 'SaveImage'
                    }
                }
            },
            {
                'id': 'img2img_basic',
                'name': 'Image to Image (Basic)',
                'description': 'Basic image-to-image generation',
                'category': 'generation',
                'workflow': {
                    # Similar structure but with image input
                }
            },
            {
                'id': 'upscale_basic',
                'name': 'Image Upscale (Basic)',
                'description': 'Basic image upscaling',
                'category': 'upscale',
                'workflow': {
                    # Upscaling workflow
                }
            }
        ]
        
        return templates
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get ComfyUI server status"""
        try:
            if not self.is_running:
                return {
                    'running': False,
                    'message': 'Server not running'
                }
            
            # Check server health
            response = requests.get(f'{self.server_url}/system_stats', timeout=5)
            if response.status_code == 200:
                stats = response.json()
                return {
                    'running': True,
                    'url': self.server_url,
                    'stats': stats
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
    
    def get_user_workflows(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's ComfyUI workflows"""
        try:
            workflows = ComfyUIWorkflow.query.filter_by(user_id=user_id, is_active=True).all()
            
            result = []
            for workflow in workflows:
                # Get recent generations
                recent_generations = ImageGeneration.query.filter_by(
                    workflow_id=workflow.id
                ).order_by(ImageGeneration.created_at.desc()).limit(5).all()
                
                result.append({
                    'id': workflow.id,
                    'name': workflow.name,
                    'description': workflow.description,
                    'version': workflow.version,
                    'created_at': workflow.created_at.isoformat(),
                    'updated_at': workflow.updated_at.isoformat(),
                    'recent_generations': [
                        {
                            'id': gen.id,
                            'status': gen.status,
                            'created_at': gen.created_at.isoformat(),
                            'completed_at': gen.completed_at.isoformat() if gen.completed_at else None
                        }
                        for gen in recent_generations
                    ]
                })
            
            return result
            
        except Exception as e:
            return []