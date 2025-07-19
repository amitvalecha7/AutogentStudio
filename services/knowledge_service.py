import json
import numpy as np
from typing import List, Dict, Any
from app import db
from models import KnowledgeBase, KnowledgeBaseFile, File, FileChunk
import logging

class KnowledgeService:
    def __init__(self):
        self.embedding_dimension = 1536  # OpenAI embedding dimension
    
    def create_knowledge_base(self, name: str, description: str, user_id: int) -> Dict[str, Any]:
        """Create a new knowledge base"""
        try:
            kb = KnowledgeBase(
                user_id=user_id,
                name=name,
                description=description,
                settings=json.dumps({
                    'embedding_model': 'text-embedding-3-small',
                    'chunk_size': 1000,
                    'chunk_overlap': 200
                })
            )
            
            db.session.add(kb)
            db.session.commit()
            
            return {
                'success': True,
                'knowledge_base_id': kb.id,
                'message': 'Knowledge base created successfully'
            }
            
        except Exception as e:
            logging.error(f"Error creating knowledge base: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_file_to_knowledge_base(self, kb_id: int, file_id: int, user_id: int) -> Dict[str, Any]:
        """Add file to knowledge base"""
        try:
            # Verify ownership
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return {'success': False, 'error': 'Knowledge base not found'}
            
            file_record = File.query.filter_by(id=file_id, user_id=user_id).first()
            if not file_record:
                return {'success': False, 'error': 'File not found'}
            
            # Check if file already in KB
            existing = KnowledgeBaseFile.query.filter_by(
                knowledge_base_id=kb_id, 
                file_id=file_id
            ).first()
            
            if existing:
                return {'success': False, 'error': 'File already in knowledge base'}
            
            # Add to knowledge base
            kb_file = KnowledgeBaseFile(
                knowledge_base_id=kb_id,
                file_id=file_id
            )
            
            db.session.add(kb_file)
            db.session.commit()
            
            # Generate embeddings for file chunks
            self.generate_embeddings_for_file(file_record)
            
            return {
                'success': True,
                'message': 'File added to knowledge base successfully'
            }
            
        except Exception as e:
            logging.error(f"Error adding file to knowledge base: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_embeddings_for_file(self, file_record: File):
        """Generate embeddings for file chunks"""
        try:
            # Get file chunks
            chunks = FileChunk.query.filter_by(file_id=file_record.id).all()
            
            for chunk in chunks:
                if not chunk.embedding:
                    # Generate embedding (placeholder - use real embedding service)
                    embedding = self.generate_embedding(chunk.content)
                    chunk.embedding = json.dumps(embedding)
            
            file_record.embeddings_generated = True
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error generating embeddings: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder implementation)"""
        # In real implementation, use OpenAI embeddings API
        # For now, return random vector for demonstration
        return np.random.random(self.embedding_dimension).tolist()
    
    def search_knowledge_base(self, kb_id: int, query: str, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Search knowledge base using semantic similarity"""
        try:
            # Verify ownership
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return {'success': False, 'error': 'Knowledge base not found'}
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Get all chunks in knowledge base
            kb_files = KnowledgeBaseFile.query.filter_by(knowledge_base_id=kb_id).all()
            file_ids = [kf.file_id for kf in kb_files]
            
            chunks = FileChunk.query.filter(FileChunk.file_id.in_(file_ids)).all()
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    chunk_embedding = json.loads(chunk.embedding)
                    similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                    similarities.append({
                        'chunk': chunk,
                        'similarity': similarity
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:limit]
            
            results = []
            for result in top_results:
                chunk = result['chunk']
                file_record = File.query.get(chunk.file_id)
                
                results.append({
                    'content': chunk.content,
                    'filename': file_record.original_filename,
                    'similarity': result['similarity'],
                    'chunk_index': chunk.chunk_index
                })
            
            return {
                'success': True,
                'results': results,
                'total_chunks_searched': len(chunks)
            }
            
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logging.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def get_knowledge_base_stats(self, kb_id: int, user_id: int) -> Dict[str, Any]:
        """Get statistics for knowledge base"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return {'success': False, 'error': 'Knowledge base not found'}
            
            # Count files and chunks
            kb_files = KnowledgeBaseFile.query.filter_by(knowledge_base_id=kb_id).all()
            file_count = len(kb_files)
            
            chunk_count = 0
            processed_files = 0
            
            for kb_file in kb_files:
                file_record = File.query.get(kb_file.file_id)
                if file_record.is_processed:
                    processed_files += 1
                
                chunks = FileChunk.query.filter_by(file_id=file_record.id).count()
                chunk_count += chunks
            
            return {
                'success': True,
                'stats': {
                    'file_count': file_count,
                    'processed_files': processed_files,
                    'chunk_count': chunk_count,
                    'embeddings_ready': processed_files
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting knowledge base stats: {str(e)}")
            return {'success': False, 'error': str(e)}
