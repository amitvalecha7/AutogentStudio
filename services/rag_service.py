import os
import logging
import json
from typing import List, Dict, Any
from app import db
from models import File, FileChunk, KnowledgeBase, KnowledgeBaseFile
from services.openai_service import OpenAIService
import PyPDF2
import docx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RAGService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def process_file(self, file_record: File):
        """Process a file for RAG by creating chunks and embeddings"""
        try:
            content = self._extract_text_from_file(file_record)
            if not content:
                return
            
            chunks = self._create_chunks(content)
            
            for i, chunk_text in enumerate(chunks):
                # Create embedding
                embedding = self.openai_service.create_embedding(chunk_text)
                
                # Store chunk with embedding
                chunk = FileChunk(
                    file_id=file_record.id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=json.dumps(embedding),  # Store as JSON string
                    metadata={
                        'file_type': file_record.file_type,
                        'original_filename': file_record.original_filename,
                        'chunk_size': len(chunk_text)
                    }
                )
                
                db.session.add(chunk)
            
            # Update file as processed
            file_record.is_processed = True
            file_record.chunk_count = len(chunks)
            file_record.embedding_model = 'text-embedding-3-small'
            
            db.session.commit()
            logging.info(f"Processed file {file_record.filename} into {len(chunks)} chunks")
            
        except Exception as e:
            logging.error(f"Error processing file {file_record.filename}: {str(e)}")
            raise e
    
    def _extract_text_from_file(self, file_record: File) -> str:
        """Extract text content from various file types"""
        try:
            file_path = file_record.file_path
            
            if file_record.file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_record.file_type == 'pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                return text
            
            elif file_record.file_type in ['doc', 'docx']:
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            else:
                logging.warning(f"Unsupported file type: {file_record.file_type}")
                return ""
                
        except Exception as e:
            logging.error(f"Error extracting text from {file_record.filename}: {str(e)}")
            return ""
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
        
        return chunks
    
    def search(self, query: str, user_id: str, knowledge_base_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks using semantic similarity"""
        try:
            # Create embedding for query
            query_embedding = self.openai_service.create_embedding(query)
            
            # Build query to get chunks
            chunks_query = db.session.query(FileChunk).join(File).filter(File.user_id == user_id)
            
            if knowledge_base_id:
                chunks_query = chunks_query.join(KnowledgeBaseFile).filter(
                    KnowledgeBaseFile.knowledge_base_id == knowledge_base_id
                )
            
            chunks = chunks_query.all()
            
            if not chunks:
                return []
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                chunk_embedding = json.loads(chunk.embedding)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    [query_embedding], 
                    [chunk_embedding]
                )[0][0]
                
                results.append({
                    'chunk_id': chunk.id,
                    'file_id': chunk.file_id,
                    'content': chunk.content,
                    'similarity': float(similarity),
                    'metadata': chunk.metadata,
                    'filename': chunk.file.original_filename
                })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logging.error(f"Error searching chunks: {str(e)}")
            raise e
    
    def generate_rag_response(self, query: str, user_id: str, knowledge_base_id: str = None, 
                             model: str = "gpt-4o") -> Dict[str, Any]:
        """Generate a response using RAG (Retrieval-Augmented Generation)"""
        try:
            # Search for relevant context
            relevant_chunks = self.search(query, user_id, knowledge_base_id)
            
            if not relevant_chunks:
                return {
                    'response': "I don't have relevant information to answer your question based on your uploaded files.",
                    'sources': [],
                    'context_used': False
                }
            
            # Prepare context from top chunks
            context_texts = []
            sources = []
            
            for chunk in relevant_chunks[:3]:  # Use top 3 most relevant chunks
                context_texts.append(f"From {chunk['filename']}:\n{chunk['content']}")
                sources.append({
                    'filename': chunk['filename'],
                    'similarity': chunk['similarity'],
                    'chunk_id': chunk['chunk_id']
                })
            
            context = "\n\n".join(context_texts)
            
            # Create RAG prompt
            messages = [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant that answers questions based on the provided context from uploaded documents. Use only the information from the context to answer questions. If the context does not contain enough information to answer the question, say so clearly.'
                },
                {
                    'role': 'user',
                    'content': f"""Context from uploaded documents:
{context}

Question: {query}

Please answer the question based only on the provided context. If the context doesn't contain enough information, please say so."""
                }
            ]
            
            # Generate response
            response = self.openai_service.generate_response(
                messages=messages,
                model=model
            )
            
            return {
                'response': response,
                'sources': sources,
                'context_used': True,
                'total_chunks_found': len(relevant_chunks)
            }
            
        except Exception as e:
            logging.error(f"Error generating RAG response: {str(e)}")
            raise e
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Re-rank search results using more sophisticated methods"""
        # This is a placeholder for more advanced re-ranking algorithms
        # In a production system, you might use a separate re-ranking model
        return results
    
    def query_expansion(self, query: str) -> List[str]:
        """Expand query with related terms for better search"""
        try:
            expansion_prompt = f"""
