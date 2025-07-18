from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, NeuromorphicDevice, SpikingNeuralNetwork
from blueprints.auth import login_required, get_current_user
from services.neuromorphic_service import NeuromorphicService
import logging
import json
from datetime import datetime

neuromorphic_bp = Blueprint('neuromorphic', __name__)

@neuromorphic_bp.route('/')
@login_required
def neuromorphic_index():
    user = get_current_user()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id).order_by(NeuromorphicDevice.created_at.desc()).limit(10).all()
    networks = SpikingNeuralNetwork.query.filter_by(user_id=user.id).order_by(SpikingNeuralNetwork.created_at.desc()).limit(10).all()
    
    # Calculate summary statistics
    online_devices = NeuromorphicDevice.query.filter_by(user_id=user.id, is_online=True).count()
    total_networks = SpikingNeuralNetwork.query.filter_by(user_id=user.id).count()
    
    return render_template('neuromorphic/dashboard.html', 
                         user=user, 
                         devices=devices, 
                         networks=networks,
                         online_devices=online_devices,
                         total_networks=total_networks)

@neuromorphic_bp.route('/snn')
@login_required
def spiking_neural_networks():
    user = get_current_user()
    networks = SpikingNeuralNetwork.query.filter_by(user_id=user.id).order_by(SpikingNeuralNetwork.created_at.desc()).all()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id, is_online=True).all()
    
    return render_template('neuromorphic/snn.html', 
                         user=user, 
                         networks=networks,
                         devices=devices)

@neuromorphic_bp.route('/edge')
@login_required
def edge_deployment():
    user = get_current_user()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id).order_by(NeuromorphicDevice.created_at.desc()).all()
    
    return render_template('neuromorphic/edge.html', 
                         user=user, 
                         devices=devices)

@neuromorphic_bp.route('/hardware')
@login_required
def neuromorphic_hardware():
    user = get_current_user()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id).order_by(NeuromorphicDevice.created_at.desc()).all()
    
    # Available hardware types
    hardware_types = [
        {
            'id': 'loihi',
            'name': 'Intel Loihi',
            'description': 'Intel\'s neuromorphic research chip',
            'neurons': 131072,
            'synapses': 130000000,
            'power': '30mW'
        },
        {
            'id': 'truenorth',
            'name': 'IBM TrueNorth',
            'description': 'IBM\'s brain-inspired processor',
            'neurons': 1000000,
            'synapses': 256000000,
            'power': '70mW'
        },
        {
            'id': 'spinnaker',
            'name': 'SpiNNaker',
            'description': 'Massively parallel computer architecture',
            'neurons': 1000000,
            'synapses': 1000000000,
            'power': '1W'
        },
        {
            'id': 'akida',
            'name': 'BrainChip Akida',
            'description': 'Commercial neuromorphic processor',
            'neurons': 1200000,
            'synapses': 10000000,
            'power': '200mW'
        }
    ]
    
    return render_template('neuromorphic/hardware.html', 
                         user=user, 
                         devices=devices,
                         hardware_types=hardware_types)

