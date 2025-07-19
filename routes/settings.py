from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, APIKey
from utils.encryption import encrypt_api_key, decrypt_api_key
import logging

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/settings.html', user=user)

@settings_bp.route('/settings/model')
def model_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    api_keys = APIKey.query.filter_by(user_id=user.id).all()
    
    return render_template('settings/model.html', user=user, api_keys=api_keys)

@settings_bp.route('/settings/security')
def security_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/security.html', user=user)

@settings_bp.route('/settings/image')
def image_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/image.html', user=user)

@settings_bp.route('/settings/database')
def database_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/database.html', user=user)

@settings_bp.route('/settings/rag')
def rag_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/rag.html', user=user)

@settings_bp.route('/settings/fine-tuning')
def fine_tuning_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/fine_tuning.html', user=user)

@settings_bp.route('/settings/orchestration')
def orchestration_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/orchestration.html', user=user)

@settings_bp.route('/settings/quantum')
def quantum_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/quantum.html', user=user)

@settings_bp.route('/settings/federated')
def federated_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/federated.html', user=user)

@settings_bp.route('/settings/neuromorphic')
def neuromorphic_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/neuromorphic.html', user=user)

@settings_bp.route('/settings/safety')
def safety_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/safety.html', user=user)

@settings_bp.route('/settings/self-improving')
def self_improving_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/self_improving.html', user=user)

@settings_bp.route('/settings/deployment')
def deployment_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/deployment.html', user=user)

@settings_bp.route('/settings/blockchain')
def blockchain_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/blockchain.html', user=user)

@settings_bp.route('/settings/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('settings/about.html', user=user)

@settings_bp.route('/api/settings/api-keys', methods=['GET', 'POST'])
def api_keys():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            provider = data.get('provider', '').strip()
            key_name = data.get('key_name', '').strip()
            api_key = data.get('api_key', '').strip()
            
            if not all([provider, key_name, api_key]):
                return jsonify({'error': 'All fields are required'}), 400
            
            # Encrypt the API key
            encrypted_key = encrypt_api_key(api_key)
            
            # Check if key already exists
            existing_key = APIKey.query.filter_by(
                user_id=user.id,
                provider=provider,
                key_name=key_name
            ).first()
            
            if existing_key:
                existing_key.encrypted_key = encrypted_key
                existing_key.is_active = True
            else:
                new_key = APIKey(
                    user_id=user.id,
                    provider=provider,
                    key_name=key_name,
                    encrypted_key=encrypted_key
                )
                db.session.add(new_key)
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'API key saved successfully'})
            
        except Exception as e:
            logging.error(f"Error saving API key: {str(e)}")
            return jsonify({'error': 'Failed to save API key'}), 500
    
    # GET request
    try:
        api_keys = APIKey.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'api_keys': [key.to_dict() for key in api_keys]
        })
    except Exception as e:
        logging.error(f"Error fetching API keys: {str(e)}")
        return jsonify({'error': 'Failed to fetch API keys'}), 500

@settings_bp.route('/api/settings/api-keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'API key deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting API key: {str(e)}")
        return jsonify({'error': 'Failed to delete API key'}), 500

@settings_bp.route('/api/settings/profile', methods=['GET', 'POST'])
def profile_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update user profile
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.email = data.get('email', user.email)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error updating profile: {str(e)}")
            return jsonify({'error': 'Failed to update profile'}), 500
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

@settings_bp.route('/api/settings/password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        user = User.query.get(session['user_id'])
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        logging.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500
