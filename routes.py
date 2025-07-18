from flask import render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
import json
import logging
from datetime import datetime

from app import app, db, socketio
from models import *
from services.openai_service import OpenAIService
from services.anthropic_service import AnthropicService
from services.file_service import FileService
from services.vector_service import VectorService
from services.quantum_service import QuantumService
from services.federated_service import FederatedService
from services.neuromorphic_service import NeuromorphicService
from services.safety_service import SafetyService
from services.blockchain_service import BlockchainService
from utils.helpers import get_current_user, login_required, allowed_file

# Initialize services
openai_service = OpenAIService()
anthropic_service = AnthropicService()
file_service = FileService()
vector_service = VectorService()
quantum_service = QuantumService()
federated_service = FederatedService()
neuromorphic_service = NeuromorphicService()
safety_service = SafetyService()
blockchain_service = BlockchainService()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Welcome to Autogent Studio!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Account created successfully! Welcome to Autogent Studio!', 'success')
        return redirect(url_for('chat'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # TODO: Implement password reset logic
        flash('Password reset instructions sent to your email', 'info')
        return redirect(url_for('signin'))
    
    return render_template('forgot_password.html')

@app.route('/me')
@login_required
def profile():
    user = get_current_user()
    return render_template('profile.html', user=user)

# Chat routes
@app.route('/chat')
@login_required
def chat():
    user = get_current_user()
    # Get user's recent chat sessions
    recent_sessions = ChatSession.query.filter_by(user_id=user.id).order_by(ChatSession.updated_at.desc()).limit(10).all()
    return render_template('chat.html', user=user, recent_sessions=recent_sessions)

@app.route('/chat/<int:session_id>')
@login_required
def chat_session(session_id):
    user = get_current_user()
    session_obj = ChatSession.query.filter_by(id=session_id, user_id=user.id).first_or_404()
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
    return render_template('chat_session.html', session=session_obj, messages=messages)

@app.route('/chat/settings')
@login_required
def chat_settings():
    user = get_current_user()
    return render_template('chat_settings.html', user=user)

# Files routes
@app.route('/files')
@login_required
def files():
    user = get_current_user()
    user_files = File.query.filter_by(user_id=user.id).order_by(File.created_at.desc()).all()
    return render_template('files.html', files=user_files)

@app.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    user = get_current_user()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Save file
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Create file record
            file_record = File(
                user_id=user.id,
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type=file.content_type or 'application/octet-stream',
                mime_type=file.content_type
            )
            db.session.add(file_record)
            db.session.commit()
            
            # Process file for RAG
            file_service.process_file_for_rag(file_record.id)
            
            return jsonify({'message': 'File uploaded successfully', 'file_id': file_record.id})
        except Exception as e:
            logging.error(f"File upload error: {str(e)}")
            return jsonify({'error': 'Upload failed'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/files/knowledge-base')
@login_required
def knowledge_base():
    user = get_current_user()
    knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(KnowledgeBase.created_at.desc()).all()
    return render_template('knowledge_base.html', knowledge_bases=knowledge_bases)

@app.route('/files/knowledge-base/create', methods=['POST'])
@login_required
def create_knowledge_base():
    user = get_current_user()
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        return jsonify({'error': 'Knowledge base name is required'}), 400
    
    kb = KnowledgeBase(
        user_id=user.id,
        name=name,
        description=description
    )
    db.session.add(kb)
    db.session.commit()
    
    return jsonify({'message': 'Knowledge base created successfully', 'kb_id': kb.id})

# AI Painting routes
@app.route('/image')
@login_required
def ai_painting():
    user = get_current_user()
    return render_template('image.html', user=user)

@app.route('/image/generate', methods=['POST'])
@login_required
def generate_image():
    user = get_current_user()
    
    prompt = request.form.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # Use OpenAI DALL-E for image generation
        result = openai_service.generate_image(prompt)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Image generation error: {str(e)}")
        return jsonify({'error': 'Image generation failed'}), 500

# Discover routes
@app.route('/discover')
@login_required
def discover():
    featured_assistants = Assistant.query.order_by(Assistant.downloads.desc()).limit(12).all()
    featured_plugins = Plugin.query.order_by(Plugin.downloads.desc()).limit(12).all()
    return render_template('discover.html', assistants=featured_assistants, plugins=featured_plugins)

@app.route('/discover/assistant')
@login_required
def discover_assistant():
    assistants = Assistant.query.order_by(Assistant.downloads.desc()).all()
    return render_template('discover_assistant.html', assistants=assistants)

@app.route('/discover/assistant/<int:assistant_id>')
@login_required
def discover_assistant_detail(assistant_id):
    assistant = Assistant.query.get_or_404(assistant_id)
    return render_template('discover_assistant_detail.html', assistant=assistant)

@app.route('/discover/mcp')
@login_required
def discover_mcp():
    plugins = Plugin.query.order_by(Plugin.downloads.desc()).all()
    return render_template('discover_mcp.html', plugins=plugins)

@app.route('/discover/mcp/<int:plugin_id>')
@login_required
def discover_mcp_detail(plugin_id):
    plugin = Plugin.query.get_or_404(plugin_id)
    return render_template('discover_mcp_detail.html', plugin=plugin)

@app.route('/discover/model')
@login_required
def discover_model():
    providers = ModelProvider.query.filter_by(is_active=True).all()
    return render_template('discover_model.html', providers=providers)

@app.route('/discover/provider')
@login_required
def discover_provider():
    providers = ModelProvider.query.filter_by(is_active=True).all()
    return render_template('discover_provider.html', providers=providers)

# Orchestration routes
@app.route('/orchestration')
@login_required
def orchestration():
    user = get_current_user()
    workflows = WorkflowExecution.query.filter_by(user_id=user.id).order_by(WorkflowExecution.started_at.desc()).all()
    return render_template('orchestration.html', workflows=workflows)

@app.route('/orchestration/execute', methods=['POST'])
@login_required
def execute_workflow():
    user = get_current_user()
    
    workflow_data = request.json
    if not workflow_data:
        return jsonify({'error': 'Workflow data is required'}), 400
    
    # Create workflow execution record
    execution = WorkflowExecution(
        user_id=user.id,
        workflow_name=workflow_data.get('name', 'Untitled Workflow'),
        status='running'
    )
    execution.set_workflow_data(workflow_data)
    db.session.add(execution)
    db.session.commit()
    
    # TODO: Implement actual workflow execution
    
    return jsonify({'message': 'Workflow execution started', 'execution_id': execution.id})

# Quantum Computing routes
@app.route('/quantum')
@login_required
def quantum():
    user = get_current_user()
    experiments = QuantumExperiment.query.filter_by(user_id=user.id).order_by(QuantumExperiment.created_at.desc()).all()
    return render_template('quantum.html', experiments=experiments)

@app.route('/quantum/algorithms')
@login_required
def quantum_algorithms():
    return render_template('quantum_algorithms.html')

@app.route('/quantum/circuits')
@login_required
def quantum_circuits():
    return render_template('quantum_circuits.html')

@app.route('/quantum/training')
@login_required
def quantum_training():
    return render_template('quantum_training.html')

@app.route('/quantum/analysis')
@login_required
def quantum_analysis():
    return render_template('quantum_analysis.html')

# Federated Learning routes
@app.route('/federated')
@login_required
def federated():
    user = get_current_user()
    nodes = FederatedLearningNode.query.filter_by(user_id=user.id).all()
    return render_template('federated.html', nodes=nodes)

@app.route('/federated/training')
@login_required
def federated_training():
    return render_template('federated_training.html')

@app.route('/federated/nodes')
@login_required
def federated_nodes():
    user = get_current_user()
    nodes = FederatedLearningNode.query.filter_by(user_id=user.id).all()
    return render_template('federated_nodes.html', nodes=nodes)

@app.route('/federated/aggregation')
@login_required
def federated_aggregation():
    return render_template('federated_aggregation.html')

@app.route('/federated/analytics')
@login_required
def federated_analytics():
    return render_template('federated_analytics.html')

# Neuromorphic Computing routes
@app.route('/neuromorphic')
@login_required
def neuromorphic():
    user = get_current_user()
    devices = NeuromorphicDevice.query.filter_by(user_id=user.id).all()
    return render_template('neuromorphic.html', devices=devices)

@app.route('/neuromorphic/snn')
@login_required
def neuromorphic_snn():
    return render_template('neuromorphic_snn.html')

@app.route('/neuromorphic/edge')
@login_required
def neuromorphic_edge():
    return render_template('neuromorphic_edge.html')

@app.route('/neuromorphic/hardware')
@login_required
def neuromorphic_hardware():
    return render_template('neuromorphic_hardware.html')

@app.route('/neuromorphic/learning')
@login_required
def neuromorphic_learning():
    return render_template('neuromorphic_learning.html')

@app.route('/neuromorphic/optimization')
@login_required
def neuromorphic_optimization():
    return render_template('neuromorphic_optimization.html')

@app.route('/neuromorphic/realtime')
@login_required
def neuromorphic_realtime():
    return render_template('neuromorphic_realtime.html')

# AI Safety routes
@app.route('/safety')
@login_required
def safety():
    user = get_current_user()
    assessments = SafetyAssessment.query.filter_by(user_id=user.id).order_by(SafetyAssessment.created_at.desc()).all()
    return render_template('safety.html', assessments=assessments)

@app.route('/safety/alignment')
@login_required
def safety_alignment():
    return render_template('safety_alignment.html')

@app.route('/safety/robustness')
@login_required
def safety_robustness():
    return render_template('safety_robustness.html')

@app.route('/safety/interpretability')
@login_required
def safety_interpretability():
    return render_template('safety_interpretability.html')

@app.route('/safety/bias')
@login_required
def safety_bias():
    return render_template('safety_bias.html')

@app.route('/safety/adversarial')
@login_required
def safety_adversarial():
    return render_template('safety_adversarial.html')

@app.route('/safety/constitutional')
@login_required
def safety_constitutional():
    return render_template('safety_constitutional.html')

@app.route('/safety/values')
@login_required
def safety_values():
    return render_template('safety_values.html')

@app.route('/safety/automation')
@login_required
def safety_automation():
    return render_template('safety_automation.html')

# Self-Improving AI routes
@app.route('/self-improving')
@login_required
def self_improving():
    user = get_current_user()
    projects = ResearchProject.query.filter_by(user_id=user.id).order_by(ResearchProject.created_at.desc()).all()
    return render_template('self_improving.html', projects=projects)

@app.route('/self-improving/research')
@login_required
def self_improving_research():
    return render_template('self_improving_research.html')

@app.route('/self-improving/capabilities')
@login_required
def self_improving_capabilities():
    return render_template('self_improving_capabilities.html')

@app.route('/self-improving/knowledge')
@login_required
def self_improving_knowledge():
    return render_template('self_improving_knowledge.html')

@app.route('/self-improving/optimization')
@login_required
def self_improving_optimization():
    return render_template('self_improving_optimization.html')

@app.route('/self-improving/meta-learning')
@login_required
def self_improving_meta_learning():
    return render_template('self_improving_meta_learning.html')

@app.route('/self-improving/hypotheses')
@login_required
def self_improving_hypotheses():
    return render_template('self_improving_hypotheses.html')

@app.route('/self-improving/experiments')
@login_required
def self_improving_experiments():
    return render_template('self_improving_experiments.html')

@app.route('/self-improving/discovery')
@login_required
def self_improving_discovery():
    return render_template('self_improving_discovery.html')

# Settings routes
@app.route('/settings')
@login_required
def settings():
    user = get_current_user()
    return render_template('settings.html', user=user)

@app.route('/settings/model')
@login_required
def settings_model():
    return render_template('settings_model.html')

@app.route('/settings/image')
@login_required
def settings_image():
    return render_template('settings_image.html')

@app.route('/settings/database')
@login_required
def settings_database():
    return render_template('settings_database.html')

@app.route('/settings/rag')
@login_required
def settings_rag():
    return render_template('settings_rag.html')

@app.route('/settings/fine-tuning')
@login_required
def settings_fine_tuning():
    return render_template('settings_fine_tuning.html')

@app.route('/settings/security')
@login_required
def settings_security():
    return render_template('settings_security.html')

@app.route('/settings/blockchain')
@login_required
def settings_blockchain():
    return render_template('settings_blockchain.html')

@app.route('/settings/orchestration')
@login_required
def settings_orchestration():
    return render_template('settings_orchestration.html')

@app.route('/settings/plandex')
@login_required
def settings_plandex():
    return render_template('settings_plandex.html')

@app.route('/settings/quantum')
@login_required
def settings_quantum():
    return render_template('settings_quantum.html')

@app.route('/settings/federated')
@login_required
def settings_federated():
    return render_template('settings_federated.html')

@app.route('/settings/deployment')
@login_required
def settings_deployment():
    return render_template('settings_deployment.html')

@app.route('/settings/neuromorphic')
@login_required
def settings_neuromorphic():
    return render_template('settings_neuromorphic.html')

@app.route('/settings/safety')
@login_required
def settings_safety():
    return render_template('settings_safety.html')

@app.route('/settings/self-improving')
@login_required
def settings_self_improving():
    return render_template('settings_self_improving.html')

@app.route('/settings/preferences')
@login_required
def settings_preferences():
    return render_template('settings_preferences.html')

@app.route('/settings/voice')
@login_required
def settings_voice():
    return render_template('settings_voice.html')

@app.route('/settings/about')
@login_required
def settings_about():
    return render_template('settings_about.html')

@app.route('/settings/advanced')
@login_required
def settings_advanced():
    return render_template('settings_advanced.html')

# Analytics routes
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/analytics/usage')
@login_required
def analytics_usage():
    return render_template('analytics_usage.html')

@app.route('/analytics/behavior')
@login_required
def analytics_behavior():
    return render_template('analytics_behavior.html')

@app.route('/analytics/performance')
@login_required
def analytics_performance():
    return render_template('analytics_performance.html')

@app.route('/analytics/costs')
@login_required
def analytics_costs():
    return render_template('analytics_costs.html')

@app.route('/analytics/reports')
@login_required
def analytics_reports():
    return render_template('analytics_reports.html')

@app.route('/analytics/security')
@login_required
def analytics_security():
    return render_template('analytics_security.html')

@app.route('/analytics/blockchain')
@login_required
def analytics_blockchain():
    return render_template('analytics_blockchain.html')

@app.route('/analytics/quantum')
@login_required
def analytics_quantum():
    return render_template('analytics_quantum.html')

@app.route('/analytics/federated')
@login_required
def analytics_federated():
    return render_template('analytics_federated.html')

@app.route('/analytics/models')
@login_required
def analytics_models():
    return render_template('analytics_models.html')

@app.route('/analytics/neuromorphic')
@login_required
def analytics_neuromorphic():
    return render_template('analytics_neuromorphic.html')

@app.route('/analytics/safety')
@login_required
def analytics_safety():
    return render_template('analytics_safety.html')

@app.route('/analytics/self-improving')
@login_required
def analytics_self_improving():
    return render_template('analytics_self_improving.html')

# Additional routes for comprehensive functionality
@app.route('/workspace/<int:workspace_id>')
@login_required
def workspace(workspace_id):
    return render_template('workspace.html', workspace_id=workspace_id)

@app.route('/workspace/knowledge')
@login_required
def workspace_knowledge():
    return render_template('workspace_knowledge.html')

@app.route('/workspace/chat')
@login_required
def workspace_chat():
    return render_template('workspace_chat.html')

@app.route('/workspace/permissions')
@login_required
def workspace_permissions():
    return render_template('workspace_permissions.html')

@app.route('/workspace/analytics')
@login_required
def workspace_analytics():
    return render_template('workspace_analytics.html')

@app.route('/fine-tuning')
@login_required
def fine_tuning():
    return render_template('fine_tuning.html')

@app.route('/fine-tuning/datasets')
@login_required
def fine_tuning_datasets():
    return render_template('fine_tuning_datasets.html')

@app.route('/fine-tuning/jobs')
@login_required
def fine_tuning_jobs():
    return render_template('fine_tuning_jobs.html')

@app.route('/fine-tuning/evaluation')
@login_required
def fine_tuning_evaluation():
    return render_template('fine_tuning_evaluation.html')

@app.route('/fine-tuning/deploy')
@login_required
def fine_tuning_deploy():
    return render_template('fine_tuning_deploy.html')

@app.route('/security')
@login_required
def security():
    return render_template('security.html')

@app.route('/security/audit')
@login_required
def security_audit():
    return render_template('security_audit.html')

@app.route('/security/encryption')
@login_required
def security_encryption():
    return render_template('security_encryption.html')

@app.route('/security/access')
@login_required
def security_access():
    return render_template('security_access.html')

@app.route('/security/threats')
@login_required
def security_threats():
    return render_template('security_threats.html')

@app.route('/security/compliance')
@login_required
def security_compliance():
    return render_template('security_compliance.html')

@app.route('/blockchain')
@login_required
def blockchain():
    return render_template('blockchain.html')

@app.route('/blockchain/wallet')
@login_required
def blockchain_wallet():
    return render_template('blockchain_wallet.html')

@app.route('/blockchain/contracts')
@login_required
def blockchain_contracts():
    return render_template('blockchain_contracts.html')

@app.route('/blockchain/plugins')
@login_required
def blockchain_plugins():
    return render_template('blockchain_plugins.html')

@app.route('/blockchain/revenue')
@login_required
def blockchain_revenue():
    return render_template('blockchain_revenue.html')

@app.route('/blockchain/nft')
@login_required
def blockchain_nft():
    return render_template('blockchain_nft.html')

@app.route('/marketplace')
@login_required
def marketplace():
    return render_template('marketplace.html')

@app.route('/marketplace/revenue')
@login_required
def marketplace_revenue():
    return render_template('marketplace_revenue.html')

@app.route('/marketplace/monetize')
@login_required
def marketplace_monetize():
    return render_template('marketplace_monetize.html')

@app.route('/marketplace/analytics')
@login_required
def marketplace_analytics():
    return render_template('marketplace_analytics.html')

@app.route('/marketplace/payments')
@login_required
def marketplace_payments():
    return render_template('marketplace_payments.html')

@app.route('/marketplace/create')
@login_required
def marketplace_create():
    return render_template('marketplace_create.html')

@app.route('/models/registry')
@login_required
def models_registry():
    return render_template('models_registry.html')

@app.route('/models/deploy')
@login_required
def models_deploy():
    return render_template('models_deploy.html')

@app.route('/models/testing')
@login_required
def models_testing():
    return render_template('models_testing.html')

@app.route('/models/monitoring')
@login_required
def models_monitoring():
    return render_template('models_monitoring.html')

@app.route('/models/rollback')
@login_required
def models_rollback():
    return render_template('models_rollback.html')

@app.route('/models/cicd')
@login_required
def models_cicd():
    return render_template('models_cicd.html')

@app.route('/models/governance')
@login_required
def models_governance():
    return render_template('models_governance.html')

@app.route('/plugins/ide')
@login_required
def plugins_ide():
    return render_template('plugins_ide.html')

@app.route('/plugins/submit')
@login_required
def plugins_submit():
    return render_template('plugins_submit.html')

@app.route('/plugins/test')
@login_required
def plugins_test():
    return render_template('plugins_test.html')

@app.route('/plugins/docs')
@login_required
def plugins_docs():
    return render_template('plugins_docs.html')

@app.route('/plugins/versions')
@login_required
def plugins_versions():
    return render_template('plugins_versions.html')

# API routes for chat functionality
@app.route('/api/chat/send', methods=['POST'])
@login_required
def api_chat_send():
    user = get_current_user()
    data = request.json
    
    session_id = data.get('session_id')
    message = data.get('message')
    model_provider = data.get('model_provider', 'openai')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get or create chat session
    if session_id:
        chat_session = ChatSession.query.filter_by(id=session_id, user_id=user.id).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
    else:
        chat_session = ChatSession(
            user_id=user.id,
            title=message[:50] + '...' if len(message) > 50 else message,
            model_provider=model_provider,
            model_name=data.get('model_name', 'gpt-4o')
        )
        db.session.add(chat_session)
        db.session.commit()
    
    # Add user message
    user_message = ChatMessage(
        session_id=chat_session.id,
        role='user',
        content=message
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Get AI response
    try:
        if model_provider == 'openai':
            response = openai_service.chat_completion(message, chat_session.model_name)
        elif model_provider == 'anthropic':
            response = anthropic_service.chat_completion(message, chat_session.model_name)
        else:
            response = {'content': 'Model provider not supported'}
        
        # Add AI response
        ai_message = ChatMessage(
            session_id=chat_session.id,
            role='assistant',
            content=response['content']
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            'session_id': chat_session.id,
            'response': response['content'],
            'message_id': ai_message.id
        })
    
    except Exception as e:
        logging.error(f"Chat API error: {str(e)}")
        return jsonify({'error': 'Failed to get AI response'}), 500

# WebSocket events for real-time chat
@socketio.on('join_chat')
def handle_join_chat(data):
    session_id = data['session_id']
    join_room(f"chat_{session_id}")
    emit('joined_chat', {'session_id': session_id})

@socketio.on('leave_chat')
def handle_leave_chat(data):
    session_id = data['session_id']
    leave_room(f"chat_{session_id}")
    emit('left_chat', {'session_id': session_id})

@socketio.on('send_message')
def handle_send_message(data):
    session_id = data['session_id']
    message = data['message']
    
    # Emit message to all users in the chat room
    emit('new_message', {
        'session_id': session_id,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f"chat_{session_id}")
