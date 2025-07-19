from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, SafetyProtocol
from services.safety_service import SafetyService
import logging

safety_bp = Blueprint('safety', __name__)

@safety_bp.route('/safety')
def safety_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    protocols = SafetyProtocol.query.filter_by(user_id=user.id).all()
    
    return render_template('safety/safety.html', user=user, protocols=protocols)

@safety_bp.route('/safety/alignment')
def alignment_monitoring():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/alignment.html', user=user)

@safety_bp.route('/safety/robustness')
def robustness_evaluation():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/robustness.html', user=user)

@safety_bp.route('/safety/interpretability')
def interpretability_analysis():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/interpretability.html', user=user)

@safety_bp.route('/safety/bias')
def bias_detection():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/bias.html', user=user)

@safety_bp.route('/safety/adversarial')
def adversarial_testing():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/adversarial.html', user=user)

@safety_bp.route('/safety/constitutional')
def constitutional_ai():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/constitutional.html', user=user)

@safety_bp.route('/safety/values')
def value_alignment():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/values.html', user=user)

@safety_bp.route('/safety/automation')
def safety_automation():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('safety/automation.html', user=user)

@safety_bp.route('/api/safety/protocols', methods=['GET', 'POST'])
def api_protocols():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            protocol_type = data.get('protocol_type', '').strip()
            configuration = data.get('configuration', {})
            
            if not all([name, protocol_type]):
                return jsonify({'error': 'Name and protocol type are required'}), 400
            
            protocol = SafetyProtocol(
                user_id=user.id,
                name=name,
                description=data.get('description', ''),
                protocol_type=protocol_type,
                configuration=configuration
            )
            
            db.session.add(protocol)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'protocol': protocol.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error creating safety protocol: {str(e)}")
            return jsonify({'error': 'Failed to create protocol'}), 500
    
    # GET request
    protocols = SafetyProtocol.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'protocols': [protocol.to_dict() for protocol in protocols]
    })

@safety_bp.route('/api/safety/alignment/monitor', methods=['POST'])
def monitor_alignment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_output = data.get('model_output', '')
        reference_values = data.get('reference_values', [])
        
        if not model_output:
            return jsonify({'error': 'Model output is required'}), 400
        
        safety_service = SafetyService()
        alignment_score = safety_service.assess_alignment(
            model_output=model_output,
            reference_values=reference_values
        )
        
        return jsonify({
            'success': True,
            'alignment_score': alignment_score
        })
        
    except Exception as e:
        logging.error(f"Error monitoring alignment: {str(e)}")
        return jsonify({'error': f'Alignment monitoring failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/robustness/test', methods=['POST'])
def test_robustness():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        test_cases = data.get('test_cases', [])
        perturbation_types = data.get('perturbation_types', ['noise', 'adversarial'])
        
        if not model_id:
            return jsonify({'error': 'Model ID is required'}), 400
        
        safety_service = SafetyService()
        robustness_results = safety_service.test_robustness(
            model_id=model_id,
            test_cases=test_cases,
            perturbation_types=perturbation_types
        )
        
        return jsonify({
            'success': True,
            'robustness_results': robustness_results
        })
        
    except Exception as e:
        logging.error(f"Error testing robustness: {str(e)}")
        return jsonify({'error': f'Robustness testing failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/interpretability/explain', methods=['POST'])
def explain_decision():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        input_data = data.get('input_data')
        explanation_method = data.get('explanation_method', 'lime')
        
        if not all([model_id, input_data]):
            return jsonify({'error': 'Model ID and input data are required'}), 400
        
        safety_service = SafetyService()
        explanation = safety_service.explain_decision(
            model_id=model_id,
            input_data=input_data,
            explanation_method=explanation_method
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
        
    except Exception as e:
        logging.error(f"Error explaining decision: {str(e)}")
        return jsonify({'error': f'Explanation failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/bias/detect', methods=['POST'])
def detect_bias():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        test_data = data.get('test_data', [])
        protected_attributes = data.get('protected_attributes', [])
        
        if not model_id:
            return jsonify({'error': 'Model ID is required'}), 400
        
        safety_service = SafetyService()
        bias_results = safety_service.detect_bias(
            model_id=model_id,
            test_data=test_data,
            protected_attributes=protected_attributes
        )
        
        return jsonify({
            'success': True,
            'bias_results': bias_results
        })
        
    except Exception as e:
        logging.error(f"Error detecting bias: {str(e)}")
        return jsonify({'error': f'Bias detection failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/adversarial/generate', methods=['POST'])
def generate_adversarial():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        input_data = data.get('input_data')
        attack_method = data.get('attack_method', 'fgsm')
        epsilon = data.get('epsilon', 0.1)
        
        if not all([model_id, input_data]):
            return jsonify({'error': 'Model ID and input data are required'}), 400
        
        safety_service = SafetyService()
        adversarial_examples = safety_service.generate_adversarial_examples(
            model_id=model_id,
            input_data=input_data,
            attack_method=attack_method,
            epsilon=epsilon
        )
        
        return jsonify({
            'success': True,
            'adversarial_examples': adversarial_examples
        })
        
    except Exception as e:
        logging.error(f"Error generating adversarial examples: {str(e)}")
        return jsonify({'error': f'Adversarial generation failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/constitutional/apply', methods=['POST'])
def apply_constitutional_ai():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_response = data.get('model_response', '')
        constitutional_principles = data.get('constitutional_principles', [])
        
        if not model_response:
            return jsonify({'error': 'Model response is required'}), 400
        
        safety_service = SafetyService()
        constitutional_result = safety_service.apply_constitutional_ai(
            model_response=model_response,
            constitutional_principles=constitutional_principles
        )
        
        return jsonify({
            'success': True,
            'constitutional_result': constitutional_result
        })
        
    except Exception as e:
        logging.error(f"Error applying constitutional AI: {str(e)}")
        return jsonify({'error': f'Constitutional AI failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/values/align', methods=['POST'])
def align_values():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        model_behavior = data.get('model_behavior', '')
        target_values = data.get('target_values', [])
        alignment_method = data.get('alignment_method', 'preference_learning')
        
        if not model_behavior:
            return jsonify({'error': 'Model behavior is required'}), 400
        
        safety_service = SafetyService()
        alignment_result = safety_service.align_values(
            model_behavior=model_behavior,
            target_values=target_values,
            alignment_method=alignment_method
        )
        
        return jsonify({
            'success': True,
            'alignment_result': alignment_result
        })
        
    except Exception as e:
        logging.error(f"Error aligning values: {str(e)}")
        return jsonify({'error': f'Value alignment failed: {str(e)}'}), 500

@safety_bp.route('/api/safety/monitoring/realtime')
def realtime_safety_monitoring():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        safety_service = SafetyService()
        monitoring_data = safety_service.get_realtime_monitoring()
        
        return jsonify({
            'success': True,
            'monitoring_data': monitoring_data
        })
        
    except Exception as e:
        logging.error(f"Error getting realtime monitoring: {str(e)}")
        return jsonify({'error': 'Failed to get monitoring data'}), 500

@safety_bp.route('/api/safety/analytics')
def get_safety_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        safety_service = SafetyService()
        analytics = safety_service.get_safety_analytics(user.id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logging.error(f"Error getting safety analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500
