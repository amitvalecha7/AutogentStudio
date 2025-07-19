from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Assistant, Plugin, UsageMetrics, db
from services.marketplace_service import MarketplaceService
from sqlalchemy import desc, func
import uuid

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')

@marketplace_bp.route('/')
@login_required
def index():
    # Get marketplace overview
    top_assistants = Assistant.query.filter_by(
        is_featured=True
    ).order_by(desc(Assistant.usage_count)).limit(6).all()
    
    top_plugins = Plugin.query.filter_by(
        is_featured=True
    ).order_by(desc(Plugin.download_count)).limit(6).all()
    
    return render_template('marketplace/index.html',
                         top_assistants=top_assistants,
                         top_plugins=top_plugins)

@marketplace_bp.route('/revenue')
@login_required
def revenue():
    return render_template('marketplace/revenue.html')

@marketplace_bp.route('/monetize')
@login_required
def monetize():
    return render_template('marketplace/monetize.html')

@marketplace_bp.route('/analytics')
@login_required
def analytics():
    return render_template('marketplace/analytics.html')

@marketplace_bp.route('/payments')
@login_required
def payments():
    return render_template('marketplace/payments.html')

@marketplace_bp.route('/create')
@login_required
def create():
    return render_template('marketplace/create.html')

@marketplace_bp.route('/api/revenue-dashboard')
@login_required
def api_revenue_dashboard():
    try:
        marketplace_service = MarketplaceService()
        
        # Get user's revenue data
        revenue_data = marketplace_service.get_user_revenue_dashboard(current_user.id)
        
        return jsonify({
            'success': True,
            'data': revenue_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/submit-assistant', methods=['POST'])
@login_required
def submit_assistant():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '')
    system_prompt = data.get('system_prompt', '')
    category = data.get('category', '')
    
    if not all([name, description, system_prompt]):
        return jsonify({'error': 'All required fields must be filled'}), 400
    
    try:
        marketplace_service = MarketplaceService()
        
        assistant_id = str(uuid.uuid4())
        assistant = Assistant(
            id=assistant_id,
            name=name,
            description=description,
            category=category,
            author=current_user.username,
            system_prompt=system_prompt,
            model_config=data.get('model_config', {}),
            capabilities=data.get('capabilities', []),
            is_featured=False,
            usage_count=0,
            rating=0.0
        )
        
        db.session.add(assistant)
        db.session.commit()
        
        # Submit for review
        review_result = marketplace_service.submit_for_review(assistant, 'assistant')
        
        return jsonify({
            'success': True,
            'assistant_id': assistant_id,
            'review_result': review_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/submit-plugin', methods=['POST'])
@login_required
def submit_plugin():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '')
    github_url = data.get('github_url', '')
    category = data.get('category', '')
    
    if not all([name, description, github_url]):
        return jsonify({'error': 'All required fields must be filled'}), 400
    
    try:
        marketplace_service = MarketplaceService()
        
        plugin_id = str(uuid.uuid4())
        plugin = Plugin(
            id=plugin_id,
            name=name,
            description=description,
            category=category,
            author=current_user.username,
            github_url=github_url,
            version=data.get('version', '1.0.0'),
            installation_type=data.get('installation_type', 'npm'),
            npm_package=data.get('npm_package', ''),
            is_featured=False,
            download_count=0,
            rating=0.0,
            settings_schema=data.get('settings_schema', {})
        )
        
        db.session.add(plugin)
        db.session.commit()
        
        # Submit for review
        review_result = marketplace_service.submit_for_review(plugin, 'plugin')
        
        return jsonify({
            'success': True,
            'plugin_id': plugin_id,
            'review_result': review_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/monetization-setup', methods=['POST'])
@login_required
def setup_monetization():
    data = request.get_json()
    
    item_id = data.get('item_id')
    item_type = data.get('item_type')  # assistant or plugin
    pricing_model = data.get('pricing_model', 'free')  # free, one_time, subscription, usage_based
    price = data.get('price', 0.0)
    
    if not all([item_id, item_type]):
        return jsonify({'error': 'Item ID and type are required'}), 400
    
    try:
        marketplace_service = MarketplaceService()
        
        # Set up monetization
        monetization_result = marketplace_service.setup_monetization(
            item_id=item_id,
            item_type=item_type,
            pricing_model=pricing_model,
            price=price,
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'result': monetization_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/usage-analytics/<item_id>')
@login_required
def item_usage_analytics(item_id):
    try:
        # Get usage analytics for user's marketplace item
        analytics_data = db.session.query(
            UsageMetrics.metric_name,
            func.sum(UsageMetrics.value).label('total_value'),
            func.count(UsageMetrics.id).label('count')
        ).filter(
            UsageMetrics.metadata.op('->>')('item_id') == item_id,
            UsageMetrics.user_id == current_user.id
        ).group_by(UsageMetrics.metric_name).all()
        
        return jsonify({
            'success': True,
            'analytics': [{
                'metric': row.metric_name,
                'total_value': float(row.total_value),
                'count': row.count
            } for row in analytics_data]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/payment-setup', methods=['POST'])
@login_required
def setup_payment():
    data = request.get_json()
    
    payment_method = data.get('payment_method', 'stripe')
    account_details = data.get('account_details', {})
    crypto_wallet = data.get('crypto_wallet', '')
    
    try:
        marketplace_service = MarketplaceService()
        
        # Set up payment processing
        payment_setup = marketplace_service.setup_payment_processing(
            user_id=current_user.id,
            payment_method=payment_method,
            account_details=account_details,
            crypto_wallet=crypto_wallet
        )
        
        return jsonify({
            'success': True,
            'setup': payment_setup
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/earnings')
@login_required
def earnings():
    try:
        marketplace_service = MarketplaceService()
        
        # Get user's earnings
        earnings_data = marketplace_service.get_user_earnings(current_user.id)
        
        return jsonify({
            'success': True,
            'earnings': earnings_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/marketplace-stats')
@login_required
def marketplace_stats():
    # Get overall marketplace statistics
    total_assistants = Assistant.query.count()
    total_plugins = Plugin.query.count()
    active_creators = db.session.query(func.count(func.distinct(Assistant.author))).scalar()
    
    # Top categories
    top_assistant_categories = db.session.query(
        Assistant.category,
        func.count(Assistant.id).label('count')
    ).filter(Assistant.category.isnot(None)).group_by(
        Assistant.category
    ).order_by(desc('count')).limit(5).all()
    
    top_plugin_categories = db.session.query(
        Plugin.category,
        func.count(Plugin.id).label('count')
    ).filter(Plugin.category.isnot(None)).group_by(
        Plugin.category
    ).order_by(desc('count')).limit(5).all()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_assistants': total_assistants,
            'total_plugins': total_plugins,
            'active_creators': active_creators,
            'top_assistant_categories': dict(top_assistant_categories),
            'top_plugin_categories': dict(top_plugin_categories)
        }
    })

@marketplace_bp.route('/api/trending')
@login_required
def trending():
    # Get trending items
    trending_assistants = Assistant.query.order_by(
        desc(Assistant.usage_count)
    ).limit(10).all()
    
    trending_plugins = Plugin.query.order_by(
        desc(Plugin.download_count)
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'trending': {
            'assistants': [{
                'id': assistant.id,
                'name': assistant.name,
                'author': assistant.author,
                'usage_count': assistant.usage_count,
                'rating': assistant.rating
            } for assistant in trending_assistants],
            'plugins': [{
                'id': plugin.id,
                'name': plugin.name,
                'author': plugin.author,
                'download_count': plugin.download_count,
                'rating': plugin.rating
            } for plugin in trending_plugins]
        }
    })

@marketplace_bp.route('/api/featured-items')
@login_required
def featured_items():
    # Get featured marketplace items
    featured_assistants = Assistant.query.filter_by(
        is_featured=True
    ).order_by(desc(Assistant.created_at)).all()
    
    featured_plugins = Plugin.query.filter_by(
        is_featured=True
    ).order_by(desc(Plugin.created_at)).all()
    
    return jsonify({
        'success': True,
        'featured': {
            'assistants': [{
                'id': assistant.id,
                'name': assistant.name,
                'description': assistant.description,
                'author': assistant.author,
                'category': assistant.category,
                'usage_count': assistant.usage_count,
                'rating': assistant.rating
            } for assistant in featured_assistants],
            'plugins': [{
                'id': plugin.id,
                'name': plugin.name,
                'description': plugin.description,
                'author': plugin.author,
                'category': plugin.category,
                'download_count': plugin.download_count,
                'rating': plugin.rating
            } for plugin in featured_plugins]
        }
    })

@marketplace_bp.route('/api/purchase', methods=['POST'])
@login_required
def purchase_item():
    data = request.get_json()
    
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    payment_method = data.get('payment_method', 'stripe')
    
    if not all([item_id, item_type]):
        return jsonify({'error': 'Item ID and type are required'}), 400
    
    try:
        marketplace_service = MarketplaceService()
        
        # Process purchase
        purchase_result = marketplace_service.process_purchase(
            item_id=item_id,
            item_type=item_type,
            buyer_id=current_user.id,
            payment_method=payment_method
        )
        
        return jsonify({
            'success': True,
            'purchase': purchase_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketplace_bp.route('/api/rate-item', methods=['POST'])
@login_required
def rate_item():
    data = request.get_json()
    
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    rating = data.get('rating', 0)
    review = data.get('review', '')
    
    if not all([item_id, item_type]) or not (1 <= rating <= 5):
        return jsonify({'error': 'Valid item ID, type, and rating (1-5) are required'}), 400
    
    try:
        marketplace_service = MarketplaceService()
        
        # Submit rating and review
        rating_result = marketplace_service.submit_rating(
            item_id=item_id,
            item_type=item_type,
            user_id=current_user.id,
            rating=rating,
            review=review
        )
        
        return jsonify({
            'success': True,
            'rating_result': rating_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
