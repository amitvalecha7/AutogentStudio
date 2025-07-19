import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import PyPDF2
import docx
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

class FileProcessor:
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 
            'csv', 'md', 'html', 'png', 'jpg', 'jpeg', 
            'gif', 'mp3', 'wav', 'mp4', 'avi'
        }
        self.embedding_model = None
        os.makedirs(upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, file: FileStorage) -> dict:
        """Save uploaded file and return file info"""
        if not file or file.filename == '':
            raise ValueError("No file provided")
        
        if not self.allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(self.upload_folder, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_type = file_extension
        
        return {
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size': file_size,
            'file_type': file_type
        }
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from various file types"""
        try:
            if file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_type == 'pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif file_type in ['doc', 'docx']:
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            elif file_type in ['xls', 'xlsx']:
                df = pd.read_excel(file_path)
                return df.to_string()
            
            elif file_type == 'csv':
                df = pd.read_csv(file_path)
                return df.to_string()
            
            else:
                return f"Text extraction not supported for {file_type} files"
                
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks for better RAG performance"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to end at a sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                boundary = max(last_period, last_newline)
                
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    def generate_embeddings(self, chunks: list, model_name: str = 'all-MiniLM-L6-v2') -> np.ndarray:
        """Generate embeddings for text chunks"""
        try:
            if self.embedding_model is None:
                self.embedding_model = SentenceTransformer(model_name)
            
            embeddings = self.embedding_model.encode(chunks)
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return np.array([])
    
    def process_file_for_rag(self, file_path: str, file_type: str) -> dict:
        """Process file for RAG integration"""
        try:
            # Extract text
            text = self.extract_text(file_path, file_type)
            
            if not text or text.startswith("Error"):
                return {"error": text or "Failed to extract text"}
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Generate embeddings
            embeddings = self.generate_embeddings(chunks)
            
            return {
                "text": text,
                "chunks": chunks,
                "embeddings": embeddings.tolist() if embeddings.size > 0 else [],
                "chunk_count": len(chunks),
                "status": "success"
            }
            
        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}

# Global instance
file_processor = FileProcessor()
