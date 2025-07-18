from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
import mimetypes
from app import db
from models import File, KnowledgeBase, KnowledgeBaseFile, FileEmbedding, User
from blueprints.auth import login_required, get_current_user
from utils.file_processor import FileProcessor
from utils.vector_store import VectorStore
from services.embedding_service import EmbeddingService
import logging

files_bp = Blueprint('files', __name__)

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xlsx', 'pptx', 'csv', 'json', 'xml',
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',
    'mp3', 'wav', 'ogg', 'm4a',
    'mp4', 'avi', 'mov', 'webm'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files_bp.route('/')
@login_required
def files_index():
    user = get_current_user()
    files = File.query.filter_by(user_id=user.id).order_by(File.upload_timestamp.desc()).all()
    knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(KnowledgeBase.created_at.desc()).all()
    
    return render_template('files/files.html', files=files, knowledge_bases=knowledge_bases)

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    user = get_current_user()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, unique_filename)
        
        try:
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0]
            
            # Save file record
            file_record = File(
                user_id=user.id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            # Process file for text extraction and embedding (async in real app)
            try:
                processor = FileProcessor()
                text_content = processor.extract_text(file_path, mime_type)
                
                if text_content:
                    # Generate embeddings
                    embedding_service = EmbeddingService()
                    chunks = processor.chunk_text(text_content)
                    
                    for i, chunk in enumerate(chunks):
                        embedding = embedding_service.generate_embedding(chunk)
                        
                        file_embedding = FileEmbedding(
                            file_id=file_record.id,
                            chunk_index=i,
                            chunk_text=chunk,
                            embedding=json.dumps(embedding)
                        )
                        db.session.add(file_embedding)
                    
                    file_record.is_processed = True
                    db.session.commit()
                    
                    logging.info(f"File processed and embedded: {file_record.id}")
            
            except Exception as e:
                logging.error(f"Error processing file {file_record.id}: {str(e)}")
            
            return jsonify({
                'success': True,
                'file_id': file_record.id,
                'filename': original_filename,
                'file_size': file_size,
                'mime_type': mime_type,
                'upload_timestamp': file_record.upload_timestamp.isoformat()
            })
        
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            return jsonify({'error': 'Failed to upload file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@files_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    user = get_current_user()
    file_record = File.query.filter_by(id=file_id, user_id=user.id).first_or_404()
    
    directory = os.path.dirname(file_record.file_path)
    filename = os.path.basename(file_record.file_path)
    
    return send_from_directory(directory, filename, as_attachment=True, 
                             download_name=file_record.original_filename)

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    user = get_current_user()
    file_record = File.query.filter_by(id=file_id, user_id=user.id).first()
    
    if file_record:
        try:
            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Delete database record (cascades to embeddings)
            db.session.delete(file_record)
            db.session.commit()
            
            logging.info(f"File deleted: {file_id}")
            return jsonify({'success': True})
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting file: {str(e)}")
            return jsonify({'error': 'Failed to delete file'}), 500
    
    return jsonify({'error': 'File not found'}), 404

@files_bp.route('/knowledge-base')
@login_required
def knowledge_base():
    user = get_current_user()
    knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(KnowledgeBase.created_at.desc()).all()
    files = File.query.filter_by(user_id=user.id).order_by(File.upload_timestamp.desc()).all()
    
    return render_template('files/knowledge_base.html', knowledge_bases=knowledge_bases, files=files)

@files_bp.route('/knowledge-base/create', methods=['POST'])
@login_required
def create_knowledge_base():
    user = get_current_user()
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        return jsonify({'error': 'Knowledge base name is required'}), 400
    
    knowledge_base = KnowledgeBase(
        user_id=user.id,
        name=name,
        description=description
    )
    
    try:
        db.session.add(knowledge_base)
        db.session.commit()
        
        logging.info(f"Knowledge base created: {knowledge_base.id}")
        return jsonify({
            'success': True,
            'id': knowledge_base.id,
            'name': knowledge_base.name,
            'description': knowledge_base.description,
            'created_at': knowledge_base.created_at.isoformat()
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating knowledge base: {str(e)}")
        return jsonify({'error': 'Failed to create knowledge base'}), 500

@files_bp.route('/knowledge-base/<int:kb_id>/add-file', methods=['POST'])
@login_required
def add_file_to_knowledge_base(kb_id):
    user = get_current_user()
    data = request.get_json()
    file_id = data.get('file_id')
    
    if not file_id:
        return jsonify({'error': 'File ID is required'}), 400
    
    knowledge_base = KnowledgeBase.query.filter_by(id=kb_id, user_id=user.id).first()
    file_record = File.query.filter_by(id=file_id, user_id=user.id).first()
    
    if not knowledge_base or not file_record:
        return jsonify({'error': 'Knowledge base or file not found'}), 404
    
    # Check if already associated
    existing = KnowledgeBaseFile.query.filter_by(
        knowledge_base_id=kb_id, 
        file_id=file_id
    ).first()
    
    if existing:
        return jsonify({'error': 'File already in knowledge base'}), 400
    
    try:
        association = KnowledgeBaseFile(
            knowledge_base_id=kb_id,
            file_id=file_id
        )
        
        db.session.add(association)
        knowledge_base.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"File {file_id} added to knowledge base {kb_id}")
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding file to knowledge base: {str(e)}")
        return jsonify({'error': 'Failed to add file to knowledge base'}), 500

@files_bp.route('/knowledge-base/<int:kb_id>/search', methods=['POST'])
@login_required
def search_knowledge_base(kb_id):
    user = get_current_user()
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    knowledge_base = KnowledgeBase.query.filter_by(id=kb_id, user_id=user.id).first()
    if not knowledge_base:
        return jsonify({'error': 'Knowledge base not found'}), 404
    
    try:
        vector_store = VectorStore()
        results = vector_store.semantic_search(kb_id, query, limit=10)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
    
    except Exception as e:
        logging.error(f"Error searching knowledge base: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@files_bp.route('/knowledge-base/<int:kb_id>/delete', methods=['POST'])
@login_required
def delete_knowledge_base(kb_id):
    user = get_current_user()
    knowledge_base = KnowledgeBase.query.filter_by(id=kb_id, user_id=user.id).first()
    
    if knowledge_base:
        try:
            db.session.delete(knowledge_base)
            db.session.commit()
            
            logging.info(f"Knowledge base deleted: {kb_id}")
            return jsonify({'success': True})
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting knowledge base: {str(e)}")
            return jsonify({'error': 'Failed to delete knowledge base'}), 500
    
    return jsonify({'error': 'Knowledge base not found'}), 404
