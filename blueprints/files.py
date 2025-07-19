from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import File, KnowledgeBase, FileEmbedding, db
from services.file_service import FileService
from services.vector_service import VectorService
import uuid
import os
import mimetypes

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/')
@login_required
def index():
    # Get user's files
    files = File.query.filter_by(
        user_id=current_user.id
    ).order_by(File.created_at.desc()).all()
    
    # Get user's knowledge bases
    knowledge_bases = KnowledgeBase.query.filter_by(
        user_id=current_user.id
    ).order_by(KnowledgeBase.updated_at.desc()).all()
    
    return render_template('files/index.html', 
                         files=files, 
                         knowledge_bases=knowledge_bases)

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        try:
            file_service = FileService()
            
            # Secure the filename
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            
            # Save file
            file_path = file_service.save_file(file, file_id, filename)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(filename)[0]
            
            # Create database record
            db_file = File(
                id=file_id,
                user_id=current_user.id,
                filename=f"{file_id}_{filename}",
                original_filename=filename,
                file_type=file_service.get_file_type(filename),
                file_size=file_size,
                mime_type=mime_type,
                storage_path=file_path,
                processing_status='uploaded'
            )
            
            db.session.add(db_file)
            db.session.commit()
            
            # Start background processing
            file_service.process_file_async(file_id)
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'file_size': file_size,
                'mime_type': mime_type
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>/download')
@login_required
def download_file(file_id):
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    return send_file(
        file.storage_path,
        as_attachment=True,
        download_name=file.original_filename
    )

@files_bp.route('/<file_id>/preview')
@login_required
def preview_file(file_id):
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    file_service = FileService()
    preview_data = file_service.get_file_preview(file)
    
    return jsonify({
        'success': True,
        'preview': preview_data
    })

@files_bp.route('/<file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Delete physical file
        if os.path.exists(file.storage_path):
            os.remove(file.storage_path)
        
        # Delete from database (cascades to embeddings)
        db.session.delete(file)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/knowledge-base')
@login_required
def knowledge_base():
    knowledge_bases = KnowledgeBase.query.filter_by(
        user_id=current_user.id
    ).order_by(KnowledgeBase.updated_at.desc()).all()
    
    return render_template('files/knowledge_base.html', 
                         knowledge_bases=knowledge_bases)

@files_bp.route('/knowledge-base/create', methods=['POST'])
@login_required
def create_knowledge_base():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': 'Knowledge base name is required'}), 400
    
    kb_id = str(uuid.uuid4())
    knowledge_base = KnowledgeBase(
        id=kb_id,
        user_id=current_user.id,
        name=name,
        description=description,
        settings=data.get('settings', {})
    )
    
    db.session.add(knowledge_base)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'knowledge_base_id': kb_id
    })

@files_bp.route('/knowledge-base/<kb_id>')
@login_required
def view_knowledge_base(kb_id):
    kb = KnowledgeBase.query.filter_by(
        id=kb_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get files in this knowledge base
    embeddings = FileEmbedding.query.filter_by(
        knowledge_base_id=kb_id
    ).join(File).filter_by(user_id=current_user.id).all()
    
    files = {}
    for embedding in embeddings:
        if embedding.file_id not in files:
            files[embedding.file_id] = embedding.file
    
    return render_template('files/knowledge_base_view.html', 
                         knowledge_base=kb, 
                         files=list(files.values()))

@files_bp.route('/knowledge-base/<kb_id>/add-file', methods=['POST'])
@login_required
def add_file_to_knowledge_base(kb_id):
    kb = KnowledgeBase.query.filter_by(
        id=kb_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    file_id = data.get('file_id')
    
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        vector_service = VectorService()
        vector_service.add_file_to_knowledge_base(file, kb)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/knowledge-base/<kb_id>/search', methods=['POST'])
@login_required
def search_knowledge_base(kb_id):
    kb = KnowledgeBase.query.filter_by(
        id=kb_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    try:
        vector_service = VectorService()
        results = vector_service.search_knowledge_base(kb, query)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/batch-upload', methods=['POST'])
@login_required
def batch_upload():
    files = request.files.getlist('files')
    
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    results = []
    file_service = FileService()
    
    for file in files:
        if file.filename:
            try:
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                
                file_path = file_service.save_file(file, file_id, filename)
                file_size = os.path.getsize(file_path)
                mime_type = mimetypes.guess_type(filename)[0]
                
                db_file = File(
                    id=file_id,
                    user_id=current_user.id,
                    filename=f"{file_id}_{filename}",
                    original_filename=filename,
                    file_type=file_service.get_file_type(filename),
                    file_size=file_size,
                    mime_type=mime_type,
                    storage_path=file_path,
                    processing_status='uploaded'
                )
                
                db.session.add(db_file)
                
                results.append({
                    'file_id': file_id,
                    'filename': filename,
                    'status': 'success'
                })
                
                # Start background processing
                file_service.process_file_async(file_id)
                
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'results': results
    })

@files_bp.route('/process-status/<file_id>')
@login_required
def file_process_status(file_id):
    file = File.query.filter_by(
        id=file_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'file_id': file_id,
        'status': file.processing_status,
        'is_processed': file.is_processed,
        'metadata': file.metadata
    })
