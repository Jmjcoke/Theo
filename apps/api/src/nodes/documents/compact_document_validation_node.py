"""
CompactDocumentValidationNode for file and metadata validation.

Streamlined replacement for document_validation_node.py to comply with PocketFlow 150-line limit.
Uses DocumentValidationRules utility for validation logic.
"""

import mimetypes
from typing import Dict, Any
from pathlib import Path
from pocketflow import AsyncNode
from ...utils.validation_rules import DocumentValidationRules

import logging
logger = logging.getLogger(__name__)


class CompactDocumentValidationNode(AsyncNode):
    """Validates document files and metadata for upload processing."""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate inputs and prepare execution."""
        try:
            required_keys = ['uploaded_file', 'document_type']
            missing_keys = [key for key in required_keys if key not in shared_store]
            
            if missing_keys:
                return {"error": f"Missing required keys: {missing_keys}"}
                
            uploaded_file = shared_store['uploaded_file']
            if not hasattr(uploaded_file, 'filename') or not uploaded_file.filename:
                return {"error": "Invalid file object or missing filename"}
                
            return {"success": True}
            
        except Exception as e:
            logger.error(f"CompactDocumentValidationNode prep error: {str(e)}")
            return {"error": f"Document validation preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute file validation using DocumentValidationRules."""
        try:
            uploaded_file = shared_store['uploaded_file']
            document_type = shared_store['document_type']
            max_file_size = shared_store.get('max_file_size', DocumentValidationRules.MAX_FILE_SIZE) 
            allowed_extensions = shared_store.get('allowed_extensions', DocumentValidationRules.ALLOWED_EXTENSIONS)
            
            validation_errors = []
            
            # Validate filename and extension
            filename = uploaded_file.filename
            file_extension = Path(filename).suffix.lower().lstrip('.')
            
            if not file_extension:
                validation_errors.append("File has no extension")
            elif file_extension not in allowed_extensions:
                validation_errors.append(f"File type .{file_extension} not allowed")
            
            # Validate using DocumentValidationRules
            if DocumentValidationRules.is_dangerous_extension(file_extension):
                validation_errors.append(f"Dangerous file type: .{file_extension}")
            
            if not DocumentValidationRules.is_valid_document_type(document_type):
                validation_errors.append(f"Invalid document type: {document_type}")
            
            file_size = await self._get_file_size(uploaded_file)
            
            if file_size > max_file_size:
                validation_errors.append(f"File size {file_size} exceeds maximum {max_file_size}")
            elif file_size == 0:
                validation_errors.append("File is empty")
            
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            if not DocumentValidationRules.is_valid_mime_type(file_extension, mime_type):
                validation_errors.append(f"MIME type mismatch for .{file_extension}")
            
            is_valid = len(validation_errors) == 0
            
            return {
                'success': True,
                'is_valid': is_valid,
                'validation_errors': validation_errors,
                'file_info': {
                    'filename': filename,
                    'file_extension': file_extension,
                    'file_size': file_size,
                    'mime_type': mime_type,
                    'document_type': document_type,
                    'category': shared_store.get('category')
                }
            }
            
        except Exception as e:
            error_msg = f"Document validation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'is_valid': False,
                'validation_errors': [error_msg],
                'file_info': {}
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store validation results in shared store."""
        try:
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                shared_store['validation_result'] = exec_result
                shared_store['is_valid'] = exec_result.get('is_valid', False)
                shared_store['file_info'] = exec_result.get('file_info', {})
                
                if not exec_result.get('is_valid', False):
                    shared_store['validation_errors'] = exec_result.get('validation_errors', [])
                
                return {"next_state": "validated"}
            else:
                shared_store['validation_result'] = exec_result
                shared_store['is_valid'] = False
                shared_store['validation_errors'] = exec_result.get('validation_errors', [])
                return {"next_state": "failed"}
                
        except Exception as e:
            logger.error(f"CompactDocumentValidationNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    async def _get_file_size(self, uploaded_file) -> int:
        """Get file size with proper pointer management."""
        try:
            if hasattr(uploaded_file, 'size') and uploaded_file.size:
                return uploaded_file.size
            
            # Save current position
            current_position = uploaded_file.file.tell() if hasattr(uploaded_file.file, 'tell') else 0
            
            # Read file to get size
            content = await uploaded_file.read()
            file_size = len(content)
            
            # Reset file pointer
            try:
                await uploaded_file.seek(current_position)
            except Exception:
                pass
            return file_size
        except Exception:
            return 0