Given the search query: "{query}"

Generate 3-5 related search terms or alternative phrasings that could help find relevant information. 
Return only the terms, one per line.
"""
            
            messages = [{'role': 'user', 'content': expansion_prompt}]
            response = self.openai_service.generate_response(messages=messages, model="gpt-4o")
            
            expanded_terms = [term.strip() for term in response.split('\n') if term.strip()]
            return [query] + expanded_terms
            
        except Exception as e:
            logging.error(f"Error expanding query: {str(e)}")
            return [query]
    
    def multi_hop_reasoning(self, query: str, user_id: str, knowledge_base_id: str = None) -> Dict[str, Any]:
        """Perform multi-hop reasoning across multiple document chunks"""
        try:
            # This is a simplified version of multi-hop reasoning
            # In practice, this would involve multiple search and reasoning steps
            
            initial_results = self.search(query, user_id, knowledge_base_id, top_k=10)
            
            if not initial_results:
                return self.generate_rag_response(query, user_id, knowledge_base_id)
            
            # Extract key concepts from initial results
            concept_extraction_prompt = f"""
Based on these search results for the query "{query}":

{chr(10).join([f"- {result['content'][:200]}..." for result in initial_results[:5]])}

What are the key concepts, entities, or topics that should be explored further to fully answer this query?
List them briefly, one per line.
"""
            
            messages = [{'role': 'user', 'content': concept_extraction_prompt}]
            concepts_response = self.openai_service.generate_response(messages=messages)
            
            concepts = [c.strip() for c in concepts_response.split('\n') if c.strip()]
            
            # Search for additional information about key concepts
            all_relevant_chunks = initial_results.copy()
            
            for concept in concepts[:3]:  # Limit to avoid too many API calls
                concept_results = self.search(concept, user_id, knowledge_base_id, top_k=3)
                for result in concept_results:
                    if result not in all_relevant_chunks:
                        all_relevant_chunks.append(result)
            
            # Generate final response with expanded context
            return self._generate_multi_hop_response(query, all_relevant_chunks)
            
        except Exception as e:
            logging.error(f"Error in multi-hop reasoning: {str(e)}")
            # Fallback to regular RAG
            return self.generate_rag_response(query, user_id, knowledge_base_id)
    
    def _generate_multi_hop_response(self, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using multi-hop reasoning results"""
        try:
            # Sort by similarity and take top chunks
            chunks.sort(key=lambda x: x['similarity'], reverse=True)
            top_chunks = chunks[:5]
            
            context_texts = []
            sources = []
            
            for chunk in top_chunks:
                context_texts.append(f"From {chunk['filename']}:\n{chunk['content']}")
                sources.append({
                    'filename': chunk['filename'],
                    'similarity': chunk['similarity'],
                    'chunk_id': chunk['chunk_id']
                })
            
            context = "\n\n".join(context_texts)
            
            messages = [
                {
                    'role': 'system',
                    'content': 'You are an expert at synthesizing information from multiple sources to provide comprehensive answers. Use the provided context to give a thorough, well-reasoned response that connects information across different sources when relevant.'
                },
                {
                    'role': 'user',
                    'content': f"""Context from multiple sources:
{context}

Question: {query}

Please provide a comprehensive answer that synthesizes information from the provided sources. Make connections between different pieces of information when relevant."""
                }
            ]
            
            response = self.openai_service.generate_response(
                messages=messages,
                model="gpt-4o"
            )
            
            return {
                'response': response,
                'sources': sources,
                'context_used': True,
                'multi_hop': True,
                'total_chunks_found': len(chunks)
            }
            
        except Exception as e:
            logging.error(f"Error generating multi-hop response: {str(e)}")
            raise e
