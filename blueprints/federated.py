from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import FederatedNode, FederatedTrainingJob, db
from services.federated_service import FederatedService
import uuid

federated_bp = Blueprint('federated', __name__, url_prefix='/federated')

@federated_bp.route('/')
@login_required
def index():
    # Get user's federated nodes and training jobs
    nodes = FederatedNode.query.filter_by(
        user_id=current_user.id
    ).order_by(FederatedNode.created_at.desc()).all()
    
    training_jobs = FederatedTrainingJob.query.filter_by(
        user_id=current_user.id
    ).order_by(FederatedTrainingJob.created_at.desc()).all()
    
    return render_template('federated/index.html', 
                         nodes=nodes, 
                         training_jobs=training_jobs)

@federated_bp.route('/training')
@login_required
def training():
    training_jobs = FederatedTrainingJob.query.filter_by(
        user_id=current_user.id
    ).order_by(FederatedTrainingJob.created_at.desc()).all()
    
    return render_template('federated/training.html', training_jobs=training_jobs)

@federated_bp.route('/nodes')
@login_required
def nodes():
    nodes = FederatedNode.query.filter_by(
        user_id=current_user.id
    ).order_by(FederatedNode.created_at.desc()).all()
    
    return render_template('federated/nodes.html', nodes=nodes)

@federated_bp.route('/aggregation')
@login_required
def aggregation():
    return render_template('federated/aggregation.html')

@federated_bp.route('/analytics')
@login_required
def analytics():
    return render_template('federated/analytics.html')

@federated_bp.route('/create-node', methods=['POST'])
@login_required
def create_node():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    node_type = data.get('node_type', 'participant')
    endpoint_url = data.get('endpoint_url', '')
    
    if not name:
        return jsonify({'error': 'Node name is required'}), 400
    
    try:
        federated_service = FederatedService()
        
        node_id = str(uuid.uuid4())
        node = FederatedNode(
            id=node_id,
            user_id=current_user.id,
            name=name,
            node_type=node_type,
            endpoint_url=endpoint_url,
            status='inactive',
            capabilities=data.get('capabilities', {})
        )
        
        db.session.add(node)
        db.session.commit()
        
        # Initialize node
        initialization_result = federated_service.initialize_node(node)
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'initialization': initialization_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@federated_bp.route('/node/<node_id>')
@login_required
def view_node(node_id):
    node = FederatedNode.query.filter_by(
        id=node_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('federated/node_detail.html', node=node)

@federated_bp.route('/node/<node_id>/status', methods=['POST'])
@login_required
def update_node_status(node_id):
    node = FederatedNode.query.filter_by(
        id=node_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['active', 'inactive', 'maintenance']:
        return jsonify({'error': 'Invalid status'}), 400
    
    try:
        federated_service = FederatedService()
        
        # Update node status
        result = federated_service.update_node_status(node, new_status)
        
        node.status = new_status
        node.last_seen = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'status': new_status,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@federated_bp.route('/create-training-job', methods=['POST'])
@login_required
def create_training_job():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    model_architecture = data.get('model_architecture', {})
    training_config = data.get('training_config', {})
    participating_nodes = data.get('participating_nodes', [])
    total_rounds = data.get('total_rounds', 10)
    
    if not name:
        return jsonify({'error': 'Training job name is required'}), 400
    
    if not model_architecture:
        return jsonify({'error': 'Model architecture is required'}), 400
    
    try:
        federated_service = FederatedService()
        
        job_id = str(uuid.uuid4())
        training_job = FederatedTrainingJob(
            id=job_id,
            user_id=current_user.id,
            name=name,
            model_architecture=model_architecture,
            training_config=training_config,
            participating_nodes=participating_nodes,
            total_rounds=total_rounds,
            status='pending'
        )
        
        db.session.add(training_job)
        db.session.commit()
        
        # Start federated training
        training_result = federated_service.start_federated_training(training_job)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'training_result': training_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@federated_bp.route('/training-job/<job_id>')
@login_required
def view_training_job(job_id):
    job = FederatedTrainingJob.query.filter_by(
        id=job_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('federated/training_job_detail.html', job=job)

@federated_bp.route('/training-job/<job_id>/start', methods=['POST'])
@login_required
def start_training_job(job_id):
    job = FederatedTrainingJob.query.filter_by(
        id=job_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        federated_service = FederatedService()
        
        # Start training
        result = federated_service.start_federated_training(job)
        
        job.status = 'running'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@federated_bp.route('/training-job/<job_id>/stop', methods=['POST'])
@login_required
def stop_training_job(job_id):
    job = FederatedTrainingJob.query.filter_by(
        id=job_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        federated_service = FederatedService()
        
        # Stop training
        result = federated_service.stop_federated_training(job)
        
        job.status = 'stopped'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@federated_bp.route('/privacy-settings', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        # Update privacy settings in user preferences
        preferences = current_user.preferences or {}
        preferences.update({
            'differential_privacy': data.get('differential_privacy', True),
            'privacy_budget': data.get('privacy_budget', 1.0),
            'secure_aggregation': data.get('secure_aggregation', True),
            'homomorphic_encryption': data.get('homomorphic_encryption', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Privacy settings updated'})
    
    return render_template('federated/privacy_settings.html')

@federated_bp.route('/network-topology')
@login_required
def network_topology():
    # Get network topology data for visualization
    nodes = FederatedNode.query.filter_by(
        user_id=current_user.id
    ).all()
    
    topology_data = {
        'nodes': [{
            'id': node.id,
            'name': node.name,
            'type': node.node_type,
            'status': node.status,
            'capabilities': node.capabilities
        } for node in nodes],
        'connections': []  # Would be populated based on actual network topology
    }
    
    return jsonify({
        'success': True,
        'topology': topology_data
    })
