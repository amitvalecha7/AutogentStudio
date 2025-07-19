import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import and_, or_

from app import db
from models import KnowledgeBase, File, FileEmbedding, User
from services.ai_service import AIService
from services.file_service import FileService

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        self.ai_service = AIService()
        self.file_service = FileService()
    
    def create_knowledge_base(self, name: str, description: str, user_id: int) -> KnowledgeBase:
        """Create a new knowledge base"""
        try:
            kb = KnowledgeBase(
                name=name,
                description=description,
                user_id=user_id
            )
            db.session.add(kb)
            db.session.commit()
            
            logger.info(f"Created knowledge base: {name} for user {user_id}")
            return kb
            
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            db.session.rollback()
            raise
    
    def add_files_to_knowledge_base(self, kb_id: int, file_ids: List[int], user_id: int) -> bool:
        """Add files to a knowledge base"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                logger.error(f"Knowledge base {kb_id} not found for user {user_id}")
                return False
            
            # Verify files belong to user
            files = File.query.filter(
                and_(File.id.in_(file_ids), File.user_id == user_id)
            ).all()
            
            if len(files) != len(file_ids):
                logger.error("Some files not found or don't belong to user")
                return False
            
            # Process files if not already processed
            for file in files:
                if not file.processed:
                    self.file_service.process_file(file.id)
            
            # Update knowledge base timestamp
            kb.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Added {len(files)} files to knowledge base {kb.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding files to knowledge base: {str(e)}")
            db.session.rollback()
            return False
    
    def query_knowledge_base(self, kb_id: int, query: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Query knowledge base using semantic search"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                logger.error(f"Knowledge base {kb_id} not found for user {user_id}")
                return []
            
            # Create embedding for query
            query_embedding = self.ai_service.create_embedding(query, user_id)
            
            # Get all files in knowledge base (for now, all user files)
            user_files = File.query.filter_by(user_id=user_id).all()
            file_ids = [f.id for f in user_files]
            
            if not file_ids:
                return []
            
            # Find similar embeddings
            embeddings = FileEmbedding.query.filter(FileEmbedding.file_id.in_(file_ids)).all()
            
            results = []
            for embedding in embeddings:
                try:
                    stored_embedding = json.loads(embedding.embedding)
                    similarity = self.file_service.calculate_cosine_similarity(query_embedding, stored_embedding)
                    
                    results.append({
                        'file_id': embedding.file_id,
                        'chunk_text': embedding.chunk_text,
                        'similarity': similarity,
                        'file': embedding.file,
                        'knowledge_base': kb.name
                    })
                except Exception as e:
                    logger.error(f"Error calculating similarity: {str(e)}")
                    continue
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return []
    
    def generate_answer_from_knowledge_base(self, kb_id: int, question: str, user_id: int) -> str:
        """Generate an answer using knowledge base context"""
        try:
            # Get relevant documents
            relevant_docs = self.query_knowledge_base(kb_id, question, user_id, limit=5)
            
            if not relevant_docs:
                return "I couldn't find relevant information in the knowledge base to answer your question."
            
            # Prepare context from relevant documents
            context = "\n\n".join([doc['chunk_text'] for doc in relevant_docs])
            
            # Generate answer using AI
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context. Use only the information from the context to answer the question. If the context doesn't contain enough information to answer the question, say so."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
                }
            ]
            
            answer = self.ai_service.chat_completion(
                model="gpt-4o",
                messages=messages,
                user_id=user_id
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer from knowledge base: {str(e)}")
            return "I encountered an error while trying to answer your question."
    
    def get_knowledge_base_stats(self, kb_id: int, user_id: int) -> Dict[str, Any]:
        """Get statistics for a knowledge base"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return {}
            
            # Get all files for this user (simplified approach)
            user_files = File.query.filter_by(user_id=user_id).all()
            
            stats = {
                'name': kb.name,
                'description': kb.description,
                'total_files': len(user_files),
                'total_size': sum(f.file_size for f in user_files),
                'processed_files': len([f for f in user_files if f.processed]),
                'total_embeddings': sum(len(f.embeddings) for f in user_files),
                'created_at': kb.created_at.isoformat(),
                'updated_at': kb.updated_at.isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}")
            return {}
    
    def update_knowledge_base(self, kb_id: int, name: str, description: str, user_id: int) -> bool:
        """Update knowledge base metadata"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                logger.error(f"Knowledge base {kb_id} not found for user {user_id}")
                return False
            
            kb.name = name
            kb.description = description
            kb.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated knowledge base {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            db.session.rollback()
            return False
    
    def delete_knowledge_base(self, kb_id: int, user_id: int) -> bool:
        """Delete knowledge base"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                logger.error(f"Knowledge base {kb_id} not found for user {user_id}")
                return False
            
            db.session.delete(kb)
            db.session.commit()
            
            logger.info(f"Deleted knowledge base {kb.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base: {str(e)}")
            db.session.rollback()
            return False
    
    def list_knowledge_bases(self, user_id: int) -> List[Dict[str, Any]]:
        """List all knowledge bases for a user"""
        try:
            kbs = KnowledgeBase.query.filter_by(user_id=user_id).order_by(KnowledgeBase.updated_at.desc()).all()
            
            result = []
            for kb in kbs:
                stats = self.get_knowledge_base_stats(kb.id, user_id)
                result.append({
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'created_at': kb.created_at.isoformat(),
                    'updated_at': kb.updated_at.isoformat(),
                    'stats': stats
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {str(e)}")
            return []
    
    def search_across_knowledge_bases(self, query: str, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Search across all knowledge bases for a user"""
        try:
            user_kbs = KnowledgeBase.query.filter_by(user_id=user_id).all()
            
            all_results = []
            for kb in user_kbs:
                kb_results = self.query_knowledge_base(kb.id, query, user_id, limit=limit//len(user_kbs) + 1)
                all_results.extend(kb_results)
            
            # Sort all results by similarity
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching across knowledge bases: {str(e)}")
            return []
    
    def get_related_documents(self, kb_id: int, document_id: int, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get documents related to a specific document"""
        try:
            # Get the document's embeddings
            file = File.query.filter_by(id=document_id, user_id=user_id).first()
            if not file:
                return []
            
            embeddings = FileEmbedding.query.filter_by(file_id=document_id).all()
            if not embeddings:
                return []
            
            # Use the first embedding as reference
            reference_embedding = json.loads(embeddings[0].embedding)
            
            # Find similar documents
            all_embeddings = FileEmbedding.query.filter(
                FileEmbedding.file_id != document_id
            ).all()
            
            results = []
            for embedding in all_embeddings:
                try:
                    stored_embedding = json.loads(embedding.embedding)
                    similarity = self.file_service.calculate_cosine_similarity(reference_embedding, stored_embedding)
                    
                    results.append({
                        'file_id': embedding.file_id,
                        'chunk_text': embedding.chunk_text,
                        'similarity': similarity,
                        'file': embedding.file
                    })
                except Exception as e:
                    logger.error(f"Error calculating similarity: {str(e)}")
                    continue
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting related documents: {str(e)}")
            return []
    
    def extract_key_concepts(self, kb_id: int, user_id: int) -> List[str]:
        """Extract key concepts from knowledge base"""
        try:
            kb = KnowledgeBase.query.filter_by(id=kb_id, user_id=user_id).first()
            if not kb:
                return []
            
            # Get sample text from knowledge base
            user_files = File.query.filter_by(user_id=user_id).limit(10).all()
            sample_texts = []
            
            for file in user_files:
                embeddings = FileEmbedding.query.filter_by(file_id=file.id).limit(3).all()
                sample_texts.extend([e.chunk_text for e in embeddings])
            
            if not sample_texts:
                return []
            
            # Combine sample texts
            combined_text = " ".join(sample_texts)
            
            # Extract keywords using AI
            keywords = self.ai_service.extract_keywords(combined_text, user_id)
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {str(e)}")
            return []
