import os
import logging
from typing import Dict, List, Any, Optional, Union
import json
import asyncio
import time
from datetime import datetime
import uuid

# Import AI provider services
from services.ai_providers import generate_response, generate_image, get_embedding
from services.quantum_service import execute_circuit
from services.federated_service import aggregate_models
from services.neuromorphic_service import deploy_snn_model
from services.safety_service import run_alignment_check

class WorkflowNode:
    """Base class for workflow nodes"""
    
    def __init__(self, node_id: str, node_type: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
        self.inputs = {}
        self.outputs = {}
        self.status = 'ready'
        self.execution_time = 0.0
        self.error_message = None
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node with given inputs"""
        self.status = 'running'
        start_time = time.time()
        
        try:
            self.inputs = inputs
            result = await self._process(inputs)
            self.outputs = result
            self.status = 'completed'
            
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            self.outputs = {'error': str(e)}
            logging.error(f"Node {self.node_id} execution failed: {e}")
        
        self.execution_time = time.time() - start_time
        return self.outputs
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method in subclasses"""
        raise NotImplementedError

class TextInputNode(WorkflowNode):
    """Input node for text data"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = self.config.get('default_text', inputs.get('text', ''))
        return {'text': text, 'type': 'text'}

class AIModelNode(WorkflowNode):
    """Node for AI model inference"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        provider = self.config.get('provider', 'openai')
        model = self.config.get('model', 'gpt-4o')
        temperature = self.config.get('temperature', 0.7)
        max_tokens = self.config.get('max_tokens', 2048)
        
        # Get input text
        text = inputs.get('text', '')
        if not text:
            raise ValueError("No input text provided")
        
        # Prepare messages
        messages = [{'role': 'user', 'content': text}]
        
        # Add system prompt if configured
        system_prompt = self.config.get('system_prompt')
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Generate response
        response = generate_response(
            provider=provider,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'text': response,
            'type': 'ai_response',
            'provider': provider,
            'model': model
        }

class TextProcessingNode(WorkflowNode):
    """Node for text processing operations"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get('text', '')
        operation = self.config.get('operation', 'passthrough')
        
        if operation == 'split':
            delimiter = self.config.get('delimiter', '\n')
            result = text.split(delimiter)
            return {'chunks': result, 'type': 'text_chunks'}
        
        elif operation == 'summarize':
            # Use configured length or default
            max_length = self.config.get('max_length', 100)
            words = text.split()
            summary = ' '.join(words[:max_length])
            return {'text': summary, 'type': 'summary'}
        
        elif operation == 'extract_keywords':
            # Simple keyword extraction
            words = text.lower().split()
            # Filter out common words
            common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            keywords = [word for word in set(words) if len(word) > 3 and word not in common_words]
            return {'keywords': keywords[:10], 'type': 'keywords'}
        
        else:
            return {'text': text, 'type': 'text'}

class EmbeddingNode(WorkflowNode):
    """Node for generating text embeddings"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get('text', '')
        model = self.config.get('model', 'text-embedding-3-small')
        
        if not text:
            raise ValueError("No input text provided")
        
        # Generate embedding
        embedding = get_embedding(text, model)
        
        return {
            'embedding': embedding,
            'text': text,
            'model': model,
            'type': 'embedding'
        }

class VectorSearchNode(WorkflowNode):
    """Node for vector similarity search"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query_embedding = inputs.get('embedding')
        knowledge_base_id = self.config.get('knowledge_base_id')
        top_k = self.config.get('top_k', 5)
        
        if not query_embedding:
            raise ValueError("No query embedding provided")
        
        # Simulate vector search (in real implementation, use actual vector DB)
        from services.vector_db import search_similar_chunks
        
        if knowledge_base_id:
            results = search_similar_chunks("", knowledge_base_id, top_k)
        else:
            # Mock results
            results = [
                {'content': 'Sample result 1', 'score': 0.95},
                {'content': 'Sample result 2', 'score': 0.88}
            ]
        
        return {
            'search_results': results,
            'query_embedding': query_embedding,
            'type': 'search_results'
        }

class QuantumNode(WorkflowNode):
    """Node for quantum computing operations"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        circuit_type = self.config.get('circuit_type', 'bell_state')
        num_qubits = self.config.get('num_qubits', 2)
        shots = self.config.get('shots', 1000)
        
        # Create quantum circuit
        from services.quantum_service import create_circuit
        circuit_data = create_circuit(circuit_type, num_qubits)
        
        # Execute circuit
        results = execute_circuit(circuit_data['circuit_data'], shots=shots)
        
        return {
            'quantum_results': results,
            'circuit_type': circuit_type,
            'num_qubits': num_qubits,
            'type': 'quantum_results'
        }

class FederatedNode(WorkflowNode):
    """Node for federated learning operations"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        operation = self.config.get('operation', 'aggregate')
        
        if operation == 'aggregate':
            # Mock model updates for aggregation
            model_updates = [
                {'parameters': [[0.1, 0.2], [0.3, 0.4]], 'samples': 100},
                {'parameters': [[0.15, 0.25], [0.35, 0.45]], 'samples': 120}
            ]
            
            aggregation_result = aggregate_models(model_updates)
            
            return {
                'aggregated_model': aggregation_result,
                'operation': operation,
                'type': 'federated_result'
            }
        
        return {'type': 'federated_result', 'operation': operation}

class NeuromorphicNode(WorkflowNode):
    """Node for neuromorphic computing operations"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        operation = self.config.get('operation', 'deploy')
        device_type = self.config.get('device_type', 'loihi')
        
        if operation == 'deploy':
            # Mock SNN model for deployment
            snn_model = {
                'num_neurons': self.config.get('num_neurons', 1000),
                'num_synapses': self.config.get('num_synapses', 10000),
                'learning_rules': ['STDP']
            }
            
            deployment_result = deploy_snn_model(snn_model, device_type)
            
            return {
                'deployment_result': deployment_result,
                'device_type': device_type,
                'type': 'neuromorphic_result'
            }
        
        return {'type': 'neuromorphic_result', 'operation': operation}

class SafetyNode(WorkflowNode):
    """Node for AI safety checks"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        content = inputs.get('text', '')
        check_type = self.config.get('check_type', 'general')
        
        if not content:
            raise ValueError("No content provided for safety check")
        
        # Run safety check
        safety_result = run_alignment_check(check_type, content)
        
        return {
            'safety_result': safety_result,
            'content_checked': content,
            'check_type': check_type,
            'type': 'safety_result'
        }

class ImageGenerationNode(WorkflowNode):
    """Node for AI image generation"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = inputs.get('text', self.config.get('prompt', ''))
        provider = self.config.get('provider', 'openai')
        model = self.config.get('model', 'dall-e-3')
        style = self.config.get('style', 'realistic')
        size = self.config.get('size', '1024x1024')
        
        if not prompt:
            raise ValueError("No prompt provided for image generation")
        
        # Generate image
        result = generate_image(
            prompt=prompt,
            provider=provider,
            model=model,
            style=style,
            size=size
        )
        
        return {
            'image_url': result['url'],
            'prompt': prompt,
            'provider': provider,
            'model': model,
            'type': 'image'
        }

class OutputNode(WorkflowNode):
    """Output node to collect final results"""
    
    async def _process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        output_format = self.config.get('format', 'json')
        
        # Format the output based on configuration
        if output_format == 'text':
            text_content = inputs.get('text', str(inputs))
            return {'output': text_content, 'format': 'text'}
        
        elif output_format == 'structured':
            return {'output': inputs, 'format': 'structured'}
        
        else:  # json
            return {'output': inputs, 'format': 'json'}

class WorkflowOrchestrator:
    """Main workflow orchestration engine"""
    
    def __init__(self):
        self.node_types = {
            'text_input': TextInputNode,
            'ai_model': AIModelNode,
            'text_processing': TextProcessingNode,
            'embedding': EmbeddingNode,
            'vector_search': VectorSearchNode,
            'quantum': QuantumNode,
            'federated': FederatedNode,
            'neuromorphic': NeuromorphicNode,
            'safety': SafetyNode,
            'image_generation': ImageGenerationNode,
            'output': OutputNode
        }
    
    def parse_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, WorkflowNode]:
        """Parse workflow data into node objects"""
        nodes = {}
        
        drawflow_data = workflow_data.get('drawflow', {})
        home_data = drawflow_data.get('Home', {}).get('data', {})
        
        for node_id, node_data in home_data.items():
            node_name = node_data.get('name', 'unknown')
            node_config = node_data.get('data', {})
            
            # Map node names to types
            node_type = self.map_node_name_to_type(node_name)
            
            if node_type in self.node_types:
                node_class = self.node_types[node_type]
                nodes[node_id] = node_class(node_id, node_type, node_config)
            else:
                logging.warning(f"Unknown node type: {node_type}")
        
        return nodes
    
    def map_node_name_to_type(self, node_name: str) -> str:
        """Map Drawflow node names to internal node types"""
        name_mapping = {
            'text_input': 'text_input',
            'openai_gpt4': 'ai_model',
            'claude_sonnet4': 'ai_model',
            'gemini_15_pro': 'ai_model',
            'text_splitter': 'text_processing',
            'embedder': 'embedding',
            'vector_search': 'vector_search',
            'quantum_circuit': 'quantum',
            'fed_aggregator': 'federated',
            'snn_processor': 'neuromorphic',
            'alignment_check': 'safety',
            'image_generator': 'image_generation',
            'text_output': 'output'
        }
        
        return name_mapping.get(node_name, 'text_processing')
    
    def build_execution_graph(self, nodes: Dict[str, WorkflowNode], 
                             workflow_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build execution dependency graph"""
        graph = {node_id: [] for node_id in nodes.keys()}
        
        drawflow_data = workflow_data.get('drawflow', {})
        home_data = drawflow_data.get('Home', {}).get('data', {})
        
        # Build connections
        for node_id, node_data in home_data.items():
            outputs = node_data.get('outputs', {})
            
            for output_name, output_data in outputs.items():
                connections = output_data.get('connections', [])
                
                for connection in connections:
                    target_node = connection.get('node')
                    if target_node and target_node in nodes:
                        graph[target_node].append(node_id)
        
        return graph
    
    def find_execution_order(self, graph: Dict[str, List[str]]) -> List[str]:
        """Find topological execution order"""
        # Simple topological sort
        in_degree = {node: len(deps) for node, deps in graph.items()}
        queue = [node for node, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            node = queue.pop(0)
            execution_order.append(node)
            
            # Update in-degrees
            for other_node, deps in graph.items():
                if node in deps:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        return execution_order
    
    async def execute_workflow(self, workflow_data: Dict[str, Any], 
                              input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute complete workflow"""
        try:
            # Parse workflow
            nodes = self.parse_workflow(workflow_data)
            if not nodes:
                raise ValueError("No valid nodes found in workflow")
            
            # Build execution graph
            graph = self.build_execution_graph(nodes, workflow_data)
            
            # Find execution order
            execution_order = self.find_execution_order(graph)
            
            # Execute nodes in order
            node_outputs = {}
            workflow_start_time = time.time()
            
            for node_id in execution_order:
                node = nodes[node_id]
                
                # Prepare inputs for this node
                node_inputs = self.prepare_node_inputs(node_id, graph, node_outputs, input_data)
                
                # Execute node
                try:
                    result = await node.execute(node_inputs)
                    node_outputs[node_id] = result
                    logging.info(f"Node {node_id} completed successfully")
                    
                except Exception as e:
                    logging.error(f"Node {node_id} failed: {e}")
                    node_outputs[node_id] = {'error': str(e)}
                    
                    # Decide whether to continue or stop
                    if node.config.get('critical', False):
                        raise Exception(f"Critical node {node_id} failed: {e}")
            
            workflow_execution_time = time.time() - workflow_start_time
            
            # Prepare final result
            result = {
                'success': True,
                'execution_time': workflow_execution_time,
                'nodes_executed': len(execution_order),
                'node_results': node_outputs,
                'final_output': self.extract_final_output(node_outputs, execution_order),
                'execution_order': execution_order,
                'workflow_id': str(uuid.uuid4()),
                'executed_at': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Workflow execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
    
    def prepare_node_inputs(self, node_id: str, graph: Dict[str, List[str]], 
                           node_outputs: Dict[str, Any], 
                           initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare inputs for a node based on its dependencies"""
        dependencies = graph.get(node_id, [])
        
        if not dependencies:
            # Input node - use initial input data
            return initial_input or {}
        
        # Aggregate outputs from dependency nodes
        aggregated_inputs = {}
        
        for dep_node_id in dependencies:
            if dep_node_id in node_outputs:
                dep_output = node_outputs[dep_node_id]
                
                # Merge outputs intelligently
                if 'text' in dep_output:
                    aggregated_inputs['text'] = dep_output['text']
                if 'embedding' in dep_output:
                    aggregated_inputs['embedding'] = dep_output['embedding']
                if 'search_results' in dep_output:
                    aggregated_inputs['search_results'] = dep_output['search_results']
                if 'image_url' in dep_output:
                    aggregated_inputs['image_url'] = dep_output['image_url']
                
                # Include all outputs for flexibility
                aggregated_inputs[f'{dep_node_id}_output'] = dep_output
        
        return aggregated_inputs
    
    def extract_final_output(self, node_outputs: Dict[str, Any], 
                           execution_order: List[str]) -> Any:
        """Extract the final output from workflow execution"""
        # Find output nodes
        output_nodes = []
        for node_id, output in node_outputs.items():
            if output.get('type') in ['output', 'text', 'image', 'ai_response']:
                output_nodes.append((node_id, output))
        
        if output_nodes:
            # Return the last output node result
            return output_nodes[-1][1]
        
        # If no specific output node, return the last executed node's output
        if execution_order and execution_order[-1] in node_outputs:
            return node_outputs[execution_order[-1]]
        
        return {"message": "Workflow completed but no output generated"}

# Main execution function
async def execute_workflow_flow(workflow_data: Dict[str, Any], 
                               input_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute workflow with given data and inputs"""
    try:
        orchestrator = WorkflowOrchestrator()
        result = await orchestrator.execute_workflow(workflow_data, input_data)
        return result
        
    except Exception as e:
        logging.error(f"Error executing workflow: {e}")
        return {
            'success': False,
            'error': str(e),
            'executed_at': datetime.utcnow().isoformat()
        }

# Synchronous wrapper for Flask integration
def execute_workflow_sync(workflow_data: Dict[str, Any], 
                         input_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Synchronous wrapper for workflow execution"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Execute workflow
        result = loop.run_until_complete(
            execute_workflow_flow(workflow_data, input_data)
        )
        
        loop.close()
        return result
        
    except Exception as e:
        logging.error(f"Error in synchronous workflow execution: {e}")
        return {
            'success': False,
            'error': str(e),
            'executed_at': datetime.utcnow().isoformat()
        }

