from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, SafetyProtocol, SafetyViolation
from blueprints.auth import login_required, get_current_user
from services.safety_service import SafetyService
import logging
import json
from datetime import datetime

safety_bp = Blueprint('safety', __name__)

@safety_bp.route('/')
@login_required
def safety_index():
    user = get_current_user()
    protocols = SafetyProtocol.query.filter_by(user_id=user.id).order_by(SafetyProtocol.created_at.desc()).limit(10).all()
    violations = SafetyViolation.query.join(SafetyProtocol).filter(SafetyProtocol.user_id == user.id).order_by(SafetyViolation.timestamp.desc()).limit(10).all()
    
    # Calculate summary statistics
    active_protocols = SafetyProtocol.query.filter_by(user_id=user.id, is_active=True).count()
    unresolved_violations = SafetyViolation.query.join(SafetyProtocol).filter(SafetyProtocol.user_id == user.id, SafetyViolation.resolved == False).count()
    
    return render_template('safety/dashboard.html', 
                         user=user, 
                         protocols=protocols, 
                         violations=violations,
                         active_protocols=active_protocols,
                         unresolved_violations=unresolved_violations)

@safety_bp.route('/alignment')
@login_required
def alignment_monitoring():
    user = get_current_user()
    alignment_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='alignment').all()
    
    return render_template('safety/alignment.html', 
                         user=user, 
                         protocols=alignment_protocols)

@safety_bp.route('/robustness')
@login_required
def robustness_evaluation():
    user = get_current_user()
    robustness_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='robustness').all()
    
    return render_template('safety/robustness.html', 
                         user=user, 
                         protocols=robustness_protocols)

@safety_bp.route('/interpretability')
@login_required
def interpretability_analysis():
    user = get_current_user()
    interpretability_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='interpretability').all()
    
    return render_template('safety/interpretability.html', 
                         user=user, 
                         protocols=interpretability_protocols)

@safety_bp.route('/bias')
@login_required
def bias_detection():
    user = get_current_user()
    bias_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='bias').all()
    
    return render_template('safety/bias.html', 
                         user=user, 
                         protocols=bias_protocols)

@safety_bp.route('/adversarial')
@login_required
def adversarial_testing():
    user = get_current_user()
    adversarial_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='adversarial').all()
    
    return render_template('safety/adversarial.html', 
                         user=user, 
                         protocols=adversarial_protocols)

@safety_bp.route('/constitutional')
@login_required
def constitutional_ai():
    user = get_current_user()
    constitutional_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='constitutional').all()
    
    return render_template('safety/constitutional.html', 
                         user=user, 
                         protocols=constitutional_protocols)

@safety_bp.route('/values')
@login_required
def value_alignment():
    user = get_current_user()
    value_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='values').all()
    
    return render_template('safety/values.html', 
                         user=user, 
                         protocols=value_protocols)

@safety_bp.route('/automation')
@login_required
def safety_automation():
    user = get_current_user()
    automation_protocols = SafetyProtocol.query.filter_by(user_id=user.id, protocol_type='automation').all()
    
    return render_template('safety/automation.html', 
                         user=user, 
                         protocols=automation_protocols)

