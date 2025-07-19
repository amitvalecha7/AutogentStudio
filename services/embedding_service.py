import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app import db
from models import DocumentChunk, UploadedFile, KnowledgeBase
from services.openai_service import OpenAIService

class EmbeddingService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.local_model = None
    
    def get_local_model(self):
        """Load local embedding model if not already loaded"""
        if self.local_model is None:
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.local_model
    
    def create_embedding(self, text, model='openai'):
        """Create embedding for text using specified model"""
        if model == 'openai':
            result = self.openai_service.create_embedding(text)
            return result['embedding']
        elif model == 'sentence-transformers':
            model = self.get_local_model()
            embedding = model.encode([text])[0]
            return embedding.tolist()
        else:
            raise ValueError(f"Unsupported embedding model: {model}")
    
    def search_similar_chunks(self, query, knowledge_base_id=None, user_id=None, limit=10):
        """Search for similar document chunks using embeddings"""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query, model='openai')
            
            # Build query
            query_builder = db.session.query(DocumentChunk).join(UploadedFile)
            
            if user_id:
                query_builder = query_builder.filter(UploadedFile.user_id == user_id)
            
            if knowledge_base_id:
                query_builder = query_builder.filter(
                    UploadedFile.knowledge_base_id == knowledge_base_id
                )
            
            chunks = query_builder.all()
            
            if not chunks:
                return []
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    chunk_embedding = np.array(chunk.embedding)
                    query_embedding_np = np.array(query_embedding)
                    
                    # Reshape for cosine similarity
                    similarity = cosine_similarity(
                        query_embedding_np.reshape(1, -1),
                        chunk_embedding.reshape(1, -1)
                    )[0][0]
                    
                    similarities.append({
                        'chunk': chunk,
                        'similarity': float(similarity)
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            results = []
            for item in similarities[:limit]:
                chunk = item['chunk']
                results.append({
                    'id': chunk.id,
                    'content': chunk.content,
                    'similarity': item['similarity'],
                    'file_id': chunk.file_id,
                    'filename': chunk.file.original_filename,
                    'chunk_index': chunk.chunk_index,
                    'metadata': chunk.metadata
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Search error: {str(e)}")
    
    def hybrid_search(self, query, knowledge_base_id=None, user_id=None, limit=10):
        """Perform hybrid search combining semantic and keyword search"""
        # Get semantic results
        semantic_results = self.search_similar_chunks(
            query, knowledge_base_id, user_id, limit * 2
        )
        
        # Get keyword results (simple text search)
        query_builder = db.session.query(DocumentChunk).join(UploadedFile)
        
        if user_id:
            query_builder = query_builder.filter(UploadedFile.user_id == user_id)
        
        if knowledge_base_id:
            query_builder = query_builder.filter(
                UploadedFile.knowledge_base_id == knowledge_base_id
            )
        
        keyword_chunks = query_builder.filter(
            DocumentChunk.content.contains(query)
        ).limit(limit).all()
        
        keyword_results = []
        for chunk in keyword_chunks:
            keyword_results.append({
                'id': chunk.id,
                'content': chunk.content,
                'similarity': 0.5,  # Default keyword similarity
                'file_id': chunk.file_id,
                'filename': chunk.file.original_filename,
                'chunk_index': chunk.chunk_index,
                'metadata': chunk.metadata
            })
        
        # Combine and deduplicate results
        combined_results = {}
        
        # Add semantic results with higher weight
        for result in semantic_results:
            combined_results[result['id']] = result
        
        # Add keyword results
        for result in keyword_results:
            if result['id'] not in combined_results:
                combined_results[result['id']] = result
            else:
                # Boost similarity for items found in both searches
                combined_results[result['id']]['similarity'] += 0.2
        
        # Sort and limit
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return final_results[:limit]
