from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, WorkflowTemplate
from services.orchestration_service import OrchestrationService
import logging

orchestration_bp = Blueprint('orchestration', __name__)

@orchestration_bp.route('/orchestration')
def orchestration_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    workflows = WorkflowTemplate.query.filter_by(user_id=user.id).order_by(WorkflowTemplate.created_at.desc()).all()
    
    return render_template('orchestration/orchestration.html', user=user, workflows=workflows)

@orchestration_bp.route('/api/orchestration/workflows', methods=['GET', 'POST'])
def api_workflows():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            workflow_data = data.get('workflow_data', {})
            
            if not name:
                return jsonify({'error': 'Workflow name is required'}), 400
            
            workflow = WorkflowTemplate(
                user_id=user.id,
                name=name,
                description=data.get('description', ''),
                category=data.get('category', 'general'),
                workflow_data=workflow_data
            )
            
            db.session.add(workflow)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'workflow': workflow.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error creating workflow: {str(e)}")
            return jsonify({'error': 'Failed to create workflow'}), 500
    
    # GET request
    workflows = WorkflowTemplate.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'workflows': [workflow.to_dict() for workflow in workflows]
    })

@orchestration_bp.route('/api/orchestration/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        workflow = WorkflowTemplate.query.filter_by(id=workflow_id, user_id=user.id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        data = request.get_json()
        input_data = data.get('input_data', {})
        execution_mode = data.get('execution_mode', 'sequential')
        
        orchestration_service = OrchestrationService()
        execution_result = orchestration_service.execute_workflow(
            workflow_data=workflow.workflow_data,
            input_data=input_data,
            execution_mode=execution_mode
        )
        
        # Update usage count
        workflow.usage_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'execution_result': execution_result,
            'workflow': workflow.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error executing workflow: {str(e)}")
        return jsonify({'error': f'Workflow execution failed: {str(e)}'}), 500

@orchestration_bp.route('/api/orchestration/nodes/available')
def get_available_nodes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Available node types for Drawflow integration
    nodes = [
        {
            'id': 'input',
            'name': 'Input',
            'category': 'io',
            'description': 'Input data node',
            'inputs': 0,
            'outputs': 1,
            'parameters': ['data_type', 'format']
        },
        {
            'id': 'output',
            'name': 'Output',
            'category': 'io',
            'description': 'Output data node',
            'inputs': 1,
            'outputs': 0,
            'parameters': ['format', 'destination']
        },
        {
            'id': 'llm_chat',
            'name': 'LLM Chat',
            'category': 'ai',
            'description': 'Chat with language model',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['model', 'temperature', 'max_tokens', 'system_prompt']
        },
        {
            'id': 'embedding',
            'name': 'Text Embedding',
            'category': 'ai',
            'description': 'Generate text embeddings',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['model', 'dimensions']
        },
        {
            'id': 'image_generation',
            'name': 'Image Generation',
            'category': 'ai',
            'description': 'Generate images from text',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['model', 'size', 'quality', 'style']
        },
        {
            'id': 'vector_search',
            'name': 'Vector Search',
            'category': 'search',
            'description': 'Search vector database',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['index', 'top_k', 'threshold']
        },
        {
            'id': 'text_processor',
            'name': 'Text Processor',
            'category': 'processing',
            'description': 'Process and transform text',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['operation', 'parameters']
        },
        {
            'id': 'condition',
            'name': 'Condition',
            'category': 'logic',
            'description': 'Conditional logic node',
            'inputs': 1,
            'outputs': 2,
            'parameters': ['condition', 'operator', 'value']
        },
        {
            'id': 'loop',
            'name': 'Loop',
            'category': 'logic',
            'description': 'Loop processing node',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['iterations', 'condition']
        },
        {
            'id': 'quantum_circuit',
            'name': 'Quantum Circuit',
            'category': 'quantum',
            'description': 'Execute quantum circuit',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['circuit_id', 'backend', 'shots']
        },
        {
            'id': 'federated_train',
            'name': 'Federated Training',
            'category': 'federated',
            'description': 'Federated learning node',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['model_config', 'nodes', 'rounds']
        },
        {
            'id': 'neuromorphic_snn',
            'name': 'Spiking Neural Network',
            'category': 'neuromorphic',
            'description': 'Neuromorphic SNN processing',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['network_id', 'duration', 'timestep']
        },
        {
            'id': 'safety_check',
            'name': 'Safety Check',
            'category': 'safety',
            'description': 'AI safety validation',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['protocol_id', 'threshold', 'action']
        },
        {
            'id': 'plandex_terminal',
            'name': 'Plandex Terminal',
            'category': 'coding',
            'description': 'Terminal-based AI coding agent',
            'inputs': 1,
            'outputs': 1,
            'parameters': ['command', 'project_path', 'context']
        }
    ]
    
    return jsonify({
        'success': True,
        'nodes': nodes
    })

@orchestration_bp.route('/api/orchestration/validate', methods=['POST'])
def validate_workflow():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        workflow_data = data.get('workflow_data', {})
        
        orchestration_service = OrchestrationService()
        validation_result = orchestration_service.validate_workflow(workflow_data)
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
        
    except Exception as e:
        logging.error(f"Error validating workflow: {str(e)}")
        return jsonify({'error': f'Workflow validation failed: {str(e)}'}), 500

@orchestration_bp.route('/api/orchestration/templates')
def get_workflow_templates():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Pre-built workflow templates
    templates = [
        {
            'id': 'simple_chat',
            'name': 'Simple Chat Pipeline',
            'description': 'Basic input → LLM → output workflow',
            'category': 'chat',
            'workflow_data': {
                'nodes': {
                    'node_1': {'id': 1, 'name': 'input', 'pos_x': 100, 'pos_y': 100},
                    'node_2': {'id': 2, 'name': 'llm_chat', 'pos_x': 300, 'pos_y': 100},
                    'node_3': {'id': 3, 'name': 'output', 'pos_x': 500, 'pos_y': 100}
                },
                'connections': {
                    'node_1': {'output_1': {'node': 'node_2', 'input': 'input_1'}},
                    'node_2': {'output_1': {'node': 'node_3', 'input': 'input_1'}}
                }
            }
        },
        {
            'id': 'rag_pipeline',
            'name': 'RAG Pipeline',
            'description': 'Retrieval-augmented generation workflow',
            'category': 'rag',
            'workflow_data': {
                'nodes': {
                    'node_1': {'id': 1, 'name': 'input', 'pos_x': 100, 'pos_y': 100},
                    'node_2': {'id': 2, 'name': 'embedding', 'pos_x': 300, 'pos_y': 100},
                    'node_3': {'id': 3, 'name': 'vector_search', 'pos_x': 500, 'pos_y': 100},
                    'node_4': {'id': 4, 'name': 'llm_chat', 'pos_x': 700, 'pos_y': 100},
                    'node_5': {'id': 5, 'name': 'output', 'pos_x': 900, 'pos_y': 100}
                },
                'connections': {
                    'node_1': {'output_1': {'node': 'node_2', 'input': 'input_1'}},
                    'node_2': {'output_1': {'node': 'node_3', 'input': 'input_1'}},
                    'node_3': {'output_1': {'node': 'node_4', 'input': 'input_1'}},
                    'node_4': {'output_1': {'node': 'node_5', 'input': 'input_1'}}
                }
            }
        },
        {
            'id': 'quantum_ml',
            'name': 'Quantum ML Pipeline',
            'description': 'Quantum-enhanced machine learning workflow',
            'category': 'quantum',
            'workflow_data': {
                'nodes': {
                    'node_1': {'id': 1, 'name': 'input', 'pos_x': 100, 'pos_y': 100},
                    'node_2': {'id': 2, 'name': 'text_processor', 'pos_x': 300, 'pos_y': 100},
                    'node_3': {'id': 3, 'name': 'quantum_circuit', 'pos_x': 500, 'pos_y': 100},
                    'node_4': {'id': 4, 'name': 'llm_chat', 'pos_x': 700, 'pos_y': 100},
                    'node_5': {'id': 5, 'name': 'output', 'pos_x': 900, 'pos_y': 100}
                },
                'connections': {
                    'node_1': {'output_1': {'node': 'node_2', 'input': 'input_1'}},
                    'node_2': {'output_1': {'node': 'node_3', 'input': 'input_1'}},
                    'node_3': {'output_1': {'node': 'node_4', 'input': 'input_1'}},
                    'node_4': {'output_1': {'node': 'node_5', 'input': 'input_1'}}
                }
            }
        },
        {
            'id': 'federated_pipeline',
            'name': 'Federated Learning Pipeline',
            'description': 'Distributed federated learning workflow',
            'category': 'federated',
            'workflow_data': {
                'nodes': {
                    'node_1': {'id': 1, 'name': 'input', 'pos_x': 100, 'pos_y': 100},
                    'node_2': {'id': 2, 'name': 'federated_train', 'pos_x': 300, 'pos_y': 100},
                    'node_3': {'id': 3, 'name': 'safety_check', 'pos_x': 500, 'pos_y': 100},
                    'node_4': {'id': 4, 'name': 'output', 'pos_x': 700, 'pos_y': 100}
                },
                'connections': {
                    'node_1': {'output_1': {'node': 'node_2', 'input': 'input_1'}},
                    'node_2': {'output_1': {'node': 'node_3', 'input': 'input_1'}},
                    'node_3': {'output_1': {'node': 'node_4', 'input': 'input_1'}}
                }
            }
        }
    ]
    
    return jsonify({
        'success': True,
        'templates': templates
    })

@orchestration_bp.route('/api/orchestration/export/<workflow_id>')
def export_workflow(workflow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        workflow = WorkflowTemplate.query.filter_by(id=workflow_id, user_id=user.id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        orchestration_service = OrchestrationService()
        export_data = orchestration_service.export_workflow(workflow.workflow_data)
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        logging.error(f"Error exporting workflow: {str(e)}")
        return jsonify({'error': f'Workflow export failed: {str(e)}'}), 500

@orchestration_bp.route('/api/orchestration/import', methods=['POST'])
def import_workflow():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        import_data = data.get('import_data', {})
        workflow_name = data.get('name', 'Imported Workflow')
        
        if not import_data:
            return jsonify({'error': 'Import data is required'}), 400
        
        user = User.query.get(session['user_id'])
        orchestration_service = OrchestrationService()
        
        # Validate and process import data
        workflow_data = orchestration_service.import_workflow(import_data)
        
        # Create new workflow
        workflow = WorkflowTemplate(
            user_id=user.id,
            name=workflow_name,
            description=f'Imported workflow: {workflow_name}',
            category='imported',
            workflow_data=workflow_data
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'workflow': workflow.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error importing workflow: {str(e)}")
        return jsonify({'error': f'Workflow import failed: {str(e)}'}), 500
