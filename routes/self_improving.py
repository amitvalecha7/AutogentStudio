from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User, ResearchProject
from services.research_service import ResearchService
import logging

self_improving_bp = Blueprint('self_improving', __name__)

@self_improving_bp.route('/self-improving')
def self_improving_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    projects = ResearchProject.query.filter_by(user_id=user.id).order_by(ResearchProject.created_at.desc()).all()
    
    return render_template('self_improving/self_improving.html', user=user, projects=projects)

@self_improving_bp.route('/self-improving/research')
def automated_research():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/research.html', user=user)

@self_improving_bp.route('/self-improving/capabilities')
def capability_enhancement():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/capabilities.html', user=user)

@self_improving_bp.route('/self-improving/knowledge')
def knowledge_acquisition():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/knowledge.html', user=user)

@self_improving_bp.route('/self-improving/optimization')
def performance_optimization():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/optimization.html', user=user)

@self_improving_bp.route('/self-improving/meta-learning')
def meta_learning():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/meta_learning.html', user=user)

@self_improving_bp.route('/self-improving/hypotheses')
def hypothesis_generation():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/hypotheses.html', user=user)

@self_improving_bp.route('/self-improving/experiments')
def experimental_design():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/experiments.html', user=user)

@self_improving_bp.route('/self-improving/discovery')
def scientific_discovery():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('self_improving/discovery.html', user=user)

@self_improving_bp.route('/api/self-improving/projects', methods=['GET', 'POST'])
def api_projects():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            research_area = data.get('research_area', '').strip()
            
            if not name:
                return jsonify({'error': 'Project name is required'}), 400
            
            project = ResearchProject(
                user_id=user.id,
                name=name,
                description=data.get('description', ''),
                research_area=research_area,
                status='active'
            )
            
            db.session.add(project)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'project': project.to_dict()
            })
            
        except Exception as e:
            logging.error(f"Error creating research project: {str(e)}")
            return jsonify({'error': 'Failed to create project'}), 500
    
    # GET request
    projects = ResearchProject.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'projects': [project.to_dict() for project in projects]
    })

