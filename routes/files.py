from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, send_file
from werkzeug.utils import secure_filename
from app import db
from models import User, File, FileChunk, KnowledgeBase, KnowledgeBaseFile
from services.embedding_service import EmbeddingService
from utils.file_processor import FileProcessor
import os
import logging
import uuid
import hashlib

files_bp = Blueprint('files', __name__)

@files_bp.route('/files')
def files():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    files = File.query.filter_by(user_id=user.id).order_by(File.created_at.desc()).all()
    
    return render_template('files/files.html', user=user, files=files)

@files_bp.route('/files/knowledge-base')
def knowledge_base():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(KnowledgeBase.created_at.desc()).all()
    
    return render_template('files/knowledge_base.html', user=user, knowledge_bases=knowledge_bases)

@files_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        user = User.query.get(session['user_id'])
        
        # Generate unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        
        # Ensure upload directory exists
        os.makedirs('uploads', exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Calculate file hash
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Create file record
        file_record = File(
            user_id=user.id,
            filename=filename,
            original_filename=file.filename,
            file_type=file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown',
            file_size=os.path.getsize(file_path),
            file_path=file_path,
            mime_type=file.content_type,
            checksum=file_hash,
            processing_status='pending'
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        # Process file asynchronously
        try:
            processor = FileProcessor()
            content = processor.extract_text(file_path, file.content_type)
            
            if content:
                # Create embeddings
                embedding_service = EmbeddingService()
                chunks = processor.chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    try:
                        embedding = embedding_service.create_embedding(chunk)
                        
                        file_chunk = FileChunk(
                            file_id=file_record.id,
                            chunk_index=i,
                            content=chunk,
                            embedding=embedding.tobytes() if embedding is not None else None
                        )
                        db.session.add(file_chunk)
                    except Exception as e:
                        logging.error(f"Error creating embedding for chunk {i}: {str(e)}")
                        continue
                
                file_record.is_processed = True
                file_record.processing_status = 'completed'
            else:
                file_record.processing_status = 'failed'
                
        except Exception as e:
            logging.error(f"Error processing file: {str(e)}")
            file_record.processing_status = 'failed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file': file_record.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'Failed to upload file'}), 500

@files_bp.route('/api/files/<file_id>')
def get_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    file = File.query.filter_by(id=file_id, user_id=user.id).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({'file': file.to_dict()})

@files_bp.route('/api/files/<file_id>/download')
def download_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    file = File.query.filter_by(id=file_id, user_id=user.id).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    try:
        return send_file(file.file_path, as_attachment=True, download_name=file.original_filename)
    except Exception as e:
        logging.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500

@files_bp.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    file = File.query.filter_by(id=file_id, user_id=user.id).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Delete file from filesystem
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Delete from database (chunks will be deleted via cascade)
        db.session.delete(file)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': 'Failed to delete file'}), 500

@files_bp.route('/api/knowledge-bases', methods=['GET', 'POST'])
def knowledge_bases():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            
            if not name:
                return jsonify({'error': 'Knowledge base name required'}), 400
            
            kb = KnowledgeBase(
                user_id=user.id,
                name=name,
                description=data.get('description', ''),
                is_public=data.get('is_public', False),
                embedding_model=data.get('embedding_model', 'text-embedding-3-small')
            )
            
            db.session.add(kb)
            db.session.commit()
            
            return jsonify({'success': True, 'knowledge_base': kb.to_dict()})
            
        except Exception as e:
            logging.error(f"Error creating knowledge base: {str(e)}")
            return jsonify({'error': 'Failed to create knowledge base'}), 500
    
    knowledge_bases = KnowledgeBase.query.filter_by(user_id=user.id).order_by(KnowledgeBase.created_at.desc()).all()
    return jsonify({'knowledge_bases': [kb.to_dict() for kb in knowledge_bases]})

@files_bp.route('/api/knowledge-bases/<kb_id>/files', methods=['GET', 'POST', 'DELETE'])
def knowledge_base_files(kb_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user.id).first()
    
    if not kb:
        return jsonify({'error': 'Knowledge base not found'}), 404
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            file_ids = data.get('file_ids', [])
            
            for file_id in file_ids:
                file = File.query.filter_by(id=file_id, user_id=user.id).first()
                if file:
                    # Check if file is already in knowledge base
                    existing = KnowledgeBaseFile.query.filter_by(
                        knowledge_base_id=kb.id,
                        file_id=file.id
                    ).first()
                    
                    if not existing:
                        kb_file = KnowledgeBaseFile(
                            knowledge_base_id=kb.id,
                            file_id=file.id
                        )
                        db.session.add(kb_file)
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            logging.error(f"Error adding files to knowledge base: {str(e)}")
            return jsonify({'error': 'Failed to add files'}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            file_ids = data.get('file_ids', [])
            
            for file_id in file_ids:
                KnowledgeBaseFile.query.filter_by(
                    knowledge_base_id=kb.id,
                    file_id=file_id
                ).delete()
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            logging.error(f"Error removing files from knowledge base: {str(e)}")
            return jsonify({'error': 'Failed to remove files'}), 500
    
    # GET request
    kb_files = db.session.query(File).join(KnowledgeBaseFile).filter(
        KnowledgeBaseFile.knowledge_base_id == kb.id
    ).all()
    
    return jsonify({'files': [file.to_dict() for file in kb_files]})

@files_bp.route('/api/files/search')
def search_files():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'files': []})
    
    try:
        # Search in file names and content
        files = File.query.filter(
            File.user_id == user.id,
            db.or_(
                File.original_filename.ilike(f'%{query}%'),
                File.chunks.any(FileChunk.content.ilike(f'%{query}%'))
            )
        ).all()
        
        return jsonify({'files': [file.to_dict() for file in files]})
        
    except Exception as e:
        logging.error(f"Error searching files: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500
