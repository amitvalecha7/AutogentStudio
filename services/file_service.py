import os
import json
from typing import List, Dict
from werkzeug.datastructures import FileStorage
from models import File, KnowledgeBase, User
from app import db
from utils.file_processor import file_processor

class FileService:
    def __init__(self):
        self.file_processor = file_processor
    
    def upload_file(self, user_id: str, file: FileStorage) -> dict:
        """Upload and process a file"""
        try:
            # Save file
            file_info = self.file_processor.save_file(file)
            
            # Create database record
            file_record = File(
                user_id=user_id,
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_size=file_info['file_size'],
                file_type=file_info['file_type'],
                file_path=file_info['file_path']
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            # Process for RAG asynchronously (in a real app, use Celery)
            self.process_file_for_rag(str(file_record.id))
            
            return {
                'file_id': str(file_record.id),
                'filename': file_info['original_filename'],
                'file_size': file_info['file_size'],
                'file_type': file_info['file_type'],
                'status': 'uploaded'
            }
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"File upload failed: {str(e)}")
    
    def process_file_for_rag(self, file_id: str):
        """Process file for RAG integration"""
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                raise ValueError("File not found")
            
            # Process file
            result = self.file_processor.process_file_for_rag(
                file_record.file_path,
                file_record.file_type
            )
            
            if 'error' in result:
                print(f"Error processing file {file_id}: {result['error']}")
                return
            
            # Mark as processed
            file_record.processed = True
            file_record.embedding_model = 'all-MiniLM-L6-v2'
            db.session.commit()
            
            print(f"File {file_id} processed successfully")
            
        except Exception as e:
            print(f"Error processing file {file_id}: {str(e)}")
    
    def get_user_files(self, user_id: str) -> List[Dict]:
        """Get all files for a user"""
        try:
            files = File.query.filter_by(user_id=user_id).order_by(File.created_at.desc()).all()
            
            return [
                {
                    'id': str(file.id),
                    'filename': file.original_filename,
                    'file_size': file.file_size,
                    'file_type': file.file_type,
                    'processed': file.processed,
                    'embedding_model': file.embedding_model,
                    'created_at': file.created_at.isoformat()
                }
                for file in files
            ]
        except Exception as e:
            raise Exception(f"Failed to get user files: {str(e)}")
    
    def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete a file"""
        try:
            file_record = File.query.filter_by(id=file_id, user_id=user_id).first()
            if not file_record:
                raise ValueError("File not found")
            
            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Delete database record
            db.session.delete(file_record)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def create_knowledge_base(self, user_id: str, name: str, description: str = None) -> str:
        """Create a new knowledge base"""
        try:
            kb = KnowledgeBase(
                user_id=user_id,
                name=name,
                description=description
            )
            
            db.session.add(kb)
            db.session.commit()
            
            return str(kb.id)
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create knowledge base: {str(e)}")
    
    def get_user_knowledge_bases(self, user_id: str) -> List[Dict]:
        """Get all knowledge bases for a user"""
        try:
            kbs = KnowledgeBase.query.filter_by(user_id=user_id).order_by(KnowledgeBase.created_at.desc()).all()
            
            return [
                {
                    'id': str(kb.id),
                    'name': kb.name,
                    'description': kb.description,
                    'embedding_model': kb.embedding_model,
                    'created_at': kb.created_at.isoformat(),
                    'updated_at': kb.updated_at.isoformat()
                }
                for kb in kbs
            ]
        except Exception as e:
            raise Exception(f"Failed to get knowledge bases: {str(e)}")
    
    def search_files(self, user_id: str, query: str, file_types: List[str] = None) -> List[Dict]:
        """Search user files by content and metadata"""
        try:
            # Basic implementation - in production, use vector search
            files_query = File.query.filter_by(user_id=user_id)
            
            if file_types:
                files_query = files_query.filter(File.file_type.in_(file_types))
            
            files = files_query.all()
            
            # Simple text matching (in production, use semantic search)
            results = []
            for file in files:
                if query.lower() in file.original_filename.lower():
                    results.append({
                        'id': str(file.id),
                        'filename': file.original_filename,
                        'file_type': file.file_type,
                        'relevance_score': 0.8,  # Mock score
                        'created_at': file.created_at.isoformat()
                    })
            
            return results
        except Exception as e:
            raise Exception(f"File search failed: {str(e)}")

# Global instance
file_service = FileService()
