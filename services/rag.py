import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from app import db
from models import File, FileEmbedding, KnowledgeBase, KnowledgeBaseFile
from .embeddings import EmbeddingService
from .openai_service import OpenAIService
from .anthropic_service import AnthropicService
from sqlalchemy import text

class RAGService:
    def __init__(self):
        """Initialize RAG service with advanced capabilities"""
        self.embedding_service = EmbeddingService(provider="openai")
        self.openai_service = OpenAIService()
        self.anthropic_service = AnthropicService()
        
        # Advanced RAG parameters
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_context_length = 8000
        self.similarity_threshold = 0.7
        self.reranking_enabled = True
        self.query_expansion_enabled = True
        self.multi_hop_enabled = True

    def search(self, query: str, user_id: int, knowledge_base_id: Optional[int] = None, 
               top_k: int = 5, rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Advanced RAG search with multiple enhancement techniques
        
        Args:
            query: Search query
            user_id: User ID
            knowledge_base_id: Optional knowledge base filter
            top_k: Number of results to return
            rerank: Whether to apply reranking
            
        Returns:
            List of search results with enhanced relevance
        """
        try:
            # Query expansion
            if self.query_expansion_enabled:
                expanded_queries = self._expand_query(query)
            else:
                expanded_queries = [query]
            
            all_results = []
            
            # Search with expanded queries
            for expanded_query in expanded_queries:
                # Get query embedding
                query_embedding = self.embedding_service.get_embedding(expanded_query)
                
                # Build search query
                search_query = self._build_search_query(user_id, knowledge_base_id)
                
                # Execute vector search
                results = db.session.execute(search_query).fetchall()
                
                # Calculate similarities
                candidates = []
                for result in results:
                    embedding_vector = json.loads(result.embedding_vector)
                    similarity = self.embedding_service.compute_similarity(
                        query_embedding, embedding_vector
                    )
                    
                    if similarity >= self.similarity_threshold:
                        candidates.append({
                            'file_id': result.file_id,
                            'filename': result.filename,
                            'chunk_text': result.chunk_text,
                            'chunk_index': result.chunk_index,
                            'similarity': similarity,
                            'query': expanded_query
                        })
                
                all_results.extend(candidates)
            
            # Remove duplicates and sort by similarity
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Apply reranking if enabled
            if rerank and self.reranking_enabled:
                unique_results = self._rerank_results(query, unique_results)
            
            # Multi-hop reasoning if enabled
            if self.multi_hop_enabled and len(unique_results) > 0:
                unique_results = self._apply_multi_hop_reasoning(query, unique_results)
            
            return unique_results[:top_k]
            
        except Exception as e:
            current_app.logger.error(f"RAG search failed: {str(e)}")
            return []

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]], 
                       model: str = "gpt-4o") -> Dict[str, Any]:
        """
        Generate answer using RAG with context
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            model: AI model to use
            
        Returns:
            Generated answer with citations
        """
        try:
            # Prepare context
            context = self._prepare_context(context_chunks)
            
            # Create RAG prompt
            prompt = self._create_rag_prompt(query, context)
            
            # Generate answer
            if model.startswith('gpt-'):
                answer = self.openai_service.chat_completion([
                    {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately. Always cite your sources using [Source: filename] format."},
                    {"role": "user", "content": prompt}
                ], model=model)
            elif model.startswith('claude-'):
                answer = self.anthropic_service.chat_completion([
                    {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately. Always cite your sources using [Source: filename] format."},
                    {"role": "user", "content": prompt}
                ], model=model)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            # Extract citations
            citations = self._extract_citations(answer, context_chunks)
            
            return {
                'answer': answer,
                'citations': citations,
                'context_used': len(context_chunks),
                'model': model
            }
            
        except Exception as e:
            current_app.logger.error(f"RAG answer generation failed: {str(e)}")
            return {
                'answer': f"I apologize, but I encountered an error while generating the answer: {str(e)}",
                'citations': [],
                'context_used': 0,
                'model': model
            }

    def hybrid_search(self, query: str, user_id: int, knowledge_base_id: Optional[int] = None,
                     alpha: float = 0.7, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and keyword search
        
        Args:
            query: Search query
            user_id: User ID
            knowledge_base_id: Optional knowledge base filter
            alpha: Weight for vector search (1-alpha for keyword search)
            top_k: Number of results to return
            
        Returns:
            Hybrid search results
        """
        try:
            # Vector search results
            vector_results = self.search(query, user_id, knowledge_base_id, top_k * 2, rerank=False)
            
            # Keyword search results
            keyword_results = self._keyword_search(query, user_id, knowledge_base_id, top_k * 2)
            
            # Combine and rerank
            hybrid_results = self._combine_search_results(
                vector_results, keyword_results, alpha
            )
            
            return hybrid_results[:top_k]
            
        except Exception as e:
            current_app.logger.error(f"Hybrid search failed: {str(e)}")
            return []

    def _expand_query(self, query: str) -> List[str]:
        """Expand query using semantic variations"""
        try:
            expansion_prompt = f"""Generate 2-3 semantically similar variations of this query that could help find relevant information:

Original query: "{query}"

Provide variations that:
1. Use synonyms and related terms
2. Rephrase the question differently
3. Include domain-specific terminology

Return only the variations, one per line."""

            expanded = self.openai_service.chat_completion([
                {"role": "user", "content": expansion_prompt}
            ])
            
            variations = [line.strip() for line in expanded.split('\n') if line.strip()]
            return [query] + variations[:3]  # Original + up to 3 variations
            
        except Exception as e:
            current_app.logger.error(f"Query expansion failed: {str(e)}")
            return [query]

    def _build_search_query(self, user_id: int, knowledge_base_id: Optional[int] = None):
        """Build SQL query for vector search"""
        base_query = """
        SELECT fe.file_id, f.filename, fe.chunk_text, fe.chunk_index, fe.embedding_vector
        FROM file_embedding fe
        JOIN file f ON fe.file_id = f.id
        WHERE f.user_id = :user_id
        """
        
        if knowledge_base_id:
            base_query += """
            AND fe.file_id IN (
                SELECT kbf.file_id FROM knowledge_base_file kbf
                WHERE kbf.knowledge_base_id = :knowledge_base_id
            )
            """
        
        return text(base_query).bindparam(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id
        )

    def _keyword_search(self, query: str, user_id: int, knowledge_base_id: Optional[int] = None,
                       top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        try:
            # Simple keyword search using SQL LIKE
            search_query = """
            SELECT fe.file_id, f.filename, fe.chunk_text, fe.chunk_index,
                   ts_rank(to_tsvector('english', fe.chunk_text), plainto_tsquery('english', :query)) as rank
            FROM file_embedding fe
            JOIN file f ON fe.file_id = f.id
            WHERE f.user_id = :user_id
            AND to_tsvector('english', fe.chunk_text) @@ plainto_tsquery('english', :query)
            """
            
            if knowledge_base_id:
                search_query += """
                AND fe.file_id IN (
                    SELECT kbf.file_id FROM knowledge_base_file kbf
                    WHERE kbf.knowledge_base_id = :knowledge_base_id
                )
                """
            
            search_query += " ORDER BY rank DESC LIMIT :limit"
            
            results = db.session.execute(
                text(search_query),
                {
                    'query': query,
                    'user_id': user_id,
                    'knowledge_base_id': knowledge_base_id,
                    'limit': top_k
                }
            ).fetchall()
            
            return [
                {
                    'file_id': result.file_id,
                    'filename': result.filename,
                    'chunk_text': result.chunk_text,
                    'chunk_index': result.chunk_index,
                    'similarity': result.rank,
                    'search_type': 'keyword'
                }
                for result in results
            ]
            
        except Exception as e:
            current_app.logger.error(f"Keyword search failed: {str(e)}")
            return []

    def _combine_search_results(self, vector_results: List[Dict], keyword_results: List[Dict],
                               alpha: float) -> List[Dict]:
        """Combine vector and keyword search results"""
        combined = {}
        
        # Add vector results
        for result in vector_results:
            key = (result['file_id'], result['chunk_index'])
            combined[key] = result.copy()
            combined[key]['combined_score'] = alpha * result['similarity']
        
        # Add keyword results
        for result in keyword_results:
            key = (result['file_id'], result['chunk_index'])
            if key in combined:
                combined[key]['combined_score'] += (1 - alpha) * result['similarity']
            else:
                combined[key] = result.copy()
                combined[key]['combined_score'] = (1 - alpha) * result['similarity']
        
        # Sort by combined score
        sorted_results = sorted(combined.values(), key=lambda x: x['combined_score'], reverse=True)
        return sorted_results

    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank results using cross-encoder or LLM"""
        try:
            # Use LLM-based reranking
            rerank_prompt = f"""Given this query: "{query}"

Rank the following text chunks from most relevant (1) to least relevant based on how well they answer the query.

Chunks:
"""
            
            for i, result in enumerate(results[:10]):  # Limit to top 10 for reranking
                rerank_prompt += f"\n{i+1}. {result['chunk_text'][:200]}..."
            
            rerank_prompt += "\n\nProvide only the ranking as numbers separated by commas (e.g., 3,1,5,2,4):"
            
            ranking_response = self.openai_service.chat_completion([
                {"role": "user", "content": rerank_prompt}
            ])
            
            # Parse ranking
            try:
                ranking = [int(x.strip()) - 1 for x in ranking_response.split(',')]
                reranked_results = [results[i] for i in ranking if i < len(results)]
                return reranked_results + results[len(reranked_results):]
            except:
                return results
            
        except Exception as e:
            current_app.logger.error(f"Reranking failed: {str(e)}")
            return results

    def _apply_multi_hop_reasoning(self, query: str, results: List[Dict]) -> List[Dict]:
        """Apply multi-hop reasoning to enhance results"""
        try:
            # Extract key entities and concepts from query
            entity_prompt = f"""Extract the main entities, concepts, and relationships from this query: "{query}"

Provide:
1. Key entities (people, places, things)
2. Main concepts (ideas, processes, methods)
3. Relationships (how entities connect)

Format as JSON with keys: entities, concepts, relationships"""

            entities_response = self.openai_service.chat_completion([
                {"role": "user", "content": entity_prompt}
            ])
            
            # Use entities to find additional relevant chunks
            try:
                entities_data = json.loads(entities_response)
                additional_queries = entities_data.get('entities', []) + entities_data.get('concepts', [])
                
                # Search for additional context
                for additional_query in additional_queries[:3]:  # Limit additional searches
                    additional_results = self.search(additional_query, 
                                                   results[0]['file_id'] if results else 0, 
                                                   None, 3, rerank=False)
                    
                    # Add unique results
                    for add_result in additional_results:
                        if not any(r['chunk_text'] == add_result['chunk_text'] for r in results):
                            add_result['multi_hop'] = True
                            results.append(add_result)
                
            except json.JSONDecodeError:
                pass
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Multi-hop reasoning failed: {str(e)}")
            return results

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result['file_id'], result['chunk_index'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results

    def _prepare_context(self, context_chunks: List[Dict]) -> str:
        """Prepare context string from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(context_chunks):
            context_parts.append(f"[Source {i+1}: {chunk['filename']}]\n{chunk['chunk_text']}\n")
        
        return "\n".join(context_parts)

    def _create_rag_prompt(self, query: str, context: str) -> str:
        """Create RAG prompt with context"""
        return f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {query}

Answer:"""

    def _extract_citations(self, answer: str, context_chunks: List[Dict]) -> List[Dict]:
        """Extract citations from answer"""
        citations = []
        
        for i, chunk in enumerate(context_chunks):
            if f"Source {i+1}" in answer or chunk['filename'] in answer:
                citations.append({
                    'filename': chunk['filename'],
                    'chunk_text': chunk['chunk_text'][:100] + "...",
                    'file_id': chunk['file_id']
                })
        
        return citations

    def get_conversation_context(self, conversation_history: List[Dict], user_id: int,
                               knowledge_base_id: Optional[int] = None) -> List[Dict]:
        """Get relevant context for conversation"""
        try:
            # Extract queries from conversation
            queries = []
            for msg in conversation_history[-5:]:  # Last 5 messages
                if msg['role'] == 'user':
                    queries.append(msg['content'])
            
            # Search for relevant context
            all_results = []
            for query in queries:
                results = self.search(query, user_id, knowledge_base_id, 3)
                all_results.extend(results)
            
            # Deduplicate and return
            return self._deduplicate_results(all_results)
            
        except Exception as e:
            current_app.logger.error(f"Conversation context retrieval failed: {str(e)}")
            return []

    def summarize_document(self, file_id: int, user_id: int) -> Dict[str, Any]:
        """Summarize a document using RAG"""
        try:
            # Get all chunks for the document
            chunks = FileEmbedding.query.join(File).filter(
                File.id == file_id,
                File.user_id == user_id
            ).order_by(FileEmbedding.chunk_index).all()
            
            if not chunks:
                return {'error': 'Document not found'}
            
            # Combine chunks
            full_text = ' '.join([chunk.chunk_text for chunk in chunks])
            
            # Generate summary
            summary_prompt = f"""Please provide a comprehensive summary of the following document:

{full_text[:self.max_context_length]}

Include:
1. Main topics and themes
2. Key findings or conclusions
3. Important details
4. Overall structure and organization

Summary:"""

            summary = self.openai_service.chat_completion([
                {"role": "user", "content": summary_prompt}
            ])
            
            return {
                'summary': summary,
                'chunk_count': len(chunks),
                'filename': chunks[0].file.filename
            }
            
        except Exception as e:
            current_app.logger.error(f"Document summarization failed: {str(e)}")
            return {'error': str(e)}
