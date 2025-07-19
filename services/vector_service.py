import os
import numpy as np
from typing import List, Dict, Any
from models import FileEmbedding, KnowledgeBase, File, db
from services.ai_service import AIService
import uuid
from sqlalchemy import text

class VectorService:
    def __init__(self):
        self.ai_service = AIService()
        self.embedding_model = "text-embedding-3-small"  # OpenAI's latest embedding model
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def create_embeddings(self, text_chunks: List[str], model: str = None) -> List[List[float]]:
        """Create embeddings for text chunks"""
        if not model:
            model = self.embedding_model
        
        embeddings = []
        for chunk in text_chunks:
            if chunk.strip():  # Only process non-empty chunks
                embedding = self.ai_service.get_embedding(chunk, model)
                embeddings.append(embedding)
            else:
                embeddings.append([0.0] * 1536)  # Default embedding dimension
        
        return embeddings
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks with overlap"""
        if not chunk_size:
            chunk_size = self.chunk_size
        if not overlap:
            overlap = self.chunk_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                last_period = text.rfind('.', start, end)
                last_exclamation = text.rfind('!', start, end)
                last_question = text.rfind('?', start, end)
                
                sentence_end = max(last_period, last_exclamation, last_question)
                
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end - overlap > start else end
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def add_file_to_knowledge_base(self, file: File, knowledge_base: KnowledgeBase):
        """Add file embeddings to knowledge base"""
        try:
            # Read file content (this would be expanded for different file types)
            with open(file.storage_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Chunk the text
            chunks = self.chunk_text(content)
            
            # Create embeddings
            embeddings = self.create_embeddings(chunks)
            
            # Store embeddings in database
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                file_embedding = FileEmbedding(
                    id=str(uuid.uuid4()),
                    file_id=file.id,
                    knowledge_base_id=knowledge_base.id,
                    chunk_text=chunk,
                    chunk_index=i,
                    embedding_model=self.embedding_model,
                    embedding_vector=embedding,
                    metadata={
                        'chunk_size': len(chunk),
                        'file_name': file.original_filename,
                        'file_type': file.file_type
                    }
                )
                
                db.session.add(file_embedding)
            
            # Update knowledge base stats
            knowledge_base.total_chunks += len(chunks)
            if file.id not in [f.id for f in knowledge_base.embeddings]:
                knowledge_base.file_count += 1
            
            db.session.commit()
            
            # Mark file as processed
            file.is_processed = True
            file.processing_status = 'completed'
            db.session.commit()
            
            return {
                'success': True,
                'chunks_created': len(chunks),
                'embeddings_created': len(embeddings)
            }
            
        except Exception as e:
            db.session.rollback()
            file.processing_status = 'failed'
            file.metadata = {'error': str(e)}
            db.session.commit()
            raise Exception(f"Failed to add file to knowledge base: {str(e)}")
    
    def search_knowledge_base(self, knowledge_base: KnowledgeBase, query: str, 
                             limit: int = 5, similarity_threshold: float = 0.7) -> List[Dict]:
        """Search knowledge base using vector similarity"""
        try:
            # Get query embedding
            query_embedding = self.ai_service.get_embedding(query)
            
            # Convert to string format for PostgreSQL
            query_vector_str = str(query_embedding).replace('[', '{').replace(']', '}')
            
            # Use pgvector similarity search
            # This requires pgvector extension to be installed
            sql_query = text("""
                SELECT 
                    fe.id,
                    fe.chunk_text,
                    fe.chunk_index,
                    fe.metadata,
                    f.original_filename,
                    f.file_type,
                    (fe.embedding_vector <=> :query_vector) as distance
                FROM file_embeddings fe
                JOIN files f ON fe.file_id = f.id
                WHERE fe.knowledge_base_id = :kb_id
                ORDER BY fe.embedding_vector <=> :query_vector
                LIMIT :limit
            """)
            
            results = db.session.execute(sql_query, {
                'query_vector': query_vector_str,
                'kb_id': knowledge_base.id,
                'limit': limit
            }).fetchall()
            
            # Filter by similarity threshold (distance = 1 - cosine_similarity)
            filtered_results = []
            for result in results:
                similarity = 1 - result.distance
                if similarity >= similarity_threshold:
                    filtered_results.append({
                        'id': result.id,
                        'text': result.chunk_text,
                        'chunk_index': result.chunk_index,
                        'filename': result.original_filename,
                        'file_type': result.file_type,
                        'similarity': similarity,
                        'metadata': result.metadata
                    })
            
            return filtered_results
            
        except Exception as e:
            # Fallback to simple text search if vector search fails
            return self._fallback_text_search(knowledge_base, query, limit)
    
    def _fallback_text_search(self, knowledge_base: KnowledgeBase, query: str, limit: int) -> List[Dict]:
        """Fallback text search when vector search is unavailable"""
        try:
            # Simple text matching
            embeddings = FileEmbedding.query.filter(
                FileEmbedding.knowledge_base_id == knowledge_base.id,
                FileEmbedding.chunk_text.ilike(f'%{query}%')
            ).join(File).limit(limit).all()
            
            results = []
            for embedding in embeddings:
                results.append({
                    'id': embedding.id,
                    'text': embedding.chunk_text,
                    'chunk_index': embedding.chunk_index,
                    'filename': embedding.file.original_filename,
                    'file_type': embedding.file.file_type,
                    'similarity': 0.5,  # Default similarity for text search
                    'metadata': embedding.metadata
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Text search failed: {str(e)}")
    
    def get_relevant_context(self, knowledge_base: KnowledgeBase, query: str, 
                           max_tokens: int = 4000) -> str:
        """Get relevant context for RAG (Retrieval-Augmented Generation)"""
        search_results = self.search_knowledge_base(knowledge_base, query)
        
        context_parts = []
        current_tokens = 0
        
        for result in search_results:
            # Rough token estimation (1 token ≈ 4 characters)
            estimated_tokens = len(result['text']) // 4
            
            if current_tokens + estimated_tokens > max_tokens:
                break
            
            context_parts.append(
                f"[{result['filename']}] {result['text']}"
            )
            current_tokens += estimated_tokens
        
        return "\n\n".join(context_parts)
    
    def hybrid_search(self, knowledge_base: KnowledgeBase, query: str, 
                     alpha: float = 0.7) -> List[Dict]:
        """Combine vector search with keyword search"""
        # Vector search
        vector_results = self.search_knowledge_base(knowledge_base, query)
        
        # Keyword search
        keyword_results = self._fallback_text_search(knowledge_base, query, 10)
        
        # Combine and re-rank results
        combined_results = {}
        
        # Add vector results with vector weight
        for result in vector_results:
            result_id = result['id']
            combined_results[result_id] = result.copy()
            combined_results[result_id]['combined_score'] = alpha * result['similarity']
        
        # Add keyword results with keyword weight
        for result in keyword_results:
            result_id = result['id']
            if result_id in combined_results:
                # Boost existing result
                combined_results[result_id]['combined_score'] += (1 - alpha) * 0.8
            else:
                # New result from keyword search
                combined_results[result_id] = result.copy()
                combined_results[result_id]['combined_score'] = (1 - alpha) * 0.6
        
        # Sort by combined score
        final_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return final_results[:10]  # Return top 10
    
    def rerank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Re-rank search results using advanced techniques"""
        # This could be expanded with more sophisticated re-ranking
        # For now, we'll use a simple scoring approach
        
        for result in results:
            # Calculate additional scoring factors
            text = result['text'].lower()
            query_lower = query.lower()
            
            # Keyword density score
            keywords = query_lower.split()
            keyword_count = sum(text.count(keyword) for keyword in keywords)
            keyword_density = keyword_count / len(text.split()) if text.split() else 0
            
            # Position score (earlier chunks might be more relevant)
            position_score = 1 / (1 + result['chunk_index'] * 0.1)
            
            # File type score (some file types might be more relevant)
            type_score = 1.0
            if result['file_type'] in ['pdf', 'docx', 'txt']:
                type_score = 1.2
            
            # Combine scores
            original_similarity = result.get('similarity', 0.5)
            result['reranked_score'] = (
                original_similarity * 0.6 +
                keyword_density * 0.2 +
                position_score * 0.1 +
                type_score * 0.1
            )
        
        # Sort by reranked score
        return sorted(results, key=lambda x: x.get('reranked_score', 0), reverse=True)
    
    def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        try:
            # Use AI to expand the query
            expansion_prompt = f"""
            Expand the following query with related terms, synonyms, and variations that would help find relevant information:
            
            Query: "{query}"
            
            Provide 5-10 related search terms, separated by commas:
            """
            
            response = self.ai_service.chat_completion(
                messages=[{'role': 'user', 'content': expansion_prompt}],
                provider='openai',
                model='gpt-4o-mini',  # Use faster model for query expansion
                settings={'temperature': 0.3, 'max_tokens': 200}
            )
            
            # Parse the response to extract terms
            expanded_terms = [term.strip() for term in response['content'].split(',')]
            return [query] + expanded_terms[:10]  # Include original query + expansions
            
        except:
            # Fallback to original query
            return [query]
    
    def multi_hop_reasoning(self, knowledge_base: KnowledgeBase, query: str, 
                           max_hops: int = 3) -> List[Dict]:
        """Perform multi-hop reasoning across knowledge base"""
        all_results = []
        current_query = query
        
        for hop in range(max_hops):
            # Search with current query
            results = self.search_knowledge_base(knowledge_base, current_query, limit=3)
            
            if not results:
                break
            
            # Add hop information to results
            for result in results:
                result['hop'] = hop + 1
                result['reasoning_chain'] = current_query
            
            all_results.extend(results)
            
            # Generate next query based on results
            if hop < max_hops - 1:
                context = ' '.join([r['text'][:200] for r in results])
                next_query_prompt = f"""
                Based on the following context, what would be a good follow-up question to get more information related to: "{query}"?
                
                Context: {context}
                
                Provide a single follow-up question:
                """
                
                try:
                    response = self.ai_service.chat_completion(
                        messages=[{'role': 'user', 'content': next_query_prompt}],
                        provider='openai',
                        model='gpt-4o-mini',
                        settings={'temperature': 0.5, 'max_tokens': 100}
                    )
                    current_query = response['content'].strip()
                except:
                    break  # Stop if query generation fails
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            if result['id'] not in unique_results:
                unique_results[result['id']] = result
        
        return list(unique_results.values())
    
    def get_embedding_stats(self, knowledge_base: KnowledgeBase) -> Dict:
        """Get statistics about embeddings in knowledge base"""
        try:
            total_embeddings = FileEmbedding.query.filter_by(
                knowledge_base_id=knowledge_base.id
            ).count()
            
            # Get embedding models used
            models = db.session.query(FileEmbedding.embedding_model).filter_by(
                knowledge_base_id=knowledge_base.id
            ).distinct().all()
            
            # Get file types
            file_types = db.session.query(File.file_type).join(FileEmbedding).filter(
                FileEmbedding.knowledge_base_id == knowledge_base.id
            ).distinct().all()
            
            return {
                'total_embeddings': total_embeddings,
                'embedding_models': [model[0] for model in models],
                'file_types': [ft[0] for ft in file_types],
                'total_files': knowledge_base.file_count,
                'total_chunks': knowledge_base.total_chunks
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_embeddings': 0,
                'embedding_models': [],
                'file_types': [],
                'total_files': 0,
                'total_chunks': 0
            }
