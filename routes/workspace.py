from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, Conversation, KnowledgeBase, WorkflowTemplate
import logging

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/workspace/<workspace_id>')
def workspace_detail(workspace_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    # For now, treat workspace_id as user workspace
    return render_template('workspace/workspace.html', user=user, workspace_id=workspace_id)

@workspace_bp.route('/workspace/knowledge')
def workspace_knowledge():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('workspace/knowledge.html', user=user)

@workspace_bp.route('/workspace/chat')
def workspace_chat():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('workspace/chat.html', user=user)

@workspace_bp.route('/workspace/permissions')
def workspace_permissions():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('workspace/permissions.html', user=user)

@workspace_bp.route('/workspace/analytics')
def workspace_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('workspace/analytics.html', user=user)

@workspace_bp.route('/api/workspace/overview')
def get_workspace_overview():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get workspace statistics
        conversation_count = Conversation.query.filter_by(user_id=user.id).count()
        knowledge_base_count = KnowledgeBase.query.filter_by(user_id=user.id).count()
        workflow_count = WorkflowTemplate.query.filter_by(user_id=user.id).count()
        
        # Get recent activity
        recent_conversations = Conversation.query.filter_by(user_id=user.id).order_by(
            Conversation.updated_at.desc()
        ).limit(5).all()
        
        recent_knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(
            KnowledgeBase.updated_at.desc()
        ).limit(5).all()
        
        overview = {
            'statistics': {
                'conversations': conversation_count,
                'knowledge_bases': knowledge_base_count,
                'workflows': workflow_count
            },
            'recent_conversations': [conv.to_dict() for conv in recent_conversations],
            'recent_knowledge_bases': [kb.to_dict() for kb in recent_knowledge_bases],
            'user_info': user.to_dict()
        }
        
        return jsonify({
            'success': True,
            'overview': overview
        })
        
    except Exception as e:
        logging.error(f"Error getting workspace overview: {str(e)}")
        return jsonify({'error': 'Failed to get workspace overview'}), 500

@workspace_bp.route('/api/workspace/collaboration/status')
def get_collaboration_status():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Mock collaboration data - in a real implementation, this would track active collaborators
        collaboration_status = {
            'active_collaborators': [],
            'pending_invites': [],
            'shared_resources': {
                'conversations': 0,
                'knowledge_bases': 0,
                'workflows': 0
            },
            'collaboration_features': [
                'Real-time chat collaboration',
                'Shared knowledge bases',
                'Collaborative workflows',
                'Team analytics',
                'Permission management'
            ]
        }
        
        return jsonify({
            'success': True,
            'collaboration_status': collaboration_status
        })
        
    except Exception as e:
        logging.error(f"Error getting collaboration status: {str(e)}")
        return jsonify({'error': 'Failed to get collaboration status'}), 500

@workspace_bp.route('/api/workspace/share', methods=['POST'])
def share_resource():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        resource_type = data.get('resource_type', '')  # 'conversation', 'knowledge_base', 'workflow'
        resource_id = data.get('resource_id', '')
        share_with = data.get('share_with', [])  # list of user IDs or emails
        permissions = data.get('permissions', 'read')  # 'read', 'write', 'admin'
        
        if not all([resource_type, resource_id]):
            return jsonify({'error': 'Resource type and ID are required'}), 400
        
        # Mock sharing functionality
        sharing_result = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'shared_with': share_with,
            'permissions': permissions,
            'share_link': f'/workspace/shared/{resource_type}/{resource_id}',
            'expires_at': None,
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        return jsonify({
            'success': True,
            'sharing_result': sharing_result
        })
        
    except Exception as e:
        logging.error(f"Error sharing resource: {str(e)}")
        return jsonify({'error': 'Failed to share resource'}), 500

@workspace_bp.route('/api/workspace/permissions', methods=['GET', 'POST'])
def manage_permissions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            resource_type = data.get('resource_type', '')
            resource_id = data.get('resource_id', '')
            user_email = data.get('user_email', '')
            permission_level = data.get('permission_level', 'read')
            
            if not all([resource_type, resource_id, user_email, permission_level]):
                return jsonify({'error': 'All fields are required'}), 400
            
            # Mock permission management
            permission_result = {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'user_email': user_email,
                'permission_level': permission_level,
                'granted_by': user.email,
                'granted_at': '2023-01-01T00:00:00Z'
            }
            
            return jsonify({
                'success': True,
                'permission_result': permission_result
            })
            
        except Exception as e:
            logging.error(f"Error managing permissions: {str(e)}")
            return jsonify({'error': 'Failed to manage permissions'}), 500
    
    # GET request - return current permissions
    try:
        # Mock permissions data
        permissions = {
            'owned_resources': {
                'conversations': [],
                'knowledge_bases': [],
                'workflows': []
            },
            'shared_with_me': {
                'conversations': [],
                'knowledge_bases': [],
                'workflows': []
            },
            'permission_levels': ['read', 'write', 'admin']
        }
        
        return jsonify({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        logging.error(f"Error getting permissions: {str(e)}")
        return jsonify({'error': 'Failed to get permissions'}), 500

@workspace_bp.route('/api/workspace/activity/feed')
def get_activity_feed():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get recent activity across different resources
        recent_conversations = Conversation.query.filter_by(user_id=user.id).order_by(
            Conversation.updated_at.desc()
        ).limit(10).all()
        
        recent_knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(
            KnowledgeBase.updated_at.desc()
        ).limit(10).all()
        
        recent_workflows = WorkflowTemplate.query.filter_by(user_id=user.id).order_by(
            WorkflowTemplate.updated_at.desc()
        ).limit(10).all()
        
        # Combine and sort activity
        activity_feed = []
        
        for conv in recent_conversations:
            activity_feed.append({
                'type': 'conversation',
                'action': 'updated',
                'resource': conv.to_dict(),
                'timestamp': conv.updated_at.isoformat()
            })
        
        for kb in recent_knowledge_bases:
            activity_feed.append({
                'type': 'knowledge_base',
                'action': 'updated',
                'resource': kb.to_dict(),
                'timestamp': kb.updated_at.isoformat()
            })
        
        for wf in recent_workflows:
            activity_feed.append({
                'type': 'workflow',
                'action': 'updated',
                'resource': wf.to_dict(),
                'timestamp': wf.updated_at.isoformat()
            })
        
        # Sort by timestamp (most recent first)
        activity_feed.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'activity_feed': activity_feed[:20]  # Return top 20 activities
        })
        
    except Exception as e:
        logging.error(f"Error getting activity feed: {str(e)}")
        return jsonify({'error': 'Failed to get activity feed'}), 500

@workspace_bp.route('/api/workspace/search')
def search_workspace():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        query = request.args.get('q', '').strip()
        resource_types = request.args.getlist('types')  # ['conversation', 'knowledge_base', 'workflow']
        
        if not query:
            return jsonify({'results': []})
        
        results = []
        
        # Search conversations
        if not resource_types or 'conversation' in resource_types:
            conversations = Conversation.query.filter(
                Conversation.user_id == user.id,
                Conversation.title.ilike(f'%{query}%')
            ).limit(10).all()
            
            for conv in conversations:
                results.append({
                    'type': 'conversation',
                    'resource': conv.to_dict(),
                    'relevance_score': 1.0
                })
        
        # Search knowledge bases
        if not resource_types or 'knowledge_base' in resource_types:
            knowledge_bases = KnowledgeBase.query.filter(
                KnowledgeBase.user_id == user.id,
                db.or_(
                    KnowledgeBase.name.ilike(f'%{query}%'),
                    KnowledgeBase.description.ilike(f'%{query}%')
                )
            ).limit(10).all()
            
            for kb in knowledge_bases:
                results.append({
                    'type': 'knowledge_base',
                    'resource': kb.to_dict(),
                    'relevance_score': 1.0
                })
        
        # Search workflows
        if not resource_types or 'workflow' in resource_types:
            workflows = WorkflowTemplate.query.filter(
                WorkflowTemplate.user_id == user.id,
                db.or_(
                    WorkflowTemplate.name.ilike(f'%{query}%'),
                    WorkflowTemplate.description.ilike(f'%{query}%')
                )
            ).limit(10).all()
            
            for wf in workflows:
                results.append({
                    'type': 'workflow',
                    'resource': wf.to_dict(),
                    'relevance_score': 1.0
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })
        
    except Exception as e:
        logging.error(f"Error searching workspace: {str(e)}")
        return jsonify({'error': 'Failed to search workspace'}), 500
