import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from collections import defaultdict

class RAGUtils:
    """Utility functions for Retrieval-Augmented Generation (RAG)"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_chunks_per_query = 10
        
    def advanced_text_chunking(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Advanced text chunking with semantic awareness
        """
        try:
            chunk_size = chunk_size or self.chunk_size
            overlap = overlap or self.chunk_overlap
            
            if not text:
                return []
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Split into sentences first
            sentences = self._split_into_sentences(text)
            
            chunks = []
            current_chunk = ""
            current_chunk_sentences = []
            
            for sentence in sentences:
                # Check if adding this sentence would exceed chunk size
                if len(current_chunk + sentence) > chunk_size and current_chunk:
                    # Create chunk
                    chunk_data = {
                        'text': current_chunk.strip(),
                        'sentences': current_chunk_sentences,
                        'word_count': len(current_chunk.split()),
                        'char_count': len(current_chunk),
                        'keywords': self._extract_keywords(current_chunk)
                    }
                    chunks.append(chunk_data)
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk_sentences, overlap)
                    current_chunk = overlap_text + sentence
                    current_chunk_sentences = [sentence]
                else:
                    current_chunk += sentence
                    current_chunk_sentences.append(sentence)
            
            # Add final chunk
            if current_chunk.strip():
                chunk_data = {
                    'text': current_chunk.strip(),
                    'sentences': current_chunk_sentences,
                    'word_count': len(current_chunk.split()),
                    'char_count': len(current_chunk),
                    'keywords': self._extract_keywords(current_chunk)
                }
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            logging.error(f"Error in advanced text chunking: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep basic punctuation
            text = re.sub(r'[^\w\s\.\?\!\,\;\:\-\(\)\'\"]+', '', text)
            
            # Fix spacing around punctuation
            text = re.sub(r'\s+([\.!\?])', r'\1', text)
            text = re.sub(r'([\.!\?])\s*', r'\1 ', text)
            
            return text.strip()
            
        except Exception as e:
            logging.error(f"Error cleaning text: {e}")
            return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        try:
            # Simple sentence splitting - could be enhanced with NLP libraries
            sentences = re.split(r'[.!?]+', text)
            
            # Clean and filter sentences
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:  # Filter very short sentences
                    cleaned_sentences.append(sentence + '. ')
            
            return cleaned_sentences
            
        except Exception as e:
            logging.error(f"Error splitting into sentences: {e}")
            return [text]
    
    def _get_overlap_text(self, sentences: List[str], overlap: int) -> str:
        """Get overlap text from previous chunk"""
        try:
            if not sentences:
                return ""
            
            # Take last few sentences for overlap
            overlap_sentences = sentences[-2:] if len(sentences) > 1 else sentences
            overlap_text = ''.join(overlap_sentences)
            
            # Ensure overlap doesn't exceed specified length
            if len(overlap_text) > overlap:
                overlap_text = overlap_text[-overlap:]
            
            return overlap_text
            
        except Exception as e:
            logging.error(f"Error getting overlap text: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using TF-IDF"""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Get most frequent keywords
            word_freq = defaultdict(int)
            for word in keywords:
                word_freq[word] += 1
            
            # Return top keywords
            sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_keywords[:10]]
            
        except Exception as e:
            logging.error(f"Error extracting keywords: {e}")
            return []
    
    def hybrid_search(self, query: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]], 
                     query_embedding: List[float], alpha: float = 0.7) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic similarity and keyword matching
        """
        try:
            if not chunks or not embeddings or not query_embedding:
                return []
            
            # Semantic similarity scores
            semantic_scores = []
            for embedding in embeddings:
                if embedding:
                    similarity = cosine_similarity([query_embedding], [embedding])[0][0]
                    semantic_scores.append(similarity)
                else:
                    semantic_scores.append(0.0)
            
            # Keyword matching scores
            keyword_scores = self._calculate_keyword_scores(query, chunks)
            
            # Combine scores
            combined_scores = []
            for i in range(len(chunks)):
                semantic_score = semantic_scores[i] if i < len(semantic_scores) else 0.0
                keyword_score = keyword_scores[i] if i < len(keyword_scores) else 0.0
                
                # Weighted combination
                combined_score = alpha * semantic_score + (1 - alpha) * keyword_score
                combined_scores.append(combined_score)
            
            # Sort by combined score
            scored_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_copy = chunk.copy()
                chunk_copy['score'] = combined_scores[i]
                chunk_copy['semantic_score'] = semantic_scores[i] if i < len(semantic_scores) else 0.0
                chunk_copy['keyword_score'] = keyword_scores[i] if i < len(keyword_scores) else 0.0
                scored_chunks.append(chunk_copy)
            
            # Sort by score and return top results
            scored_chunks.sort(key=lambda x: x['score'], reverse=True)
            return scored_chunks[:self.max_chunks_per_query]
            
        except Exception as e:
            logging.error(f"Error in hybrid search: {e}")
            return []
    
    def _calculate_keyword_scores(self, query: str, chunks: List[Dict[str, Any]]) -> List[float]:
        """Calculate keyword matching scores"""
        try:
            query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
            
            scores = []
            for chunk in chunks:
                chunk_text = chunk.get('text', '').lower()
                chunk_keywords = set(re.findall(r'\b\w+\b', chunk_text))
                
                # Calculate Jaccard similarity
                intersection = len(query_keywords.intersection(chunk_keywords))
                union = len(query_keywords.union(chunk_keywords))
                
                if union > 0:
                    jaccard_score = intersection / union
                else:
                    jaccard_score = 0.0
                
                # Boost score for exact phrase matches
                phrase_boost = 0.0
                if len(query) > 5:  # Only for longer queries
                    if query.lower() in chunk_text:
                        phrase_boost = 0.3
                
                final_score = jaccard_score + phrase_boost
                scores.append(min(final_score, 1.0))  # Cap at 1.0
            
            return scores
            
        except Exception as e:
            logging.error(f"Error calculating keyword scores: {e}")
            return [0.0] * len(chunks)
    
    def rerank_results(self, query: str, search_results: List[Dict[str, Any]], 
                      rerank_model: str = "cross-encoder") -> List[Dict[str, Any]]:
        """
        Re-rank search results using more sophisticated methods
        """
        try:
            if not search_results:
                return []
            
            # For now, implement a simple re-ranking based on query-document similarity
            # In production, this could use specialized re-ranking models
            
            reranked_results = []
            for result in search_results:
                chunk_text = result.get('text', '')
                
                # Calculate query-document similarity metrics
                query_coverage = self._calculate_query_coverage(query, chunk_text)
                document_quality = self._calculate_document_quality(chunk_text)
                relevance_score = self._calculate_relevance_score(query, chunk_text)
                
                # Combine metrics
                rerank_score = (
                    0.4 * query_coverage +
                    0.3 * relevance_score +
                    0.2 * document_quality +
                    0.1 * result.get('score', 0.0)
                )
                
                result_copy = result.copy()
                result_copy['rerank_score'] = rerank_score
                result_copy['query_coverage'] = query_coverage
                result_copy['document_quality'] = document_quality
                result_copy['relevance_score'] = relevance_score
                
                reranked_results.append(result_copy)
            
            # Sort by re-rank score
            reranked_results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            logging.error(f"Error in re-ranking: {e}")
            return search_results
    
    def _calculate_query_coverage(self, query: str, document: str) -> float:
        """Calculate how well the document covers the query terms"""
        try:
            query_terms = set(re.findall(r'\b\w+\b', query.lower()))
            document_terms = set(re.findall(r'\b\w+\b', document.lower()))
            
            if not query_terms:
                return 0.0
            
            covered_terms = query_terms.intersection(document_terms)
            coverage = len(covered_terms) / len(query_terms)
            
            return coverage
            
        except Exception as e:
            logging.error(f"Error calculating query coverage: {e}")
            return 0.0
    
    def _calculate_document_quality(self, document: str) -> float:
        """Calculate document quality score"""
        try:
            # Simple quality metrics
            word_count = len(document.split())
            sentence_count = len(re.findall(r'[.!?]+', document))
            
            # Prefer documents with reasonable length
            length_score = min(word_count / 200, 1.0)  # Normalize to 200 words
            
            # Prefer documents with proper sentence structure
            structure_score = min(sentence_count / 10, 1.0)  # Normalize to 10 sentences
            
            # Check for informative content (not just stop words)
            content_words = len([word for word in document.split() if len(word) > 3])
            content_score = min(content_words / word_count, 1.0) if word_count > 0 else 0.0
            
            quality_score = (length_score + structure_score + content_score) / 3
            
            return quality_score
            
        except Exception as e:
            logging.error(f"Error calculating document quality: {e}")
            return 0.0
    
    def _calculate_relevance_score(self, query: str, document: str) -> float:
        """Calculate relevance score between query and document"""
        try:
            # Use TF-IDF similarity
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            
            try:
                tfidf_matrix = vectorizer.fit_transform([query, document])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return similarity
            except:
                # Fallback to simple word overlap
                query_words = set(re.findall(r'\b\w+\b', query.lower()))
                doc_words = set(re.findall(r'\b\w+\b', document.lower()))
                
                if not query_words or not doc_words:
                    return 0.0
                
                intersection = len(query_words.intersection(doc_words))
                union = len(query_words.union(doc_words))
                
                return intersection / union if union > 0 else 0.0
                
        except Exception as e:
            logging.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def query_expansion(self, query: str, knowledge_base_chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Expand query with related terms from knowledge base
        """
        try:
            if not query or not knowledge_base_chunks:
                return [query]
            
            # Find related terms from knowledge base
            related_terms = set()
            query_terms = set(re.findall(r'\b\w+\b', query.lower()))
            
            for chunk in knowledge_base_chunks:
                chunk_text = chunk.get('text', '').lower()
                chunk_keywords = chunk.get('keywords', [])
                
                # If chunk contains query terms, extract related terms
                if any(term in chunk_text for term in query_terms):
                    for keyword in chunk_keywords:
                        if keyword not in query_terms:
                            related_terms.add(keyword)
            
            # Create expanded queries
            expanded_queries = [query]
            
            # Add query with top related terms
            if related_terms:
                top_related = list(related_terms)[:3]  # Top 3 related terms
                expanded_query = query + " " + " ".join(top_related)
                expanded_queries.append(expanded_query)
            
            return expanded_queries
            
        except Exception as e:
            logging.error(f"Error in query expansion: {e}")
            return [query]
    
    def multi_hop_reasoning(self, query: str, search_results: List[Dict[str, Any]], 
                          max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        Perform multi-hop reasoning to find connected information
        """
        try:
            if not search_results:
                return []
            
            reasoning_chain = []
            current_results = search_results[:5]  # Start with top 5 results
            
            for hop in range(max_hops):
                # Extract entities/concepts from current results
                entities = self._extract_entities_from_results(current_results)
                
                # Find related information
                related_info = self._find_related_information(entities, search_results)
                
                if related_info:
                    reasoning_chain.extend(related_info)
                    current_results = related_info
                else:
                    break
            
            # Combine original results with reasoning chain
            final_results = search_results + reasoning_chain
            
            # Remove duplicates
            seen_texts = set()
            unique_results = []
            for result in final_results:
                text = result.get('text', '')
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logging.error(f"Error in multi-hop reasoning: {e}")
            return search_results
    
    def _extract_entities_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract entities/concepts from search results"""
        try:
            entities = set()
            
            for result in results:
                text = result.get('text', '')
                keywords = result.get('keywords', [])
                
                # Add keywords as entities
                entities.update(keywords)
                
                # Extract capitalized words (potential entities)
                capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', text)
                entities.update(capitalized_words)
            
            return list(entities)
            
        except Exception as e:
            logging.error(f"Error extracting entities: {e}")
            return []
    
    def _find_related_information(self, entities: List[str], all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find information related to extracted entities"""
        try:
            related_results = []
            
            for result in all_results:
                text = result.get('text', '').lower()
                
                # Check if result contains any of the entities
                entity_matches = 0
                for entity in entities:
                    if entity.lower() in text:
                        entity_matches += 1
                
                # If multiple entities match, consider it related
                if entity_matches >= 2:
                    result_copy = result.copy()
                    result_copy['entity_matches'] = entity_matches
                    result_copy['hop_type'] = 'entity_related'
                    related_results.append(result_copy)
            
            # Sort by entity matches
            related_results.sort(key=lambda x: x['entity_matches'], reverse=True)
            
            return related_results[:3]  # Top 3 related results
            
        except Exception as e:
            logging.error(f"Error finding related information: {e}")
            return []
    
    def generate_context_summary(self, search_results: List[Dict[str, Any]], query: str) -> str:
        """
        Generate a summary of the search results as context
        """
        try:
            if not search_results:
                return "No relevant information found."
            
            # Combine top results
            combined_text = ""
            for i, result in enumerate(search_results[:5]):
                text = result.get('text', '')
                score = result.get('score', 0.0)
                
                # Add result with context
                combined_text += f"[Source {i+1}, Relevance: {score:.2f}]\n{text}\n\n"
            
            # Create summary
            summary = f"Based on the query '{query}', here are the most relevant pieces of information:\n\n"
            summary += combined_text
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating context summary: {e}")
            return "Error generating summary."
    
    def filter_results_by_quality(self, results: List[Dict[str, Any]], min_score: float = 0.1) -> List[Dict[str, Any]]:
        """Filter results by quality thresholds"""
        try:
            filtered_results = []
            
            for result in results:
                score = result.get('score', 0.0)
                text = result.get('text', '')
                
                # Quality checks
                if score < min_score:
                    continue
                
                if len(text) < 50:  # Too short
                    continue
                
                if len(text) > 5000:  # Too long
                    continue
                
                # Check for meaningful content
                words = text.split()
                if len(words) < 10:  # Too few words
                    continue
                
                filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logging.error(f"Error filtering results: {e}")
            return results
