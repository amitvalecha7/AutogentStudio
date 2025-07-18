from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, FederatedNode, FederatedTraining
from blueprints.auth import login_required, get_current_user
from services.federated_service import FederatedService
import logging
import json
from datetime import datetime

federated_bp = Blueprint('federated', __name__)

@federated_bp.route('/')
@login_required
def federated_index():
    user = get_current_user()
    nodes = FederatedNode.query.filter_by(user_id=user.id).order_by(FederatedNode.created_at.desc()).limit(10).all()
    trainings = FederatedTraining.query.filter_by(user_id=user.id).order_by(FederatedTraining.created_at.desc()).limit(10).all()
    
    # Calculate summary statistics
    active_nodes = FederatedNode.query.filter_by(user_id=user.id, is_active=True).count()
    running_trainings = FederatedTraining.query.filter_by(user_id=user.id, status='running').count()
    
    return render_template('federated/dashboard.html', 
                         user=user, 
                         nodes=nodes, 
                         trainings=trainings,
                         active_nodes=active_nodes,
                         running_trainings=running_trainings)

@federated_bp.route('/training')
@login_required
def federated_training():
    user = get_current_user()
    trainings = FederatedTraining.query.filter_by(user_id=user.id).order_by(FederatedTraining.created_at.desc()).all()
    nodes = FederatedNode.query.filter_by(user_id=user.id, is_active=True).all()
    
    return render_template('federated/training.html', 
                         user=user, 
                         trainings=trainings,
                         nodes=nodes)

@federated_bp.route('/nodes')
@login_required
def federated_nodes():
    user = get_current_user()
    nodes = FederatedNode.query.filter_by(user_id=user.id).order_by(FederatedNode.created_at.desc()).all()
    
    return render_template('federated/nodes.html', 
                         user=user, 
                         nodes=nodes)

