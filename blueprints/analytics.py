from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, UsageMetrics, Conversation, File, QuantumJob, FederatedTraining, SpikingNeuralNetwork, SafetyViolation, ResearchProject
from blueprints.auth import login_required, get_current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@analytics_bp.route('/usage')
@login_required
def analytics_index():
    user = get_current_user()
    
    # Calculate date ranges
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic usage statistics
    total_conversations = Conversation.query.filter_by(user_id=user.id).count()
    total_files = File.query.filter_by(user_id=user.id).count()
    
    # Recent activity
    recent_conversations = Conversation.query.filter_by(user_id=user.id)\
        .filter(Conversation.created_at >= week_ago).count()
    recent_files = File.query.filter_by(user_id=user.id)\
        .filter(File.upload_timestamp >= week_ago).count()
    
    # Usage metrics
    usage_stats = {
        'total_conversations': total_conversations,
        'total_files': total_files,
        'recent_conversations': recent_conversations,
        'recent_files': recent_files,
        'quantum_jobs': QuantumJob.query.filter_by(user_id=user.id).count(),
        'federated_trainings': FederatedTraining.query.filter_by(user_id=user.id).count(),
        'neural_networks': SpikingNeuralNetwork.query.filter_by(user_id=user.id).count(),
        'safety_violations': SafetyViolation.query.join(SafetyProtocol)\
            .filter(SafetyProtocol.user_id == user.id).count(),
        'research_projects': ResearchProject.query.filter_by(user_id=user.id).count()
    }
    
    return render_template('analytics/analytics.html', 
                         user=user, 
                         usage_stats=usage_stats)

@analytics_bp.route('/behavior')
@login_required
def user_behavior():
    user = get_current_user()
    
    # Get behavior patterns
    behavior_data = {
        'most_used_features': get_most_used_features(user.id),
        'activity_timeline': get_activity_timeline(user.id),
        'peak_usage_hours': get_peak_usage_hours(user.id),
        'feature_adoption': get_feature_adoption(user.id)
    }
    
    return render_template('analytics/behavior.html', 
                         user=user, 
                         behavior_data=behavior_data)

@analytics_bp.route('/performance')
@login_required
def performance_monitoring():
    user = get_current_user()
    
    # Get performance metrics
    performance_data = {
        'response_times': get_response_times(user.id),
        'success_rates': get_success_rates(user.id),
        'error_rates': get_error_rates(user.id),
        'throughput': get_throughput_metrics(user.id)
    }
    
    return render_template('analytics/performance.html', 
                         user=user, 
                         performance_data=performance_data)

@analytics_bp.route('/costs')
@login_required
def cost_tracking():
    user = get_current_user()
    
    # Calculate API usage costs
    cost_data = {
        'monthly_costs': calculate_monthly_costs(user.id),
        'cost_breakdown': get_cost_breakdown(user.id),
        'usage_trends': get_usage_trends(user.id),
        'cost_projections': project_future_costs(user.id)
    }
    
    return render_template('analytics/costs.html', 
                         user=user, 
                         cost_data=cost_data)

@analytics_bp.route('/reports')
@login_required
def custom_reports():
    user = get_current_user()
    return render_template('analytics/reports.html', user=user)

@analytics_bp.route('/security')
@login_required
def security_analytics():
    user = get_current_user()
    
    # Get security metrics
    security_data = {
        'login_attempts': get_login_attempts(user.id),
        'access_patterns': get_access_patterns(user.id),
        'security_events': get_security_events(user.id),
        'threat_indicators': get_threat_indicators(user.id)
    }
    
    return render_template('analytics/security.html', 
                         user=user, 
                         security_data=security_data)

@analytics_bp.route('/blockchain')
@login_required
def blockchain_analytics():
    user = get_current_user()
    
    # Get blockchain transaction analytics
    blockchain_data = {
        'transaction_volume': get_transaction_volume(user.id),
        'gas_usage': get_gas_usage(user.id),
        'smart_contract_interactions': get_contract_interactions(user.id),
        'token_flows': get_token_flows(user.id)
    }
    
    return render_template('analytics/blockchain.html', 
                         user=user, 
                         blockchain_data=blockchain_data)

@analytics_bp.route('/quantum')
@login_required
def quantum_analytics():
    user = get_current_user()
    
    # Get quantum computing analytics
    quantum_data = {
        'circuit_complexity': get_circuit_complexity(user.id),
        'quantum_advantage': get_quantum_advantage(user.id),
        'error_rates': get_quantum_error_rates(user.id),
        'resource_utilization': get_quantum_resource_utilization(user.id)
    }
    
    return render_template('analytics/quantum.html', 
                         user=user, 
                         quantum_data=quantum_data)

