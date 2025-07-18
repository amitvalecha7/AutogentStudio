from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User, ResearchProject, Hypothesis, Experiment
from blueprints.auth import login_required, get_current_user
from services.research_service import ResearchService
import logging
import json
from datetime import datetime

self_improving_bp = Blueprint('self_improving', __name__)

@self_improving_bp.route('/')
@login_required
def self_improving_index():
    user = get_current_user()
    projects = ResearchProject.query.filter_by(user_id=user.id).order_by(ResearchProject.created_at.desc()).limit(10).all()
    hypotheses = Hypothesis.query.join(ResearchProject).filter(ResearchProject.user_id == user.id).order_by(Hypothesis.created_at.desc()).limit(10).all()
    experiments = Experiment.query.join(Hypothesis).join(ResearchProject).filter(ResearchProject.user_id == user.id).order_by(Experiment.created_at.desc()).limit(10).all()
    
    # Calculate summary statistics
    active_projects = ResearchProject.query.filter_by(user_id=user.id, current_status='active').count()
    validated_hypotheses = Hypothesis.query.join(ResearchProject).filter(ResearchProject.user_id == user.id, Hypothesis.is_validated == True).count()
    running_experiments = Experiment.query.join(Hypothesis).join(ResearchProject).filter(ResearchProject.user_id == user.id, Experiment.execution_status == 'running').count()
    
    return render_template('self_improving/dashboard.html', 
                         user=user, 
                         projects=projects, 
                         hypotheses=hypotheses,
                         experiments=experiments,
                         active_projects=active_projects,
                         validated_hypotheses=validated_hypotheses,
                         running_experiments=running_experiments)

@self_improving_bp.route('/research')
@login_required
def automated_research():
    user = get_current_user()
    projects = ResearchProject.query.filter_by(user_id=user.id).order_by(ResearchProject.created_at.desc()).all()
    
    return render_template('self_improving/research.html', 
                         user=user, 
                         projects=projects)

@self_improving_bp.route('/capabilities')
@login_required
def capability_enhancement():
    user = get_current_user()
    
    # Get capability enhancement metrics
    capability_metrics = {
        'reasoning_ability': 85,
        'knowledge_acquisition': 78,
        'problem_solving': 82,
        'creativity': 75,
        'learning_efficiency': 88,
        'meta_learning': 70
    }
    
    return render_template('self_improving/capabilities.html', 
                         user=user, 
                         capability_metrics=capability_metrics)

@self_improving_bp.route('/knowledge')
@login_required
def knowledge_acquisition():
    user = get_current_user()
    projects = ResearchProject.query.filter_by(user_id=user.id, research_domain='knowledge_acquisition').all()
    
    return render_template('self_improving/knowledge.html', 
                         user=user, 
                         projects=projects)

@self_improving_bp.route('/optimization')
@login_required
def performance_optimization():
    user = get_current_user()
    optimization_projects = ResearchProject.query.filter_by(user_id=user.id, research_domain='optimization').all()
    
    return render_template('self_improving/optimization.html', 
                         user=user, 
                         projects=optimization_projects)

@self_improving_bp.route('/meta-learning')
@login_required
def meta_learning():
    user = get_current_user()
    meta_learning_projects = ResearchProject.query.filter_by(user_id=user.id, research_domain='meta_learning').all()
    
    return render_template('self_improving/meta_learning.html', 
                         user=user, 
                         projects=meta_learning_projects)

@self_improving_bp.route('/hypotheses')
@login_required
def hypothesis_generation():
    user = get_current_user()
    hypotheses = Hypothesis.query.join(ResearchProject).filter(ResearchProject.user_id == user.id).order_by(Hypothesis.created_at.desc()).all()
    
    return render_template('self_improving/hypotheses.html', 
                         user=user, 
                         hypotheses=hypotheses)

@self_improving_bp.route('/experiments')
@login_required
def experiment_design():
    user = get_current_user()
    experiments = Experiment.query.join(Hypothesis).join(ResearchProject).filter(ResearchProject.user_id == user.id).order_by(Experiment.created_at.desc()).all()
    
    return render_template('self_improving/experiments.html', 
                         user=user, 
                         experiments=experiments)

