import os
import magic
import PyPDF2
import docx
from PIL import Image
import mimetypes
import hashlib
from models import File, FileEmbedding
from app import db
from services.ai_providers import AIProviders
import logging

class FileManager:
    def __init__(self):
        self.supported_types = {
            'text': ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.cpp', '.c', '.h'],
            'document': ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'audio': ['.mp3', '.wav', '.m4a', '.flac', '.ogg'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        }
        
        self.ai_providers = AIProviders()
    
    def process_file(self, file_id):
        """Process uploaded file and extract content"""
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                raise ValueError(f"File with ID {file_id} not found")
            
            # Update processing status
            file_record.processing_status = 'processing'
            db.session.commit()
            
            # Extract content based on file type
            content = self._extract_content(file_record)
            
            if content:
                # Save extracted content
                file_record.content_extracted = content
                file_record.is_processed = True
                file_record.processing_status = 'completed'
                
                # Generate embeddings
                self._generate_embeddings(file_record, content)
            else:
                file_record.processing_status = 'failed'
            
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error processing file {file_id}: {str(e)}")
            file_record.processing_status = 'failed'
            db.session.commit()
    
    def _extract_content(self, file_record):
        """Extract text content from file"""
        try:
            file_path = file_record.file_path
            file_extension = os.path.splitext(file_record.filename)[1].lower()
            
            if file_extension in self.supported_types['text']:
                return self._extract_text_content(file_path)
            elif file_extension in self.supported_types['document']:
                return self._extract_document_content(file_path, file_extension)
            elif file_extension in self.supported_types['image']:
                return self._extract_image_content(file_path)
            else:
                logging.warning(f"Unsupported file type: {file_extension}")
                return None
        
        except Exception as e:
            logging.error(f"Error extracting content: {str(e)}")
            return None
    
    def _extract_text_content(self, file_path):
        """Extract content from text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _extract_document_content(self, file_path, file_extension):
        """Extract content from document files"""
        try:
            if file_extension == '.pdf':
                return self._extract_pdf_content(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_word_content(file_path)
            elif file_extension in ['.pptx', '.ppt']:
                return self._extract_powerpoint_content(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                return self._extract_excel_content(file_path)
            else:
                return None
        
        except Exception as e:
            logging.error(f"Error extracting document content: {str(e)}")
            return None
    
    def _extract_pdf_content(self, file_path):
        """Extract content from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    content.append(page.extract_text())
                
                return '\n'.join(content)
        
        except Exception as e:
            logging.error(f"Error extracting PDF content: {str(e)}")
            return None
    
    def _extract_word_content(self, file_path):
        """Extract content from Word documents"""
        try:
            doc = docx.Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                content.append(paragraph.text)
            
            return '\n'.join(content)
        
        except Exception as e:
            logging.error(f"Error extracting Word content: {str(e)}")
            return None
    
    def _extract_powerpoint_content(self, file_path):
        """Extract content from PowerPoint presentations"""
        try:
            # This would require python-pptx library
            # For now, return placeholder
            return "PowerPoint content extraction not implemented"
        
        except Exception as e:
            logging.error(f"Error extracting PowerPoint content: {str(e)}")
            return None
    
    def _extract_excel_content(self, file_path):
        """Extract content from Excel files"""
        try:
            # This would require pandas or openpyxl library
            # For now, return placeholder
            return "Excel content extraction not implemented"
        
        except Exception as e:
            logging.error(f"Error extracting Excel content: {str(e)}")
            return None
    
    def _extract_image_content(self, file_path):
        """Extract content from images using OCR or AI vision"""
        try:
            # This would integrate with OCR services or AI vision APIs
            # For now, return placeholder
            return "Image content extraction not implemented"
        
        except Exception as e:
            logging.error(f"Error extracting image content: {str(e)}")
            return None
    
    def _generate_embeddings(self, file_record, content):
        """Generate embeddings for file content"""
        try:
            # Split content into chunks
            chunks = self._split_content(content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 0:
                    # Generate embedding
                    embedding = self.ai_providers.get_embeddings(chunk)
                    
                    # Save embedding
                    file_embedding = FileEmbedding(
                        file_id=file_record.id,
                        chunk_text=chunk,
                        embedding=embedding,
                        chunk_index=i
                    )
                    db.session.add(file_embedding)
            
            db.session.commit()
        
        except Exception as e:
            logging.error(f"Error generating embeddings: {str(e)}")
    
    def _split_content(self, content, chunk_size=1000, overlap=200):
        """Split content into chunks for embedding"""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Find the last space before the end to avoid splitting words
            if end < len(content):
                while end > start and content[end] != ' ':
                    end -= 1
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def search_files(self, query, user_id, limit=10):
        """Search files using semantic search"""
        try:
            # Generate query embedding
            query_embedding = self.ai_providers.get_embeddings(query)
            
            # This would implement vector similarity search
            # For now, return simple text search
            files = File.query.filter(
                File.user_id == user_id,
                File.content_extracted.contains(query)
            ).limit(limit).all()
            
            return files
        
        except Exception as e:
            logging.error(f"Error searching files: {str(e)}")
            return []
    
    def get_file_info(self, file_id):
        """Get detailed file information"""
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                return None
            
            return {
                'id': file_record.id,
                'filename': file_record.original_filename,
                'file_type': file_record.file_type,
                'file_size': file_record.file_size,
                'is_processed': file_record.is_processed,
                'processing_status': file_record.processing_status,
                'created_at': file_record.created_at.isoformat(),
                'content_length': len(file_record.content_extracted) if file_record.content_extracted else 0
            }
        
        except Exception as e:
            logging.error(f"Error getting file info: {str(e)}")
            return None
    
    def delete_file(self, file_id, user_id):
        """Delete file and associated data"""
        try:
            file_record = File.query.filter_by(id=file_id, user_id=user_id).first()
            if not file_record:
                raise ValueError("File not found")
            
            # Delete file from filesystem
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Delete embeddings
            FileEmbedding.query.filter_by(file_id=file_id).delete()
            
            # Delete file record
            db.session.delete(file_record)
            db.session.commit()
            
            return True
        
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")
            return False
