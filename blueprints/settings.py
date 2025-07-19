from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from models import AIModel, User, db
from utils.encryption import encrypt_api_keys, decrypt_api_keys
import json

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def index():
    return render_template('settings/index.html', user=current_user)

@settings_bp.route('/model', methods=['GET', 'POST'])
@login_required
def model_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        # Update API keys
        api_keys = {}
        if 'openai_api_key' in data:
            api_keys['openai'] = data['openai_api_key']
        if 'anthropic_api_key' in data:
            api_keys['anthropic'] = data['anthropic_api_key']
        if 'google_api_key' in data:
            api_keys['google'] = data['google_api_key']
        if 'cohere_api_key' in data:
            api_keys['cohere'] = data['cohere_api_key']
        
        # Encrypt and store API keys
        if api_keys:
            encrypted_keys = encrypt_api_keys(api_keys)
            current_user.api_keys = encrypted_keys
        
        # Update model preferences
        preferences = current_user.preferences or {}
        preferences.update({
            'default_model_provider': data.get('default_provider', 'openai'),
            'default_chat_model': data.get('default_chat_model', 'gpt-4o'),
            'default_image_model': data.get('default_image_model', 'dall-e-3'),
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 2048),
            'top_p': data.get('top_p', 1.0)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    
    # Get available models
    available_models = AIModel.query.filter_by(is_active=True).all()
    models_by_provider = {}
    for model in available_models:
        if model.provider not in models_by_provider:
            models_by_provider[model.provider] = []
        models_by_provider[model.provider].append(model)
    
    # Decrypt API keys for display (masked)
    api_keys = {}
    if current_user.api_keys:
        try:
            decrypted_keys = decrypt_api_keys(current_user.api_keys)
            for provider, key in decrypted_keys.items():
                if key:
                    api_keys[provider] = key[:8] + '...' + key[-4:] if len(key) > 12 else '***'
        except:
            pass
    
    return render_template('settings/model.html',
                         models_by_provider=models_by_provider,
                         api_keys=api_keys,
                         preferences=current_user.preferences or {})

@settings_bp.route('/image', methods=['GET', 'POST'])
@login_required
def image_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'image_provider': data.get('image_provider', 'openai'),
            'default_image_size': data.get('default_size', '1024x1024'),
            'default_image_style': data.get('default_style', 'natural'),
            'default_image_quality': data.get('default_quality', 'standard'),
            'auto_enhance': data.get('auto_enhance', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image settings saved'})
    
    return render_template('settings/image.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/database', methods=['GET', 'POST'])
@login_required
def database_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'vector_database': data.get('vector_database', 'pgvector'),
            'embedding_model': data.get('embedding_model', 'text-embedding-3-small'),
            'chunk_size': data.get('chunk_size', 1000),
            'chunk_overlap': data.get('chunk_overlap', 200)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Database settings saved'})
    
    return render_template('settings/database.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/rag', methods=['GET', 'POST'])
@login_required
def rag_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'rag_enabled': data.get('rag_enabled', True),
            'similarity_threshold': data.get('similarity_threshold', 0.7),
            'max_chunks': data.get('max_chunks', 5),
            'reranking_enabled': data.get('reranking_enabled', False),
            'query_expansion': data.get('query_expansion', False),
            'hybrid_search': data.get('hybrid_search', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'RAG settings saved'})
    
    return render_template('settings/rag.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/fine-tuning', methods=['GET', 'POST'])
@login_required
def fine_tuning_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'fine_tuning_enabled': data.get('fine_tuning_enabled', False),
            'auto_fine_tune': data.get('auto_fine_tune', False),
            'training_data_threshold': data.get('training_data_threshold', 1000)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Fine-tuning settings saved'})
    
    return render_template('settings/fine_tuning.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'two_factor_enabled': data.get('two_factor_enabled', False),
            'session_timeout': data.get('session_timeout', 24),
            'audit_logging': data.get('audit_logging', True),
            'data_encryption': data.get('data_encryption', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Security settings saved'})
    
    return render_template('settings/security.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/blockchain', methods=['GET', 'POST'])
@login_required
def blockchain_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'blockchain_enabled': data.get('blockchain_enabled', False),
            'preferred_network': data.get('preferred_network', 'ethereum'),
            'wallet_address': data.get('wallet_address', ''),
            'revenue_sharing': data.get('revenue_sharing', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Blockchain settings saved'})
    
    return render_template('settings/blockchain.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/orchestration', methods=['GET', 'POST'])
@login_required
def orchestration_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'drawflow_enabled': data.get('drawflow_enabled', True),
            'auto_save_workflows': data.get('auto_save_workflows', True),
            'parallel_execution': data.get('parallel_execution', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Orchestration settings saved'})
    
    return render_template('settings/orchestration.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/plandex', methods=['GET', 'POST'])
@login_required
def plandex_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'plandex_enabled': data.get('plandex_enabled', True),
            'auto_code_review': data.get('auto_code_review', True),
            'project_templates': data.get('project_templates', [])
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Plandex settings saved'})
    
    return render_template('settings/plandex.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/quantum', methods=['GET', 'POST'])
@login_required
def quantum_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'quantum_provider': data.get('quantum_provider', 'ibm'),
            'quantum_api_key': data.get('quantum_api_key', ''),
            'default_backend': data.get('default_backend', 'qasm_simulator')
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Quantum settings saved'})
    
    return render_template('settings/quantum.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/federated', methods=['GET', 'POST'])
@login_required
def federated_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'federated_enabled': data.get('federated_enabled', False),
            'node_type': data.get('node_type', 'participant'),
            'privacy_level': data.get('privacy_level', 'high')
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Federated learning settings saved'})
    
    return render_template('settings/federated.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/deployment', methods=['GET', 'POST'])
@login_required
def deployment_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'auto_deployment': data.get('auto_deployment', False),
            'deployment_platform': data.get('deployment_platform', 'docker'),
            'ci_cd_enabled': data.get('ci_cd_enabled', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Deployment settings saved'})
    
    return render_template('settings/deployment.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/neuromorphic', methods=['GET', 'POST'])
@login_required
def neuromorphic_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'neuromorphic_enabled': data.get('neuromorphic_enabled', False),
            'hardware_platform': data.get('hardware_platform', 'loihi'),
            'edge_deployment': data.get('edge_deployment', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Neuromorphic settings saved'})
    
    return render_template('settings/neuromorphic.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/safety', methods=['GET', 'POST'])
@login_required
def safety_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'safety_protocols_enabled': data.get('safety_protocols_enabled', True),
            'alignment_monitoring': data.get('alignment_monitoring', True),
            'bias_detection': data.get('bias_detection', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'AI safety settings saved'})
    
    return render_template('settings/safety.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/self-improving', methods=['GET', 'POST'])
@login_required
def self_improving_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'self_improvement_enabled': data.get('self_improvement_enabled', False),
            'auto_research': data.get('auto_research', False),
            'capability_enhancement': data.get('capability_enhancement', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Self-improving AI settings saved'})
    
    return render_template('settings/self_improving.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'theme': data.get('theme', 'dark'),
            'language': data.get('language', 'en'),
            'timezone': data.get('timezone', 'UTC'),
            'notifications': data.get('notifications', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Preferences saved'})
    
    return render_template('settings/preferences.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/voice', methods=['GET', 'POST'])
@login_required
def voice_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'voice_enabled': data.get('voice_enabled', False),
            'tts_voice': data.get('tts_voice', 'alloy'),
            'stt_language': data.get('stt_language', 'en'),
            'auto_play': data.get('auto_play', False)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Voice settings saved'})
    
    return render_template('settings/voice.html',
                         preferences=current_user.preferences or {})

@settings_bp.route('/about')
def about():
    return render_template('settings/about.html')

@settings_bp.route('/advanced', methods=['GET', 'POST'])
@login_required
def advanced_settings():
    if request.method == 'POST':
        data = request.get_json()
        
        preferences = current_user.preferences or {}
        preferences.update({
            'debug_mode': data.get('debug_mode', False),
            'experimental_features': data.get('experimental_features', False),
            'telemetry': data.get('telemetry', True)
        })
        current_user.preferences = preferences
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Advanced settings saved'})
    
    return render_template('settings/advanced.html',
                         preferences=current_user.preferences or {})