@self_improving_bp.route('/discovery')
@login_required
def scientific_discovery():
    user = get_current_user()
    discovery_projects = ResearchProject.query.filter_by(user_id=user.id, research_domain='discovery').all()
    
    return render_template('self_improving/discovery.html', 
                         user=user, 
                         projects=discovery_projects)

@self_improving_bp.route('/projects/create', methods=['POST'])
@login_required
def create_project():
    user = get_current_user()
    data = request.get_json()
    
    project_name = data.get('project_name')
    research_domain = data.get('research_domain')
    objectives = data.get('objectives')
    
    if not project_name or not research_domain:
        return jsonify({'error': 'Project name and research domain are required'}), 400
    
    try:
        project = ResearchProject(
            user_id=user.id,
            project_name=project_name,
            research_domain=research_domain,
            objectives=objectives,
            current_status='active',
            progress_metrics=json.dumps({}),
            automated_discoveries=json.dumps([])
        )
        
        db.session.add(project)
        db.session.commit()
        
        logging.info(f"Research project created: {project.id}")
        return jsonify({
            'success': True,
            'project_id': project.id,
            'message': 'Research project created successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating research project: {str(e)}")
        return jsonify({'error': 'Failed to create research project'}), 500

@self_improving_bp.route('/projects/<int:project_id>/generate-hypotheses', methods=['POST'])
@login_required
def generate_hypotheses(project_id):
    user = get_current_user()
    project = ResearchProject.query.filter_by(id=project_id, user_id=user.id).first_or_404()
    
    data = request.get_json()
    context = data.get('context', '')
    num_hypotheses = data.get('num_hypotheses', 5)
    
    try:
        research_service = ResearchService()
        generated_hypotheses = research_service.generate_hypotheses(
            project_id=project.id,
            research_domain=project.research_domain,
            context=context,
            num_hypotheses=num_hypotheses
        )
        
        # Save generated hypotheses
        saved_hypotheses = []
        for hyp_data in generated_hypotheses:
            hypothesis = Hypothesis(
                project_id=project.id,
                hypothesis_text=hyp_data['text'],
                confidence_score=hyp_data['confidence'],
                generated_by='ai_system',
                test_results=json.dumps({}),
                is_validated=False
            )
            db.session.add(hypothesis)
            saved_hypotheses.append(hypothesis)
        
        db.session.commit()
        
        logging.info(f"Generated {len(generated_hypotheses)} hypotheses for project {project.id}")
        return jsonify({
            'success': True,
            'hypotheses': [{
                'id': h.id,
                'text': h.hypothesis_text,
                'confidence': h.confidence_score
            } for h in saved_hypotheses]
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating hypotheses: {str(e)}")
        return jsonify({'error': 'Failed to generate hypotheses'}), 500

@self_improving_bp.route('/hypotheses/<int:hypothesis_id>/design-experiment', methods=['POST'])
@login_required
def design_experiment(hypothesis_id):
    user = get_current_user()
    hypothesis = Hypothesis.query.join(ResearchProject).filter(
        Hypothesis.id == hypothesis_id,
        ResearchProject.user_id == user.id
    ).first_or_404()
    
    data = request.get_json()
    constraints = data.get('constraints', {})
    
    try:
        research_service = ResearchService()
        experiment_design = research_service.design_experiment(
            hypothesis_id=hypothesis.id,
            hypothesis_text=hypothesis.hypothesis_text,
            constraints=constraints
        )
        
        # Save experiment design
        experiment = Experiment(
            hypothesis_id=hypothesis.id,
            experiment_design=json.dumps(experiment_design),
            execution_status='planned',
            results=json.dumps({}),
            analysis=''
        )
        
        db.session.add(experiment)
        db.session.commit()
        
        logging.info(f"Experiment designed for hypothesis {hypothesis.id}")
        return jsonify({
            'success': True,
            'experiment_id': experiment.id,
            'experiment_design': experiment_design
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error designing experiment: {str(e)}")
        return jsonify({'error': 'Failed to design experiment'}), 500

@self_improving_bp.route('/experiments/<int:experiment_id>/execute', methods=['POST'])
@login_required
def execute_experiment(experiment_id):
    user = get_current_user()
    experiment = Experiment.query.join(Hypothesis).join(ResearchProject).filter(
        Experiment.id == experiment_id,
        ResearchProject.user_id == user.id
    ).first_or_404()
    
    try:
        research_service = ResearchService()
        execution_result = research_service.execute_experiment(
            experiment_id=experiment.id,
            experiment_design=json.loads(experiment.experiment_design)
        )
        
        # Update experiment with results
        experiment.execution_status = 'completed'
        experiment.results = json.dumps(execution_result['results'])
        experiment.analysis = execution_result['analysis']
        
        # Update hypothesis validation if experiment provides evidence
        if execution_result.get('validates_hypothesis'):
            experiment.hypothesis.is_validated = True
            experiment.hypothesis.test_results = json.dumps(execution_result['results'])
        
        db.session.commit()
        
        logging.info(f"Experiment executed: {experiment.id}")
        return jsonify({
            'success': True,
            'results': execution_result['results'],
            'analysis': execution_result['analysis'],
            'validates_hypothesis': execution_result.get('validates_hypothesis', False)
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error executing experiment: {str(e)}")
        return jsonify({'error': 'Failed to execute experiment'}), 500

@self_improving_bp.route('/discovery/automated', methods=['POST'])
@login_required
def automated_discovery():
    user = get_current_user()
    data = request.get_json()
    
    domain = data.get('domain')
    search_depth = data.get('search_depth', 'medium')
    
    if not domain:
        return jsonify({'error': 'Research domain is required'}), 400
    
    try:
        research_service = ResearchService()
        discoveries = research_service.automated_scientific_discovery(
            user_id=user.id,
            domain=domain,
            search_depth=search_depth
        )
        
        logging.info(f"Automated discovery completed for user {user.id} in domain {domain}")
        return jsonify({
            'success': True,
            'discoveries': discoveries,
            'domain': domain
        })
    
    except Exception as e:
        logging.error(f"Error in automated discovery: {str(e)}")
        return jsonify({'error': 'Failed to perform automated discovery'}), 500

@self_improving_bp.route('/capability-enhancement/run', methods=['POST'])
@login_required
def run_capability_enhancement():
    user = get_current_user()
    data = request.get_json()
    
    enhancement_type = data.get('enhancement_type')
    target_capability = data.get('target_capability')
    
    if not enhancement_type or not target_capability:
        return jsonify({'error': 'Enhancement type and target capability are required'}), 400
    
    try:
        research_service = ResearchService()
        enhancement_result = research_service.enhance_capability(
            user_id=user.id,
            enhancement_type=enhancement_type,
            target_capability=target_capability
        )
        
        logging.info(f"Capability enhancement completed for user {user.id}")
        return jsonify({
            'success': True,
            'enhancement_result': enhancement_result
        })
    
    except Exception as e:
        logging.error(f"Error in capability enhancement: {str(e)}")
        return jsonify({'error': 'Failed to enhance capability'}), 500

@self_improving_bp.route('/meta-learning/adapt', methods=['POST'])
@login_required
def meta_learning_adaptation():
    user = get_current_user()
    data = request.get_json()
    
    learning_task = data.get('learning_task')
    performance_data = data.get('performance_data', {})
    
    if not learning_task:
        return jsonify({'error': 'Learning task is required'}), 400
    
    try:
        research_service = ResearchService()
        adaptation_result = research_service.meta_learning_adaptation(
            user_id=user.id,
            learning_task=learning_task,
            performance_data=performance_data
        )
        
        logging.info(f"Meta-learning adaptation completed for user {user.id}")
        return jsonify({
            'success': True,
            'adaptation_result': adaptation_result
        })
    
    except Exception as e:
        logging.error(f"Error in meta-learning adaptation: {str(e)}")
        return jsonify({'error': 'Failed to perform meta-learning adaptation'}), 500
