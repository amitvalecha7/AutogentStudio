from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import NeuromorphicDevice, SpikingNeuralNetwork, db
from services.neuromorphic_service import NeuromorphicService
import uuid

neuromorphic_bp = Blueprint('neuromorphic', __name__, url_prefix='/neuromorphic')

@neuromorphic_bp.route('/')
@login_required
def index():
    # Get user's neuromorphic devices and networks
    devices = NeuromorphicDevice.query.filter_by(
        user_id=current_user.id
    ).order_by(NeuromorphicDevice.created_at.desc()).all()
    
    networks = SpikingNeuralNetwork.query.filter_by(
        user_id=current_user.id
    ).order_by(SpikingNeuralNetwork.created_at.desc()).all()
    
    return render_template('neuromorphic/index.html', 
                         devices=devices, 
                         networks=networks)

@neuromorphic_bp.route('/snn')
@login_required
def snn():
    networks = SpikingNeuralNetwork.query.filter_by(
        user_id=current_user.id
    ).order_by(SpikingNeuralNetwork.created_at.desc()).all()
    
    return render_template('neuromorphic/snn.html', networks=networks)

@neuromorphic_bp.route('/edge')
@login_required
def edge():
    return render_template('neuromorphic/edge.html')

@neuromorphic_bp.route('/hardware')
@login_required
def hardware():
    devices = NeuromorphicDevice.query.filter_by(
        user_id=current_user.id
    ).order_by(NeuromorphicDevice.created_at.desc()).all()
    
    return render_template('neuromorphic/hardware.html', devices=devices)

@neuromorphic_bp.route('/learning')
@login_required
def learning():
    return render_template('neuromorphic/learning.html')

@neuromorphic_bp.route('/optimization')
@login_required
def optimization():
    return render_template('neuromorphic/optimization.html')

@neuromorphic_bp.route('/realtime')
@login_required
def realtime():
    return render_template('neuromorphic/realtime.html')

@neuromorphic_bp.route('/create-snn', methods=['POST'])
@login_required
def create_snn():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    neuron_model = data.get('neuron_model', 'lif')
    architecture = data.get('architecture', {})
    
    if not name:
        return jsonify({'error': 'SNN name is required'}), 400
    
    if not architecture:
        return jsonify({'error': 'Network architecture is required'}), 400
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Create spiking neural network
        network_data = neuromorphic_service.create_snn(
            architecture=architecture,
            neuron_model=neuron_model
        )
        
        network_id = str(uuid.uuid4())
        snn = SpikingNeuralNetwork(
            id=network_id,
            user_id=current_user.id,
            name=name,
            architecture=architecture,
            neuron_model=neuron_model,
            network_size=architecture.get('size', 0),
            deployment_target=data.get('deployment_target', ''),
            performance_metrics={}
        )
        
        db.session.add(snn)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'network_id': network_id,
            'network_data': network_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/snn/<network_id>')
@login_required
def view_snn(network_id):
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('neuromorphic/snn_detail.html', network=network)

@neuromorphic_bp.route('/snn/<network_id>/train', methods=['POST'])
@login_required
def train_snn(network_id):
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    training_data = data.get('training_data', {})
    learning_rule = data.get('learning_rule', 'stdp')
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Train SNN
        training_results = neuromorphic_service.train_snn(
            network=network,
            training_data=training_data,
            learning_rule=learning_rule
        )
        
        # Update performance metrics
        network.performance_metrics = training_results.get('metrics', {})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': training_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/snn/<network_id>/simulate', methods=['POST'])
@login_required
def simulate_snn(network_id):
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    input_spikes = data.get('input_spikes', [])
    simulation_time = data.get('simulation_time', 1000)  # ms
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Simulate SNN
        simulation_results = neuromorphic_service.simulate_snn(
            network=network,
            input_spikes=input_spikes,
            simulation_time=simulation_time
        )
        
        return jsonify({
            'success': True,
            'results': simulation_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/register-device', methods=['POST'])
@login_required
def register_device():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    device_type = data.get('device_type', 'loihi')
    location = data.get('location', '')
    
    if not name:
        return jsonify({'error': 'Device name is required'}), 400
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        device_id = str(uuid.uuid4())
        device = NeuromorphicDevice(
            id=device_id,
            user_id=current_user.id,
            name=name,
            device_type=device_type,
            location=location,
            capabilities=data.get('capabilities', {}),
            status='offline'
        )
        
        db.session.add(device)
        db.session.commit()
        
        # Initialize device connection
        connection_result = neuromorphic_service.connect_device(device)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'connection': connection_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/device/<device_id>')
@login_required
def view_device(device_id):
    device = NeuromorphicDevice.query.filter_by(
        id=device_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('neuromorphic/device_detail.html', device=device)

@neuromorphic_bp.route('/device/<device_id>/deploy', methods=['POST'])
@login_required
def deploy_to_device(device_id):
    device = NeuromorphicDevice.query.filter_by(
        id=device_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    network_id = data.get('network_id')
    
    if not network_id:
        return jsonify({'error': 'Network ID is required'}), 400
    
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Deploy network to device
        deployment_results = neuromorphic_service.deploy_to_device(
            network=network,
            device=device
        )
        
        # Update network deployment target
        network.deployment_target = device_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': deployment_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/spike-visualization/<network_id>')
@login_required
def spike_visualization(network_id):
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Generate spike visualization data
        visualization_data = neuromorphic_service.generate_spike_visualization(network)
        
        return jsonify({
            'success': True,
            'visualization': visualization_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/energy-analysis', methods=['POST'])
@login_required
def energy_analysis():
    data = request.get_json()
    
    network_id = data.get('network_id')
    workload = data.get('workload', {})
    
    if not network_id:
        return jsonify({'error': 'Network ID is required'}), 400
    
    network = SpikingNeuralNetwork.query.filter_by(
        id=network_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        neuromorphic_service = NeuromorphicService()
        
        # Analyze energy consumption
        energy_analysis = neuromorphic_service.analyze_energy_consumption(
            network=network,
            workload=workload
        )
        
        return jsonify({
            'success': True,
            'analysis': energy_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@neuromorphic_bp.route('/platforms')
@login_required
def platforms():
    platforms = {
        'loihi': {
            'name': 'Intel Loihi',
            'description': 'Neuromorphic research chip by Intel',
            'neuron_capacity': 131072,
            'synapse_capacity': 131000000,
            'power_consumption': '30mW',
            'supported_models': ['lif', 'adaptive_lif']
        },
        'truenorth': {
            'name': 'IBM TrueNorth',
            'description': 'Neuromorphic processor by IBM',
            'neuron_capacity': 1000000,
            'synapse_capacity': 256000000,
            'power_consumption': '65mW',
            'supported_models': ['lif']
        },
        'spinnaker': {
            'name': 'SpiNNaker',
            'description': 'Spiking neural network architecture',
            'neuron_capacity': 1000000,
            'synapse_capacity': 1000000000,
            'power_consumption': '1W',
            'supported_models': ['lif', 'izhikevich', 'hodgkin_huxley']
        }
    }
    
    return jsonify({
        'success': True,
        'platforms': platforms
    })