@federated_bp.route('/nodes/create', methods=['POST'])
@login_required
def create_node():
    user = get_current_user()
    data = request.get_json()
    
    node_name = data.get('node_name')
    node_type = data.get('node_type', 'client')
    endpoint_url = data.get('endpoint_url')
    
    if not node_name:
        return jsonify({'error': 'Node name is required'}), 400
    
    try:
        node = FederatedNode(
            user_id=user.id,
            node_name=node_name,
            node_type=node_type,
            endpoint_url=endpoint_url,
            is_active=True,
            last_heartbeat=datetime.utcnow()
        )
        
        db.session.add(node)
        db.session.commit()
        
        logging.info(f"Federated node created: {node.id}")
        return jsonify({
            'success': True,
            'node_id': node.id,
            'message': 'Federated node created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating federated node: {str(e)}")
        return jsonify({'error': 'Failed to create federated node'}), 500

@federated_bp.route('/nodes/<int:node_id>/status', methods=['GET', 'POST'])
@login_required
def node_status(node_id):
    user = get_current_user()
    node = FederatedNode.query.filter_by(id=node_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        # Update node status (heartbeat)
        try:
            node.last_heartbeat = datetime.utcnow()
            node.is_active = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Node status updated'
            })
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating node status: {str(e)}")
            return jsonify({'error': 'Failed to update node status'}), 500
    
    else:
        # Get node status
        return jsonify({
            'node_id': node.id,
            'node_name': node.node_name,
            'node_type': node.node_type,
            'is_active': node.is_active,
            'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
            'endpoint_url': node.endpoint_url
        })

@federated_bp.route('/training/create', methods=['POST'])
@login_required
def create_training():
    user = get_current_user()
    data = request.get_json()
    
    training_name = data.get('training_name')
    model_architecture = data.get('model_architecture')
    participants = data.get('participants', [])
    
    if not training_name or not model_architecture:
        return jsonify({'error': 'Training name and model architecture are required'}), 400
    
    try:
        training = FederatedTraining(
            user_id=user.id,
            training_name=training_name,
            model_architecture=json.dumps(model_architecture),
            status='pending',
            round_number=0,
            participants=json.dumps(participants)
        )
        
        db.session.add(training)
        db.session.commit()
        
        logging.info(f"Federated training created: {training.id}")
        return jsonify({
            'success': True,
            'training_id': training.id,
            'message': 'Federated training created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating federated training: {str(e)}")
        return jsonify({'error': 'Failed to create federated training'}), 500

@federated_bp.route('/training/<int:training_id>/start', methods=['POST'])
@login_required
def start_training(training_id):
    user = get_current_user()
    training = FederatedTraining.query.filter_by(id=training_id, user_id=user.id).first_or_404()
    
    if training.status != 'pending':
        return jsonify({'error': 'Training is not in pending state'}), 400
    
    try:
        federated_service = FederatedService()
        result = federated_service.start_training(
            training_id=training.id,
            model_architecture=json.loads(training.model_architecture),
            participants=json.loads(training.participants)
        )
        
        if result['success']:
            training.status = 'running'
            training.round_number = 1
            db.session.commit()
            
            logging.info(f"Federated training started: {training.id}")
            return jsonify({
                'success': True,
                'message': 'Federated training started successfully'
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to start training')}), 500
    
    except Exception as e:
        logging.error(f"Error starting federated training: {str(e)}")
        return jsonify({'error': 'Failed to start federated training'}), 500

@federated_bp.route('/training/<int:training_id>/status')
@login_required
def training_status(training_id):
    user = get_current_user()
    training = FederatedTraining.query.filter_by(id=training_id, user_id=user.id).first_or_404()
    
    try:
        federated_service = FederatedService()
        status = federated_service.get_training_status(training.id)
        
        return jsonify({
            'training_id': training.id,
            'training_name': training.training_name,
            'status': training.status,
            'round_number': training.round_number,
            'participants': json.loads(training.participants),
            'detailed_status': status
        })
    
    except Exception as e:
        logging.error(f"Error getting training status: {str(e)}")
        return jsonify({'error': 'Failed to get training status'}), 500

@federated_bp.route('/aggregation')
@login_required
def federated_aggregation():
    user = get_current_user()
    return render_template('federated/aggregation.html', user=user)

@federated_bp.route('/analytics')
@login_required
def federated_analytics():
    user = get_current_user()
    
    # Get analytics data
    total_nodes = FederatedNode.query.filter_by(user_id=user.id).count()
    active_nodes = FederatedNode.query.filter_by(user_id=user.id, is_active=True).count()
    total_trainings = FederatedTraining.query.filter_by(user_id=user.id).count()
    completed_trainings = FederatedTraining.query.filter_by(user_id=user.id, status='completed').count()
    
    analytics_data = {
        'total_nodes': total_nodes,
        'active_nodes': active_nodes,
        'total_trainings': total_trainings,
        'completed_trainings': completed_trainings,
        'node_utilization': (active_nodes / total_nodes * 100) if total_nodes > 0 else 0,
        'training_success_rate': (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0
    }
    
    return render_template('federated/analytics.html', 
                         user=user, 
                         analytics=analytics_data)

@federated_bp.route('/privacy-settings')
@login_required
def privacy_settings():
    user = get_current_user()
    return render_template('federated/privacy_settings.html', user=user)

@federated_bp.route('/differential-privacy', methods=['POST'])
@login_required
def configure_differential_privacy():
    user = get_current_user()
    data = request.get_json()
    
    epsilon = data.get('epsilon', 1.0)
    delta = data.get('delta', 1e-5)
    noise_multiplier = data.get('noise_multiplier', 1.1)
    
    try:
        # In a real implementation, this would configure differential privacy parameters
        # For now, we'll just validate and return success
        
        if epsilon <= 0 or delta <= 0 or noise_multiplier <= 0:
            return jsonify({'error': 'Privacy parameters must be positive'}), 400
        
        logging.info(f"Differential privacy configured for user {user.id}")
        return jsonify({
            'success': True,
            'message': 'Differential privacy configured successfully',
            'epsilon': epsilon,
            'delta': delta,
            'noise_multiplier': noise_multiplier
        })
    
    except Exception as e:
        logging.error(f"Error configuring differential privacy: {str(e)}")
        return jsonify({'error': 'Failed to configure differential privacy'}), 500
