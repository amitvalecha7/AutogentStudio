from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, Conversation, Message, File, QuantumCircuit, FederatedNode, ResearchProject
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/analytics.html', user=user)

@analytics_bp.route('/analytics/usage')
def usage_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/usage.html', user=user)

@analytics_bp.route('/analytics/behavior')
def behavior_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/behavior.html', user=user)

@analytics_bp.route('/analytics/performance')
def performance_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/performance.html', user=user)

@analytics_bp.route('/analytics/costs')
def cost_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/costs.html', user=user)

@analytics_bp.route('/analytics/reports')
def custom_reports():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/reports.html', user=user)

@analytics_bp.route('/analytics/security')
def security_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/security.html', user=user)

@analytics_bp.route('/analytics/blockchain')
def blockchain_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/blockchain.html', user=user)

@analytics_bp.route('/analytics/quantum')
def quantum_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/quantum.html', user=user)

@analytics_bp.route('/analytics/federated')
def federated_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/federated.html', user=user)

@analytics_bp.route('/analytics/models')
def model_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/models.html', user=user)

@analytics_bp.route('/analytics/neuromorphic')
def neuromorphic_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/neuromorphic.html', user=user)

@analytics_bp.route('/analytics/safety')
def safety_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/safety.html', user=user)

@analytics_bp.route('/analytics/self-improving')
def self_improving_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('analytics/self_improving.html', user=user)

@analytics_bp.route('/api/analytics/overview')
def get_overview():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get basic statistics
        conversation_count = Conversation.query.filter_by(user_id=user.id).count()
        message_count = db.session.query(Message).join(Conversation).filter(Conversation.user_id == user.id).count()
        file_count = File.query.filter_by(user_id=user.id).count()
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_conversations = Conversation.query.filter(
            Conversation.user_id == user.id,
            Conversation.created_at >= thirty_days_ago
        ).count()
        
        recent_messages = db.session.query(Message).join(Conversation).filter(
            Conversation.user_id == user.id,
            Message.created_at >= thirty_days_ago
        ).count()
        
        overview = {
            'total_conversations': conversation_count,
            'total_messages': message_count,
            'total_files': file_count,
            'recent_conversations': recent_conversations,
            'recent_messages': recent_messages,
            'user_since': user.created_at.isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'overview': overview
        })
        
    except Exception as e:
        logging.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({'error': 'Failed to get overview'}), 500

@analytics_bp.route('/api/analytics/usage/daily')
def get_daily_usage():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        days = int(request.args.get('days', 30))
        
        # Get daily message counts
        start_date = datetime.utcnow() - timedelta(days=days)
        
        daily_messages = db.session.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).join(Conversation).filter(
            Conversation.user_id == user.id,
            Message.created_at >= start_date
        ).group_by(func.date(Message.created_at)).all()
        
        # Get daily conversation counts
        daily_conversations = db.session.query(
            func.date(Conversation.created_at).label('date'),
            func.count(Conversation.id).label('count')
        ).filter(
            Conversation.user_id == user.id,
            Conversation.created_at >= start_date
        ).group_by(func.date(Conversation.created_at)).all()
        
        usage_data = {
            'messages': [{'date': str(row.date), 'count': row.count} for row in daily_messages],
            'conversations': [{'date': str(row.date), 'count': row.count} for row in daily_conversations]
        }
        
        return jsonify({
            'success': True,
            'usage_data': usage_data
        })
        
    except Exception as e:
        logging.error(f"Error getting daily usage: {str(e)}")
        return jsonify({'error': 'Failed to get usage data'}), 500

@analytics_bp.route('/api/analytics/models/usage')
def get_model_usage():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get model usage statistics
        model_usage = db.session.query(
            Conversation.model_provider,
            Conversation.model_name,
            func.count(Conversation.id).label('conversation_count'),
            func.count(Message.id).label('message_count')
        ).outerjoin(Message).filter(
            Conversation.user_id == user.id
        ).group_by(
            Conversation.model_provider,
            Conversation.model_name
        ).all()
        
        usage_stats = []
        for row in model_usage:
            usage_stats.append({
                'provider': row.model_provider,
                'model': row.model_name,
                'conversations': row.conversation_count,
                'messages': row.message_count or 0
            })
        
        return jsonify({
            'success': True,
            'model_usage': usage_stats
        })
        
    except Exception as e:
        logging.error(f"Error getting model usage: {str(e)}")
        return jsonify({'error': 'Failed to get model usage'}), 500

