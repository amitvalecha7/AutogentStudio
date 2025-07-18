import os
import logging
import numpy as np
from services.openai_service import OpenAIService
from app import db
from models import FileChunk, File

class VectorService:
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def create_embedding(self, text):
        """Create embedding for text using OpenAI"""
        try:
            result = self.openai_service.create_embedding(text)
            # Convert to numpy array and then to bytes for storage
            embedding_array = np.array(result['embedding'], dtype=np.float32)
            return embedding_array.tobytes()
        except Exception as e:
            logging.error(f"Error creating embedding: {str(e)}")
            raise
    
    def search_similar_chunks(self, query_embedding, user_id, limit=10):
        """Search for similar chunks using cosine similarity"""
        try:
            # Convert query embedding to numpy array
            query_array = np.frombuffer(query_embedding, dtype=np.float32)
            
            # Get all chunks for user's files
            chunks = db.session.query(FileChunk).join(File).filter(
                File.user_id == user_id,
                FileChunk.embedding.isnot(None)
            ).all()
            
            similarities = []
            for chunk in chunks:
                # Convert stored embedding to numpy array
                chunk_array = np.frombuffer(chunk.embedding, dtype=np.float32)
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_array, chunk_array)
                similarities.append((chunk, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]
        
        except Exception as e:
            logging.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norms = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return dot_product / norms if norms > 0 else 0
    
    def get_context_for_query(self, query, user_id, max_context_length=4000):
        """Get relevant context for a query from user's files"""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            
            # Search for similar chunks
            similar_chunks = self.search_similar_chunks(query_embedding, user_id)
            
            # Combine chunks into context
            context = ""
            for chunk, similarity in similar_chunks:
                if len(context) + len(chunk.content) > max_context_length:
                    break
                context += chunk.content + "\n\n"
            
            return context.strip()
        
        except Exception as e:
            logging.error(f"Error getting context for query: {str(e)}")
            return ""
