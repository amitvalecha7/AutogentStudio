from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import Assistant, Plugin, ModelProvider, User
from blueprints.auth import login_required, get_current_user
import logging

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/')
def discover_index():
    # Featured assistants
    featured_assistants = Assistant.query.filter_by(is_public=True)\
        .order_by(Assistant.downloads.desc()).limit(8).all()
    
    # Featured plugins
    featured_plugins = Plugin.query.filter_by(is_featured=True)\
        .order_by(Plugin.install_count.desc()).limit(8).all()
    
    return render_template('discover/discover.html', 
                         featured_assistants=featured_assistants,
                         featured_plugins=featured_plugins)

@discover_bp.route('/assistant')
def assistant_marketplace():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Assistant.query.filter_by(is_public=True)
    
    if search:
        query = query.filter(
            db.or_(
                Assistant.name.contains(search),
                Assistant.description.contains(search)
            )
        )
    
    assistants = query.order_by(Assistant.downloads.desc())\
        .paginate(page=page, per_page=12, error_out=False)
    
    return render_template('discover/assistant.html', 
                         assistants=assistants,
                         search=search,
                         category=category)

@discover_bp.route('/assistant/<int:assistant_id>')
def assistant_detail(assistant_id):
    assistant = Assistant.query.get_or_404(assistant_id)
    creator = User.query.get(assistant.creator_id) if assistant.creator_id else None
    
    # Similar assistants
    similar_assistants = Assistant.query\
        .filter(Assistant.id != assistant_id)\
        .filter_by(is_public=True)\
        .limit(4).all()
    
    return render_template('discover/assistant_detail.html', 
                         assistant=assistant,
                         creator=creator,
                         similar_assistants=similar_assistants)

@discover_bp.route('/assistant/<int:assistant_id>/install', methods=['POST'])
@login_required
def install_assistant(assistant_id):
    user = get_current_user()
    assistant = Assistant.query.get_or_404(assistant_id)
    
    try:
        # Create a copy for the user (simplified implementation)
        user_assistant = Assistant(
            name=f"{assistant.name} (Copy)",
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            model_provider=assistant.model_provider,
            model_name=assistant.model_name,
            creator_id=user.id,
            is_public=False
        )
        
        db.session.add(user_assistant)
        
        # Increment download count
        assistant.downloads += 1
        
        db.session.commit()
        
        logging.info(f"Assistant {assistant_id} installed by user {user.id}")
        return jsonify({'success': True, 'message': 'Assistant installed successfully'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error installing assistant: {str(e)}")
        return jsonify({'error': 'Failed to install assistant'}), 500

@discover_bp.route('/mcp')
def plugin_marketplace():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Plugin.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                Plugin.name.contains(search),
                Plugin.description.contains(search)
            )
        )
    
    plugins = query.order_by(Plugin.install_count.desc())\
        .paginate(page=page, per_page=12, error_out=False)
    
    # Get categories for filter
    categories = db.session.query(Plugin.category)\
        .filter(Plugin.category.isnot(None))\
        .distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('discover/mcp.html', 
                         plugins=plugins,
                         categories=categories,
                         search=search,
                         selected_category=category)

@discover_bp.route('/mcp/<int:plugin_id>')
def plugin_detail(plugin_id):
    plugin = Plugin.query.get_or_404(plugin_id)
    
    # Related plugins
    related_plugins = Plugin.query\
        .filter(Plugin.id != plugin_id)\
        .filter_by(category=plugin.category)\
        .limit(4).all()
    
    return render_template('discover/mcp_detail.html', 
                         plugin=plugin,
                         related_plugins=related_plugins)

@discover_bp.route('/mcp/<int:plugin_id>/install', methods=['POST'])
@login_required
def install_plugin(plugin_id):
    user = get_current_user()
    plugin = Plugin.query.get_or_404(plugin_id)
    
    try:
        # In a real implementation, this would handle actual plugin installation
        # For now, just increment the install count
        plugin.install_count += 1
        db.session.commit()
        
        logging.info(f"Plugin {plugin_id} installed by user {user.id}")
        return jsonify({'success': True, 'message': 'Plugin installed successfully'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error installing plugin: {str(e)}")
        return jsonify({'error': 'Failed to install plugin'}), 500

@discover_bp.route('/model')
def model_marketplace():
    providers = ModelProvider.query.filter_by(is_active=True).all()
    
    # Group models by provider
    model_data = []
    for provider in providers:
        if provider.supported_models:
            import json
            models = json.loads(provider.supported_models)
            model_data.append({
                'provider': provider,
                'models': models
            })
    
    return render_template('discover/model.html', model_data=model_data)

@discover_bp.route('/provider')
def provider_marketplace():
    providers = ModelProvider.query.filter_by(is_active=True).all()
    return render_template('discover/provider.html', providers=providers)

@discover_bp.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    results = {
        'assistants': [],
        'plugins': [],
        'models': []
    }
    
    if query:
        if category in ['all', 'assistants']:
            results['assistants'] = Assistant.query\
                .filter_by(is_public=True)\
                .filter(
                    db.or_(
                        Assistant.name.contains(query),
                        Assistant.description.contains(query)
                    )
                ).limit(10).all()
        
        if category in ['all', 'plugins']:
            results['plugins'] = Plugin.query\
                .filter(
                    db.or_(
                        Plugin.name.contains(query),
                        Plugin.description.contains(query)
                    )
                ).limit(10).all()
        
        if category in ['all', 'models']:
            results['models'] = ModelProvider.query\
                .filter_by(is_active=True)\
                .filter(
                    db.or_(
                        ModelProvider.name.contains(query),
                        ModelProvider.description.contains(query)
                    )
                ).limit(10).all()
    
    return jsonify({
        'query': query,
        'category': category,
        'results': {
            'assistants': [{'id': a.id, 'name': a.name, 'description': a.description} for a in results['assistants']],
            'plugins': [{'id': p.id, 'name': p.name, 'description': p.description} for p in results['plugins']],
            'models': [{'id': m.id, 'name': m.display_name, 'description': m.description} for m in results['models']]
        }
    })