@safety_bp.route('/protocols/create', methods=['POST'])
@login_required
def create_protocol():
    user = get_current_user()
    data = request.get_json()
    
    protocol_name = data.get('protocol_name')
    protocol_type = data.get('protocol_type')
    configuration = data.get('configuration', {})
    
    if not protocol_name or not protocol_type:
        return jsonify({'error': 'Protocol name and type are required'}), 400
    
    try:
        protocol = SafetyProtocol(
            user_id=user.id,
            protocol_name=protocol_name,
            protocol_type=protocol_type,
            configuration=json.dumps(configuration),
            is_active=True
        )
        
        db.session.add(protocol)
        db.session.commit()
        
        logging.info(f"Safety protocol created: {protocol.id}")
        return jsonify({
            'success': True,
            'protocol_id': protocol.id,
            'message': 'Safety protocol created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating safety protocol: {str(e)}")
        return jsonify({'error': 'Failed to create safety protocol'}), 500

@safety_bp.route('/protocols/<int:protocol_id>/run', methods=['POST'])
@login_required
def run_protocol(protocol_id):
    user = get_current_user()
    protocol = SafetyProtocol.query.filter_by(id=protocol_id, user_id=user.id).first_or_404()
    
    data = request.get_json()
    test_data = data.get('test_data', {})
    
    try:
        safety_service = SafetyService()
        result = safety_service.run_safety_protocol(
            protocol_id=protocol.id,
            protocol_type=protocol.protocol_type,
            configuration=json.loads(protocol.configuration),
            test_data=test_data
        )
        
        # Record any violations found
        if result.get('violations'):
            for violation in result['violations']:
                safety_violation = SafetyViolation(
                    protocol_id=protocol.id,
                    violation_type=violation['type'],
                    severity=violation['severity'],
                    details=violation['details'],
                    resolved=False
                )
                db.session.add(safety_violation)
        
        db.session.commit()
        
        logging.info(f"Safety protocol executed: {protocol.id}")
        return jsonify({
            'success': True,
            'results': result,
            'violations_found': len(result.get('violations', []))
        })
    
    except Exception as e:
        logging.error(f"Error running safety protocol: {str(e)}")
        return jsonify({'error': 'Failed to run safety protocol'}), 500

@safety_bp.route('/violations/<int:violation_id>/resolve', methods=['POST'])
@login_required
def resolve_violation(violation_id):
    user = get_current_user()
    violation = SafetyViolation.query.join(SafetyProtocol).filter(
        SafetyViolation.id == violation_id,
        SafetyProtocol.user_id == user.id
    ).first_or_404()
    
    data = request.get_json()
    resolution_notes = data.get('resolution_notes', '')
    
    try:
        violation.resolved = True
        violation.details = json.dumps({
            **json.loads(violation.details) if violation.details else {},
            'resolution_notes': resolution_notes,
            'resolved_at': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        logging.info(f"Safety violation resolved: {violation.id}")
        return jsonify({
            'success': True,
            'message': 'Safety violation marked as resolved'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error resolving safety violation: {str(e)}")
        return jsonify({'error': 'Failed to resolve safety violation'}), 500

@safety_bp.route('/monitoring/realtime')
@login_required
def realtime_monitoring():
    user = get_current_user()
    active_protocols = SafetyProtocol.query.filter_by(user_id=user.id, is_active=True).all()
    
    try:
        safety_service = SafetyService()
        monitoring_data = safety_service.get_realtime_monitoring_data(user.id)
        
        return jsonify({
            'success': True,
            'monitoring_data': monitoring_data,
            'active_protocols': len(active_protocols)
        })
    
    except Exception as e:
        logging.error(f"Error getting realtime monitoring data: {str(e)}")
        return jsonify({'error': 'Failed to get monitoring data'}), 500

@safety_bp.route('/assessment/comprehensive', methods=['POST'])
@login_required
def comprehensive_assessment():
    user = get_current_user()
    data = request.get_json()
    
    model_id = data.get('model_id')
    assessment_type = data.get('assessment_type', 'full')
    
    if not model_id:
        return jsonify({'error': 'Model ID is required'}), 400
    
    try:
        safety_service = SafetyService()
        assessment_result = safety_service.run_comprehensive_assessment(
            user_id=user.id,
            model_id=model_id,
            assessment_type=assessment_type
        )
        
        logging.info(f"Comprehensive safety assessment completed for user {user.id}")
        return jsonify({
            'success': True,
            'assessment_result': assessment_result
        })
    
    except Exception as e:
        logging.error(f"Error running comprehensive assessment: {str(e)}")
        return jsonify({'error': 'Failed to run comprehensive assessment'}), 500
