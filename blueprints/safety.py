from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import SafetyProtocol, SafetyViolation, db
from services.safety_service import SafetyService
import uuid

safety_bp = Blueprint('safety', __name__, url_prefix='/safety')

@safety_bp.route('/')
@login_required
def index():
    # Get safety protocols and recent violations
    protocols = SafetyProtocol.query.filter_by(
        is_active=True
    ).order_by(SafetyProtocol.created_at.desc()).all()
    
    recent_violations = SafetyViolation.query.filter_by(
        user_id=current_user.id,
        resolved=False
    ).order_by(SafetyViolation.created_at.desc()).limit(10).all()
    
    return render_template('safety/index.html', 
                         protocols=protocols, 
                         violations=recent_violations)

@safety_bp.route('/alignment')
@login_required
def alignment():
    return render_template('safety/alignment.html')

@safety_bp.route('/robustness')
@login_required
def robustness():
    return render_template('safety/robustness.html')

@safety_bp.route('/interpretability')
@login_required
def interpretability():
    return render_template('safety/interpretability.html')

@safety_bp.route('/bias')
@login_required
def bias():
    return render_template('safety/bias.html')

@safety_bp.route('/adversarial')
@login_required
def adversarial():
    return render_template('safety/adversarial.html')

@safety_bp.route('/constitutional')
@login_required
def constitutional():
    return render_template('safety/constitutional.html')

@safety_bp.route('/values')
@login_required
def values():
    return render_template('safety/values.html')

@safety_bp.route('/automation')
@login_required
def automation():
    return render_template('safety/automation.html')