@analytics_bp.route('/api/analytics/quantum/metrics')
def get_quantum_metrics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get quantum circuit statistics
        circuit_count = QuantumCircuit.query.filter_by(user_id=user.id).count()
        total_executions = db.session.query(func.sum(QuantumCircuit.execution_count)).filter_by(user_id=user.id).scalar() or 0
        
        # Get circuits by backend
        backend_usage = db.session.query(
            QuantumCircuit.backend,
            func.count(QuantumCircuit.id).label('count'),
            func.sum(QuantumCircuit.execution_count).label('executions')
        ).filter_by(user_id=user.id).group_by(QuantumCircuit.backend).all()
        
        quantum_metrics = {
            'total_circuits': circuit_count,
            'total_executions': total_executions,
            'backend_usage': [
                {
                    'backend': row.backend,
                    'circuits': row.count,
                    'executions': row.executions or 0
                } for row in backend_usage
            ]
        }
        
        return jsonify({
            'success': True,
            'quantum_metrics': quantum_metrics
        })
        
    except Exception as e:
        logging.error(f"Error getting quantum metrics: {str(e)}")
        return jsonify({'error': 'Failed to get quantum metrics'}), 500

@analytics_bp.route('/api/analytics/federated/metrics')
def get_federated_metrics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get federated learning statistics
        node_count = FederatedNode.query.filter_by(user_id=user.id).count()
        active_nodes = FederatedNode.query.filter_by(user_id=user.id, status='active').count()
        
        # Get nodes by status
        node_status = db.session.query(
            FederatedNode.status,
            func.count(FederatedNode.id).label('count')
        ).filter_by(user_id=user.id).group_by(FederatedNode.status).all()
        
        federated_metrics = {
            'total_nodes': node_count,
            'active_nodes': active_nodes,
            'node_status': [
                {
                    'status': row.status,
                    'count': row.count
                } for row in node_status
            ]
        }
        
        return jsonify({
            'success': True,
            'federated_metrics': federated_metrics
        })
        
    except Exception as e:
        logging.error(f"Error getting federated metrics: {str(e)}")
        return jsonify({'error': 'Failed to get federated metrics'}), 500

@analytics_bp.route('/api/analytics/research/metrics')
def get_research_metrics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get research project statistics
        project_count = ResearchProject.query.filter_by(user_id=user.id).count()
        active_projects = ResearchProject.query.filter_by(user_id=user.id, status='active').count()
        
        # Get projects by research area
        research_areas = db.session.query(
            ResearchProject.research_area,
            func.count(ResearchProject.id).label('count'),
            func.avg(ResearchProject.progress).label('avg_progress')
        ).filter_by(user_id=user.id).group_by(ResearchProject.research_area).all()
        
        # Get projects by status
        project_status = db.session.query(
            ResearchProject.status,
            func.count(ResearchProject.id).label('count')
        ).filter_by(user_id=user.id).group_by(ResearchProject.status).all()
        
        research_metrics = {
            'total_projects': project_count,
            'active_projects': active_projects,
            'research_areas': [
                {
                    'area': row.research_area or 'General',
                    'count': row.count,
                    'avg_progress': float(row.avg_progress or 0)
                } for row in research_areas
            ],
            'project_status': [
                {
                    'status': row.status,
                    'count': row.count
                } for row in project_status
            ]
        }
        
        return jsonify({
            'success': True,
            'research_metrics': research_metrics
        })
        
    except Exception as e:
        logging.error(f"Error getting research metrics: {str(e)}")
        return jsonify({'error': 'Failed to get research metrics'}), 500

@analytics_bp.route('/api/analytics/export', methods=['POST'])
def export_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        export_type = data.get('export_type', 'csv')
        date_range = data.get('date_range', 30)
        metrics = data.get('metrics', ['usage', 'models'])
        
        user = User.query.get(session['user_id'])
        
        # Collect analytics data based on requested metrics
        export_data = {}
        
        if 'usage' in metrics:
            # Get usage data
            start_date = datetime.utcnow() - timedelta(days=date_range)
            usage_data = db.session.query(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('message_count')
            ).join(Conversation).filter(
                Conversation.user_id == user.id,
                Message.created_at >= start_date
            ).group_by(func.date(Message.created_at)).all()
            
            export_data['usage'] = [
                {'date': str(row.date), 'messages': row.message_count}
                for row in usage_data
            ]
        
        if 'models' in metrics:
            # Get model usage data
            model_data = db.session.query(
                Conversation.model_provider,
                Conversation.model_name,
                func.count(Conversation.id).label('count')
            ).filter_by(user_id=user.id).group_by(
                Conversation.model_provider,
                Conversation.model_name
            ).all()
            
            export_data['models'] = [
                {
                    'provider': row.model_provider,
                    'model': row.model_name,
                    'conversations': row.count
                } for row in model_data
            ]
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'format': export_type
        })
        
    except Exception as e:
        logging.error(f"Error exporting analytics: {str(e)}")
        return jsonify({'error': 'Failed to export analytics'}), 500
