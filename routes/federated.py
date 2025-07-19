from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, FederatedNode
from services.federated_service import FederatedService
import logging

federated_bp = Blueprint('federated', __name__)

@federated_bp.route('/federated')
def federated_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    nodes = FederatedNode.query.filter_by(user_id=user.id).all()
    
    return render_template('federated/federated.html', user=user, nodes=nodes)

@federated_bp.route('/federated/training')
def federated_training():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('federated/training.html', user=user)

@federated_bp.route('/federated/nodes')
def federated_nodes():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    nodes = FederatedNode.query.filter_by(user_id=user.id).all()
    
    return render_template('federated/nodes.html', user=user, nodes=nodes)

@federated_bp.route('/federated/aggregation')
def federated_aggregation():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('federated/aggregation.html', user=user)

@federated_bp.route('/federated/analytics')
def federated_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('federated/analytics.html', user=user)

@federated_bp.route('/api/federated/nodes', methods=['GET', 'POST'])
def api_nodes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            node_name = data.get('node_name', '').strip()
            endpoint_url = data.get('endpoint_url', '').strip()
            capabilities = data.get('capabilities', {})
            
            if not all([node_name, endpoint_url]):
                return jsonify({'error': 'Node name and endpoint URL are required'}), 400
            
            node = FederatedNode(
                user_id=user.id,
                node_name=node_name,
                endpoint_url=endpoint_url,
                capabilities=capabilities,
                status='inactive'
            )
            
            db.session.add(node)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'node': node.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error creating federated node: {str(e)}")
            return jsonify({'error': 'Failed to create node'}), 500
    
    # GET request
    nodes = FederatedNode.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'nodes': [node.to_dict() for node in nodes]
    })

@federated_bp.route('/api/federated/nodes/<node_id>/status', methods=['POST'])
def update_node_status(node_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        node = FederatedNode.query.filter_by(id=node_id, user_id=user.id).first()
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status', '').strip()
        
        if new_status not in ['active', 'inactive', 'error']:
            return jsonify({'error': 'Invalid status'}), 400
        
        node.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'node': node.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating node status: {str(e)}")
        return jsonify({'error': 'Failed to update node status'}), 500

@federated_bp.route('/api/federated/training/start', methods=['POST'])
def start_training():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_config = data.get('model_config', {})
        training_config = data.get('training_config', {})
        node_ids = data.get('node_ids', [])
        
        if not node_ids:
            return jsonify({'error': 'At least one node is required'}), 400
        
        user = User.query.get(session['user_id'])
        
        # Verify nodes belong to user
        nodes = FederatedNode.query.filter(
            FederatedNode.id.in_(node_ids),
            FederatedNode.user_id == user.id
        ).all()
        
        if len(nodes) != len(node_ids):
            return jsonify({'error': 'Some nodes not found'}), 404
        
        # Start federated training
        federated_service = FederatedService()
        training_job = federated_service.start_training(
            nodes=nodes,
            model_config=model_config,
            training_config=training_config
        )
        
        return jsonify({
            'success': True,
            'training_job': training_job
        })
        
    except Exception as e:
        logging.error(f"Error starting federated training: {str(e)}")
        return jsonify({'error': f'Failed to start training: {str(e)}'}), 500

@federated_bp.route('/api/federated/training/status/<job_id>')
def get_training_status(job_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        federated_service = FederatedService()
        status = federated_service.get_training_status(job_id)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logging.error(f"Error getting training status: {str(e)}")
        return jsonify({'error': 'Failed to get training status'}), 500

@federated_bp.route('/api/federated/aggregation/fedavg', methods=['POST'])
def federated_averaging():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_updates = data.get('model_updates', [])
        weights = data.get('weights', [])
        
        if not model_updates:
            return jsonify({'error': 'Model updates are required'}), 400
        
        federated_service = FederatedService()
        aggregated_model = federated_service.federated_averaging(
            model_updates=model_updates,
            weights=weights
        )
        
        return jsonify({
            'success': True,
            'aggregated_model': aggregated_model
        })
        
    except Exception as e:
        logging.error(f"Error in federated averaging: {str(e)}")
        return jsonify({'error': f'Aggregation failed: {str(e)}'}), 500

@federated_bp.route('/api/federated/privacy/differential', methods=['POST'])
def apply_differential_privacy():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_updates = data.get('model_updates', [])
        epsilon = data.get('epsilon', 1.0)
        delta = data.get('delta', 1e-5)
        
        if not model_updates:
            return jsonify({'error': 'Model updates are required'}), 400
        
        federated_service = FederatedService()
        private_updates = federated_service.apply_differential_privacy(
            model_updates=model_updates,
            epsilon=epsilon,
            delta=delta
        )
        
        return jsonify({
            'success': True,
            'private_updates': private_updates,
            'privacy_budget': {
                'epsilon': epsilon,
                'delta': delta
            }
        })
        
    except Exception as e:
        logging.error(f"Error applying differential privacy: {str(e)}")
        return jsonify({'error': f'Privacy mechanism failed: {str(e)}'}), 500

@federated_bp.route('/api/federated/secure-aggregation', methods=['POST'])
def secure_aggregation():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        encrypted_updates = data.get('encrypted_updates', [])
        
        if not encrypted_updates:
            return jsonify({'error': 'Encrypted updates are required'}), 400
        
        federated_service = FederatedService()
        result = federated_service.secure_multiparty_aggregation(
            encrypted_updates=encrypted_updates
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Error in secure aggregation: {str(e)}")
        return jsonify({'error': f'Secure aggregation failed: {str(e)}'}), 500

@federated_bp.route('/api/federated/analytics/performance')
def get_performance_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        nodes = FederatedNode.query.filter_by(user_id=user.id).all()
        
        # Mock analytics data
        analytics = {
            'total_nodes': len(nodes),
            'active_nodes': len([n for n in nodes if n.status == 'active']),
            'training_rounds': 0,
            'average_accuracy': 0.0,
            'communication_rounds': 0,
            'convergence_time': 0.0,
            'privacy_budget_used': 0.0,
            'node_performance': []
        }
        
        for node in nodes:
            analytics['node_performance'].append({
                'node_id': str(node.id),
                'node_name': node.node_name,
                'status': node.status,
                'last_seen': node.last_seen.isoformat() if node.last_seen else None,
                'capabilities': node.capabilities
            })
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logging.error(f"Error getting federated analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500