@safety_bp.route('/create-protocol', methods=['POST'])
@login_required
def create_protocol():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    protocol_type = data.get('protocol_type', 'alignment')
    implementation = data.get('implementation', {})
    severity_level = data.get('severity_level', 'medium')
    
    if not name:
        return jsonify({'error': 'Protocol name is required'}), 400
    
    if not implementation:
        return jsonify({'error': 'Protocol implementation is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        protocol_id = str(uuid.uuid4())
        protocol = SafetyProtocol(
            id=protocol_id,
            name=name,
            description=data.get('description', ''),
            protocol_type=protocol_type,
            implementation=implementation,
            severity_level=severity_level,
            is_active=True
        )
        
        db.session.add(protocol)
        db.session.commit()
        
        # Initialize protocol
        initialization_result = safety_service.initialize_protocol(protocol)
        
        return jsonify({
            'success': True,
            'protocol_id': protocol_id,
            'initialization': initialization_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/protocol/<protocol_id>')
@login_required
def view_protocol(protocol_id):
    protocol = SafetyProtocol.query.get_or_404(protocol_id)
    
    # Get violations for this protocol
    violations = SafetyViolation.query.filter_by(
        protocol_id=protocol_id
    ).order_by(SafetyViolation.created_at.desc()).all()
    
    return render_template('safety/protocol_detail.html', 
                         protocol=protocol, 
                         violations=violations)

@safety_bp.route('/protocol/<protocol_id>/test', methods=['POST'])
@login_required
def test_protocol(protocol_id):
    protocol = SafetyProtocol.query.get_or_404(protocol_id)
    
    data = request.get_json()
    test_input = data.get('test_input', '')
    test_type = data.get('test_type', 'basic')
    
    if not test_input:
        return jsonify({'error': 'Test input is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Run safety test
        test_results = safety_service.test_protocol(
            protocol=protocol,
            test_input=test_input,
            test_type=test_type
        )
        
        return jsonify({
            'success': True,
            'results': test_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/check-alignment', methods=['POST'])
@login_required
def check_alignment():
    data = request.get_json()
    
    model_output = data.get('model_output', '')
    context = data.get('context', {})
    
    if not model_output:
        return jsonify({'error': 'Model output is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Check alignment
        alignment_results = safety_service.check_alignment(
            model_output=model_output,
            context=context
        )
        
        # Log potential violations
        if alignment_results.get('violation_detected'):
            violation_id = str(uuid.uuid4())
            violation = SafetyViolation(
                id=violation_id,
                protocol_id=None,  # General alignment check
                user_id=current_user.id,
                violation_type='alignment',
                severity=alignment_results.get('severity', 'medium'),
                details=alignment_results,
                resolved=False
            )
            
            db.session.add(violation)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'results': alignment_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/detect-bias', methods=['POST'])
@login_required
def detect_bias():
    data = request.get_json()
    
    text_input = data.get('text_input', '')
    bias_types = data.get('bias_types', ['gender', 'racial', 'age'])
    
    if not text_input:
        return jsonify({'error': 'Text input is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Detect bias
        bias_results = safety_service.detect_bias(
            text_input=text_input,
            bias_types=bias_types
        )
        
        # Log bias detection results
        if bias_results.get('bias_detected'):
            violation_id = str(uuid.uuid4())
            violation = SafetyViolation(
                id=violation_id,
                protocol_id=None,
                user_id=current_user.id,
                violation_type='bias',
                severity=bias_results.get('severity', 'medium'),
                details=bias_results,
                resolved=False
            )
            
            db.session.add(violation)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'results': bias_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/adversarial-test', methods=['POST'])
@login_required
def adversarial_test():
    data = request.get_json()
    
    model_id = data.get('model_id', '')
    attack_type = data.get('attack_type', 'prompt_injection')
    test_cases = data.get('test_cases', [])
    
    if not model_id:
        return jsonify({'error': 'Model ID is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Run adversarial tests
        test_results = safety_service.run_adversarial_tests(
            model_id=model_id,
            attack_type=attack_type,
            test_cases=test_cases
        )
        
        return jsonify({
            'success': True,
            'results': test_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/constitutional-ai', methods=['POST'])
@login_required
def constitutional_ai():
    data = request.get_json()
    
    prompt = data.get('prompt', '')
    constitution_rules = data.get('constitution_rules', [])
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Apply constitutional AI
        constitutional_results = safety_service.apply_constitutional_ai(
            prompt=prompt,
            constitution_rules=constitution_rules
        )
        
        return jsonify({
            'success': True,
            'results': constitutional_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/interpretability-analysis', methods=['POST'])
@login_required
def interpretability_analysis():
    data = request.get_json()
    
    model_output = data.get('model_output', '')
    analysis_type = data.get('analysis_type', 'attention')
    
    if not model_output:
        return jsonify({'error': 'Model output is required'}), 400
    
    try:
        safety_service = SafetyService()
        
        # Run interpretability analysis
        analysis_results = safety_service.analyze_interpretability(
            model_output=model_output,
            analysis_type=analysis_type
        )
        
        return jsonify({
            'success': True,
            'results': analysis_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/violations')
@login_required
def violations():
    user_violations = SafetyViolation.query.filter_by(
        user_id=current_user.id
    ).order_by(SafetyViolation.created_at.desc()).all()
    
    return render_template('safety/violations.html', violations=user_violations)

@safety_bp.route('/violation/<violation_id>/resolve', methods=['POST'])
@login_required
def resolve_violation(violation_id):
    violation = SafetyViolation.query.filter_by(
        id=violation_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    resolution_notes = data.get('resolution_notes', '')
    
    try:
        violation.resolved = True
        violation.details['resolution_notes'] = resolution_notes
        violation.details['resolved_at'] = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Violation marked as resolved'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@safety_bp.route('/monitoring-dashboard')
@login_required
def monitoring_dashboard():
    # Get real-time safety monitoring data
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Recent violations
    recent_violations = SafetyViolation.query.filter(
        SafetyViolation.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Violation types breakdown
    violation_types = db.session.query(
        SafetyViolation.violation_type,
        func.count(SafetyViolation.id)
    ).group_by(SafetyViolation.violation_type).all()
    
    # Active protocols
    active_protocols = SafetyProtocol.query.filter_by(is_active=True).count()
    
    monitoring_data = {
        'recent_violations': recent_violations,
        'violation_types': dict(violation_types),
        'active_protocols': active_protocols,
        'safety_score': 95.7  # Would be calculated based on actual metrics
    }
    
    return jsonify({
        'success': True,
        'data': monitoring_data
    })
