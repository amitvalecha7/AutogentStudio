from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import *
from services.openai_service import OpenAIService
from services.anthropic_service import AnthropicService
from services.quantum_service import QuantumService
from services.neuromorphic_service import NeuromorphicService
from services.safety_service import SafetyService
from services.blockchain_service import BlockchainService
from utils.rag_processor import RAGProcessor
from app import db
import logging
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Initialize services
openai_service = OpenAIService()
anthropic_service = AnthropicService()
quantum_service = QuantumService()
neuromorphic_service = NeuromorphicService()
safety_service = SafetyService()
blockchain_service = BlockchainService()
rag_processor = RAGProcessor()

@api_bp.route('/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'Autogent Studio API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/chat/completions', methods=['POST'])
@login_required
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    try:
        data = request.get_json()
        
        messages = data.get('messages', [])
        model = data.get('model', 'gpt-4o')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
        stream = data.get('stream', False)
        
        if not messages:
            return jsonify({'error': 'Messages are required'}), 400
        
        # Get user settings for advanced features
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        # Safety check
        if settings and settings.enable_safety_protocols:
            for message in messages:
                if message.get('role') == 'user':
                    safety_result = safety_service.check_message_safety(message.get('content', ''))
                    if not safety_result.get('safe', True):
                        return jsonify({
                            'error': 'Message blocked by safety protocols',
                            'code': 'safety_violation'
                        }), 400
        
        # Generate response based on model
        if model.startswith('gpt-'):
            response = openai_service.generate_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
        elif model.startswith('claude-'):
            response = anthropic_service.generate_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            return jsonify({'error': 'Unsupported model'}), 400
        
        # Apply advanced processing if enabled
        if settings and settings.enable_quantum:
            response = quantum_service.enhance_response(response)
        
        if settings and settings.enable_neuromorphic:
            response = neuromorphic_service.process_response(response)
        
        # Safety scoring
        safety_score = None
        if settings and settings.enable_safety_protocols:
            safety_result = safety_service.score_response(response)
            safety_score = safety_result.get('score', 0.0)
        
        # Return OpenAI-compatible response
        return jsonify({
            'id': f'chatcmpl-{datetime.utcnow().timestamp()}',
            'object': 'chat.completion',
            'created': int(datetime.utcnow().timestamp()),
            'model': model,
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': response
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': sum(len(m.get('content', '').split()) for m in messages),
                'completion_tokens': len(response.split()),
                'total_tokens': sum(len(m.get('content', '').split()) for m in messages) + len(response.split())
            },
            'autogent_metadata': {
                'safety_score': safety_score,
                'quantum_enhanced': settings.enable_quantum if settings else False,
                'neuromorphic_processed': settings.enable_neuromorphic if settings else False
            }
        })
        
    except Exception as e:
        logging.error(f"Error in chat completions: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@api_bp.route('/embeddings', methods=['POST'])
@login_required
def embeddings():
    """Generate embeddings for text"""
    try:
        data = request.get_json()
        
        input_text = data.get('input', '')
        model = data.get('model', 'text-embedding-3-small')
        
        if not input_text:
            return jsonify({'error': 'Input text is required'}), 400
        
        # Generate embeddings
        embeddings = rag_processor.generate_embeddings(input_text, model)
        
        return jsonify({
            'object': 'list',
            'data': [{
                'object': 'embedding',
                'embedding': embeddings,
                'index': 0
            }],
            'model': model,
            'usage': {
                'prompt_tokens': len(input_text.split()),
                'total_tokens': len(input_text.split())
            }
        })
        
    except Exception as e:
        logging.error(f"Error generating embeddings: {str(e)}")
        return jsonify({'error': 'Failed to generate embeddings'}), 500

@api_bp.route('/semantic-search', methods=['POST'])
@login_required
def semantic_search():
    """Semantic search endpoint"""
    try:
        data = request.get_json()
        
        query = data.get('query', '')
        file_ids = data.get('file_ids', [])
        limit = data.get('limit', 10)
        threshold = data.get('threshold', 0.7)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform semantic search
        results = rag_processor.semantic_search(
            query=query,
            user_id=current_user.id,
            file_ids=file_ids,
            limit=limit,
            threshold=threshold
        )
        
        return jsonify({
            'query': query,
            'results': results,
            'total_results': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error in semantic search: {str(e)}")
        return jsonify({'error': 'Failed to perform semantic search'}), 500

@api_bp.route('/quantum/enhance', methods=['POST'])
@login_required
def quantum_enhance():
    """Quantum enhancement endpoint"""
    try:
        data = request.get_json()
        
        text = data.get('text', '')
        enhancement_type = data.get('enhancement_type', 'optimization')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Check quantum access
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings or not settings.enable_quantum:
            return jsonify({'error': 'Quantum enhancement not enabled'}), 403
        
        # Apply quantum enhancement
        enhanced_text = quantum_service.enhance_response(text, enhancement_type)
        
        return jsonify({
            'original_text': text,
            'enhanced_text': enhanced_text,
            'enhancement_type': enhancement_type,
            'quantum_processed': True
        })
        
    except Exception as e:
        logging.error(f"Error in quantum enhancement: {str(e)}")
        return jsonify({'error': 'Failed to apply quantum enhancement'}), 500

@api_bp.route('/neuromorphic/process', methods=['POST'])
@login_required
def neuromorphic_process():
    """Neuromorphic processing endpoint"""
    try:
        data = request.get_json()
        
        input_data = data.get('input_data', [])
        processing_type = data.get('processing_type', 'classification')
        
        if not input_data:
            return jsonify({'error': 'Input data is required'}), 400
        
        # Check neuromorphic access
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings or not settings.enable_neuromorphic:
            return jsonify({'error': 'Neuromorphic processing not enabled'}), 403
        
        # Process with neuromorphic computing
        results = neuromorphic_service.process_data(
            input_data=input_data,
            processing_type=processing_type
        )
        
        return jsonify({
            'input_data': input_data,
            'processing_type': processing_type,
            'results': results,
            'neuromorphic_processed': True
        })
        
    except Exception as e:
        logging.error(f"Error in neuromorphic processing: {str(e)}")
        return jsonify({'error': 'Failed to process with neuromorphic computing'}), 500

@api_bp.route('/safety/check', methods=['POST'])
@login_required
def safety_check():
    """Safety checking endpoint"""
    try:
        data = request.get_json()
        
        content = data.get('content', '')
        check_type = data.get('check_type', 'comprehensive')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Perform safety check
        results = safety_service.check_content_safety(content, check_type)
        
        return jsonify({
            'content': content,
            'check_type': check_type,
            'results': results
        })
        
    except Exception as e:
        logging.error(f"Error in safety check: {str(e)}")
        return jsonify({'error': 'Failed to perform safety check'}), 500

@api_bp.route('/federated/train', methods=['POST'])
@login_required
def federated_train():
    """Federated learning training endpoint"""
    try:
        data = request.get_json()
        
        model_config = data.get('model_config', {})
        training_data = data.get('training_data', [])
        node_ids = data.get('node_ids', [])
        
        if not model_config or not training_data:
            return jsonify({'error': 'Model config and training data are required'}), 400
        
        # Check federated access
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings or not settings.enable_federated:
            return jsonify({'error': 'Federated learning not enabled'}), 403
        
        # Start federated training
        from services.federated_service import FederatedService
        federated_service = FederatedService()
        
        training_result = federated_service.start_federated_training(
            user_id=current_user.id,
            model_config=model_config,
            training_data=training_data,
            node_ids=node_ids
        )
        
        return jsonify({
            'training_id': training_result['training_id'],
            'status': 'started',
            'participating_nodes': len(node_ids)
        })
        
    except Exception as e:
        logging.error(f"Error in federated training: {str(e)}")
        return jsonify({'error': 'Failed to start federated training'}), 500

@api_bp.route('/blockchain/transaction', methods=['POST'])
@login_required
def blockchain_transaction():
    """Blockchain transaction endpoint"""
    try:
        data = request.get_json()
        
        transaction_type = data.get('transaction_type')
        amount = data.get('amount')
        currency = data.get('currency', 'ETH')
        to_address = data.get('to_address')
        
        if not transaction_type or not amount:
            return jsonify({'error': 'Transaction type and amount are required'}), 400
        
        # Create blockchain transaction
        result = blockchain_service.create_transaction(
            user_id=current_user.id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            to_address=to_address
        )
        
        return jsonify({
            'transaction_hash': result['transaction_hash'],
            'status': 'pending',
            'amount': amount,
            'currency': currency
        })
        
    except Exception as e:
        logging.error(f"Error in blockchain transaction: {str(e)}")
        return jsonify({'error': 'Failed to create blockchain transaction'}), 500

@api_bp.route('/models', methods=['GET'])
@login_required
def list_models():
    """List available models"""
    models = [
        {
            'id': 'gpt-4o',
            'object': 'model',
            'created': 1640995200,
            'owned_by': 'openai',
            'capabilities': ['text', 'vision', 'function_calling'],
            'context_length': 128000,
            'supports_quantum': True,
            'supports_neuromorphic': True
        },
        {
            'id': 'gpt-4o-mini',
            'object': 'model',
            'created': 1640995200,
            'owned_by': 'openai',
            'capabilities': ['text', 'vision', 'function_calling'],
            'context_length': 128000,
            'supports_quantum': True,
            'supports_neuromorphic': True
        },
        {
            'id': 'claude-sonnet-4-20250514',
            'object': 'model',
            'created': 1640995200,
            'owned_by': 'anthropic',
            'capabilities': ['text', 'vision', 'function_calling'],
            'context_length': 200000,
            'supports_quantum': True,
            'supports_neuromorphic': True
        },
        {
            'id': 'claude-3-7-sonnet-20250219',
            'object': 'model',
            'created': 1640995200,
            'owned_by': 'anthropic',
            'capabilities': ['text', 'vision', 'function_calling'],
            'context_length': 200000,
            'supports_quantum': True,
            'supports_neuromorphic': True
        }
    ]
    
    return jsonify({
        'object': 'list',
        'data': models
    })

@api_bp.route('/user/stats', methods=['GET'])
@login_required
def user_stats():
    """Get user statistics"""
    try:
        # Basic statistics
        conversations_count = Conversation.query.filter_by(user_id=current_user.id).count()
        messages_count = db.session.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id
        ).count()
        files_count = File.query.filter_by(user_id=current_user.id).count()
        
        # Advanced features usage
        quantum_jobs = QuantumJob.query.filter_by(user_id=current_user.id).count()
        federated_nodes = FederatedNode.query.filter_by(user_id=current_user.id).count()
        neuromorphic_devices = NeuromorphicDevice.query.filter_by(user_id=current_user.id).count()
        
        # Safety statistics
        safety_messages = db.session.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Message.safety_score.isnot(None)
        ).count()
        
        avg_safety_score = db.session.query(
            func.avg(Message.safety_score)
        ).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Message.safety_score.isnot(None)
        ).scalar() or 0
        
        return jsonify({
            'conversations': conversations_count,
            'messages': messages_count,
            'files': files_count,
            'quantum_jobs': quantum_jobs,
            'federated_nodes': federated_nodes,
            'neuromorphic_devices': neuromorphic_devices,
            'safety_messages': safety_messages,
            'avg_safety_score': float(avg_safety_score)
        })
        
    except Exception as e:
        logging.error(f"Error getting user stats: {str(e)}")
        return jsonify({'error': 'Failed to get user statistics'}), 500

