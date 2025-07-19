import os
import numpy as np
from typing import List, Union, Optional
import json

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from .openai_service import OpenAIService

class EmbeddingService:
    def __init__(self, provider: str = "openai", model_name: Optional[str] = None):
        """
        Initialize embedding service
        
        Args:
            provider: Embedding provider ('openai', 'sentence_transformers', 'cohere')
            model_name: Specific model to use
        """
        self.provider = provider.lower()
        self.model_name = model_name
        
        if self.provider == "openai":
            self.openai_service = OpenAIService()
            self.model_name = model_name or "text-embedding-3-small"
            
        elif self.provider == "sentence_transformers":
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model_name = model_name or "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
            
        elif self.provider == "cohere":
            try:
                import cohere
                self.cohere_client = cohere.Client(os.environ.get("COHERE_API_KEY"))
                self.model_name = model_name or "embed-english-v3.0"
            except ImportError:
                raise ImportError("cohere not installed. Install with: pip install cohere")
            
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        return self.get_embeddings([text])[0]

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.provider == "openai":
                return self.openai_service.get_embeddings(texts, self.model_name)
                
            elif self.provider == "sentence_transformers":
                embeddings = self.model.encode(texts)
                return embeddings.tolist()
                
            elif self.provider == "cohere":
                response = self.cohere_client.embed(
                    texts=texts,
                    model=self.model_name
                )
                return response.embeddings
                
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            raise Exception(f"Similarity computation failed: {str(e)}")

    def find_similar_texts(self, query_embedding: List[float], 
                          candidate_embeddings: List[List[float]], 
                          texts: List[str], 
                          top_k: int = 5) -> List[Dict]:
        """
        Find most similar texts to query
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            texts: Corresponding texts for candidates
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with text and similarity score
        """
        try:
            similarities = []
            
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate_embedding)
                similarities.append({
                    'text': texts[i],
                    'similarity': similarity,
                    'index': i
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            raise Exception(f"Similar text search failed: {str(e)}")

    def cluster_embeddings(self, embeddings: List[List[float]], n_clusters: int = 5) -> List[int]:
        """
        Cluster embeddings using K-means
        
        Args:
            embeddings: List of embedding vectors
            n_clusters: Number of clusters
            
        Returns:
            List of cluster labels
        """
        try:
            from sklearn.cluster import KMeans
            
            # Convert to numpy array
            embedding_matrix = np.array(embeddings)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embedding_matrix)
            
            return cluster_labels.tolist()
            
        except ImportError:
            raise ImportError("scikit-learn not installed. Install with: pip install scikit-learn")
        except Exception as e:
            raise Exception(f"Embedding clustering failed: {str(e)}")

    def reduce_dimensionality(self, embeddings: List[List[float]], n_components: int = 2) -> List[List[float]]:
        """
        Reduce embedding dimensionality using PCA
        
        Args:
            embeddings: List of embedding vectors
            n_components: Number of components to keep
            
        Returns:
            List of reduced embedding vectors
        """
        try:
            from sklearn.decomposition import PCA
            
            # Convert to numpy array
            embedding_matrix = np.array(embeddings)
            
            # Apply PCA
            pca = PCA(n_components=n_components)
            reduced_embeddings = pca.fit_transform(embedding_matrix)
            
            return reduced_embeddings.tolist()
            
        except ImportError:
            raise ImportError("scikit-learn not installed. Install with: pip install scikit-learn")
        except Exception as e:
            raise Exception(f"Dimensionality reduction failed: {str(e)}")

    def save_embeddings(self, embeddings: List[List[float]], file_path: str):
        """
        Save embeddings to file
        
        Args:
            embeddings: List of embedding vectors
            file_path: Path to save file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(embeddings, f)
                
        except Exception as e:
            raise Exception(f"Failed to save embeddings: {str(e)}")

    def load_embeddings(self, file_path: str) -> List[List[float]]:
        """
        Load embeddings from file
        
        Args:
            file_path: Path to embedding file
            
        Returns:
            List of embedding vectors
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            raise Exception(f"Failed to load embeddings: {str(e)}")

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model
        
        Returns:
            Embedding dimension
        """
        if self.provider == "openai":
            if "text-embedding-3-small" in self.model_name:
                return 1536
            elif "text-embedding-3-large" in self.model_name:
                return 3072
            elif "text-embedding-ada-002" in self.model_name:
                return 1536
            else:
                return 1536  # Default
                
        elif self.provider == "sentence_transformers":
            return self.model.get_sentence_embedding_dimension()
            
        elif self.provider == "cohere":
            if "embed-english-v3.0" in self.model_name:
                return 1024
            elif "embed-multilingual-v3.0" in self.model_name:
                return 1024
            else:
                return 1024  # Default
                
        return 768  # Fallback default

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for the current provider
        
        Returns:
            List of model names
        """
        if self.provider == "openai":
            return [
                "text-embedding-3-small",
                "text-embedding-3-large", 
                "text-embedding-ada-002"
            ]
            
        elif self.provider == "sentence_transformers":
            return [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "multi-qa-MiniLM-L6-cos-v1",
                "paraphrase-MiniLM-L6-v2",
                "distilbert-base-nli-stsb-mean-tokens"
            ]
            
        elif self.provider == "cohere":
            return [
                "embed-english-v3.0",
                "embed-multilingual-v3.0",
                "embed-english-light-v3.0",
                "embed-multilingual-light-v3.0"
            ]
            
        return []
