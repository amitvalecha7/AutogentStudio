from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from blueprints.auth import login_required, get_current_user
from models import ModelVersion, DeploymentPipeline, User
from app import db
import json
import uuid
from datetime import datetime, timezone

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/')
@login_required
def index():
    user = get_current_user()
    
    # Sample deployment statistics
    stats = {
        'active_deployments': 8,
        'successful_deployments': 156,
        'deployment_success_rate': 0.94,
        'average_deployment_time': '12 minutes',
        'rollbacks_this_month': 3
    }
    
    return render_template('deployment/index.html', stats=stats)

@deployment_bp.route('/registry')
@login_required
def registry():
    user = get_current_user()
    
    # Sample model registry
    models = [
        {
            'id': 'model_001',
            'name': 'Customer Support Assistant',
            'version': '2.1.0',
            'base_model': 'gpt-4o',
            'size': '13.7 GB',
            'accuracy': 0.92,
            'status': 'Production',
            'created_at': '2025-07-18T16:30:00Z',
            'tags': ['customer-support', 'gpt-4o', 'fine-tuned']
        },
        {
            'id': 'model_002',
            'name': 'Research Assistant',
            'version': '1.5.2',
            'base_model': 'claude-sonnet-4-20250514',
            'size': '21.3 GB',
            'accuracy': 0.89,
            'status': 'Staging',
            'created_at': '2025-07-17T14:20:00Z',
            'tags': ['research', 'claude', 'scientific']
        },
        {
            'id': 'model_003',
            'name': 'Code Documentation Generator',
            'version': '1.0.0',
            'base_model': 'gpt-4o',
            'size': '15.2 GB',
            'accuracy': 0.88,
            'status': 'Development',
            'created_at': '2025-07-16T09:15:00Z',
            'tags': ['coding', 'documentation', 'gpt-4o']
        }
    ]
    
    return render_template('deployment/registry.html', models=models)

@deployment_bp.route('/deploy')
@login_required
def deploy():
    user = get_current_user()
    
    # Sample deployment pipelines
    pipelines = [
        {
            'id': 'pipeline_001',
            'name': 'Production Deployment',
            'model': 'Customer Support Assistant v2.1',
            'environment': 'Production',
            'status': 'Running',
            'progress': 0.75,
            'started_at': '2025-07-19T10:00:00Z',
            'estimated_completion': '2025-07-19T10:15:00Z',
            'stages': [
                {'name': 'Build', 'status': 'Completed', 'duration': '2m 30s'},
                {'name': 'Test', 'status': 'Completed', 'duration': '5m 15s'},
                {'name': 'Deploy', 'status': 'Running', 'duration': '3m 22s'},
                {'name': 'Validate', 'status': 'Pending', 'duration': None}
            ]
        },
        {
            'id': 'pipeline_002',
            'name': 'Staging Update',
            'model': 'Research Assistant v1.5.2',
            'environment': 'Staging',
            'status': 'Completed',
            'progress': 1.0,
            'started_at': '2025-07-19T09:00:00Z',
            'completed_at': '2025-07-19T09:18:00Z',
            'stages': [
                {'name': 'Build', 'status': 'Completed', 'duration': '3m 45s'},
                {'name': 'Test', 'status': 'Completed', 'duration': '6m 30s'},
                {'name': 'Deploy', 'status': 'Completed', 'duration': '4m 12s'},
                {'name': 'Validate', 'status': 'Completed', 'duration': '3m 51s'}
            ]
        }
    ]
    
    return render_template('deployment/deploy.html', pipelines=pipelines)

