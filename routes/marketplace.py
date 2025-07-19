from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, Assistant, Plugin
import logging
import secrets
from datetime import datetime, timedelta

marketplace_bp = Blueprint('marketplace', __name__)

@marketplace_bp.route('/marketplace')
def marketplace_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/marketplace.html', user=user)

@marketplace_bp.route('/marketplace/revenue')
def revenue_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/revenue.html', user=user)

@marketplace_bp.route('/marketplace/monetize')
def monetization_tools():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/monetize.html', user=user)

@marketplace_bp.route('/marketplace/analytics')
def creator_analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/analytics.html', user=user)

@marketplace_bp.route('/marketplace/payments')
def payment_processing():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/payments.html', user=user)

@marketplace_bp.route('/marketplace/create')
def creator_tools():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('marketplace/create.html', user=user)

@marketplace_bp.route('/api/marketplace/revenue/summary')
def get_revenue_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Mock revenue data
        revenue_summary = {
            'total_earnings': {
                'lifetime': 2845.67,
                'this_month': 456.78,
                'last_month': 389.23,
                'currency': 'USD'
            },
            'revenue_sources': [
                {
                    'source': 'AI Agent Sales',
                    'amount': 1245.32,
                    'percentage': 43.7,
                    'transactions': 156
                },
                {
                    'source': 'Plugin Licensing',
                    'amount': 987.45,
                    'percentage': 34.7,
                    'transactions': 89
                },
                {
                    'source': 'Subscription Fees',
                    'amount': 456.78,
                    'percentage': 16.1,
                    'transactions': 23
                },
                {
                    'source': 'Training Data',
                    'amount': 156.12,
                    'percentage': 5.5,
                    'transactions': 12
                }
            ],
            'payout_status': {
                'pending': 456.78,
                'processing': 0.00,
                'completed': 2388.89,
                'next_payout': (datetime.utcnow() + timedelta(days=3)).isoformat()
            },
            'performance_metrics': {
                'total_downloads': 12456,
                'active_users': 3456,
                'user_retention': 78.5,
                'average_rating': 4.6
            }
        }
        
        return jsonify({
            'success': True,
            'revenue_summary': revenue_summary
        })
        
    except Exception as e:
        logging.error(f"Error getting revenue summary: {str(e)}")
        return jsonify({'error': 'Failed to get revenue summary'}), 500

