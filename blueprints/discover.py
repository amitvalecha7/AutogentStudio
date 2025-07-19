from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Assistant, Plugin, AIModel, db
from sqlalchemy import or_, desc

discover_bp = Blueprint('discover', __name__, url_prefix='/discover')

@discover_bp.route('/')
def index():
    # Get featured content
    featured_assistants = Assistant.query.filter_by(
        is_featured=True
    ).order_by(desc(Assistant.usage_count)).limit(8).all()
    
    featured_plugins = Plugin.query.filter_by(
        is_featured=True
    ).order_by(desc(Plugin.download_count)).limit(8).all()
    
    # Get recent additions
    recent_assistants = Assistant.query.order_by(
        desc(Assistant.created_at)
    ).limit(4).all()
    
    recent_plugins = Plugin.query.order_by(
        desc(Plugin.created_at)
    ).limit(4).all()
    
    return render_template('discover/index.html',
                         featured_assistants=featured_assistants,
                         featured_plugins=featured_plugins,
                         recent_assistants=recent_assistants,
                         recent_plugins=recent_plugins)

@discover_bp.route('/assistant')
def assistant_marketplace():
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'featured')  # featured, popular, recent
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build query
    query = Assistant.query
    
    if category:
        query = query.filter_by(category=category)
    
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
    elif sort_by == 'recent':
        query = query.order_by(desc(Assistant.created_at))
    elif sort_by == 'rating':
        query = query.order_by(desc(Assistant.rating))
    else:  # featured
        query = query.order_by(desc(Assistant.is_featured), desc(Assistant.usage_count))
    
    # Paginate
    assistants = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(Assistant.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('discover/assistant.html',
                         assistants=assistants,
                         categories=categories,
                         current_category=category,
                         current_search=search,
                         current_sort=sort_by)

@discover_bp.route('/assistant/<assistant_id>')
def assistant_detail(assistant_id):
    assistant = Assistant.query.get_or_404(assistant_id)
    
    # Increment usage count
    assistant.usage_count += 1
    db.session.commit()
    
    # Get related assistants
    related = Assistant.query.filter(
        Assistant.category == assistant.category,
        Assistant.id != assistant_id
    ).order_by(desc(Assistant.usage_count)).limit(4).all()
    
    return render_template('discover/assistant_detail.html',
                         assistant=assistant,
                         related_assistants=related)

@discover_bp.route('/mcp')
def plugin_marketplace():
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'featured')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build query
    query = Plugin.query
    
    if category:
        query = query.filter_by(category=category)
    
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
    elif sort_by == 'recent':
        query = query.order_by(desc(Plugin.created_at))
    elif sort_by == 'rating':
        query = query.order_by(desc(Plugin.rating))
    else:  # featured
        query = query.order_by(desc(Plugin.is_featured), desc(Plugin.download_count))
    
    # Paginate
    plugins = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(Plugin.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('discover/mcp.html',
                         plugins=plugins,
                         categories=categories,
                         current_category=category,
                         current_search=search,
                         current_sort=sort_by)

@discover_bp.route('/mcp/<plugin_id>')
def plugin_detail(plugin_id):
    plugin = Plugin.query.get_or_404(plugin_id)
    
    # Increment download count
    plugin.download_count += 1
    db.session.commit()
    
    # Get related plugins
    related = Plugin.query.filter(
        Plugin.category == plugin.category,
        Plugin.id != plugin_id
    ).order_by(desc(Plugin.download_count)).limit(4).all()
    
    return render_template('discover/plugin_detail.html',
                         plugin=plugin,
                         related_plugins=related)

@discover_bp.route('/model')
def model_marketplace():
    # Get available AI models
    sort_by = request.args.get('sort', 'provider')
    search = request.args.get('search', '')
    model_type = request.args.get('type', '')  # chat, image, embedding
    
    query = AIModel.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            or_(
                AIModel.name.ilike(f'%{search}%'),
                AIModel.provider.ilike(f'%{search}%')
            )
        )
    
    if model_type:
        query = query.filter_by(model_type=model_type)
    
    if sort_by == 'name':
        query = query.order_by(AIModel.name)
    elif sort_by == 'cost':
        query = query.order_by(AIModel.cost_per_token_input)
    else:  # provider
        query = query.order_by(AIModel.provider, AIModel.name)
    
    models = query.all()
    
    # Group by provider
    models_by_provider = {}
    for model in models:
        if model.provider not in models_by_provider:
            models_by_provider[model.provider] = []
        models_by_provider[model.provider].append(model)
    
    # Get model types for filter
    model_types = db.session.query(AIModel.model_type).distinct().all()
    model_types = [mt[0] for mt in model_types if mt[0]]
    
    return render_template('discover/model.html',
                         models_by_provider=models_by_provider,
                         model_types=model_types,
                         current_type=model_type,
                         current_search=search,
                         current_sort=sort_by)

