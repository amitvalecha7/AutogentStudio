from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import UsageMetrics, ChatMessage, ChatSession, File, db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def index():
    # Get overview analytics
    analytics_data = get_overview_analytics()
    
    return render_template('analytics/index.html', analytics=analytics_data)

@analytics_bp.route('/usage')
@login_required
def usage():
    return render_template('analytics/usage.html')

@analytics_bp.route('/behavior')
@login_required
def behavior():
    return render_template('analytics/behavior.html')

@analytics_bp.route('/performance')
@login_required
def performance():
    return render_template('analytics/performance.html')

@analytics_bp.route('/costs')
@login_required
def costs():
    return render_template('analytics/costs.html')

@analytics_bp.route('/reports')
@login_required
def reports():
    return render_template('analytics/reports.html')

@analytics_bp.route('/security')
@login_required
def security():
    return render_template('analytics/security.html')

@analytics_bp.route('/blockchain')
@login_required
def blockchain():
    return render_template('analytics/blockchain.html')

@analytics_bp.route('/quantum')
@login_required
def quantum():
    return render_template('analytics/quantum.html')

@analytics_bp.route('/federated')
@login_required
def federated():
    return render_template('analytics/federated.html')

@analytics_bp.route('/models')
@login_required
def models():
    return render_template('analytics/models.html')

@analytics_bp.route('/neuromorphic')
@login_required
def neuromorphic():
    return render_template('analytics/neuromorphic.html')

@analytics_bp.route('/safety')
@login_required
def safety():
    return render_template('analytics/safety.html')

@analytics_bp.route('/self-improving')
@login_required
def self_improving():
    return render_template('analytics/self_improving.html')

@analytics_bp.route('/api/overview')
@login_required
def api_overview():
    analytics_data = get_overview_analytics()
    return jsonify(analytics_data)

@analytics_bp.route('/api/usage-metrics')
@login_required
def api_usage_metrics():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Messages per day
    messages_per_day = db.session.query(
        func.date(ChatMessage.created_at).label('date'),
        func.count(ChatMessage.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).group_by(func.date(ChatMessage.created_at)).all()
    
    # Tokens used per day
    tokens_per_day = db.session.query(
        func.date(ChatMessage.created_at).label('date'),
        func.sum(ChatMessage.tokens_used).label('total')
    ).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date,
        ChatMessage.tokens_used > 0
    ).group_by(func.date(ChatMessage.created_at)).all()
    
    # Cost per day
    cost_per_day = db.session.query(
        func.date(ChatMessage.created_at).label('date'),
        func.sum(ChatMessage.cost).label('total')
    ).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date,
        ChatMessage.cost > 0
    ).group_by(func.date(ChatMessage.created_at)).all()
    
    return jsonify({
        'success': True,
        'data': {
            'messages_per_day': [{'date': str(row.date), 'count': row.count} for row in messages_per_day],
            'tokens_per_day': [{'date': str(row.date), 'total': int(row.total or 0)} for row in tokens_per_day],
            'cost_per_day': [{'date': str(row.date), 'total': float(row.total or 0)} for row in cost_per_day]
        }
    })

@analytics_bp.route('/api/model-usage')
@login_required
def api_model_usage():
    # Model usage statistics
    model_usage = db.session.query(
        ChatSession.model_provider,
        ChatSession.model_name,
        func.count(ChatMessage.id).label('message_count'),
        func.sum(ChatMessage.tokens_used).label('total_tokens'),
        func.sum(ChatMessage.cost).label('total_cost')
    ).join(ChatMessage).filter(
        ChatSession.user_id == current_user.id
    ).group_by(
        ChatSession.model_provider,
        ChatSession.model_name
    ).order_by(desc('message_count')).all()
    
    return jsonify({
        'success': True,
        'data': {
            'model_usage': [{
                'provider': row.model_provider,
                'model': row.model_name,
                'message_count': row.message_count,
                'total_tokens': int(row.total_tokens or 0),
                'total_cost': float(row.total_cost or 0)
            } for row in model_usage]
        }
    })

@analytics_bp.route('/api/file-analytics')
@login_required
def api_file_analytics():
    # File upload statistics
    file_types = db.session.query(
        File.file_type,
        func.count(File.id).label('count'),
        func.sum(File.file_size).label('total_size')
    ).filter(
        File.user_id == current_user.id
    ).group_by(File.file_type).all()
    
    # Processing status
    processing_status = db.session.query(
        File.processing_status,
        func.count(File.id).label('count')
    ).filter(
        File.user_id == current_user.id
    ).group_by(File.processing_status).all()
    
    return jsonify({
        'success': True,
        'data': {
            'file_types': [{
                'type': row.file_type,
                'count': row.count,
                'total_size': int(row.total_size or 0)
            } for row in file_types],
            'processing_status': [{
                'status': row.processing_status,
                'count': row.count
            } for row in processing_status]
        }
    })

@analytics_bp.route('/api/performance-metrics')
@login_required
def api_performance_metrics():
    # Average response times, error rates, etc.
    # This would be populated from actual performance monitoring
    
    performance_data = {
        'average_response_time': 1.2,  # seconds
        'error_rate': 0.02,  # 2%
        'uptime': 99.8,  # percentage
        'throughput': 150,  # requests per minute
        'concurrent_users': 25
    }
    
    return jsonify({
        'success': True,
        'data': performance_data
    })

