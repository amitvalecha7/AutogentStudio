from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, Assistant, Plugin, WorkflowTemplate
from sqlalchemy import or_, desc
import logging

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/discover')
def discover():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    
    # Get featured content
    featured_assistants = Assistant.query.filter_by(is_featured=True).limit(8).all()
    featured_plugins = Plugin.query.filter_by(is_featured=True).limit(8).all()
    featured_workflows = WorkflowTemplate.query.filter_by(is_featured=True).limit(8).all()
    
    return render_template('discover/discover.html', 
                         user=user,
                         featured_assistants=featured_assistants,
                         featured_plugins=featured_plugins,
                         featured_workflows=featured_workflows)

@discover_bp.route('/discover/assistant')
def assistant_marketplace():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'latest')
    
    # Build query
    query = Assistant.query.filter_by(is_public=True)
    
    if category:
        query = query.filter(Assistant.category == category)
    
    if search:
        query = query.filter(
            or_(
                Assistant.name.ilike(f'%{search}%'),
                Assistant.description.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'popular':
        query = query.order_by(desc(Assistant.usage_count))
    elif sort_by == 'rating':
        query = query.order_by(desc(Assistant.rating))
    else:  # latest
        query = query.order_by(desc(Assistant.created_at))
    
    assistants = query.all()
    
    # Get available categories
    categories = db.session.query(Assistant.category).filter(
        Assistant.is_public == True,
        Assistant.category.isnot(None)
    ).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('discover/assistant.html', 
                         user=user,
                         assistants=assistants,
                         categories=categories,
                         current_category=category,
                         current_search=search,
                         current_sort=sort_by)

@discover_bp.route('/discover/assistant/<assistant_id>')
def assistant_detail(assistant_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    assistant = Assistant.query.filter_by(id=assistant_id, is_public=True).first()
    
    if not assistant:
        return redirect(url_for('discover.assistant_marketplace'))
    
    # Get related assistants
    related_assistants = Assistant.query.filter(
        Assistant.category == assistant.category,
        Assistant.id != assistant.id,
        Assistant.is_public == True
    ).limit(4).all()
    
    return render_template('discover/assistant_detail.html', 
                         user=user,
                         assistant=assistant,
                         related_assistants=related_assistants)

@discover_bp.route('/discover/mcp')
def mcp_marketplace():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'latest')
    
    # Build query
    query = Plugin.query
    
    if category:
        query = query.filter(Plugin.category == category)
    
    if search:
        query = query.filter(
            or_(
                Plugin.name.ilike(f'%{search}%'),
                Plugin.description.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'popular':
        query = query.order_by(desc(Plugin.download_count))
    elif sort_by == 'rating':
        query = query.order_by(desc(Plugin.rating))
    else:  # latest
        query = query.order_by(desc(Plugin.created_at))
    
    plugins = query.all()
    
    # Get available categories
    categories = db.session.query(Plugin.category).filter(
        Plugin.category.isnot(None)
    ).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('discover/mcp.html', 
                         user=user,
                         plugins=plugins,
                         categories=categories,
                         current_category=category,
                         current_search=search,
                         current_sort=sort_by)

@discover_bp.route('/discover/mcp/<plugin_id>')
def mcp_detail(plugin_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    plugin = Plugin.query.get(plugin_id)
    
    if not plugin:
        return redirect(url_for('discover.mcp_marketplace'))
    
    # Get related plugins
    related_plugins = Plugin.query.filter(
        Plugin.category == plugin.category,
        Plugin.id != plugin.id
    ).limit(4).all()
    
    return render_template('discover/mcp_detail.html', 
                         user=user,
                         plugin=plugin,
                         related_plugins=related_plugins)

@discover_bp.route('/discover/model')
def model_marketplace():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    
    # Mock model data (in a real implementation, this would come from model providers)
    models = [
        {
            'id': 'gpt-4o',
            'name': 'GPT-4o',
            'provider': 'OpenAI',
            'description': 'Most advanced GPT-4 model with multimodal capabilities',
            'type': 'Language Model',
            'context_length': 128000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'pricing': {'input': 0.005, 'output': 0.015}
        },
        {
            'id': 'claude-sonnet-4-20250514',
            'name': 'Claude Sonnet 4',
            'provider': 'Anthropic',
            'description': 'Latest Claude model with enhanced reasoning capabilities',
            'type': 'Language Model',
            'context_length': 200000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'pricing': {'input': 0.003, 'output': 0.015}
        },
        {
            'id': 'gemini-pro',
            'name': 'Gemini Pro',
            'provider': 'Google',
            'description': 'Google\'s most capable multimodal model',
            'type': 'Language Model',
            'context_length': 100000,
            'capabilities': ['text', 'vision', 'function_calling'],
            'pricing': {'input': 0.0025, 'output': 0.0075}
        }
    ]
    
    return render_template('discover/model.html', 
                         user=user,
                         models=models)

@discover_bp.route('/discover/provider')
def provider_marketplace():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    
    # Mock provider data
    providers = [
        {
            'id': 'openai',
            'name': 'OpenAI',
            'description': 'Leading AI research company with GPT and DALL-E models',
            'logo': '/static/images/providers/openai.png',
            'models': ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo', 'dall-e-3'],
            'capabilities': ['text', 'vision', 'image_generation', 'function_calling'],
            'website': 'https://openai.com'
        },
        {
            'id': 'anthropic',
            'name': 'Anthropic',
            'description': 'AI safety company focused on helpful, harmless, and honest AI',
            'logo': '/static/images/providers/anthropic.png',
            'models': ['claude-sonnet-4-20250514', 'claude-3-opus', 'claude-3-sonnet'],
            'capabilities': ['text', 'vision', 'function_calling'],
            'website': 'https://anthropic.com'
        },
        {
            'id': 'google',
            'name': 'Google AI',
            'description': 'Google\'s AI division with Gemini and PaLM models',
            'logo': '/static/images/providers/google.png',
            'models': ['gemini-pro', 'gemini-pro-vision', 'palm-2'],
            'capabilities': ['text', 'vision', 'function_calling'],
            'website': 'https://ai.google.com'
        }
    ]
    
    return render_template('discover/provider.html', 
                         user=user,
                         providers=providers)

@discover_bp.route('/api/discover/assistants')
def api_assistants():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        assistants = Assistant.query.filter_by(is_public=True).all()
        return jsonify({
            'success': True,
            'assistants': [assistant.to_dict() for assistant in assistants]
        })
    except Exception as e:
        logging.error(f"Error fetching assistants: {str(e)}")
        return jsonify({'error': 'Failed to fetch assistants'}), 500

@discover_bp.route('/api/discover/plugins')
def api_plugins():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        plugins = Plugin.query.all()
        return jsonify({
            'success': True,
            'plugins': [plugin.to_dict() for plugin in plugins]
        })
    except Exception as e:
        logging.error(f"Error fetching plugins: {str(e)}")
        return jsonify({'error': 'Failed to fetch plugins'}), 500

@discover_bp.route('/api/discover/assistant/<assistant_id>/use', methods=['POST'])
def use_assistant(assistant_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        assistant = Assistant.query.get(assistant_id)
        if not assistant:
            return jsonify({'error': 'Assistant not found'}), 404
        
        # Increment usage count
        assistant.usage_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assistant': assistant.to_dict()
        })
    except Exception as e:
        logging.error(f"Error using assistant: {str(e)}")
        return jsonify({'error': 'Failed to use assistant'}), 500

@discover_bp.route('/api/discover/plugin/<plugin_id>/install', methods=['POST'])
def install_plugin(plugin_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        plugin = Plugin.query.get(plugin_id)
        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404
        
        # Increment download count
        plugin.download_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'plugin': plugin.to_dict(),
            'message': 'Plugin installed successfully'
        })
    except Exception as e:
        logging.error(f"Error installing plugin: {str(e)}")
        return jsonify({'error': 'Failed to install plugin'}), 500
