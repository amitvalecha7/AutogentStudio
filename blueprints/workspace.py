from flask import Blueprint, render_template, request, jsonify, session, flash
from blueprints.auth import require_auth
from models import User, ChatSession, File, KnowledgeBase
from app import db
import uuid
from datetime import datetime

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/')
@require_auth
def index():
    """Collaborative workspaces overview"""
    user_id = session['user_id']
    
    # Mock workspace data for demonstration
    workspaces = [
        {
            'id': str(uuid.uuid4()),
            'name': 'AI Safety Research',
            'description': 'Collaborative research on AI alignment and safety protocols',
            'members': 5,
            'created_at': '2025-01-15',
            'last_activity': '2 hours ago',
            'role': 'admin'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Quantum ML Development',
            'description': 'Developing quantum machine learning algorithms',
            'members': 3,
            'created_at': '2025-01-10',
            'last_activity': '1 day ago',
            'role': 'member'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Neuromorphic Edge AI',
            'description': 'Edge AI deployment with neuromorphic computing',
            'members': 7,
            'created_at': '2025-01-05',
            'last_activity': '3 days ago',
            'role': 'collaborator'
        }
    ]
    
    return render_template('workspace/index.html', workspaces=workspaces)

@workspace_bp.route('/<workspace_id>')
@require_auth
def workspace_detail(workspace_id):
    """Individual workspace detail page"""
    user_id = session['user_id']
    
    # Mock workspace detail data
    workspace = {
        'id': workspace_id,
        'name': 'AI Safety Research',
        'description': 'Collaborative research on AI alignment and safety protocols',
        'members': [
            {'id': '1', 'name': 'Dr. Sarah Chen', 'role': 'admin', 'avatar': None},
            {'id': '2', 'name': 'Prof. Michael Rodriguez', 'role': 'member', 'avatar': None},
            {'id': '3', 'name': 'Dr. Emily Watson', 'role': 'member', 'avatar': None},
            {'id': '4', 'name': 'Alex Thompson', 'role': 'collaborator', 'avatar': None},
            {'id': '5', 'name': 'Jordan Lee', 'role': 'collaborator', 'avatar': None}
        ],
        'recent_activity': [
            {
                'user': 'Dr. Sarah Chen',
                'action': 'uploaded safety protocol document',
                'timestamp': '2 hours ago',
                'type': 'file'
            },
            {
                'user': 'Prof. Michael Rodriguez',
                'action': 'created new chat session on alignment research',
                'timestamp': '4 hours ago',
                'type': 'chat'
            },
            {
                'user': 'Dr. Emily Watson',
                'action': 'shared quantum circuit for safety verification',
                'timestamp': '1 day ago',
                'type': 'quantum'
            }
        ]
    }
    
    try:
        # Get user's actual data for this workspace context
        chat_sessions = ChatSession.query.filter_by(user_id=user_id).limit(10).all()
        files = File.query.filter_by(user_id=user_id).limit(10).all()
        knowledge_bases = KnowledgeBase.query.filter_by(user_id=user_id).limit(5).all()
        
        return render_template('workspace/detail.html', 
                             workspace=workspace, 
                             chat_sessions=chat_sessions,
                             files=files,
                             knowledge_bases=knowledge_bases)
    except Exception as e:
        flash(f'Error loading workspace: {str(e)}', 'error')
        return render_template('workspace/detail.html', workspace=workspace)

@workspace_bp.route('/knowledge')
@require_auth
def knowledge():
    """Shared knowledge bases"""
    user_id = session['user_id']
    
    try:
        knowledge_bases = KnowledgeBase.query.filter_by(user_id=user_id).all()
        return render_template('workspace/knowledge.html', knowledge_bases=knowledge_bases)
    except Exception as e:
        flash(f'Error loading knowledge bases: {str(e)}', 'error')
        return render_template('workspace/knowledge.html', knowledge_bases=[])

@workspace_bp.route('/chat')
@require_auth
def chat():
    """Team chat rooms"""
    return render_template('workspace/chat.html')

@workspace_bp.route('/permissions')
@require_auth
def permissions():
    """Permission management"""
    return render_template('workspace/permissions.html')

@workspace_bp.route('/analytics')
@require_auth
def analytics():
    """Team analytics"""
    return render_template('workspace/analytics.html')

@workspace_bp.route('/api/workspaces', methods=['GET'])
@require_auth
def get_workspaces():
    """Get user's workspaces"""
    user_id = session['user_id']
    
    # In a real implementation, fetch from database
    workspaces = [
        {
            'id': str(uuid.uuid4()),
            'name': 'AI Safety Research',
            'description': 'Collaborative research on AI alignment and safety protocols',
            'members_count': 5,
            'role': 'admin',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    return jsonify({
        'success': True,
        'workspaces': workspaces
    })

@workspace_bp.route('/api/workspaces', methods=['POST'])
@require_auth
def create_workspace():
    """Create a new workspace"""
    user_id = session['user_id']
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Workspace name is required'}), 400
    
    try:
        # In a real implementation, create workspace in database
        workspace_id = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'workspace_id': workspace_id,
            'message': 'Workspace created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/api/workspaces/<workspace_id>/invite', methods=['POST'])
@require_auth
def invite_member():
    """Invite member to workspace"""
    data = request.get_json()
    
    email = data.get('email', '').strip()
    role = data.get('role', 'collaborator')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    
    try:
        # In a real implementation, send invitation email
        return jsonify({
            'success': True,
            'message': f'Invitation sent to {email}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/api/workspaces/<workspace_id>/activity')
@require_auth
def get_workspace_activity(workspace_id):
    """Get workspace activity feed"""
    try:
        # Mock activity data
        activities = [
            {
                'id': str(uuid.uuid4()),
                'user': 'Dr. Sarah Chen',
                'action': 'uploaded safety protocol document',
                'type': 'file',
                'timestamp': datetime.now().isoformat(),
                'details': 'Constitutional AI Safety Protocols v2.1.pdf'
            },
            {
                'id': str(uuid.uuid4()),
                'user': 'Prof. Michael Rodriguez',
                'action': 'created new chat session',
                'type': 'chat',
                'timestamp': datetime.now().isoformat(),
                'details': 'Alignment Research Discussion'
            }
        ]
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/api/workspaces/<workspace_id>/members')
@require_auth
def get_workspace_members(workspace_id):
    """Get workspace members"""
    try:
        # Mock members data
        members = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Dr. Sarah Chen',
                'email': 'sarah.chen@university.edu',
                'role': 'admin',
                'joined_at': '2025-01-15',
                'last_active': '2 hours ago'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Prof. Michael Rodriguez',
                'email': 'm.rodriguez@research.org',
                'role': 'member',
                'joined_at': '2025-01-16',
                'last_active': '1 day ago'
            }
        ]
        
        return jsonify({
            'success': True,
            'members': members
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