@discover_bp.route('/provider')
def provider_marketplace():
    # Get unique providers with their model counts
    providers = db.session.query(
        AIModel.provider,
        db.func.count(AIModel.id).label('model_count')
    ).filter_by(is_active=True).group_by(AIModel.provider).all()
    
    provider_info = {
        'openai': {
            'name': 'OpenAI',
            'description': 'Leading AI research company with GPT models',
            'website': 'https://openai.com',
            'capabilities': ['chat', 'image', 'embedding', 'audio']
        },
        'anthropic': {
            'name': 'Anthropic',
            'description': 'AI safety company behind Claude models',
            'website': 'https://anthropic.com',
            'capabilities': ['chat', 'analysis']
        },
        'google': {
            'name': 'Google AI',
            'description': 'Google\'s AI platform with Gemini models',
            'website': 'https://ai.google',
            'capabilities': ['chat', 'multimodal', 'code']
        },
        'cohere': {
            'name': 'Cohere',
            'description': 'Enterprise AI platform for language understanding',
            'website': 'https://cohere.com',
            'capabilities': ['chat', 'embedding', 'classification']
        }
    }
    
    return render_template('discover/provider.html',
                         providers=providers,
                         provider_info=provider_info)

@discover_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')  # all, assistant, plugin, model
    
    results = {
        'assistants': [],
        'plugins': [],
        'models': []
    }
    
    if query:
        if category in ['all', 'assistant']:
            assistants = Assistant.query.filter(
                or_(
                    Assistant.name.ilike(f'%{query}%'),
                    Assistant.description.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['assistants'] = assistants
        
        if category in ['all', 'plugin']:
            plugins = Plugin.query.filter(
                or_(
                    Plugin.name.ilike(f'%{query}%'),
                    Plugin.description.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['plugins'] = plugins
        
        if category in ['all', 'model']:
            models = AIModel.query.filter(
                or_(
                    AIModel.name.ilike(f'%{query}%'),
                    AIModel.provider.ilike(f'%{query}%')
                )
            ).limit(10).all()
            results['models'] = models
    
    return render_template('discover/search.html',
                         query=query,
                         category=category,
                         results=results)

@discover_bp.route('/assistant/<assistant_id>/install', methods=['POST'])
@login_required
def install_assistant(assistant_id):
    assistant = Assistant.query.get_or_404(assistant_id)
    
    # Create a new chat session with this assistant
    from blueprints.chat import new_session
    from flask import request as flask_request
    
    # Temporarily modify request to include assistant data
    original_json = flask_request.get_json
    flask_request.get_json = lambda: {
        'title': f"Chat with {assistant.name}",
        'model_provider': assistant.model_config.get('provider', 'openai'),
        'model_name': assistant.model_config.get('model', 'gpt-4o'),
        'system_prompt': assistant.system_prompt,
        'settings': assistant.model_config
    }
    
    result = new_session()
    flask_request.get_json = original_json
    
    return result

@discover_bp.route('/mcp/<plugin_id>/install', methods=['POST'])
@login_required
def install_plugin(plugin_id):
    plugin = Plugin.query.get_or_404(plugin_id)
    
    # In a real implementation, this would:
    # 1. Add plugin to user's installed plugins
    # 2. Set up plugin configuration
    # 3. Install dependencies if needed
    
    return jsonify({
        'success': True,
        'message': f'Plugin {plugin.name} installed successfully',
        'plugin_id': plugin_id
    })
