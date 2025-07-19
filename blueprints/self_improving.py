from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import ResearchProject, Experiment, db
from services.research_service import ResearchService
import uuid

self_improving_bp = Blueprint('self_improving', __name__, url_prefix='/self-improving')

@self_improving_bp.route('/')
@login_required
def index():
    # Get user's research projects
    projects = ResearchProject.query.filter_by(
        user_id=current_user.id
    ).order_by(ResearchProject.created_at.desc()).all()
    
    return render_template('self_improving/index.html', projects=projects)

@self_improving_bp.route('/research')
@login_required
def research():
    projects = ResearchProject.query.filter_by(
        user_id=current_user.id
    ).order_by(ResearchProject.created_at.desc()).all()
    
    return render_template('self_improving/research.html', projects=projects)

@self_improving_bp.route('/capabilities')
@login_required
def capabilities():
    return render_template('self_improving/capabilities.html')

@self_improving_bp.route('/knowledge')
@login_required
def knowledge():
    return render_template('self_improving/knowledge.html')

@self_improving_bp.route('/optimization')
@login_required
def optimization():
    return render_template('self_improving/optimization.html')

@self_improving_bp.route('/meta-learning')
@login_required
def meta_learning():
    return render_template('self_improving/meta_learning.html')

@self_improving_bp.route('/hypotheses')
@login_required
def hypotheses():
    return render_template('self_improving/hypotheses.html')

@self_improving_bp.route('/experiments')
@login_required
def experiments():
    # Get user's experiments across all projects
    experiments = Experiment.query.join(ResearchProject).filter(
        ResearchProject.user_id == current_user.id
    ).order_by(Experiment.created_at.desc()).all()
    
    return render_template('self_improving/experiments.html', experiments=experiments)

@self_improving_bp.route('/discovery')
@login_required
def discovery():
    return render_template('self_improving/discovery.html')