@api_bp.route('/workflow/execute', methods=['POST'])
@login_required
def execute_workflow():
    """Execute workflow via API"""
    try:
        data = request.get_json()
        
        workflow_id = data.get('workflow_id')
        inputs = data.get('inputs', {})
        
        if not workflow_id:
            return jsonify({'error': 'Workflow ID is required'}), 400
        
        # Get workflow
        workflow = Workflow.query.filter_by(
            id=workflow_id,
            user_id=current_user.id
        ).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        # Execute workflow
        from services.orchestration_service import OrchestrationService
        orchestration_service = OrchestrationService()
        
        result = orchestration_service.execute_workflow(workflow, inputs)
        
        return jsonify({
            'workflow_id': workflow_id,
            'execution_result': result,
            'status': 'completed' if result.get('success') else 'failed'
        })
        
    except Exception as e:
        logging.error(f"Error executing workflow: {str(e)}")
        return jsonify({'error': 'Failed to execute workflow'}), 500

@api_bp.route('/research/generate-hypothesis', methods=['POST'])
@login_required
def generate_hypothesis():
    """Generate research hypothesis"""
    try:
        data = request.get_json()
        
        research_area = data.get('research_area')
        existing_knowledge = data.get('existing_knowledge', [])
        
        if not research_area:
            return jsonify({'error': 'Research area is required'}), 400
        
        # Check self-improving access
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings or not settings.enable_self_improving:
            return jsonify({'error': 'Self-improving AI not enabled'}), 403
        
        # Generate hypothesis using AI
        prompt = f"""
        Generate a novel research hypothesis in {research_area}.
        
        Existing knowledge: {json.dumps(existing_knowledge)}
        
        Provide a JSON response with:
        - hypothesis: Clear, testable hypothesis
        - rationale: Scientific reasoning
        - methodology: Suggested research approach
        - expected_outcomes: Predicted results
        """
        
        response = openai_service.generate_response(
            messages=[{'role': 'user', 'content': prompt}],
            model='gpt-4o',
            temperature=0.7
        )
        
        try:
            hypothesis_data = json.loads(response)
        except json.JSONDecodeError:
            hypothesis_data = {'hypothesis': response}
        
        return jsonify({
            'research_area': research_area,
            'generated_hypothesis': hypothesis_data,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error generating hypothesis: {str(e)}")
        return jsonify({'error': 'Failed to generate hypothesis'}), 500

@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@api_bp.errorhandler(403)
def api_forbidden(error):
    return jsonify({'error': 'Access forbidden'}), 403

@api_bp.errorhandler(401)
def api_unauthorized(error):
    return jsonify({'error': 'Authentication required'}), 401