@analytics_bp.route('/federated')
@login_required
def federated_analytics():
    user = get_current_user()
    
    # Get federated learning analytics
    federated_data = {
        'node_performance': get_node_performance(user.id),
        'convergence_rates': get_convergence_rates(user.id),
        'privacy_metrics': get_privacy_metrics(user.id),
        'communication_efficiency': get_communication_efficiency(user.id)
    }
    
    return render_template('analytics/federated.html', 
                         user=user, 
                         federated_data=federated_data)

@analytics_bp.route('/models')
@login_required
def model_analytics():
    user = get_current_user()
    
    # Get model performance analytics
    model_data = {
        'accuracy_trends': get_accuracy_trends(user.id),
        'inference_times': get_inference_times(user.id),
        'model_drift': get_model_drift(user.id),
        'resource_consumption': get_model_resource_consumption(user.id)
    }
    
    return render_template('analytics/models.html', 
                         user=user, 
                         model_data=model_data)

@analytics_bp.route('/neuromorphic')
@login_required
def neuromorphic_analytics():
    user = get_current_user()
    
    # Get neuromorphic computing analytics
    neuromorphic_data = {
        'spike_patterns': get_spike_patterns(user.id),
        'energy_efficiency': get_energy_efficiency(user.id),
        'learning_rates': get_neuromorphic_learning_rates(user.id),
        'synaptic_plasticity': get_synaptic_plasticity(user.id)
    }
    
    return render_template('analytics/neuromorphic.html', 
                         user=user, 
                         neuromorphic_data=neuromorphic_data)

@analytics_bp.route('/safety')
@login_required
def safety_analytics():
    user = get_current_user()
    
    # Get AI safety analytics
    safety_data = {
        'violation_trends': get_violation_trends(user.id),
        'alignment_scores': get_alignment_scores(user.id),
        'robustness_metrics': get_robustness_metrics(user.id),
        'interpretability_scores': get_interpretability_scores(user.id)
    }
    
    return render_template('analytics/safety.html', 
                         user=user, 
                         safety_data=safety_data)

@analytics_bp.route('/self-improving')
@login_required
def self_improving_analytics():
    user = get_current_user()
    
    # Get self-improvement analytics
    improvement_data = {
        'capability_growth': get_capability_growth(user.id),
        'learning_efficiency': get_learning_efficiency(user.id),
        'discovery_rates': get_discovery_rates(user.id),
        'adaptation_metrics': get_adaptation_metrics(user.id)
    }
    
    return render_template('analytics/self_improving.html', 
                         user=user, 
                         improvement_data=improvement_data)

# Helper functions for analytics calculations
def get_most_used_features(user_id):
    """Get most frequently used features by user"""
    metrics = UsageMetrics.query.filter_by(user_id=user_id)\
        .with_entities(UsageMetrics.metric_type, func.count(UsageMetrics.id).label('count'))\
        .group_by(UsageMetrics.metric_type)\
        .order_by(desc('count')).limit(10).all()
    
    return [{'feature': m.metric_type, 'usage_count': m.count} for m in metrics]

