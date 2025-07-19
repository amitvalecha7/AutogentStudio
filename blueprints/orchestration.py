from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Workflow, WorkflowExecution, db
from services.orchestration_service import OrchestrationService
import uuid

orchestration_bp = Blueprint('orchestration', __name__, url_prefix='/orchestration')

@orchestration_bp.route('/')
@login_required
def index():
    # Get user's workflows
    workflows = Workflow.query.filter_by(
        user_id=current_user.id
    ).order_by(Workflow.created_at.desc()).all()
    
    return render_template('orchestration/index.html', workflows=workflows)

@orchestration_bp.route('/editor')
@login_required
def editor():
    return render_template('orchestration/editor.html')

@orchestration_bp.route('/workflow/<workflow_id>')
@login_required
def view_workflow(workflow_id):
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get execution history
    executions = WorkflowExecution.query.filter_by(
        workflow_id=workflow_id
    ).order_by(WorkflowExecution.start_time.desc()).limit(20).all()
    
    return render_template('orchestration/workflow_detail.html', 
                         workflow=workflow, 
                         executions=executions)

@orchestration_bp.route('/create-workflow', methods=['POST'])
@login_required
def create_workflow():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    flow_definition = data.get('flow_definition', {})
    
    if not name:
        return jsonify({'error': 'Workflow name is required'}), 400
    
    if not flow_definition:
        return jsonify({'error': 'Workflow definition is required'}), 400
    
    try:
        orchestration_service = OrchestrationService()
        
        # Validate workflow definition
        validation_result = orchestration_service.validate_workflow(flow_definition)
        
        if not validation_result.get('valid'):
            return jsonify({
                'error': 'Invalid workflow definition',
                'details': validation_result.get('errors', [])
            }), 400
        
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            user_id=current_user.id,
            name=name,
            description=data.get('description', ''),
            flow_definition=flow_definition,
            is_active=True
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'validation': validation_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/workflow/<workflow_id>/update', methods=['POST'])
@login_required
def update_workflow(workflow_id):
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    
    try:
        orchestration_service = OrchestrationService()
        
        # Update workflow
        if 'name' in data:
            workflow.name = data['name']
        if 'description' in data:
            workflow.description = data['description']
        if 'flow_definition' in data:
            # Validate new definition
            validation_result = orchestration_service.validate_workflow(data['flow_definition'])
            if not validation_result.get('valid'):
                return jsonify({
                    'error': 'Invalid workflow definition',
                    'details': validation_result.get('errors', [])
                }), 400
            workflow.flow_definition = data['flow_definition']
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/workflow/<workflow_id>/execute', methods=['POST'])
@login_required
def execute_workflow(workflow_id):
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    input_data = data.get('input_data', {})
    
    try:
        orchestration_service = OrchestrationService()
        
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status='running',
            input_data=input_data,
            start_time=db.func.now()
        )
        
        db.session.add(execution)
        db.session.commit()
        
        # Execute workflow asynchronously
        execution_result = orchestration_service.execute_workflow_async(
            workflow=workflow,
            execution=execution,
            input_data=input_data
        )
        
        # Update workflow execution count
        workflow.execution_count += 1
        workflow.last_execution = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'status': 'running',
            'result': execution_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/execution/<execution_id>')
@login_required
def view_execution(execution_id):
    execution = WorkflowExecution.query.join(Workflow).filter(
        WorkflowExecution.id == execution_id,
        Workflow.user_id == current_user.id
    ).first_or_404()
    
    return render_template('orchestration/execution_detail.html', execution=execution)

@orchestration_bp.route('/execution/<execution_id>/status')
@login_required
def execution_status(execution_id):
    execution = WorkflowExecution.query.join(Workflow).filter(
        WorkflowExecution.id == execution_id,
        Workflow.user_id == current_user.id
    ).first_or_404()
    
    return jsonify({
        'execution_id': execution_id,
        'status': execution.status,
        'start_time': execution.start_time.isoformat() if execution.start_time else None,
        'end_time': execution.end_time.isoformat() if execution.end_time else None,
        'output_data': execution.output_data,
        'execution_log': execution.execution_log
    })

@orchestration_bp.route('/execution/<execution_id>/stop', methods=['POST'])
@login_required
def stop_execution(execution_id):
    execution = WorkflowExecution.query.join(Workflow).filter(
        WorkflowExecution.id == execution_id,
        Workflow.user_id == current_user.id
    ).first_or_404()
    
    try:
        orchestration_service = OrchestrationService()
        
        # Stop workflow execution
        stop_result = orchestration_service.stop_workflow_execution(execution)
        
        execution.status = 'stopped'
        execution.end_time = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': stop_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestration_bp.route('/templates')