@self_improving_bp.route('/api/self-improving/research/automate', methods=['POST'])
def automate_research():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        research_topic = data.get('research_topic', '').strip()
        research_goals = data.get('research_goals', [])
        
        if not research_topic:
            return jsonify({'error': 'Research topic is required'}), 400
        
        research_service = ResearchService()
        automation_result = research_service.automate_research(
            research_topic=research_topic,
            research_goals=research_goals
        )
        
        return jsonify({
            'success': True,
            'automation_result': automation_result
        })
        
    except Exception as e:
        logging.error(f"Error automating research: {str(e)}")
        return jsonify({'error': f'Research automation failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/capabilities/enhance', methods=['POST'])
def enhance_capabilities():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        capability_area = data.get('capability_area', '')
        current_performance = data.get('current_performance', {})
        target_improvement = data.get('target_improvement', 0.1)
        
        if not capability_area:
            return jsonify({'error': 'Capability area is required'}), 400
        
        research_service = ResearchService()
        enhancement_result = research_service.enhance_capabilities(
            capability_area=capability_area,
            current_performance=current_performance,
            target_improvement=target_improvement
        )
        
        return jsonify({
            'success': True,
            'enhancement_result': enhancement_result
        })
        
    except Exception as e:
        logging.error(f"Error enhancing capabilities: {str(e)}")
        return jsonify({'error': f'Capability enhancement failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/knowledge/acquire', methods=['POST'])
def acquire_knowledge():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        knowledge_domain = data.get('knowledge_domain', '')
        acquisition_method = data.get('acquisition_method', 'literature_review')
        sources = data.get('sources', [])
        
        if not knowledge_domain:
            return jsonify({'error': 'Knowledge domain is required'}), 400
        
        research_service = ResearchService()
        acquisition_result = research_service.acquire_knowledge(
            knowledge_domain=knowledge_domain,
            acquisition_method=acquisition_method,
            sources=sources
        )
        
        return jsonify({
            'success': True,
            'acquisition_result': acquisition_result
        })
        
    except Exception as e:
        logging.error(f"Error acquiring knowledge: {str(e)}")
        return jsonify({'error': f'Knowledge acquisition failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/hypotheses/generate', methods=['POST'])
def generate_hypotheses():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        research_context = data.get('research_context', '')
        existing_knowledge = data.get('existing_knowledge', [])
        hypothesis_count = data.get('hypothesis_count', 5)
        
        if not research_context:
            return jsonify({'error': 'Research context is required'}), 400
        
        research_service = ResearchService()
        hypotheses = research_service.generate_hypotheses(
            research_context=research_context,
            existing_knowledge=existing_knowledge,
            hypothesis_count=hypothesis_count
        )
        
        return jsonify({
            'success': True,
            'hypotheses': hypotheses
        })
        
    except Exception as e:
        logging.error(f"Error generating hypotheses: {str(e)}")
        return jsonify({'error': f'Hypothesis generation failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/experiments/design', methods=['POST'])
def design_experiments():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        hypothesis = data.get('hypothesis', '')
        research_question = data.get('research_question', '')
        constraints = data.get('constraints', {})
        
        if not hypothesis:
            return jsonify({'error': 'Hypothesis is required'}), 400
        
        research_service = ResearchService()
        experiment_design = research_service.design_experiment(
            hypothesis=hypothesis,
            research_question=research_question,
            constraints=constraints
        )
        
        return jsonify({
            'success': True,
            'experiment_design': experiment_design
        })
        
    except Exception as e:
        logging.error(f"Error designing experiment: {str(e)}")
        return jsonify({'error': f'Experiment design failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/discovery/accelerate', methods=['POST'])
def accelerate_discovery():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        research_area = data.get('research_area', '')
        discovery_goals = data.get('discovery_goals', [])
        acceleration_factor = data.get('acceleration_factor', 2.0)
        
        if not research_area:
            return jsonify({'error': 'Research area is required'}), 400
        
        research_service = ResearchService()
        discovery_result = research_service.accelerate_discovery(
            research_area=research_area,
            discovery_goals=discovery_goals,
            acceleration_factor=acceleration_factor
        )
        
        return jsonify({
            'success': True,
            'discovery_result': discovery_result
        })
        
    except Exception as e:
        logging.error(f"Error accelerating discovery: {str(e)}")
        return jsonify({'error': f'Discovery acceleration failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/meta-learning/train', methods=['POST'])
def train_meta_learner():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        task_distribution = data.get('task_distribution', [])
        meta_algorithm = data.get('meta_algorithm', 'maml')
        adaptation_steps = data.get('adaptation_steps', 5)
        
        if not task_distribution:
            return jsonify({'error': 'Task distribution is required'}), 400
        
        research_service = ResearchService()
        meta_learning_result = research_service.train_meta_learner(
            task_distribution=task_distribution,
            meta_algorithm=meta_algorithm,
            adaptation_steps=adaptation_steps
        )
        
        return jsonify({
            'success': True,
            'meta_learning_result': meta_learning_result
        })
        
    except Exception as e:
        logging.error(f"Error training meta-learner: {str(e)}")
        return jsonify({'error': f'Meta-learning failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/optimization/performance', methods=['POST'])
def optimize_performance():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        performance_metrics = data.get('performance_metrics', {})
        optimization_target = data.get('optimization_target', 'accuracy')
        constraints = data.get('constraints', {})
        
        if not performance_metrics:
            return jsonify({'error': 'Performance metrics are required'}), 400
        
        research_service = ResearchService()
        optimization_result = research_service.optimize_performance(
            performance_metrics=performance_metrics,
            optimization_target=optimization_target,
            constraints=constraints
        )
        
        return jsonify({
            'success': True,
            'optimization_result': optimization_result
        })
        
    except Exception as e:
        logging.error(f"Error optimizing performance: {str(e)}")
        return jsonify({'error': f'Performance optimization failed: {str(e)}'}), 500

@self_improving_bp.route('/api/self-improving/analytics')
def get_self_improving_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        research_service = ResearchService()
        analytics = research_service.get_self_improving_analytics(user.id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logging.error(f"Error getting self-improving analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500
