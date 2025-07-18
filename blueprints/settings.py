from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app import db
from models import User, APIKey
from blueprints.auth import login_required, get_current_user
from utils.encryption import encrypt_api_key, decrypt_api_key
import logging
import json

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def settings_index():
    user = get_current_user()
    api_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).all()
    
    # Group API keys by provider
    provider_keys = {}
    for key in api_keys:
        provider_keys[key.provider] = key
    
    return render_template('settings/settings.html', 
                         user=user, 
                         provider_keys=provider_keys)

@settings_bp.route('/model')
@login_required
def model_settings():
    user = get_current_user()
    api_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).all()
    
    provider_keys = {}
    for key in api_keys:
        provider_keys[key.provider] = {
            'id': key.id,
            'provider': key.provider,
            'created_at': key.created_at.isoformat()
        }
    
    return render_template('settings/model.html', 
                         user=user, 
                         provider_keys=provider_keys)

@settings_bp.route('/api-key', methods=['POST'])
@login_required
def save_api_key():
    user = get_current_user()
    data = request.get_json()
    
    provider = data.get('provider')
    api_key = data.get('api_key')
    
    if not provider or not api_key:
        return jsonify({'error': 'Provider and API key are required'}), 400
    
    # Validate provider
    valid_providers = ['openai', 'anthropic', 'google', 'groq', 'deepseek', 'qwen']
    if provider not in valid_providers:
        return jsonify({'error': 'Invalid provider'}), 400
    
    try:
        # Check if API key already exists for this provider
        existing_key = APIKey.query.filter_by(
            user_id=user.id, 
            provider=provider, 
            is_active=True
        ).first()
        
        encrypted_key = encrypt_api_key(api_key)
        
        if existing_key:
            # Update existing key
            existing_key.encrypted_key = encrypted_key
        else:
            # Create new key
            new_key = APIKey(
                user_id=user.id,
                provider=provider,
                encrypted_key=encrypted_key
            )
            db.session.add(new_key)
        
        db.session.commit()
        
        logging.info(f"API key saved for provider {provider} by user {user.id}")
        return jsonify({'success': True, 'message': f'{provider.title()} API key saved successfully'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving API key: {str(e)}")
        return jsonify({'error': 'Failed to save API key'}), 500

@settings_bp.route('/api-key/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    user = get_current_user()
    api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
    
    if api_key:
        try:
            api_key.is_active = False
            db.session.commit()
            
            logging.info(f"API key {key_id} deleted by user {user.id}")
            return jsonify({'success': True, 'message': 'API key deleted successfully'})
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting API key: {str(e)}")
            return jsonify({'error': 'Failed to delete API key'}), 500
    
    return jsonify({'error': 'API key not found'}), 404

@settings_bp.route('/security')
@login_required
def security_settings():
    user = get_current_user()
    return render_template('settings/security.html', user=user)

@settings_bp.route('/quantum')
@login_required
def quantum_settings():
    user = get_current_user()
    return render_template('settings/quantum.html', user=user)

@settings_bp.route('/federated')
@login_required
def federated_settings():
    user = get_current_user()
    return render_template('settings/federated.html', user=user)

@settings_bp.route('/neuromorphic')
@login_required
def neuromorphic_settings():
    user = get_current_user()
    return render_template('settings/neuromorphic.html', user=user)

@settings_bp.route('/safety')
@login_required
def safety_settings():
    user = get_current_user()
    return render_template('settings/safety.html', user=user)

@settings_bp.route('/self-improving')
@login_required
def self_improving_settings():
    user = get_current_user()
    return render_template('settings/self_improving.html', user=user)

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_settings():
    user = get_current_user()
    
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'profile_image_url' in data:
                user.profile_image_url = data['profile_image_url']
            
            db.session.commit()
            
            logging.info(f"Profile updated for user {user.id}")
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating profile: {str(e)}")
            return jsonify({'error': 'Failed to update profile'}), 500
    
    return render_template('settings/profile.html', user=user)

@settings_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    user = get_current_user()
    
    if request.method == 'POST':
        data = request.get_json()
        
        # In a real application, you'd store user preferences
        # For now, we'll just return success
        return jsonify({'success': True, 'message': 'Preferences saved successfully'})
    
    return render_template('settings/preferences.html', user=user)

@settings_bp.route('/about')
def about():
    return render_template('settings/about.html')

@settings_bp.route('/test-api-key', methods=['POST'])
@login_required
def test_api_key():
    user = get_current_user()
    data = request.get_json()
    
    provider = data.get('provider')
    
    if not provider:
        return jsonify({'error': 'Provider is required'}), 400
    
    api_key_record = APIKey.query.filter_by(
        user_id=user.id,
        provider=provider,
        is_active=True
    ).first()
    
    if not api_key_record:
        return jsonify({'error': f'No {provider} API key found'}), 404
    
    try:
        api_key = decrypt_api_key(api_key_record.encrypted_key)
        
        # Test the API key with a simple request
        if provider == 'openai':
            from services.openai_service import OpenAIService
            service = OpenAIService(api_key)
            test_result = service.test_connection()
        elif provider == 'anthropic':
            from services.anthropic_service import AnthropicService
            service = AnthropicService(api_key)
            test_result = service.test_connection()
        else:
            return jsonify({'error': f'Testing not implemented for {provider}'}), 400
        
        if test_result:
            return jsonify({'success': True, 'message': f'{provider.title()} API key is valid'})
        else:
            return jsonify({'error': f'{provider.title()} API key test failed'}), 400
    
    except Exception as e:
        logging.error(f"Error testing API key: {str(e)}")
        return jsonify({'error': f'Failed to test {provider} API key'}), 500