@marketplace_bp.route('/api/marketplace/products', methods=['GET', 'POST'])
def manage_products():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            product_type = data.get('product_type', '')  # 'agent', 'plugin', 'dataset'
            name = data.get('name', '')
            description = data.get('description', '')
            price = data.get('price', 0)
            pricing_model = data.get('pricing_model', 'one_time')  # 'one_time', 'subscription', 'usage_based'
            
            if not all([product_type, name]):
                return jsonify({'error': 'Product type and name are required'}), 400
            
            # Mock product creation
            product = {
                'id': secrets.token_hex(16),
                'type': product_type,
                'name': name,
                'description': description,
                'price': price,
                'pricing_model': pricing_model,
                'creator_id': str(user.id),
                'status': 'draft',
                'created_at': datetime.utcnow().isoformat(),
                'revenue_share': 70,  # Creator gets 70%
                'blockchain_verified': False,
                'nft_tokenized': False
            }
            
            return jsonify({
                'success': True,
                'product': product
            })
            
        except Exception as e:
            logging.error(f"Error creating product: {str(e)}")
            return jsonify({'error': 'Failed to create product'}), 500
    
    # GET request - return user's products
    try:
        # Mock products data
        products = [
            {
                'id': 'prod-1',
                'type': 'agent',
                'name': 'Advanced Code Assistant',
                'description': 'AI agent specialized in code generation and debugging',
                'price': 29.99,
                'pricing_model': 'subscription',
                'status': 'published',
                'downloads': 1245,
                'revenue': 856.32,
                'rating': 4.8,
                'created_at': '2023-01-01T00:00:00Z'
            },
            {
                'id': 'prod-2',
                'type': 'plugin',
                'name': 'Quantum Circuit Builder',
                'description': 'Plugin for designing quantum circuits visually',
                'price': 49.99,
                'pricing_model': 'one_time',
                'status': 'published',
                'downloads': 456,
                'revenue': 1234.56,
                'rating': 4.6,
                'created_at': '2023-02-01T00:00:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        logging.error(f"Error getting products: {str(e)}")
        return jsonify({'error': 'Failed to get products'}), 500

@marketplace_bp.route('/api/marketplace/analytics/detailed')
def get_detailed_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Mock detailed analytics
        analytics = {
            'user_engagement': {
                'total_users': 5678,
                'active_users': 3456,
                'new_users_this_month': 234,
                'user_retention_rates': {
                    'day_1': 85.2,
                    'day_7': 72.1,
                    'day_30': 45.6
                }
            },
            'product_performance': [
                {
                    'product_id': 'prod-1',
                    'name': 'Advanced Code Assistant',
                    'views': 12456,
                    'downloads': 1245,
                    'conversion_rate': 10.0,
                    'revenue': 856.32,
                    'user_feedback': {
                        'average_rating': 4.8,
                        'total_reviews': 234,
                        'sentiment_score': 0.89
                    }
                }
            ],
            'geographic_distribution': [
                {'country': 'United States', 'users': 2134, 'revenue': 1456.78},
                {'country': 'Germany', 'users': 867, 'revenue': 654.32},
                {'country': 'Japan', 'users': 543, 'revenue': 432.10},
                {'country': 'United Kingdom', 'users': 456, 'revenue': 234.56}
            ],
            'revenue_trends': [
                {'month': '2023-01', 'revenue': 234.56},
                {'month': '2023-02', 'revenue': 456.78},
                {'month': '2023-03', 'revenue': 654.32},
                {'month': '2023-04', 'revenue': 789.10}
            ]
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logging.error(f"Error getting detailed analytics: {str(e)}")
        return jsonify({'error': 'Failed to get detailed analytics'}), 500

@marketplace_bp.route('/api/marketplace/payments/setup', methods=['POST'])
def setup_payment_method():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        payment_type = data.get('payment_type', '')  # 'bank', 'crypto', 'paypal'
        payment_details = data.get('payment_details', {})
        
        if not payment_type:
            return jsonify({'error': 'Payment type is required'}), 400
        
        # Mock payment method setup
        payment_method = {
            'id': secrets.token_hex(16),
            'type': payment_type,
            'status': 'pending_verification',
            'details': {
                'masked_account': payment_details.get('account_number', '')[-4:] if payment_details.get('account_number') else '',
                'currency': payment_details.get('currency', 'USD'),
                'country': payment_details.get('country', 'US')
            },
            'verification_required': True,
            'setup_at': datetime.utcnow().isoformat(),
            'minimum_payout': 50.00 if payment_type == 'bank' else 0.01
        }
        
        return jsonify({
            'success': True,
            'payment_method': payment_method
        })
        
    except Exception as e:
        logging.error(f"Error setting up payment method: {str(e)}")
        return jsonify({'error': 'Failed to setup payment method'}), 500

@marketplace_bp.route('/api/marketplace/pricing/optimize', methods=['POST'])
def optimize_pricing():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id', '')
        current_price = data.get('current_price', 0)
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        # Mock pricing optimization analysis
        optimization = {
            'current_price': current_price,
            'recommended_price': current_price * 1.15,
            'analysis': {
                'market_position': 'underpriced',
                'competitor_average': current_price * 1.25,
                'demand_elasticity': 0.8,
                'conversion_impact': '+12%',
                'revenue_impact': '+28%'
            },
            'price_testing': {
                'ab_test_suggested': True,
                'test_prices': [
                    current_price * 1.1,
                    current_price * 1.15,
                    current_price * 1.2
                ],
                'test_duration': '2 weeks'
            },
            'dynamic_pricing': {
                'recommended': True,
                'peak_hours': '9AM-5PM EST',
                'peak_multiplier': 1.1,
                'off_peak_multiplier': 0.9
            }
        }
        
        return jsonify({
            'success': True,
            'optimization': optimization
        })
        
    except Exception as e:
        logging.error(f"Error optimizing pricing: {str(e)}")
        return jsonify({'error': 'Failed to optimize pricing'}), 500

@marketplace_bp.route('/api/marketplace/reviews/sentiment')
def analyze_review_sentiment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        product_id = request.args.get('product_id', '')
        
        # Mock sentiment analysis
        sentiment_analysis = {
            'overall_sentiment': 0.89,
            'sentiment_distribution': {
                'positive': 78.5,
                'neutral': 15.2,
                'negative': 6.3
            },
            'key_topics': [
                {
                    'topic': 'ease of use',
                    'sentiment': 0.92,
                    'mentions': 156,
                    'sample_quotes': [
                        'Very easy to use and intuitive',
                        'User-friendly interface'
                    ]
                },
                {
                    'topic': 'performance',
                    'sentiment': 0.85,
                    'mentions': 134,
                    'sample_quotes': [
                        'Fast and reliable',
                        'Good performance overall'
                    ]
                },
                {
                    'topic': 'pricing',
                    'sentiment': 0.72,
                    'mentions': 89,
                    'sample_quotes': [
                        'Worth the price',
                        'Could be cheaper'
                    ]
                }
            ],
            'improvement_suggestions': [
                'Add more customization options',
                'Improve documentation',
                'Consider volume discounts'
            ],
            'competitor_comparison': {
                'your_product': 0.89,
                'competitor_average': 0.76,
                'advantage': '+17%'
            }
        }
        
        return jsonify({
            'success': True,
            'sentiment_analysis': sentiment_analysis
        })
        
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {str(e)}")
        return jsonify({'error': 'Failed to analyze sentiment'}), 500

@marketplace_bp.route('/api/marketplace/promotion/campaigns', methods=['GET', 'POST'])
def manage_promotion_campaigns():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            campaign_type = data.get('campaign_type', '')  # 'discount', 'featured', 'bundle'
            product_ids = data.get('product_ids', [])
            campaign_details = data.get('campaign_details', {})
            
            if not all([campaign_type, product_ids]):
                return jsonify({'error': 'Campaign type and product IDs are required'}), 400
            
            # Mock campaign creation
            campaign = {
                'id': secrets.token_hex(16),
                'type': campaign_type,
                'product_ids': product_ids,
                'name': campaign_details.get('name', f'{campaign_type.title()} Campaign'),
                'discount_percentage': campaign_details.get('discount', 0),
                'start_date': campaign_details.get('start_date', datetime.utcnow().isoformat()),
                'end_date': campaign_details.get('end_date', (datetime.utcnow() + timedelta(days=7)).isoformat()),
                'budget': campaign_details.get('budget', 100),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
            return jsonify({
                'success': True,
                'campaign': campaign
            })
            
        except Exception as e:
            logging.error(f"Error creating campaign: {str(e)}")
            return jsonify({'error': 'Failed to create campaign'}), 500
    
    # GET request - return active campaigns
    try:
        campaigns = [
            {
                'id': 'camp-1',
                'type': 'discount',
                'name': 'Summer Sale 2024',
                'discount_percentage': 20,
                'products_count': 3,
                'clicks': 1456,
                'conversions': 89,
                'revenue': 567.89,
                'roi': 2.3,
                'status': 'active',
                'end_date': (datetime.utcnow() + timedelta(days=5)).isoformat()
            }
        ]
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        logging.error(f"Error getting campaigns: {str(e)}")
        return jsonify({'error': 'Failed to get campaigns'}), 500
