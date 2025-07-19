from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User
from services.neuromorphic_service import NeuromorphicService
import logging

neuromorphic_bp = Blueprint('neuromorphic', __name__)

@neuromorphic_bp.route('/neuromorphic')
def neuromorphic_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/neuromorphic.html', user=user)

@neuromorphic_bp.route('/neuromorphic/snn')
def spiking_networks():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/snn.html', user=user)

@neuromorphic_bp.route('/neuromorphic/edge')
def edge_deployment():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/edge.html', user=user)

@neuromorphic_bp.route('/neuromorphic/hardware')
def hardware_integration():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/hardware.html', user=user)

@neuromorphic_bp.route('/neuromorphic/learning')
def spike_learning():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/learning.html', user=user)

@neuromorphic_bp.route('/neuromorphic/optimization')
def energy_optimization():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/optimization.html', user=user)

@neuromorphic_bp.route('/neuromorphic/realtime')
def realtime_processing():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('neuromorphic/realtime.html', user=user)

@neuromorphic_bp.route('/api/neuromorphic/networks', methods=['POST'])
def create_snn():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        network_config = data.get('network_config', {})
        
        neuromorphic_service = NeuromorphicService()
        network = neuromorphic_service.create_spiking_network(network_config)
        
        return jsonify({
            'success': True,
            'network': network
        })
        
    except Exception as e:
        logging.error(f"Error creating SNN: {str(e)}")
        return jsonify({'error': f'Failed to create network: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/simulate', methods=['POST'])
def simulate_spikes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        network_id = data.get('network_id')
        input_spikes = data.get('input_spikes', [])
        duration = data.get('duration', 1000)  # ms
        
        neuromorphic_service = NeuromorphicService()
        result = neuromorphic_service.simulate_network(
            network_id=network_id,
            input_spikes=input_spikes,
            duration=duration
        )
        
        return jsonify({
            'success': True,
            'simulation_result': result
        })
        
    except Exception as e:
        logging.error(f"Error simulating spikes: {str(e)}")
        return jsonify({'error': f'Simulation failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/edge/deploy', methods=['POST'])
def deploy_to_edge():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        edge_device = data.get('edge_device', {})
        optimization_level = data.get('optimization_level', 'medium')
        
        neuromorphic_service = NeuromorphicService()
        deployment = neuromorphic_service.deploy_to_edge(
            model_id=model_id,
            edge_device=edge_device,
            optimization_level=optimization_level
        )
        
        return jsonify({
            'success': True,
            'deployment': deployment
        })
        
    except Exception as e:
        logging.error(f"Error deploying to edge: {str(e)}")
        return jsonify({'error': f'Edge deployment failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/hardware/loihi', methods=['POST'])
def connect_loihi():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        loihi_config = data.get('loihi_config', {})
        
        neuromorphic_service = NeuromorphicService()
        connection = neuromorphic_service.connect_intel_loihi(loihi_config)
        
        return jsonify({
            'success': True,
            'connection': connection
        })
        
    except Exception as e:
        logging.error(f"Error connecting to Loihi: {str(e)}")
        return jsonify({'error': f'Loihi connection failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/hardware/truenorth', methods=['POST'])
def connect_truenorth():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        truenorth_config = data.get('truenorth_config', {})
        
        neuromorphic_service = NeuromorphicService()
        connection = neuromorphic_service.connect_ibm_truenorth(truenorth_config)
        
        return jsonify({
            'success': True,
            'connection': connection
        })
        
    except Exception as e:
        logging.error(f"Error connecting to TrueNorth: {str(e)}")
        return jsonify({'error': f'TrueNorth connection failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/learning/stdp', methods=['POST'])
def apply_stdp_learning():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        network_id = data.get('network_id')
        learning_params = data.get('learning_params', {})
        
        neuromorphic_service = NeuromorphicService()
        result = neuromorphic_service.apply_stdp_learning(
            network_id=network_id,
            learning_params=learning_params
        )
        
        return jsonify({
            'success': True,
            'learning_result': result
        })
        
    except Exception as e:
        logging.error(f"Error applying STDP learning: {str(e)}")
        return jsonify({'error': f'STDP learning failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/optimization/energy', methods=['POST'])
def optimize_energy():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        network_id = data.get('network_id')
        power_budget = data.get('power_budget', 1.0)  # watts
        
        neuromorphic_service = NeuromorphicService()
        optimization = neuromorphic_service.optimize_energy_consumption(
            network_id=network_id,
            power_budget=power_budget
        )
        
        return jsonify({
            'success': True,
            'optimization': optimization
        })
        
    except Exception as e:
        logging.error(f"Error optimizing energy: {str(e)}")
        return jsonify({'error': f'Energy optimization failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/realtime/process', methods=['POST'])
def realtime_spike_processing():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        input_stream = data.get('input_stream', [])
        processing_config = data.get('processing_config', {})
        
        neuromorphic_service = NeuromorphicService()
        result = neuromorphic_service.realtime_spike_processing(
            input_stream=input_stream,
            processing_config=processing_config
        )
        
        return jsonify({
            'success': True,
            'processed_output': result
        })
        
    except Exception as e:
        logging.error(f"Error in realtime processing: {str(e)}")
        return jsonify({'error': f'Realtime processing failed: {str(e)}'}), 500

@neuromorphic_bp.route('/api/neuromorphic/analytics')
def get_neuromorphic_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        neuromorphic_service = NeuromorphicService()
        analytics = neuromorphic_service.get_analytics()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logging.error(f"Error getting neuromorphic analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500