@deployment_bp.route('/pipelines/create', methods=['POST'])
@login_required
def create_pipeline():
    user = get_current_user()
    
    data = request.get_json()
    pipeline_name = data.get('pipeline_name', '').strip()
    model_id = data.get('model_id')
    environment = data.get('environment')
    deployment_config = data.get('deployment_config', {})
    
    if not all([pipeline_name, model_id, environment]):
        return jsonify({'error': 'Pipeline name, model, and environment are required'}), 400
    
    try:
        pipeline = DeploymentPipeline(
            user_id=user.id,
            pipeline_name=pipeline_name,
            model_version_id=model_id,
            deployment_config=json.dumps(deployment_config),
            status='created'
        )
        
        db.session.add(pipeline)
        db.session.commit()
        
        return jsonify({
            'message': 'Deployment pipeline created successfully',
            'pipeline_id': pipeline.id,
            'name': pipeline.pipeline_name
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating pipeline: {str(e)}'}), 500

@deployment_bp.route('/pipelines/<int:pipeline_id>/execute', methods=['POST'])
@login_required
def execute_pipeline(pipeline_id):
    user = get_current_user()
    pipeline = DeploymentPipeline.query.filter_by(id=pipeline_id, user_id=user.id).first()
    
    if not pipeline:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    try:
        # Execute deployment pipeline
        pipeline.status = 'running'
        pipeline.logs = 'Pipeline execution started'
        db.session.commit()
        
        return jsonify({
            'message': 'Deployment pipeline started',
            'pipeline_id': pipeline.id,
            'status': 'running',
            'estimated_duration': '10-15 minutes'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error executing pipeline: {str(e)}'}), 500

@deployment_bp.route('/testing')
@login_required
def testing():
    user = get_current_user()
    
    # Sample A/B testing configurations
    ab_tests = [
        {
            'id': 'test_001',
            'name': 'Customer Support Model Comparison',
            'description': 'Testing v2.1 vs v2.0 performance',
            'model_a': 'Customer Support v2.0',
            'model_b': 'Customer Support v2.1',
            'traffic_split': '50/50',
            'status': 'Running',
            'start_date': '2025-07-15T00:00:00Z',
            'end_date': '2025-07-29T23:59:59Z',
            'metrics': {
                'requests_a': 5420,
                'requests_b': 5380,
                'success_rate_a': 0.94,
                'success_rate_b': 0.96,
                'avg_latency_a': '150ms',
                'avg_latency_b': '145ms'
            }
        },
        {
            'id': 'test_002',
            'name': 'Research Assistant Features',
            'description': 'Testing new research capabilities',
            'model_a': 'Research Assistant v1.5.1',
            'model_b': 'Research Assistant v1.5.2',
            'traffic_split': '80/20',
            'status': 'Completed',
            'start_date': '2025-07-01T00:00:00Z',
            'end_date': '2025-07-14T23:59:59Z',
            'metrics': {
                'requests_a': 12840,
                'requests_b': 3210,
                'success_rate_a': 0.89,
                'success_rate_b': 0.91,
                'avg_latency_a': '180ms',
                'avg_latency_b': '165ms'
            },
            'winner': 'Model B'
        }
    ]
    
    return render_template('deployment/testing.html', ab_tests=ab_tests)

@deployment_bp.route('/testing/create', methods=['POST'])
@login_required
def create_ab_test():
    user = get_current_user()
    
    data = request.get_json()
    test_name = data.get('test_name', '').strip()
    model_a_id = data.get('model_a_id')
    model_b_id = data.get('model_b_id')
    traffic_split = data.get('traffic_split', 50)
    duration_days = data.get('duration_days', 14)
    
    if not all([test_name, model_a_id, model_b_id]):
        return jsonify({'error': 'Test name and both models are required'}), 400
    
    try:
        # Create A/B test
        test_id = f'test_{uuid.uuid4().hex[:8]}'
        
        ab_test = {
            'id': test_id,
            'name': test_name,
            'model_a_id': model_a_id,
            'model_b_id': model_b_id,
            'traffic_split': traffic_split,
            'duration_days': duration_days,
            'status': 'Created',
            'created_by': user.id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify({
            'message': 'A/B test created successfully',
            'test': ab_test
        })
    
    except Exception as e:
        return jsonify({'error': f'Error creating A/B test: {str(e)}'}), 500

@deployment_bp.route('/monitoring')
@login_required
def monitoring():
    user = get_current_user()
    
    # Sample monitoring data
    monitoring_data = {
        'active_deployments': [
            {
                'name': 'Customer Support v2.1',
                'environment': 'Production',
                'health': 'Healthy',
                'requests_per_minute': 1250,
                'error_rate': 0.02,
                'avg_latency': '145ms',
                'cpu_usage': '45%',
                'memory_usage': '67%',
                'replicas': 3
            },
            {
                'name': 'Research Assistant v1.5.2',
                'environment': 'Staging',
                'health': 'Healthy',
                'requests_per_minute': 340,
                'error_rate': 0.01,
                'avg_latency': '165ms',
                'cpu_usage': '32%',
                'memory_usage': '54%',
                'replicas': 2
            }
        ],
        'alerts': [
            {
                'id': 'alert_001',
                'type': 'High Error Rate',
                'deployment': 'Code Generator v1.0',
                'severity': 'Warning',
                'message': 'Error rate increased to 5.2%',
                'timestamp': '2025-07-19T09:30:00Z',
                'status': 'Active'
            }
        ],
        'system_metrics': {
            'total_requests_24h': 125000,
            'success_rate': 0.97,
            'avg_response_time': '152ms',
            'data_processed': '45.2 GB'
        }
    }
    
    return render_template('deployment/monitoring.html', monitoring=monitoring_data)

@deployment_bp.route('/rollback')
@login_required
def rollback():
    user = get_current_user()
    
    # Sample rollback configurations
    rollback_data = {
        'available_rollbacks': [
            {
                'deployment': 'Customer Support v2.1',
                'current_version': '2.1.0',
                'previous_versions': [
                    {'version': '2.0.3', 'deployed_at': '2025-07-10T14:20:00Z', 'stability': 'Stable'},
                    {'version': '2.0.2', 'deployed_at': '2025-07-05T09:15:00Z', 'stability': 'Stable'},
                    {'version': '2.0.1', 'deployed_at': '2025-06-28T16:45:00Z', 'stability': 'Stable'}
                ]
            },
            {
                'deployment': 'Research Assistant v1.5.2',
                'current_version': '1.5.2',
                'previous_versions': [
                    {'version': '1.5.1', 'deployed_at': '2025-07-08T11:30:00Z', 'stability': 'Stable'},
                    {'version': '1.5.0', 'deployed_at': '2025-06-25T08:00:00Z', 'stability': 'Stable'},
                    {'version': '1.4.8', 'deployed_at': '2025-06-18T13:22:00Z', 'stability': 'Stable'}
                ]
            }
        ],
        'recent_rollbacks': [
            {
                'deployment': 'Code Generator v1.0',
                'from_version': '1.0.1',
                'to_version': '1.0.0',
                'reason': 'High error rate',
                'rollback_time': '5 minutes',
                'performed_at': '2025-07-18T14:30:00Z',
                'performed_by': 'auto-rollback'
            }
        ]
    }
    
    return render_template('deployment/rollback.html', rollback=rollback_data)

@deployment_bp.route('/rollback/execute', methods=['POST'])
@login_required
def execute_rollback():
    user = get_current_user()
    
    data = request.get_json()
    deployment_id = data.get('deployment_id')
    target_version = data.get('target_version')
    reason = data.get('reason', '').strip()
    
    if not all([deployment_id, target_version]):
        return jsonify({'error': 'Deployment ID and target version are required'}), 400
    
    try:
        # Execute rollback
        rollback_id = f'rollback_{uuid.uuid4().hex[:8]}'
        
        rollback = {
            'id': rollback_id,
            'deployment_id': deployment_id,
            'target_version': target_version,
            'reason': reason,
            'status': 'In Progress',
            'initiated_by': user.username,
            'initiated_at': datetime.now(timezone.utc).isoformat(),
            'estimated_completion': '3-5 minutes'
        }
        
        return jsonify({
            'message': 'Rollback initiated successfully',
            'rollback': rollback
        })
    
    except Exception as e:
        return jsonify({'error': f'Error executing rollback: {str(e)}'}), 500

@deployment_bp.route('/cicd')
@login_required
def cicd():
    user = get_current_user()
    
    # CI/CD pipeline configurations
    cicd_data = {
        'repositories': [
            {
                'name': 'autogent-models',
                'provider': 'GitHub',
                'url': 'https://github.com/autogent/models',
                'branch': 'main',
                'last_commit': '2025-07-19T10:00:00Z',
                'webhook_status': 'Active'
            },
            {
                'name': 'autogent-training',
                'provider': 'GitLab',
                'url': 'https://gitlab.com/autogent/training',
                'branch': 'develop',
                'last_commit': '2025-07-18T16:30:00Z',
                'webhook_status': 'Active'
            }
        ],
        'build_triggers': [
            {
                'name': 'Auto Deploy on Merge',
                'repository': 'autogent-models',
                'trigger': 'Push to main',
                'environment': 'Production',
                'enabled': True
            },
            {
                'name': 'Staging Build',
                'repository': 'autogent-training',
                'trigger': 'Pull Request',
                'environment': 'Staging',
                'enabled': True
            }
        ],
        'recent_builds': [
            {
                'id': 'build_001',
                'repository': 'autogent-models',
                'commit': 'a1b2c3d',
                'status': 'Success',
                'duration': '8m 32s',
                'started_at': '2025-07-19T10:00:00Z'
            },
            {
                'id': 'build_002',
                'repository': 'autogent-training',
                'commit': 'e4f5g6h',
                'status': 'Failed',
                'duration': '3m 15s',
                'started_at': '2025-07-19T09:30:00Z'
            }
        ]
    }
    
    return render_template('deployment/cicd.html', cicd=cicd_data)

@deployment_bp.route('/governance')
@login_required
def governance():
    user = get_current_user()
    
    # Model governance and compliance
    governance_data = {
        'model_approvals': [
            {
                'model': 'Customer Support v2.1',
                'status': 'Approved',
                'approver': 'AI Safety Team',
                'approval_date': '2025-07-17T14:00:00Z',
                'compliance_checks': ['Safety', 'Bias', 'Performance'],
                'next_review': '2025-10-17T14:00:00Z'
            },
            {
                'model': 'Research Assistant v1.5.2',
                'status': 'Pending Review',
                'submitted_date': '2025-07-18T10:00:00Z',
                'compliance_checks': ['Safety', 'Bias', 'Performance'],
                'estimated_approval': '2025-07-25T10:00:00Z'
            }
        ],
        'compliance_policies': [
            {
                'name': 'AI Safety Standards',
                'version': '2.1',
                'last_updated': '2025-06-01T00:00:00Z',
                'mandatory': True,
                'models_compliant': 12
            },
            {
                'name': 'Bias Testing Protocol',
                'version': '1.8',
                'last_updated': '2025-05-15T00:00:00Z',
                'mandatory': True,
                'models_compliant': 10
            },
            {
                'name': 'Performance Benchmarks',
                'version': '3.2',
                'last_updated': '2025-07-01T00:00:00Z',
                'mandatory': False,
                'models_compliant': 8
            }
        ],
        'audit_trail': [
            {
                'timestamp': '2025-07-19T10:00:00Z',
                'action': 'Model Deployed',
                'model': 'Customer Support v2.1',
                'user': user.username,
                'environment': 'Production'
            },
            {
                'timestamp': '2025-07-18T16:30:00Z',
                'action': 'Model Approved',
                'model': 'Customer Support v2.1',
                'user': 'AI Safety Team',
                'notes': 'All compliance checks passed'
            }
        ]
    }
    
    return render_template('deployment/governance.html', governance=governance_data)

@deployment_bp.route('/environments')
@login_required
def environments():
    """Get deployment environments"""
    environments = [
        {
            'name': 'Development',
            'status': 'Active',
            'models': 3,
            'cpu_usage': '25%',
            'memory_usage': '40%',
            'last_deployment': '2025-07-19T08:00:00Z'
        },
        {
            'name': 'Staging',
            'status': 'Active',
            'models': 2,
            'cpu_usage': '45%',
            'memory_usage': '60%',
            'last_deployment': '2025-07-19T09:00:00Z'
        },
        {
            'name': 'Production',
            'status': 'Active',
            'models': 5,
            'cpu_usage': '70%',
            'memory_usage': '75%',
            'last_deployment': '2025-07-19T10:00:00Z'
        }
    ]
    
    return jsonify({'environments': environments})

