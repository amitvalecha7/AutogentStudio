import os
import logging
import mimetypes
from typing import List, Optional
import PyPDF2
import docx
import json
import csv

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'text/plain': self._process_text,
            'application/pdf': self._process_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx,
            'application/json': self._process_json,
            'text/csv': self._process_csv,
            'application/vnd.ms-excel': self._process_csv,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': self._process_csv
        }
    
    def extract_text(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extract text content from file"""
        try:
            if mime_type in self.supported_types:
                processor = self.supported_types[mime_type]
                return processor(file_path)
            else:
                logging.warning(f"Unsupported file type: {mime_type}")
                return None
        except Exception as e:
            logging.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _process_text(self, file_path: str) -> str:
        """Process plain text files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    def _process_pdf(self, file_path: str) -> str:
        """Process PDF files"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}")
            # Fallback: try to read as text
            return self._process_text(file_path)
        
        return text
    
    def _process_docx(self, file_path: str) -> str:
        """Process Word documents"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logging.error(f"Error processing DOCX: {str(e)}")
            return ""
    
    def _process_json(self, file_path: str) -> str:
        """Process JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return json.dumps(data, indent=2)
        except Exception as e:
            logging.error(f"Error processing JSON: {str(e)}")
            return self._process_text(file_path)
    
    def _process_csv(self, file_path: str) -> str:
        """Process CSV files"""
        try:
            text = ""
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text += " ".join(row) + "\n"
            return text
        except Exception as e:
            logging.error(f"Error processing CSV: {str(e)}")
            return self._process_text(file_path)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings
                sentence_ends = ['.', '!', '?', '\n']
                for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                    if chunk[i] in sentence_ends and i > len(chunk) * 0.5:
                        chunk = chunk[:i + 1]
                        end = start + i + 1
                        break
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def get_file_metadata(self, file_path: str) -> dict:
        """Extract metadata from file"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            metadata = {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'mime_type': mime_type,
                'extension': os.path.splitext(file_path)[1].lower()
            }
            
            # Add type-specific metadata
            if mime_type == 'application/pdf':
                metadata.update(self._get_pdf_metadata(file_path))
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                metadata.update(self._get_docx_metadata(file_path))
            
            return metadata
        except Exception as e:
            logging.error(f"Error extracting metadata: {str(e)}")
            return {}
    
    def _get_pdf_metadata(self, file_path: str) -> dict:
        """Extract PDF-specific metadata"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    'pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    'subject': pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else ''
                }
                return metadata
        except Exception as e:
            logging.error(f"Error extracting PDF metadata: {str(e)}")
            return {}
    
    def _get_docx_metadata(self, file_path: str) -> dict:
        """Extract DOCX-specific metadata"""
        try:
            doc = docx.Document(file_path)
            core_props = doc.core_properties
            metadata = {
                'title': core_props.title or '',
                'author': core_props.author or '',
                'subject': core_props.subject or '',
                'paragraphs': len(doc.paragraphs),
                'words': sum(len(p.text.split()) for p in doc.paragraphs)
            }
            return metadata
        except Exception as e:
            logging.error(f"Error extracting DOCX metadata: {str(e)}")
            return {}