def get_activity_timeline(user_id):
    """Get user activity timeline for the past month"""
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    timeline = []
    # Conversations
    conversations = Conversation.query.filter_by(user_id=user_id)\
        .filter(Conversation.created_at >= month_ago)\
        .order_by(Conversation.created_at.desc()).limit(50).all()
    
    for conv in conversations:
        timeline.append({
            'type': 'conversation',
            'timestamp': conv.created_at.isoformat(),
            'title': conv.title
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'], reverse=True)
    return timeline[:20]

def get_peak_usage_hours(user_id):
    """Get peak usage hours for the user"""
    metrics = UsageMetrics.query.filter_by(user_id=user_id).all()
    
    hour_counts = {}
    for metric in metrics:
        hour = metric.timestamp.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    return sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]

def get_feature_adoption(user_id):
    """Get feature adoption timeline"""
    # Simplified implementation
    return {
        'chat': '2024-01-01',
        'files': '2024-01-15',
        'quantum': '2024-02-01',
        'federated': '2024-02-15',
        'neuromorphic': '2024-03-01',
        'safety': '2024-03-15'
    }

def calculate_monthly_costs(user_id):
    """Calculate estimated monthly costs based on usage"""
    # Simplified cost calculation
    conversations = Conversation.query.filter_by(user_id=user_id).count()
    files = File.query.filter_by(user_id=user_id).count()
    
    # Rough cost estimates (in USD)
    conversation_cost = conversations * 0.01  # $0.01 per conversation
    file_processing_cost = files * 0.05  # $0.05 per file
    
    return {
        'total': conversation_cost + file_processing_cost,
        'conversations': conversation_cost,
        'file_processing': file_processing_cost
    }

# Additional helper functions would be implemented similarly...
def get_response_times(user_id):
    return {'average': 1.2, 'p95': 2.5, 'p99': 4.0}

def get_success_rates(user_id):
    return {'overall': 98.5, 'chat': 99.2, 'file_processing': 97.8}

def get_error_rates(user_id):
    return {'overall': 1.5, 'chat': 0.8, 'file_processing': 2.2}

def get_throughput_metrics(user_id):
    return {'requests_per_minute': 12, 'files_per_hour': 8}

def get_cost_breakdown(user_id):
    return {'api_calls': 45.50, 'storage': 12.30, 'compute': 23.40}

def get_usage_trends(user_id):
    return {'trend': 'increasing', 'growth_rate': 15.2}

def project_future_costs(user_id):
    return {'next_month': 85.40, 'next_quarter': 260.50}

def get_login_attempts(user_id):
    return {'successful': 45, 'failed': 2, 'suspicious': 0}

def get_access_patterns(user_id):
    return {'normal': 98, 'unusual': 2}

def get_security_events(user_id):
    return {'low': 5, 'medium': 1, 'high': 0, 'critical': 0}

def get_threat_indicators(user_id):
    return {'score': 95, 'status': 'low_risk'}

# Additional analytics helper functions would continue...
def get_transaction_volume(user_id):
    return {'daily': 12, 'weekly': 84, 'monthly': 360}

def get_gas_usage(user_id):
    return {'average': 0.002, 'total': 0.45}

def get_contract_interactions(user_id):
    return {'plugin_registry': 25, 'revenue_sharing': 8}

def get_token_flows(user_id):
    return {'earned': 125.50, 'spent': 89.30}

def get_circuit_complexity(user_id):
    return {'average_qubits': 8, 'max_depth': 15}

def get_quantum_advantage(user_id):
    return {'speedup_factor': 2.3, 'problems_solved': 12}

def get_quantum_error_rates(user_id):
    return {'gate_error': 0.001, 'readout_error': 0.02}

def get_quantum_resource_utilization(user_id):
    return {'cpu_hours': 45.2, 'gpu_hours': 12.8}

def get_node_performance(user_id):
    return {'average_accuracy': 87.5, 'convergence_rounds': 15}

def get_convergence_rates(user_id):
    return {'average_rounds': 18, 'best_case': 12}

def get_privacy_metrics(user_id):
    return {'epsilon': 1.0, 'delta': 1e-5}

def get_communication_efficiency(user_id):
    return {'compression_ratio': 0.15, 'bandwidth_saved': 75}

def get_accuracy_trends(user_id):
    return {'current': 92.3, 'trend': 'stable'}

def get_inference_times(user_id):
    return {'average': 0.85, 'p95': 1.2}

def get_model_drift(user_id):
    return {'drift_score': 0.05, 'status': 'stable'}

def get_model_resource_consumption(user_id):
    return {'memory_mb': 512, 'cpu_utilization': 35}

def get_spike_patterns(user_id):
    return {'frequency': 50, 'synchrony': 0.7}

def get_energy_efficiency(user_id):
    return {'ops_per_joule': 1000000, 'efficiency_score': 95}

def get_neuromorphic_learning_rates(user_id):
    return {'stdp_rate': 0.01, 'adaptation_speed': 0.85}

def get_synaptic_plasticity(user_id):
    return {'potentiation': 0.7, 'depression': 0.3}

def get_violation_trends(user_id):
    return {'this_month': 2, 'last_month': 5, 'trend': 'decreasing'}

def get_alignment_scores(user_id):
    return {'current': 94.5, 'target': 95.0}

def get_robustness_metrics(user_id):
    return {'adversarial_resistance': 88, 'out_of_distribution': 76}

def get_interpretability_scores(user_id):
    return {'explanation_quality': 82, 'feature_importance': 78}

def get_capability_growth(user_id):
    return {'reasoning': 15, 'creativity': 12, 'learning': 18}

def get_learning_efficiency(user_id):
    return {'sample_efficiency': 85, 'transfer_learning': 92}

def get_discovery_rates(user_id):
    return {'novel_insights': 8, 'validated_hypotheses': 5}

def get_adaptation_metrics(user_id):
    return {'adaptation_speed': 0.75, 'robustness': 0.88}