@login_required
def workflow_templates():
    templates = {
        'data_processing': {
            'name': 'Data Processing Pipeline',
            'description': 'Process and transform data through multiple stages',
            'nodes': ['data_input', 'data_cleaner', 'transformer', 'output'],
            'flow_definition': {
                'drawflow': {
                    'Home': {
                        'data': {
                            '1': {
                                'name': 'data_input',
                                'data': {},
                                'class': 'data_input',
                                'html': 'Data Input',
                                'typenode': 'vue',
                                'inputs': {},
                                'outputs': {'output_1': {'connections': [{'node': '2', 'output': 'input_1'}]}},
                                'pos_x': 100,
                                'pos_y': 100
                            },
                            '2': {
                                'name': 'data_cleaner',
                                'data': {},
                                'class': 'data_cleaner',
                                'html': 'Data Cleaner',
                                'typenode': 'vue',
                                'inputs': {'input_1': {'connections': [{'node': '1', 'input': 'output_1'}]}},
                                'outputs': {'output_1': {'connections': [{'node': '3', 'output': 'input_1'}]}},
                                'pos_x': 300,
                                'pos_y': 100
                            }
                        }
                    }
                }
            }
        },
        'ai_model_chain': {
            'name': 'AI Model Chain',
            'description': 'Chain multiple AI models for complex processing',
            'nodes': ['input', 'gpt4', 'claude', 'output'],
            'flow_definition': {
                # Simplified template structure
                'type': 'ai_chain',
                'models': ['gpt-4o', 'claude-sonnet-4-20250514']
            }
        },
        'quantum_classical_hybrid': {
            'name': 'Quantum-Classical Hybrid',
            'description': 'Combine quantum and classical computing',
            'nodes': ['classical_input', 'quantum_processor', 'classical_output'],
            'flow_definition': {
                'type': 'hybrid',
                'quantum_backend': 'ibm',
                'classical_backend': 'cpu'
            }
        }
    }
    
    return jsonify({
        'success': True,
        'templates': templates
    })

@orchestration_bp.route('/nodes/available')
@login_required
def available_nodes():
    nodes = {
        'input_nodes': [
            {'type': 'text_input', 'name': 'Text Input', 'description': 'Text input node'},
            {'type': 'file_input', 'name': 'File Input', 'description': 'File input node'},
            {'type': 'api_input', 'name': 'API Input', 'description': 'API data input'}
        ],
        'processing_nodes': [
            {'type': 'gpt4', 'name': 'GPT-4o', 'description': 'OpenAI GPT-4o model'},
            {'type': 'claude', 'name': 'Claude Sonnet 4', 'description': 'Anthropic Claude Sonnet 4'},
            {'type': 'gemini', 'name': 'Gemini Pro', 'description': 'Google Gemini Pro'},
            {'type': 'data_transformer', 'name': 'Data Transformer', 'description': 'Transform data format'},
            {'type': 'text_analyzer', 'name': 'Text Analyzer', 'description': 'Analyze text content'}
        ],
        'quantum_nodes': [
            {'type': 'quantum_circuit', 'name': 'Quantum Circuit', 'description': 'Quantum computation node'},
            {'type': 'quantum_simulator', 'name': 'Quantum Simulator', 'description': 'Simulate quantum circuits'},
            {'type': 'hybrid_processor', 'name': 'Hybrid Processor', 'description': 'Quantum-classical hybrid'}
        ],
        'output_nodes': [
            {'type': 'text_output', 'name': 'Text Output', 'description': 'Text output node'},
            {'type': 'file_output', 'name': 'File Output', 'description': 'File output node'},
            {'type': 'api_output', 'name': 'API Output', 'description': 'Send to API endpoint'}
        ]
    }
    
    return jsonify({
        'success': True,
        'nodes': nodes
    })

@orchestration_bp.route('/workflow/<workflow_id>/clone', methods=['POST'])
@login_required
def clone_workflow(workflow_id):
    original_workflow = Workflow.query.filter_by(
        id=workflow_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        new_workflow_id = str(uuid.uuid4())
        cloned_workflow = Workflow(
            id=new_workflow_id,
            user_id=current_user.id,
            name=f"{original_workflow.name} (Copy)",
            description=original_workflow.description,
            flow_definition=original_workflow.flow_definition,
            is_active=True
        )
        
        db.session.add(cloned_workflow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'workflow_id': new_workflow_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
