import logging
from models import KnowledgeBase, File, FileEmbedding
from app import db
from services.ai_providers import AIProviders
from sqlalchemy import func
import numpy as np

class KnowledgeBaseManager:
    def __init__(self):
        self.ai_providers = AIProviders()
    
    def create_knowledge_base(self, user_id, name, description, embedding_model='text-embedding-3-small'):
        """Create a new knowledge base"""
        try:
            knowledge_base = KnowledgeBase(
                user_id=user_id,
                name=name,
                description=description,
                embedding_model=embedding_model
            )
            db.session.add(knowledge_base)
            db.session.commit()
            
            return knowledge_base
        
        except Exception as e:
            logging.error(f"Error creating knowledge base: {str(e)}")
            return None
    
    def add_file_to_knowledge_base(self, knowledge_base_id, file_id):
        """Add a file to a knowledge base"""
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            file_record = File.query.get(file_id)
            
            if not knowledge_base or not file_record:
                raise ValueError("Knowledge base or file not found")
            
            # Update file metadata to include knowledge base
            if not file_record.metadata:
                file_record.metadata = {}
            
            if 'knowledge_bases' not in file_record.metadata:
                file_record.metadata['knowledge_bases'] = []
            
            if knowledge_base_id not in file_record.metadata['knowledge_bases']:
                file_record.metadata['knowledge_bases'].append(knowledge_base_id)
            
            db.session.commit()
            
            return True
        
        except Exception as e:
            logging.error(f"Error adding file to knowledge base: {str(e)}")
            return False
    
    def search_knowledge_base(self, knowledge_base_id, query, limit=10, threshold=0.7):
        """Search within a knowledge base using semantic search"""
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise ValueError("Knowledge base not found")
            
            # Generate query embedding
            query_embedding = self.ai_providers.get_embeddings(query, knowledge_base.embedding_model)
            
            # Get files in this knowledge base
            files = File.query.filter(
                File.user_id == knowledge_base.user_id,
                File.metadata.contains(f'"knowledge_bases": [{knowledge_base_id}]')
            ).all()
            
            file_ids = [f.id for f in files]
            
            if not file_ids:
                return []
            
            # Search embeddings
            embeddings = FileEmbedding.query.filter(
                FileEmbedding.file_id.in_(file_ids)
            ).all()
            
            # Calculate similarity scores
            results = []
            for embedding in embeddings:
                similarity = self._calculate_similarity(query_embedding, embedding.embedding)
                
                if similarity >= threshold:
                    results.append({
                        'file_id': embedding.file_id,
                        'chunk_text': embedding.chunk_text,
                        'similarity': similarity,
                        'chunk_index': embedding.chunk_index,
                        'file': embedding.file
                    })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
        
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def _calculate_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            return dot_product / (norm1 * norm2)
        
        except Exception as e:
            logging.error(f"Error calculating similarity: {str(e)}")
            return 0
    
    def get_knowledge_base_stats(self, knowledge_base_id):
        """Get statistics for a knowledge base"""
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                return None
            
            # Count files in knowledge base
            files = File.query.filter(
                File.user_id == knowledge_base.user_id,
                File.metadata.contains(f'"knowledge_bases": [{knowledge_base_id}]')
            ).all()
            
            file_count = len(files)
            total_size = sum(f.file_size for f in files)
            
            # Count embeddings
            file_ids = [f.id for f in files]
            embedding_count = 0
            
            if file_ids:
                embedding_count = FileEmbedding.query.filter(
                    FileEmbedding.file_id.in_(file_ids)
                ).count()
            
            return {
                'file_count': file_count,
                'total_size': total_size,
                'embedding_count': embedding_count,
                'embedding_model': knowledge_base.embedding_model
            }
        
        except Exception as e:
            logging.error(f"Error getting knowledge base stats: {str(e)}")
            return None
    
    def generate_answer(self, knowledge_base_id, query, context_limit=3):
        """Generate an answer using knowledge base context"""
        try:
            # Search knowledge base for relevant context
            search_results = self.search_knowledge_base(knowledge_base_id, query, context_limit)
            
            if not search_results:
                return "I couldn't find relevant information in the knowledge base to answer your question."
            
            # Build context from search results
            context_parts = []
            for result in search_results:
                context_parts.append(f"From {result['file'].original_filename}:\n{result['chunk_text']}")
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using AI
            prompt = f"""Based on the following context from the knowledge base, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please say so."""
            
            response = self.ai_providers.get_chat_response(prompt)
            
            return {
                'answer': response,
                'sources': [
                    {
                        'filename': result['file'].original_filename,
                        'similarity': result['similarity'],
                        'chunk_text': result['chunk_text'][:200] + "..." if len(result['chunk_text']) > 200 else result['chunk_text']
                    }
                    for result in search_results
                ]
            }
        
        except Exception as e:
            logging.error(f"Error generating answer: {str(e)}")
            return "An error occurred while generating the answer."
    
    def update_knowledge_base(self, knowledge_base_id, name=None, description=None):
        """Update knowledge base details"""
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise ValueError("Knowledge base not found")
            
            if name:
                knowledge_base.name = name
            if description is not None:
                knowledge_base.description = description
            
            db.session.commit()
            return True
        
        except Exception as e:
            logging.error(f"Error updating knowledge base: {str(e)}")
            return False
    
    def delete_knowledge_base(self, knowledge_base_id, user_id):
        """Delete a knowledge base"""
        try:
            knowledge_base = KnowledgeBase.query.filter_by(
                id=knowledge_base_id,
                user_id=user_id
            ).first()
            
            if not knowledge_base:
                raise ValueError("Knowledge base not found")
            
            # Remove knowledge base references from files
            files = File.query.filter(
                File.user_id == user_id,
                File.metadata.contains(f'"knowledge_bases": [{knowledge_base_id}]')
            ).all()
            
            for file in files:
                if file.metadata and 'knowledge_bases' in file.metadata:
                    file.metadata['knowledge_bases'] = [
                        kb_id for kb_id in file.metadata['knowledge_bases'] 
                        if kb_id != knowledge_base_id
                    ]
            
            # Delete knowledge base
            db.session.delete(knowledge_base)
            db.session.commit()
            
            return True
        
        except Exception as e:
            logging.error(f"Error deleting knowledge base: {str(e)}")
            return False
