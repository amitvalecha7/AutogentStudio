import os
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import WorkflowTemplate, WorkflowExecution, WorkflowNode, WorkflowConnection
from app import db
import requests
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time

class DrawflowService:
    """Service for Drawflow visual workflow editor integration"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.active_executions = {}
        self.node_registry = self._initialize_node_registry()
    
    def _initialize_node_registry(self) -> Dict[str, Dict]:
        """Initialize registry of available workflow nodes"""
        return {
            # AI Model Nodes
            'openai_chat': {
                'name': 'OpenAI Chat',
                'category': 'ai_models',
                'inputs': ['prompt', 'system_message', 'temperature'],
                'outputs': ['response', 'tokens_used'],
                'icon': 'cpu',
                'description': 'Generate text using OpenAI GPT models'
            },
            'claude_chat': {
                'name': 'Claude Chat',
                'category': 'ai_models',
                'inputs': ['prompt', 'system_message', 'temperature'],
                'outputs': ['response', 'tokens_used'],
                'icon': 'cpu',
                'description': 'Generate text using Anthropic Claude models'
            },
            'google_ai_chat': {
                'name': 'Google AI Chat',
                'category': 'ai_models',
                'inputs': ['prompt', 'system_message', 'temperature'],
                'outputs': ['response', 'tokens_used'],
                'icon': 'cpu',
                'description': 'Generate text using Google AI models'
            },
            
            # Image Generation Nodes
            'dalle_image': {
                'name': 'DALL-E Image',
                'category': 'image_generation',
                'inputs': ['prompt', 'size', 'quality'],
                'outputs': ['image_url', 'image_data'],
                'icon': 'image',
                'description': 'Generate images using DALL-E'
            },
            'midjourney_image': {
                'name': 'Midjourney Image',
                'category': 'image_generation',
                'inputs': ['prompt', 'aspect_ratio', 'style'],
                'outputs': ['image_url', 'job_id'],
                'icon': 'image',
                'description': 'Generate images using Midjourney'
            },
            'comfyui_workflow': {
                'name': 'ComfyUI Workflow',
                'category': 'image_generation',
                'inputs': ['workflow_json', 'input_image', 'prompt'],
                'outputs': ['output_image', 'execution_id'],
                'icon': 'layers',
                'description': 'Execute ComfyUI workflows'
            },
            
            # Data Processing Nodes
            'text_splitter': {
                'name': 'Text Splitter',
                'category': 'data_processing',
                'inputs': ['text', 'chunk_size', 'overlap'],
                'outputs': ['chunks'],
                'icon': 'scissors',
                'description': 'Split text into chunks'
            },
            'json_parser': {
                'name': 'JSON Parser',
                'category': 'data_processing',
                'inputs': ['json_string', 'path'],
                'outputs': ['parsed_data'],
                'icon': 'code',
                'description': 'Parse and extract data from JSON'
            },
            'file_reader': {
                'name': 'File Reader',
                'category': 'data_processing',
                'inputs': ['file_path', 'encoding'],
                'outputs': ['content'],
                'icon': 'file-text',
                'description': 'Read content from files'
            },
            
            # Logic and Control Nodes
            'condition': {
                'name': 'Condition',
                'category': 'logic',
                'inputs': ['input_value', 'condition', 'comparison_value'],
                'outputs': ['true_output', 'false_output'],
                'icon': 'git-branch',
                'description': 'Branch workflow based on conditions'
            },
            'loop': {
                'name': 'Loop',
                'category': 'logic',
                'inputs': ['input_array', 'max_iterations'],
                'outputs': ['current_item', 'iteration_count', 'results'],
                'icon': 'repeat',
                'description': 'Iterate over data'
            },
            'delay': {
                'name': 'Delay',
                'category': 'logic',
                'inputs': ['duration_seconds'],
                'outputs': ['completed'],
                'icon': 'clock',
                'description': 'Add delay to workflow'
            },
            
            # API and Integration Nodes
            'http_request': {
                'name': 'HTTP Request',
                'category': 'integrations',
                'inputs': ['url', 'method', 'headers', 'body'],
                'outputs': ['response', 'status_code'],
                'icon': 'globe',
                'description': 'Make HTTP requests to external APIs'
            },
            'webhook': {
                'name': 'Webhook',
                'category': 'integrations',
                'inputs': ['webhook_url', 'payload'],
                'outputs': ['response'],
                'icon': 'send',
                'description': 'Send data to webhook endpoints'
            },
            'email_sender': {
                'name': 'Email Sender',
                'category': 'integrations',
                'inputs': ['to_email', 'subject', 'body'],
                'outputs': ['sent_status'],
                'icon': 'mail',
                'description': 'Send email notifications'
            },
            
            # Knowledge Base Nodes
            'rag_query': {
                'name': 'RAG Query',
                'category': 'knowledge_base',
                'inputs': ['query', 'knowledge_base_id', 'max_results'],
                'outputs': ['relevant_docs', 'context'],
                'icon': 'search',
                'description': 'Query knowledge base using RAG'
            },
            'embed_text': {
                'name': 'Embed Text',
                'category': 'knowledge_base',
                'inputs': ['text', 'model'],
                'outputs': ['embedding'],
                'icon': 'hash',
                'description': 'Generate text embeddings'
            },
            
            # Quantum Computing Nodes
            'quantum_circuit': {
                'name': 'Quantum Circuit',
                'category': 'quantum',
                'inputs': ['circuit_definition', 'shots'],
                'outputs': ['measurement_results', 'quantum_state'],
                'icon': 'zap',
                'description': 'Execute quantum circuits'
            },
            'quantum_optimization': {
                'name': 'Quantum Optimization',
                'category': 'quantum',
                'inputs': ['objective_function', 'constraints'],
                'outputs': ['optimal_solution'],
                'icon': 'target',
                'description': 'Solve optimization problems using quantum algorithms'
            }
        }
    
    def get_node_categories(self) -> Dict[str, List[Dict]]:
        """Get available node categories and nodes"""
        categories = {}
        for node_id, node_info in self.node_registry.items():
            category = node_info['category']
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'id': node_id,
                'name': node_info['name'],
                'icon': node_info['icon'],
                'description': node_info['description'],
                'inputs': node_info['inputs'],
                'outputs': node_info['outputs']
            })
        
        return categories
    
    def create_workflow_template(self, user_id: int, name: str, description: str, 
                               drawflow_data: Dict) -> WorkflowTemplate:
        """Create a new workflow template"""
        try:
            # Validate drawflow data
            if not self._validate_drawflow_data(drawflow_data):
                raise ValueError("Invalid drawflow data structure")
            
            template = WorkflowTemplate(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                description=description,
                drawflow_data=drawflow_data,
                version=1,
                is_active=True
            )
            
            db.session.add(template)
            db.session.commit()
            
            return template
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create workflow template: {str(e)}")
    
    def update_workflow_template(self, template_id: str, drawflow_data: Dict, 
                               increment_version: bool = True) -> WorkflowTemplate:
        """Update existing workflow template"""
        try:
            template = WorkflowTemplate.query.get(template_id)
            if not template:
                raise ValueError("Workflow template not found")
            
            if not self._validate_drawflow_data(drawflow_data):
                raise ValueError("Invalid drawflow data structure")
            
            template.drawflow_data = drawflow_data
            template.updated_at = datetime.now()
            
            if increment_version:
                template.version += 1
            
            db.session.commit()
            return template
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update workflow template: {str(e)}")
    
    def execute_workflow(self, template_id: str, input_data: Dict = None) -> WorkflowExecution:
        """Execute a workflow template"""
        try:
            template = WorkflowTemplate.query.get(template_id)
            if not template:
                raise ValueError("Workflow template not found")
            
            execution = WorkflowExecution(
                id=str(uuid.uuid4()),
                template_id=template_id,
                status='running',
                input_data=input_data or {},
                started_at=datetime.now()
            )
            
            db.session.add(execution)
            db.session.commit()
            
            # Start workflow execution in background
            self.active_executions[execution.id] = execution
            self.executor.submit(self._execute_workflow_async, execution.id, template.drawflow_data)
            
            return execution
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to start workflow execution: {str(e)}")
    
    def _execute_workflow_async(self, execution_id: str, drawflow_data: Dict):
        """Execute workflow asynchronously"""
        try:
            execution = WorkflowExecution.query.get(execution_id)
            if not execution:
                return
            
            # Parse drawflow data and create execution graph
            nodes = drawflow_data.get('drawflow', {}).get('Home', {}).get('data', {})
            
            # Build execution order based on connections
            execution_order = self._build_execution_order(nodes)
            
            # Execute nodes in order
            node_outputs = {}
            
            for node_id in execution_order:
                node_data = nodes[node_id]
                node_type = node_data.get('name', '')
                
                try:
                    # Get node inputs from connections
                    node_inputs = self._get_node_inputs(node_id, nodes, node_outputs)
                    
                    # Execute node
                    node_result = self._execute_node(node_type, node_inputs, node_data.get('data', {}))
                    node_outputs[node_id] = node_result
                    
                    # Update execution progress
                    execution.progress = len(node_outputs) / len(execution_order) * 100
                    db.session.commit()
                    
                except Exception as e:
                    # Node execution failed
                    execution.status = 'failed'
                    execution.error_message = f"Node {node_id} failed: {str(e)}"
                    execution.completed_at = datetime.now()
                    db.session.commit()
                    return
            
            # Workflow completed successfully
            execution.status = 'completed'
            execution.output_data = node_outputs
            execution.completed_at = datetime.now()
            execution.progress = 100
            db.session.commit()
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            db.session.commit()
        
        finally:
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    def _validate_drawflow_data(self, drawflow_data: Dict) -> bool:
        """Validate drawflow data structure"""
        try:
            if not isinstance(drawflow_data, dict):
                return False
            
            if 'drawflow' not in drawflow_data:
                return False
            
            drawflow = drawflow_data['drawflow']
            if not isinstance(drawflow, dict) or 'Home' not in drawflow:
                return False
            
            home = drawflow['Home']
            if not isinstance(home, dict) or 'data' not in home:
                return False
            
            # Validate nodes structure
            nodes = home['data']
            if not isinstance(nodes, dict):
                return False
            
            for node_id, node_data in nodes.items():
                if not isinstance(node_data, dict):
                    return False
                
                required_fields = ['name', 'class', 'html', 'typenode', 'inputs', 'outputs', 'pos_x', 'pos_y']
                for field in required_fields:
                    if field not in node_data:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _build_execution_order(self, nodes: Dict) -> List[str]:
        """Build execution order based on node connections"""
        # Simple topological sort
        in_degree = {node_id: 0 for node_id in nodes.keys()}
        adjacency = {node_id: [] for node_id in nodes.keys()}
        
        # Build graph
        for node_id, node_data in nodes.items():
            outputs = node_data.get('outputs', {})
            for output_name, output_data in outputs.items():
                connections = output_data.get('connections', [])
                for connection in connections:
                    target_node = connection.get('node')
                    if target_node and target_node in nodes:
                        adjacency[node_id].append(target_node)
                        in_degree[target_node] += 1
        
        # Topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            node_id = queue.pop(0)
            execution_order.append(node_id)
            
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return execution_order
    
    def _get_node_inputs(self, node_id: str, nodes: Dict, node_outputs: Dict) -> Dict:
        """Get inputs for a node from connected outputs"""
        node_data = nodes[node_id]
        inputs = {}
        
        node_inputs = node_data.get('inputs', {})
        for input_name, input_data in node_inputs.items():
            connections = input_data.get('connections', [])
            if connections:
                # Get value from first connection
                connection = connections[0]
                source_node = connection.get('node')
                source_output = connection.get('output')
                
                if source_node in node_outputs and source_output in node_outputs[source_node]:
                    inputs[input_name] = node_outputs[source_node][source_output]
        
        return inputs
    
    def _execute_node(self, node_type: str, inputs: Dict, node_config: Dict) -> Dict:
        """Execute a single node"""
        if node_type not in self.node_registry:
            raise ValueError(f"Unknown node type: {node_type}")
        
        # Import services dynamically
        from services.ai_providers import AIProvidersService
        from services.rag_service import RAGService
        
        ai_service = AIProvidersService()
        rag_service = RAGService()
        
        try:
            if node_type == 'openai_chat':
                return self._execute_openai_chat(ai_service, inputs, node_config)
            elif node_type == 'claude_chat':
                return self._execute_claude_chat(ai_service, inputs, node_config)
            elif node_type == 'text_splitter':
                return self._execute_text_splitter(inputs, node_config)
            elif node_type == 'condition':
                return self._execute_condition(inputs, node_config)
            elif node_type == 'delay':
                return self._execute_delay(inputs, node_config)
            elif node_type == 'rag_query':
                return self._execute_rag_query(rag_service, inputs, node_config)
            elif node_type == 'http_request':
                return self._execute_http_request(inputs, node_config)
            else:
                return {'error': f'Node type {node_type} not implemented yet'}
                
        except Exception as e:
            raise Exception(f"Node execution failed: {str(e)}")
    
    def _execute_openai_chat(self, ai_service: Any, inputs: Dict, config: Dict) -> Dict:
        """Execute OpenAI chat node"""
        prompt = inputs.get('prompt', config.get('prompt', ''))
        system_message = inputs.get('system_message', config.get('system_message', ''))
        temperature = float(inputs.get('temperature', config.get('temperature', 0.7)))
        
        response = ai_service.chat_completion(
            provider='openai',
            model='gpt-4',
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': prompt}
            ],
            temperature=temperature
        )
        
        return {
            'response': response.get('content', ''),
            'tokens_used': response.get('usage', {}).get('total_tokens', 0)
        }
    
    def _execute_claude_chat(self, ai_service: Any, inputs: Dict, config: Dict) -> Dict:
        """Execute Claude chat node"""
        prompt = inputs.get('prompt', config.get('prompt', ''))
        system_message = inputs.get('system_message', config.get('system_message', ''))
        temperature = float(inputs.get('temperature', config.get('temperature', 0.7)))
        
        response = ai_service.chat_completion(
            provider='anthropic',
            model='claude-3-sonnet-20240229',
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': prompt}
            ],
            temperature=temperature
        )
        
        return {
            'response': response.get('content', ''),
            'tokens_used': response.get('usage', {}).get('total_tokens', 0)
        }
    
    def _execute_text_splitter(self, inputs: Dict, config: Dict) -> Dict:
        """Execute text splitter node"""
        text = inputs.get('text', config.get('text', ''))
        chunk_size = int(inputs.get('chunk_size', config.get('chunk_size', 1000)))
        overlap = int(inputs.get('overlap', config.get('overlap', 200)))
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > start + chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return {'chunks': [chunk for chunk in chunks if chunk.strip()]}
    
    def _execute_condition(self, inputs: Dict, config: Dict) -> Dict:
        """Execute condition node"""
        input_value = inputs.get('input_value', config.get('input_value'))
        condition = config.get('condition', 'equals')
        comparison_value = inputs.get('comparison_value', config.get('comparison_value'))
        
        result = False
        if condition == 'equals':
            result = str(input_value) == str(comparison_value)
        elif condition == 'not_equals':
            result = str(input_value) != str(comparison_value)
        elif condition == 'greater_than':
            result = float(input_value) > float(comparison_value)
        elif condition == 'less_than':
            result = float(input_value) < float(comparison_value)
        elif condition == 'contains':
            result = str(comparison_value) in str(input_value)
        
        if result:
            return {'true_output': input_value, 'false_output': None}
        else:
            return {'true_output': None, 'false_output': input_value}
    
    def _execute_delay(self, inputs: Dict, config: Dict) -> Dict:
        """Execute delay node"""
        duration = float(inputs.get('duration_seconds', config.get('duration_seconds', 1)))
        time.sleep(duration)
        return {'completed': True}
    
    def _execute_rag_query(self, rag_service: Any, inputs: Dict, config: Dict) -> Dict:
        """Execute RAG query node"""
        query = inputs.get('query', config.get('query', ''))
        knowledge_base_id = inputs.get('knowledge_base_id', config.get('knowledge_base_id', ''))
        max_results = int(inputs.get('max_results', config.get('max_results', 5)))
        
        try:
            results = rag_service.search_knowledge_base(knowledge_base_id, query, max_results)
            context = rag_service.get_relevant_context(knowledge_base_id, query)
            
            return {
                'relevant_docs': results,
                'context': context
            }
        except Exception as e:
            return {
                'relevant_docs': [],
                'context': f"Error: {str(e)}"
            }
    
    def _execute_http_request(self, inputs: Dict, config: Dict) -> Dict:
        """Execute HTTP request node"""
        url = inputs.get('url', config.get('url', ''))
        method = inputs.get('method', config.get('method', 'GET')).upper()
        headers = inputs.get('headers', config.get('headers', {}))
        body = inputs.get('body', config.get('body'))
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=body, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=body, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return {
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'response': f"Request failed: {str(e)}",
                'status_code': 0
            }
    
    def get_workflow_execution_status(self, execution_id: str) -> Dict:
        """Get status of workflow execution"""
        execution = WorkflowExecution.query.get(execution_id)
        if not execution:
            return {'error': 'Execution not found'}
        
        return {
            'id': execution.id,
            'status': execution.status,
            'progress': execution.progress,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'input_data': execution.input_data,
            'output_data': execution.output_data
        }
    
    def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel running workflow execution"""
        try:
            execution = WorkflowExecution.query.get(execution_id)
            if not execution:
                return False
            
            if execution.status == 'running':
                execution.status = 'cancelled'
                execution.completed_at = datetime.now()
                db.session.commit()
                
                # Remove from active executions
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
                
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_user_workflows(self, user_id: int) -> List[Dict]:
        """Get all workflow templates for a user"""
        templates = WorkflowTemplate.query.filter_by(user_id=user_id, is_active=True).all()
        
        result = []
        for template in templates:
            # Get recent executions
            recent_executions = WorkflowExecution.query.filter_by(
                template_id=template.id
            ).order_by(WorkflowExecution.created_at.desc()).limit(5).all()
            
            result.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'version': template.version,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat(),
                'recent_executions': [
                    {
                        'id': exec.id,
                        'status': exec.status,
                        'started_at': exec.started_at.isoformat() if exec.started_at else None,
                        'completed_at': exec.completed_at.isoformat() if exec.completed_at else None
                    }
                    for exec in recent_executions
                ]
            })
        
        return result