"""
Document Validation Node for file and metadata validation.

This node validates uploaded files against security and format requirements
following PocketFlow AsyncNode patterns for I/O operations.

Cookbook Reference: pocketflow-external-service
"""
import os
import mimetypes
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles
from pocketflow import AsyncNode


class DocumentValidationNode(AsyncNode):
    """
    Validates document files and metadata for upload processing.
    
    Validates file type, size, MIME type, and metadata structure
    against configured security requirements.
    
    Input (shared_store):
        - uploaded_file: UploadFile object from FastAPI
        - document_type: str ('biblical' | 'theological')
        - category: Optional[str]
        - max_file_size: int (bytes)
        - allowed_extensions: List[str]
        
    Output (shared_store):
        - validation_result: Dict with validation status
        - file_info: Dict with file metadata
        - is_valid: bool
    """
    
    def __init__(self):
        super().__init__()
        self.allowed_extensions = ['pdf', 'docx', 'txt', 'md']
        self.max_file_size = 52428800  # 50MB
        self.allowed_document_types = ['biblical', 'theological']
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs and prepare execution."""
        required_keys = ['uploaded_file', 'document_type']
        missing_keys = [key for key in required_keys if key not in shared_store]
        
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        uploaded_file = shared_store['uploaded_file']
        if not hasattr(uploaded_file, 'filename') or not uploaded_file.filename:
            raise ValueError("Invalid file object or missing filename")
        
        return {
            'uploaded_file': uploaded_file,
            'document_type': shared_store['document_type'],
            'category': shared_store.get('category'),
            'max_file_size': shared_store.get('max_file_size', self.max_file_size),
            'allowed_extensions': shared_store.get('allowed_extensions', self.allowed_extensions)
        }
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Core file validation logic."""
        uploaded_file = data['uploaded_file']
        document_type = data['document_type']
        max_file_size = data['max_file_size']
        allowed_extensions = data['allowed_extensions']
        
        validation_errors = []
        
        # Validate filename and extension
        filename = uploaded_file.filename
        file_extension = Path(filename).suffix.lower().lstrip('.')
        
        if not file_extension:
            validation_errors.append("File has no extension")
        elif file_extension not in allowed_extensions:
            validation_errors.append(f"File type .{file_extension} not allowed. Allowed types: {allowed_extensions}")
        
        # Validate document type
        if document_type not in self.allowed_document_types:
            validation_errors.append(f"Invalid document type: {document_type}")
        
        # Get file size with proper pointer management
        file_size = 0
        if hasattr(uploaded_file, 'size') and uploaded_file.size:
            file_size = uploaded_file.size
        else:
            # Save current position
            current_position = uploaded_file.file.tell() if hasattr(uploaded_file.file, 'tell') else 0
            
            # Read file to get size if not provided
            content = await uploaded_file.read()
            file_size = len(content)
            
            # Reset file pointer to original position
            try:
                await uploaded_file.seek(current_position)
            except Exception:
                # If seek fails, try to reset to beginning
                try:
                    await uploaded_file.seek(0)
                except Exception:
                    # If all else fails, re-read the content for subsequent operations
                    pass
        
        # Validate file size
        if file_size > max_file_size:
            validation_errors.append(f"File size {file_size} exceeds maximum {max_file_size} bytes")
        
        if file_size == 0:
            validation_errors.append("File is empty")
        
        # Detect MIME type with proper pointer management
        mime_type = mimetypes.guess_type(filename)[0]
        if not mime_type:
            # Try to detect from content if available
            try:
                import magic
                # Save current position
                current_position = uploaded_file.file.tell() if hasattr(uploaded_file.file, 'tell') else 0
                
                # Read first 1KB for MIME detection
                content_sample = await uploaded_file.read(1024)
                
                # Reset file pointer to original position
                try:
                    await uploaded_file.seek(current_position)
                except Exception:
                    # If seek fails, try to reset to beginning
                    try:
                        await uploaded_file.seek(0)
                    except Exception:
                        pass
                
                mime_type = magic.from_buffer(content_sample, mime=True)
            except ImportError:
                mime_type = 'application/octet-stream'
            except Exception:
                # If magic detection fails, use fallback
                mime_type = 'application/octet-stream'
        
        # Security validation - basic MIME type check
        expected_mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown'
        }
        
        expected_mime = expected_mime_types.get(file_extension)
        if expected_mime and mime_type != expected_mime:
            # Allow some common variations
            if not (file_extension == 'md' and mime_type in ['text/plain', 'text/x-markdown']):
                validation_errors.append(f"MIME type {mime_type} doesn't match extension .{file_extension}")
        
        is_valid = len(validation_errors) == 0
        
        return {
            'is_valid': is_valid,
            'validation_errors': validation_errors,
            'file_info': {
                'filename': filename,
                'file_extension': file_extension,
                'file_size': file_size,
                'mime_type': mime_type,
                'document_type': document_type,
                'category': data.get('category')
            }
        }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> None:
        """Update shared store with validation results."""
        shared_store['validation_result'] = result
        shared_store['is_valid'] = result['is_valid']
        shared_store['file_info'] = result['file_info']
        
        if not result['is_valid']:
            shared_store['validation_errors'] = result['validation_errors']