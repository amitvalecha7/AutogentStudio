import os
import logging
import numpy as np
from typing import List, Union
from services.openai_service import OpenAIService

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available, using OpenAI embeddings only")

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logging.warning("cohere not available")

class EmbeddingService:
    def __init__(self, provider="openai", model_name=None):
        self.provider = provider
        self.model_name = model_name
        
        if provider == "openai":
            self.openai_service = OpenAIService()
            self.model_name = model_name or "text-embedding-3-small"
        
        elif provider == "sentence_transformers" and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model_name = model_name or "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
        
        elif provider == "cohere" and COHERE_AVAILABLE:
            self.cohere_api_key = os.environ.get("COHERE_API_KEY")
            if self.cohere_api_key:
                self.cohere_client = cohere.Client(self.cohere_api_key)
                self.model_name = model_name or "embed-english-v3.0"
            else:
                logging.warning("Cohere API key not found, falling back to OpenAI")
                self.provider = "openai"
                self.openai_service = OpenAIService()
        
        else:
            logging.warning(f"Provider {provider} not available, falling back to OpenAI")
            self.provider = "openai"
            self.openai_service = OpenAIService()
            self.model_name = "text-embedding-3-small"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.provider == "openai":
                embeddings = self.openai_service.generate_embeddings([text], self.model_name)
                return embeddings[0] if embeddings else []
            
            elif self.provider == "sentence_transformers":
                embedding = self.model.encode(text)
                return embedding.tolist()
            
            elif self.provider == "cohere":
                response = self.cohere_client.embed(
                    texts=[text],
                    model=self.model_name,
                    input_type="search_document"
                )
                return response.embeddings[0]
            
            return []
        
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            return []
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            if self.provider == "openai":
                return self.openai_service.generate_embeddings(texts, self.model_name)
            
            elif self.provider == "sentence_transformers":
                embeddings = self.model.encode(texts)
                return [emb.tolist() for emb in embeddings]
            
            elif self.provider == "cohere":
                response = self.cohere_client.embed(
                    texts=texts,
                    model=self.model_name,
                    input_type="search_document"
                )
                return response.embeddings
            
            return []
        
        except Exception as e:
            logging.error(f"Error generating batch embeddings: {str(e)}")
            return []
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding optimized for search queries"""
        try:
            if self.provider == "openai":
                embeddings = self.openai_service.generate_embeddings([query], self.model_name)
                return embeddings[0] if embeddings else []
            
            elif self.provider == "sentence_transformers":
                embedding = self.model.encode(query)
                return embedding.tolist()
            
            elif self.provider == "cohere":
                response = self.cohere_client.embed(
                    texts=[query],
                    model=self.model_name,
                    input_type="search_query"
                )
                return response.embeddings[0]
            
            return []
        
        except Exception as e:
            logging.error(f"Error generating query embedding: {str(e)}")
            return []
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        
        except Exception as e:
            logging.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """Find the most similar embeddings to a query"""
        try:
            similarities = []
            
            for i, embedding in enumerate(embeddings):
                similarity = self.cosine_similarity(query_embedding, embedding)
                similarities.append((i, similarity))
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
        
        except Exception as e:
            logging.error(f"Error finding similar embeddings: {str(e)}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model"""
        if self.provider == "openai":
            if "text-embedding-3-small" in self.model_name:
                return 1536
            elif "text-embedding-3-large" in self.model_name:
                return 3072
            elif "text-embedding-ada-002" in self.model_name:
                return 1536
        
        elif self.provider == "sentence_transformers":
            if hasattr(self.model, 'get_sentence_embedding_dimension'):
                return self.model.get_sentence_embedding_dimension()
            return 384  # Default for all-MiniLM-L6-v2
        
        elif self.provider == "cohere":
            if "embed-english-v3.0" in self.model_name:
                return 1024
            elif "embed-multilingual-v3.0" in self.model_name:
                return 1024
        
        return 1536  # Default fallback
    
    def test_embedding_generation(self) -> bool:
        """Test if embedding generation is working"""
        try:
            test_text = "This is a test sentence for embedding generation."
            embedding = self.generate_embedding(test_text)
            return len(embedding) > 0
        
        except Exception as e:
            logging.error(f"Embedding test failed: {str(e)}")
            return False