@self_improving_bp.route('/create-project', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    research_area = data.get('research_area', '')
    hypothesis = data.get('hypothesis', '')
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    
    try:
        research_service = ResearchService()
        
        project_id = str(uuid.uuid4())
        project = ResearchProject(
            id=project_id,
            user_id=current_user.id,
            name=name,
            description=data.get('description', ''),
            research_area=research_area,
            hypothesis=hypothesis,
            methodology=data.get('methodology', {}),
            status='active'
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Initialize automated research
        research_result = research_service.initialize_research_project(project)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'research_result': research_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/project/<project_id>')
@login_required
def view_project(project_id):
    project = ResearchProject.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get project experiments
    experiments = Experiment.query.filter_by(
        project_id=project_id
    ).order_by(Experiment.created_at.desc()).all()
    
    return render_template('self_improving/project_detail.html', 
                         project=project, 
                         experiments=experiments)

@self_improving_bp.route('/generate-hypothesis', methods=['POST'])
@login_required
def generate_hypothesis():
    data = request.get_json()
    
    research_area = data.get('research_area', '')
    existing_knowledge = data.get('existing_knowledge', '')
    
    if not research_area:
        return jsonify({'error': 'Research area is required'}), 400
    
    try:
        research_service = ResearchService()
        
        # Generate hypothesis using AI
        hypothesis_results = research_service.generate_hypothesis(
            research_area=research_area,
            existing_knowledge=existing_knowledge
        )
        
        return jsonify({
            'success': True,
            'hypotheses': hypothesis_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/design-experiment', methods=['POST'])
@login_required
def design_experiment():
    data = request.get_json()
    
    project_id = data.get('project_id')
    hypothesis = data.get('hypothesis', '')
    
    if not project_id or not hypothesis:
        return jsonify({'error': 'Project ID and hypothesis are required'}), 400
    
    project = ResearchProject.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        research_service = ResearchService()
        
        # Design experiment automatically
        experimental_design = research_service.design_experiment(
            project=project,
            hypothesis=hypothesis
        )
        
        experiment_id = str(uuid.uuid4())
        experiment = Experiment(
            id=experiment_id,
            project_id=project_id,
            name=experimental_design.get('name', 'Auto-generated Experiment'),
            hypothesis=hypothesis,
            experimental_design=experimental_design,
            parameters=experimental_design.get('parameters', {}),
            status='planned'
        )
        
        db.session.add(experiment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'experiment_id': experiment_id,
            'design': experimental_design
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/experiment/<experiment_id>/run', methods=['POST'])
@login_required
def run_experiment(experiment_id):
    experiment = Experiment.query.join(ResearchProject).filter(
        Experiment.id == experiment_id,
        ResearchProject.user_id == current_user.id
    ).first_or_404()
    
    try:
        research_service = ResearchService()
        
        # Run automated experiment
        experiment_results = research_service.run_experiment(experiment)
        
        # Update experiment with results
        experiment.results = experiment_results
        experiment.status = 'completed'
        experiment.start_time = db.func.now()
        experiment.end_time = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': experiment_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/analyze-results', methods=['POST'])
@login_required
def analyze_results():
    data = request.get_json()
    
    experiment_id = data.get('experiment_id')
    
    if not experiment_id:
        return jsonify({'error': 'Experiment ID is required'}), 400
    
    experiment = Experiment.query.join(ResearchProject).filter(
        Experiment.id == experiment_id,
        ResearchProject.user_id == current_user.id
    ).first_or_404()
    
    try:
        research_service = ResearchService()
        
        # Analyze experiment results
        analysis_results = research_service.analyze_experiment_results(experiment)
        
        return jsonify({
            'success': True,
            'analysis': analysis_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/knowledge-acquisition', methods=['POST'])
@login_required
def knowledge_acquisition():
    data = request.get_json()
    
    topic = data.get('topic', '')
    sources = data.get('sources', ['arxiv', 'pubmed', 'semantic_scholar'])
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    try:
        research_service = ResearchService()
        
        # Acquire new knowledge
        knowledge_results = research_service.acquire_knowledge(
            topic=topic,
            sources=sources
        )
        
        return jsonify({
            'success': True,
            'knowledge': knowledge_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/capability-enhancement', methods=['POST'])
@login_required
def capability_enhancement():
    data = request.get_json()
    
    capability_area = data.get('capability_area', '')
    current_performance = data.get('current_performance', {})
    
    if not capability_area:
        return jsonify({'error': 'Capability area is required'}), 400
    
    try:
        research_service = ResearchService()
        
        # Enhance capabilities
        enhancement_results = research_service.enhance_capabilities(
            capability_area=capability_area,
            current_performance=current_performance
        )
        
        return jsonify({
            'success': True,
            'enhancement': enhancement_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/meta-learning-session', methods=['POST'])
@login_required
def meta_learning_session():
    data = request.get_json()
    
    task_type = data.get('task_type', '')
    training_data = data.get('training_data', {})
    
    if not task_type:
        return jsonify({'error': 'Task type is required'}), 400
    
    try:
        research_service = ResearchService()
        
        # Run meta-learning session
        meta_learning_results = research_service.run_meta_learning(
            task_type=task_type,
            training_data=training_data
        )
        
        return jsonify({
            'success': True,
            'results': meta_learning_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/scientific-discovery', methods=['POST'])
@login_required
def scientific_discovery():
    data = request.get_json()
    
    research_domain = data.get('research_domain', '')
    discovery_type = data.get('discovery_type', 'pattern')
    
    if not research_domain:
        return jsonify({'error': 'Research domain is required'}), 400
    
    try:
        research_service = ResearchService()
        
        # Attempt scientific discovery
        discovery_results = research_service.attempt_scientific_discovery(
            research_domain=research_domain,
            discovery_type=discovery_type
        )
        
        return jsonify({
            'success': True,
            'discoveries': discovery_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@self_improving_bp.route('/research-progress/<project_id>')
@login_required
def research_progress(project_id):
    project = ResearchProject.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Calculate progress metrics
    total_experiments = Experiment.query.filter_by(project_id=project_id).count()
    completed_experiments = Experiment.query.filter_by(
        project_id=project_id,
        status='completed'
    ).count()
    
    progress_percentage = (completed_experiments / total_experiments * 100) if total_experiments > 0 else 0
    
    # Update project progress
    project.progress_percentage = progress_percentage
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress': {
            'percentage': progress_percentage,
            'total_experiments': total_experiments,
            'completed_experiments': completed_experiments,
            'findings_count': len(project.findings or [])
        }
    })