@neuromorphic_bp.route('/devices/create', methods=['POST'])
@login_required
def create_device():
    user = get_current_user()
    data = request.get_json()
    
    device_name = data.get('device_name')
    device_type = data.get('device_type')
    endpoint_url = data.get('endpoint_url')
    specifications = data.get('specifications', {})
    
    if not device_name or not device_type:
        return jsonify({'error': 'Device name and type are required'}), 400
    
    try:
        device = NeuromorphicDevice(
            user_id=user.id,
            device_name=device_name,
            device_type=device_type,
            endpoint_url=endpoint_url,
            specifications=json.dumps(specifications),
            is_online=False
        )
        
        db.session.add(device)
        db.session.commit()
        
        logging.info(f"Neuromorphic device created: {device.id}")
        return jsonify({
            'success': True,
            'device_id': device.id,
            'message': 'Neuromorphic device created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating neuromorphic device: {str(e)}")
        return jsonify({'error': 'Failed to create neuromorphic device'}), 500

@neuromorphic_bp.route('/devices/<int:device_id>/connect', methods=['POST'])
@login_required
def connect_device(device_id):
    user = get_current_user()
    device = NeuromorphicDevice.query.filter_by(id=device_id, user_id=user.id).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        connection_result = neuromorphic_service.connect_device(
            device_type=device.device_type,
            endpoint_url=device.endpoint_url,
            specifications=json.loads(device.specifications) if device.specifications else {}
        )
        
        if connection_result['success']:
            device.is_online = True
            db.session.commit()
            
            logging.info(f"Neuromorphic device connected: {device.id}")
            return jsonify({
                'success': True,
                'message': 'Device connected successfully',
                'device_info': connection_result.get('device_info', {})
            })
        else:
            return jsonify({'error': connection_result.get('error', 'Failed to connect device')}), 500
    
    except Exception as e:
        logging.error(f"Error connecting neuromorphic device: {str(e)}")
        return jsonify({'error': 'Failed to connect device'}), 500

@neuromorphic_bp.route('/snn/create', methods=['POST'])
@login_required
def create_snn():
    user = get_current_user()
    data = request.get_json()
    
    network_name = data.get('network_name')
    architecture = data.get('architecture')
    device_id = data.get('device_id')
    
    if not network_name or not architecture:
        return jsonify({'error': 'Network name and architecture are required'}), 400
    
    try:
        network = SpikingNeuralNetwork(
            user_id=user.id,
            network_name=network_name,
            architecture=json.dumps(architecture),
            device_id=device_id,
            training_data=json.dumps({}),
            performance_metrics=json.dumps({})
        )
        
        db.session.add(network)
        db.session.commit()
        
        logging.info(f"Spiking neural network created: {network.id}")
        return jsonify({
            'success': True,
            'network_id': network.id,
            'message': 'Spiking neural network created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating spiking neural network: {str(e)}")
        return jsonify({'error': 'Failed to create spiking neural network'}), 500

@neuromorphic_bp.route('/snn/<int:network_id>/train', methods=['POST'])
@login_required
def train_snn(network_id):
    user = get_current_user()
    network = SpikingNeuralNetwork.query.filter_by(id=network_id, user_id=user.id).first_or_404()
    
    data = request.get_json()
    training_data = data.get('training_data', {})
    training_params = data.get('training_params', {})
    
    try:
        neuromorphic_service = NeuromorphicService()
        training_result = neuromorphic_service.train_snn(
            network_id=network.id,
            architecture=json.loads(network.architecture),
            training_data=training_data,
            training_params=training_params
        )
        
        if training_result['success']:
            # Update training data and performance metrics
            network.training_data = json.dumps(training_data)
            network.performance_metrics = json.dumps(training_result.get('metrics', {}))
            db.session.commit()
            
            logging.info(f"Spiking neural network trained: {network.id}")
            return jsonify({
                'success': True,
                'message': 'Spiking neural network trained successfully',
                'metrics': training_result.get('metrics', {})
            })
        else:
            return jsonify({'error': training_result.get('error', 'Failed to train network')}), 500
    
    except Exception as e:
        logging.error(f"Error training spiking neural network: {str(e)}")
        return jsonify({'error': 'Failed to train spiking neural network'}), 500

@neuromorphic_bp.route('/learning')
@login_required
def spike_learning():
    user = get_current_user()
    
    # Available learning algorithms
    learning_algorithms = [
        {
            'name': 'Spike-Timing Dependent Plasticity (STDP)',
            'description': 'Hebbian learning rule based on spike timing',
            'use_case': 'Unsupervised learning, pattern recognition',
            'complexity': 'Low'
        },
        {
            'name': 'Reward-Modulated STDP',
            'description': 'STDP with dopamine-like reward signal',
            'use_case': 'Reinforcement learning tasks',
            'complexity': 'Medium'
        },
        {
            'name': 'Tempotron',
            'description': 'Supervised learning for temporal patterns',
            'use_case': 'Temporal sequence learning',
            'complexity': 'Medium'
        },
        {
            'name': 'SpikeProp',
            'description': 'Backpropagation for spiking networks',
            'use_case': 'Supervised classification',
            'complexity': 'High'
        },
        {
            'name': 'Evolutionary Spike Training',
            'description': 'Evolutionary optimization of spike patterns',
            'use_case': 'Network topology optimization',
            'complexity': 'High'
        }
    ]
    
    return render_template('neuromorphic/learning.html', 
                         user=user,
                         learning_algorithms=learning_algorithms)

@neuromorphic_bp.route('/optimization')
@login_required
def energy_optimization():
    user = get_current_user()
    return render_template('neuromorphic/optimization.html', user=user)

@neuromorphic_bp.route('/realtime')
@login_required
def realtime_processing():
    user = get_current_user()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id, is_online=True).all()
    
    return render_template('neuromorphic/realtime.html', 
                         user=user,
                         devices=devices)

@neuromorphic_bp.route('/spike-visualization/<int:network_id>')
@login_required
def spike_visualization(network_id):
    user = get_current_user()
    network = SpikingNeuralNetwork.query.filter_by(id=network_id, user_id=user.id).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        spike_data = neuromorphic_service.get_spike_visualization(
            network_id=network.id,
            time_window=1000  # 1 second
        )
        
        return jsonify({
            'success': True,
            'network_id': network.id,
            'spike_data': spike_data
        })
    
    except Exception as e:
        logging.error(f"Error getting spike visualization: {str(e)}")
        return jsonify({'error': 'Failed to get spike visualization'}), 500

@neuromorphic_bp.route('/power-analysis/<int:device_id>')
@login_required
def power_analysis(device_id):
    user = get_current_user()
    device = NeuromorphicDevice.query.filter_by(id=device_id, user_id=user.id).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        power_data = neuromorphic_service.analyze_power_consumption(
            device_id=device.id,
            device_type=device.device_type
        )
        
        return jsonify({
            'success': True,
            'device_id': device.id,
            'power_analysis': power_data
        })
    
    except Exception as e:
        logging.error(f"Error analyzing power consumption: {str(e)}")
        return jsonify({'error': 'Failed to analyze power consumption'}), 500
