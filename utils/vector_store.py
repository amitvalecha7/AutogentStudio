import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from services.embedding_service import EmbeddingService
from models import FileEmbedding, KnowledgeBaseFile
from app import db

class VectorStore:
    def __init__(self, embedding_provider="openai"):
        self.embedding_service = EmbeddingService(provider=embedding_provider)
        self.dimension = self.embedding_service.get_embedding_dimension()
    
    def add_embeddings(self, file_id: int, text_chunks: List[str]) -> bool:
        """Add embeddings for text chunks to the vector store"""
        try:
            # Generate embeddings for all chunks
            embeddings = self.embedding_service.generate_embeddings_batch(text_chunks)
            
            if not embeddings:
                logging.error("Failed to generate embeddings")
                return False
            
            # Store embeddings in database
            for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                file_embedding = FileEmbedding(
                    file_id=file_id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=json.dumps(embedding)
                )
                db.session.add(file_embedding)
            
            db.session.commit()
            logging.info(f"Added {len(embeddings)} embeddings for file {file_id}")
            return True
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding embeddings: {str(e)}")
            return False
    
    def semantic_search(self, knowledge_base_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search in a knowledge base"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_query_embedding(query)
            
            if not query_embedding:
                logging.error("Failed to generate query embedding")
                return []
            
            # Get file IDs for this knowledge base
            kb_files = KnowledgeBaseFile.query.filter_by(knowledge_base_id=knowledge_base_id).all()
            file_ids = [kbf.file_id for kbf in kb_files]
            
            if not file_ids:
                return []
            
            # Get all embeddings for files in this knowledge base
            embeddings = FileEmbedding.query.filter(FileEmbedding.file_id.in_(file_ids)).all()
            
            # Calculate similarities
            results = []
            for embedding_record in embeddings:
                try:
                    stored_embedding = json.loads(embedding_record.embedding)
                    similarity = self.embedding_service.cosine_similarity(query_embedding, stored_embedding)
                    
                    results.append({
                        'id': embedding_record.id,
                        'file_id': embedding_record.file_id,
                        'chunk_index': embedding_record.chunk_index,
                        'text': embedding_record.chunk_text,
                        'similarity': similarity,
                        'score': similarity * 100  # Convert to percentage
                    })
                except (json.JSONDecodeError, TypeError) as e:
                    logging.warning(f"Invalid embedding data for record {embedding_record.id}: {str(e)}")
                    continue
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
        
        except Exception as e:
            logging.error(f"Error in semantic search: {str(e)}")
            return []
    
    def hybrid_search(self, knowledge_base_id: int, query: str, 
                     semantic_weight: float = 0.7, 
                     keyword_weight: float = 0.3, 
                     limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search"""
        try:
            # Get semantic search results
            semantic_results = self.semantic_search(knowledge_base_id, query, limit * 2)
            
            # Get keyword search results
            keyword_results = self.keyword_search(knowledge_base_id, query, limit * 2)
            
            # Combine and re-rank results
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )
            
            return combined_results[:limit]
        
        except Exception as e:
            logging.error(f"Error in hybrid search: {str(e)}")
            return []
    
    def keyword_search(self, knowledge_base_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        try:
            # Get file IDs for this knowledge base
            kb_files = KnowledgeBaseFile.query.filter_by(knowledge_base_id=knowledge_base_id).all()
            file_ids = [kbf.file_id for kbf in kb_files]
            
            if not file_ids:
                return []
            
            # Simple keyword search using SQL LIKE
            query_terms = query.lower().split()
            embeddings = FileEmbedding.query.filter(FileEmbedding.file_id.in_(file_ids)).all()
            
            results = []
            for embedding_record in embeddings:
                text_lower = embedding_record.chunk_text.lower()
                score = 0
                
                # Count keyword matches
                for term in query_terms:
                    if term in text_lower:
                        score += text_lower.count(term)
                
                if score > 0:
                    results.append({
                        'id': embedding_record.id,
                        'file_id': embedding_record.file_id,
                        'chunk_index': embedding_record.chunk_index,
                        'text': embedding_record.chunk_text,
                        'score': score,
                        'keyword_matches': score
                    })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
        
        except Exception as e:
            logging.error(f"Error in keyword search: {str(e)}")
            return []
    
    def _combine_search_results(self, semantic_results: List[Dict], keyword_results: List[Dict], 
                               semantic_weight: float, keyword_weight: float) -> List[Dict[str, Any]]:
        """Combine and re-rank semantic and keyword search results"""
        try:
            # Create a dictionary to combine results by chunk ID
            combined = {}
            
            # Add semantic results
            for result in semantic_results:
                chunk_id = result['id']
                combined[chunk_id] = result.copy()
                combined[chunk_id]['semantic_score'] = result['similarity']
                combined[chunk_id]['keyword_score'] = 0
            
            # Add keyword results
            for result in keyword_results:
                chunk_id = result['id']
                if chunk_id in combined:
                    combined[chunk_id]['keyword_score'] = result['score']
                else:
                    combined[chunk_id] = result.copy()
                    combined[chunk_id]['semantic_score'] = 0
                    combined[chunk_id]['keyword_score'] = result['score']
            
            # Calculate combined scores
            max_semantic = max((r.get('semantic_score', 0) for r in combined.values()), default=1)
            max_keyword = max((r.get('keyword_score', 0) for r in combined.values()), default=1)
            
            for result in combined.values():
                semantic_norm = result.get('semantic_score', 0) / max_semantic
                keyword_norm = result.get('keyword_score', 0) / max_keyword
                
                result['combined_score'] = (
                    semantic_weight * semantic_norm + 
                    keyword_weight * keyword_norm
                )
            
            # Convert back to list and sort
            results_list = list(combined.values())
            results_list.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return results_list
        
        except Exception as e:
            logging.error(f"Error combining search results: {str(e)}")
            return semantic_results  # Fallback to semantic results
    
    def get_similar_chunks(self, file_id: int, chunk_index: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get chunks similar to a specific chunk"""
        try:
            # Get the reference chunk
            reference_chunk = FileEmbedding.query.filter_by(
                file_id=file_id, 
                chunk_index=chunk_index
            ).first()
            
            if not reference_chunk:
                return []
            
            reference_embedding = json.loads(reference_chunk.embedding)
            
            # Get all other embeddings
            other_embeddings = FileEmbedding.query.filter(
                (FileEmbedding.file_id != file_id) | 
                (FileEmbedding.chunk_index != chunk_index)
            ).all()
            
            # Calculate similarities
            results = []
            for embedding_record in other_embeddings:
                try:
                    stored_embedding = json.loads(embedding_record.embedding)
                    similarity = self.embedding_service.cosine_similarity(reference_embedding, stored_embedding)
                    
                    results.append({
                        'id': embedding_record.id,
                        'file_id': embedding_record.file_id,
                        'chunk_index': embedding_record.chunk_index,
                        'text': embedding_record.chunk_text,
                        'similarity': similarity
                    })
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
        
        except Exception as e:
            logging.error(f"Error getting similar chunks: {str(e)}")
            return []
    
    def update_embeddings(self, file_id: int, new_text_chunks: List[str]) -> bool:
        """Update embeddings for a file"""
        try:
            # Delete existing embeddings
            FileEmbedding.query.filter_by(file_id=file_id).delete()
            
            # Add new embeddings
            success = self.add_embeddings(file_id, new_text_chunks)
            
            if success:
                logging.info(f"Updated embeddings for file {file_id}")
            
            return success
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating embeddings: {str(e)}")
            return False
    
    def delete_embeddings(self, file_id: int) -> bool:
        """Delete all embeddings for a file"""
        try:
            FileEmbedding.query.filter_by(file_id=file_id).delete()
            db.session.commit()
            logging.info(f"Deleted embeddings for file {file_id}")
            return True
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting embeddings: {str(e)}")
            return False
    
    def get_embedding_stats(self, knowledge_base_id: int = None) -> Dict[str, Any]:
        """Get statistics about embeddings"""
        try:
            query = FileEmbedding.query
            
            if knowledge_base_id:
                # Filter by knowledge base
                kb_files = KnowledgeBaseFile.query.filter_by(knowledge_base_id=knowledge_base_id).all()
                file_ids = [kbf.file_id for kbf in kb_files]
                query = query.filter(FileEmbedding.file_id.in_(file_ids))
            
            total_embeddings = query.count()
            unique_files = query.with_entities(FileEmbedding.file_id).distinct().count()
            
            # Calculate average chunk length
            avg_chunk_length = 0
            if total_embeddings > 0:
                chunk_lengths = [len(e.chunk_text) for e in query.limit(1000).all()]
                avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            
            stats = {
                'total_embeddings': total_embeddings,
                'unique_files': unique_files,
                'avg_chunk_length': round(avg_chunk_length, 2),
                'embedding_dimension': self.dimension,
                'provider': self.embedding_service.provider
            }
            
            return stats
        
        except Exception as e:
            logging.error(f"Error getting embedding stats: {str(e)}")
            return {}
