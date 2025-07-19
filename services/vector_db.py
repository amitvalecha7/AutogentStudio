import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import json

# Vector database implementations
try:
    import pinecone
except ImportError:
    pinecone = None

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    import faiss
except ImportError:
    faiss = None

from services.ai_providers import get_embedding

class VectorDB:
    """Abstract vector database interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def upsert(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors"""
        raise NotImplementedError
        
    def query(self, vector: List[float], top_k: int = 10, 
              filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query similar vectors"""
        raise NotImplementedError
        
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        raise NotImplementedError

class PineconeDB(VectorDB):
    """Pinecone vector database implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not pinecone:
            raise ImportError("Pinecone SDK not installed")
            
        api_key = os.environ.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
            
        pinecone.init(
            api_key=api_key,
            environment=config.get('environment', 'us-west1-gcp')
        )
        
        self.index_name = config.get('index_name', 'autogent-studio')
        self.index = pinecone.Index(self.index_name)
    
    def upsert(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors in Pinecone"""
        try:
            formatted_vectors = []
            for vec in vectors:
                formatted_vectors.append({
                    'id': vec['id'],
                    'values': vec['values'],
                    'metadata': vec.get('metadata', {})
                })
            
            self.index.upsert(vectors=formatted_vectors)
            return True
            
        except Exception as e:
            logging.error(f"Error upserting to Pinecone: {e}")
            return False
    
    def query(self, vector: List[float], top_k: int = 10, 
              filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query similar vectors from Pinecone"""
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
            
            results = []
            for match in response['matches']:
                results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error querying Pinecone: {e}")
            return []

class ChromaDB(VectorDB):
    """ChromaDB vector database implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not chromadb:
            raise ImportError("ChromaDB not installed")
            
        self.client = chromadb.Client()
        self.collection_name = config.get('collection_name', 'autogent_studio')
        
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(self.collection_name)
    
    def upsert(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors in ChromaDB"""
        try:
            ids = [vec['id'] for vec in vectors]
            embeddings = [vec['values'] for vec in vectors]
            metadatas = [vec.get('metadata', {}) for vec in vectors]
            documents = [meta.get('text', '') for meta in metadatas]
            
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            return True
            
        except Exception as e:
            logging.error(f"Error upserting to ChromaDB: {e}")
            return False
    
    def query(self, vector: List[float], top_k: int = 10, 
              filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query similar vectors from ChromaDB"""
        try:
            response = self.collection.query(
                query_embeddings=[vector],
                n_results=top_k,
                where=filter_dict
            )
            
            results = []
            for i in range(len(response['ids'][0])):
                results.append({
                    'id': response['ids'][0][i],
                    'score': 1 - response['distances'][0][i],  # Convert distance to similarity
                    'metadata': response['metadatas'][0][i]
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error querying ChromaDB: {e}")
            return []

class FAISSVectorDB(VectorDB):
    """FAISS vector database implementation for local storage"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not faiss:
            raise ImportError("FAISS not installed")
            
        self.dimension = config.get('dimension', 1536)
        self.index_path = config.get('index_path', 'faiss_index.bin')
        self.metadata_path = config.get('metadata_path', 'faiss_metadata.json')
        
        # Initialize or load FAISS index
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
            self.metadata = {}
    
    def upsert(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors in FAISS"""
        try:
            embeddings = np.array([vec['values'] for vec in vectors], dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            start_id = self.index.ntotal
            self.index.add(embeddings)
            
            # Store metadata
            for i, vec in enumerate(vectors):
                vector_id = start_id + i
                self.metadata[str(vector_id)] = {
                    'original_id': vec['id'],
                    'metadata': vec.get('metadata', {})
                }
            
            # Save index and metadata
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f)
            
            return True
            
        except Exception as e:
            logging.error(f"Error upserting to FAISS: {e}")
            return False
    
    def query(self, vector: List[float], top_k: int = 10, 
              filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query similar vectors from FAISS"""
        try:
            query_vector = np.array([vector], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            scores, indices = self.index.search(query_vector, top_k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # No more results
                    break
                    
                meta = self.metadata.get(str(idx), {})
                
                # Apply filters if specified
                if filter_dict:
                    item_metadata = meta.get('metadata', {})
                    if not all(item_metadata.get(k) == v for k, v in filter_dict.items()):
                        continue
                
                results.append({
                    'id': meta.get('original_id', str(idx)),
                    'score': float(score),
                    'metadata': meta.get('metadata', {})
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error querying FAISS: {e}")
            return []

def get_vector_db(db_type: str = None) -> VectorDB:
    """Get vector database instance based on configuration"""
    if db_type is None:
        # Auto-detect based on available credentials
        if os.environ.get('PINECONE_API_KEY'):
            db_type = 'pinecone'
        elif chromadb:
            db_type = 'chromadb'
        else:
            db_type = 'faiss'
    
    config = {
        'pinecone': {
            'environment': os.environ.get('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            'index_name': os.environ.get('PINECONE_INDEX', 'autogent-studio')
        },
        'chromadb': {
            'collection_name': 'autogent_studio'
        },
        'faiss': {
            'dimension': 1536,
            'index_path': 'data/faiss_index.bin',
            'metadata_path': 'data/faiss_metadata.json'
        }
    }
    
    if db_type == 'pinecone':
        return PineconeDB(config['pinecone'])
    elif db_type == 'chromadb':
        return ChromaDB(config['chromadb'])
    elif db_type == 'faiss':
        return FAISSVectorDB(config['faiss'])
    else:
        raise ValueError(f"Unsupported vector database type: {db_type}")

def generate_embeddings(text: str, model: str = 'text-embedding-3-small') -> List[float]:
    """Generate embeddings for text"""
    try:
        return get_embedding(text, model)
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        # Fallback to simple hash-based embedding (not recommended for production)
        return simple_text_embedding(text)

def simple_text_embedding(text: str, dimension: int = 1536) -> List[float]:
    """Simple fallback embedding using text hashing"""
    import hashlib
    
    # Create hash of text
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Convert to pseudo-random vector
    vector = []
    for i in range(0, len(text_hash), 2):
        hex_val = text_hash[i:i+2]
        vector.append(int(hex_val, 16) / 255.0)
    
    # Pad or truncate to desired dimension
    while len(vector) < dimension:
        vector.extend(vector[:min(len(vector), dimension - len(vector))])
    
    return vector[:dimension]

def search_similar_chunks(query: str, knowledge_base_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for similar chunks in knowledge base"""
    try:
        # Generate query embedding
        query_embedding = generate_embeddings(query)
        
        # Get vector database
        vector_db = get_vector_db()
        
        # Search with knowledge base filter
        results = vector_db.query(
            vector=query_embedding,
            top_k=limit,
            filter_dict={'knowledge_base_id': knowledge_base_id}
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'chunk_id': result['id'],
                'content': result['metadata'].get('content', ''),
                'score': result['score'],
                'file_name': result['metadata'].get('file_name', ''),
                'chunk_index': result['metadata'].get('chunk_index', 0)
            })
        
        return formatted_results
        
    except Exception as e:
        logging.error(f"Error searching similar chunks: {e}")
        return []

def index_document_chunks(chunks: List[Dict[str, Any]], knowledge_base_id: str) -> bool:
    """Index document chunks in vector database"""
    try:
        vector_db = get_vector_db()
        
        vectors = []
        for chunk in chunks:
            # Generate embedding for chunk content
            embedding = generate_embeddings(chunk['content'])
            
            vectors.append({
                'id': chunk['id'],
                'values': embedding,
                'metadata': {
                    'content': chunk['content'],
                    'knowledge_base_id': knowledge_base_id,
                    'file_id': chunk.get('file_id'),
                    'file_name': chunk.get('file_name'),
                    'chunk_index': chunk.get('chunk_index', 0)
                }
            })
        
        return vector_db.upsert(vectors)
        
    except Exception as e:
        logging.error(f"Error indexing document chunks: {e}")
        return False

def delete_knowledge_base_vectors(knowledge_base_id: str) -> bool:
    """Delete all vectors for a knowledge base"""
    try:
        vector_db = get_vector_db()
        
        # Query all vectors for this knowledge base
        dummy_vector = [0.0] * 1536  # Dummy vector for query
        results = vector_db.query(
            vector=dummy_vector,
            top_k=10000,  # Large number to get all
            filter_dict={'knowledge_base_id': knowledge_base_id}
        )
        
        # Extract IDs
        ids_to_delete = [result['id'] for result in results]
        
        if ids_to_delete:
            return vector_db.delete(ids_to_delete)
        
        return True
        
    except Exception as e:
        logging.error(f"Error deleting knowledge base vectors: {e}")
        return False

def get_vector_stats(knowledge_base_id: str) -> Dict[str, Any]:
    """Get statistics for vectors in knowledge base"""
    try:
        vector_db = get_vector_db()
        
        # Query vectors for this knowledge base
        dummy_vector = [0.0] * 1536
        results = vector_db.query(
            vector=dummy_vector,
            top_k=10000,
            filter_dict={'knowledge_base_id': knowledge_base_id}
        )
        
        stats = {
            'total_chunks': len(results),
            'files': set(),
            'avg_score': 0.0
        }
        
        total_score = 0.0
        for result in results:
            metadata = result.get('metadata', {})
            if metadata.get('file_name'):
                stats['files'].add(metadata['file_name'])
            total_score += result.get('score', 0.0)
        
        stats['unique_files'] = len(stats['files'])
        stats['files'] = list(stats['files'])
        
        if len(results) > 0:
            stats['avg_score'] = total_score / len(results)
        
        return stats
        
    except Exception as e:
        logging.error(f"Error getting vector stats: {e}")
        return {'total_chunks': 0, 'unique_files': 0, 'files': [], 'avg_score': 0.0}