@analytics_bp.route('/api/security-metrics')
@login_required
def api_security_metrics():
    from models import SafetyViolation
    
    # Security-related metrics
    recent_violations = SafetyViolation.query.filter(
        SafetyViolation.user_id == current_user.id,
        SafetyViolation.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    violation_types = db.session.query(
        SafetyViolation.violation_type,
        func.count(SafetyViolation.id).label('count')
    ).filter(
        SafetyViolation.user_id == current_user.id
    ).group_by(SafetyViolation.violation_type).all()
    
    return jsonify({
        'success': True,
        'data': {
            'recent_violations': recent_violations,
            'violation_types': dict(violation_types),
            'security_score': 98.5  # Would be calculated based on actual metrics
        }
    })

@analytics_bp.route('/api/quantum-metrics')
@login_required
def api_quantum_metrics():
    from models import QuantumCircuit
    
    # Quantum computing analytics
    quantum_stats = db.session.query(
        func.count(QuantumCircuit.id).label('total_circuits'),
        func.avg(QuantumCircuit.num_qubits).label('avg_qubits'),
        func.max(QuantumCircuit.depth).label('max_depth')
    ).filter(
        QuantumCircuit.user_id == current_user.id
    ).first()
    
    provider_usage = db.session.query(
        QuantumCircuit.provider,
        func.count(QuantumCircuit.id).label('count')
    ).filter(
        QuantumCircuit.user_id == current_user.id
    ).group_by(QuantumCircuit.provider).all()
    
    return jsonify({
        'success': True,
        'data': {
            'total_circuits': quantum_stats.total_circuits or 0,
            'avg_qubits': float(quantum_stats.avg_qubits or 0),
            'max_depth': quantum_stats.max_depth or 0,
            'provider_usage': dict(provider_usage)
        }
    })

@analytics_bp.route('/api/federated-metrics')
@login_required
def api_federated_metrics():
    from models import FederatedNode, FederatedTrainingJob
    
    # Federated learning analytics
    node_stats = db.session.query(
        func.count(FederatedNode.id).label('total_nodes'),
        func.count(func.nullif(FederatedNode.status != 'offline', False)).label('active_nodes')
    ).filter(
        FederatedNode.user_id == current_user.id
    ).first()
    
    training_stats = db.session.query(
        func.count(FederatedTrainingJob.id).label('total_jobs'),
        func.count(func.nullif(FederatedTrainingJob.status == 'completed', False)).label('completed_jobs')
    ).filter(
        FederatedTrainingJob.user_id == current_user.id
    ).first()
    
    return jsonify({
        'success': True,
        'data': {
            'total_nodes': node_stats.total_nodes or 0,
            'active_nodes': node_stats.active_nodes or 0,
            'total_jobs': training_stats.total_jobs or 0,
            'completed_jobs': training_stats.completed_jobs or 0
        }
    })

@analytics_bp.route('/api/generate-report', methods=['POST'])
@login_required
def generate_report():
    data = request.get_json()
    
    report_type = data.get('report_type', 'usage')
    date_range = data.get('date_range', 30)
    include_charts = data.get('include_charts', True)
    
    try:
        # Generate comprehensive report
        report_data = {
            'report_id': f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'date_range': date_range,
            'user_id': current_user.id
        }
        
        if report_type == 'usage':
            report_data.update(get_usage_report_data(date_range))
        elif report_type == 'performance':
            report_data.update(get_performance_report_data(date_range))
        elif report_type == 'security':
            report_data.update(get_security_report_data(date_range))
        elif report_type == 'comprehensive':
            report_data.update(get_comprehensive_report_data(date_range))
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_overview_analytics():
    """Get overview analytics for the dashboard"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Total messages
    total_messages = ChatMessage.query.join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).count()
    
    # Total tokens
    total_tokens = db.session.query(func.sum(ChatMessage.tokens_used)).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).scalar() or 0
    
    # Total cost
    total_cost = db.session.query(func.sum(ChatMessage.cost)).join(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatMessage.created_at >= start_date
    ).scalar() or 0.0
    
    # Files uploaded
    files_uploaded = File.query.filter(
        File.user_id == current_user.id,
        File.created_at >= start_date
    ).count()
    
    # Active sessions
    active_sessions = ChatSession.query.filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).count()
    
    return {
        'total_messages': total_messages,
        'total_tokens': int(total_tokens),
        'total_cost': float(total_cost),
        'files_uploaded': files_uploaded,
        'active_sessions': active_sessions,
        'period': '30_days'
    }

def get_usage_report_data(date_range):
    """Get usage report data"""
    # Implementation would gather comprehensive usage statistics
    return {
        'usage_summary': 'Comprehensive usage analysis',
        'key_metrics': {},
        'trends': {},
        'recommendations': []
    }

def get_performance_report_data(date_range):
    """Get performance report data"""
    # Implementation would gather performance metrics
    return {
        'performance_summary': 'System performance analysis',
        'response_times': {},
        'error_rates': {},
        'optimization_suggestions': []
    }

def get_security_report_data(date_range):
    """Get security report data"""
    # Implementation would gather security metrics
    return {
        'security_summary': 'Security analysis report',
        'threat_detection': {},
        'violations': {},
        'recommendations': []
    }

def get_comprehensive_report_data(date_range):
    """Get comprehensive report combining all metrics"""
    # Implementation would combine all analytics
    return {
        'comprehensive_summary': 'Complete system analysis',
        'all_metrics': {},
        'insights': {},
        'action_items': []
    }
