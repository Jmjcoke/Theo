"""
Validation Rules Utility

Centralized validation rules and configurations for document processing.
Extracted from document_validation_node.py to comply with PocketFlow 150-line limit.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path


class DocumentValidationRules:
    """Centralized validation rules for document processing"""
    
    # File extension configurations
    ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt', 'md']
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 52428800  # 50MB
    MIN_FILE_SIZE = 1  # 1 byte minimum
    
    # Document type configurations
    ALLOWED_DOCUMENT_TYPES = ['biblical', 'theological']
    
    # MIME type mappings
    EXPECTED_MIME_TYPES = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'md': 'text/markdown'
    }
    
    # MIME type variations (acceptable alternatives)
    MIME_TYPE_VARIATIONS = {
        'md': ['text/plain', 'text/x-markdown', 'text/markdown'],
        'txt': ['text/plain', 'application/octet-stream']
    }
    
    # Security: Dangerous file extensions to always reject
    DANGEROUS_EXTENSIONS = [
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar',
        'php', 'asp', 'aspx', 'jsp', 'py', 'rb', 'pl', 'sh', 'ps1'
    ]
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate file extension against allowed types"""
        if allowed_extensions is None:
            allowed_extensions = DocumentValidationRules.ALLOWED_EXTENSIONS
            
        file_extension = Path(filename).suffix.lower().lstrip('.')
        
        if not file_extension:
            return {
                'is_valid': False,
                'error': "File has no extension",
                'extension': None
            }
        
        if file_extension in DocumentValidationRules.DANGEROUS_EXTENSIONS:
            return {
                'is_valid': False,
                'error': f"Dangerous file type .{file_extension} is not allowed",
                'extension': file_extension
            }
        
        if file_extension not in allowed_extensions:
            return {
                'is_valid': False,
                'error': f"File type .{file_extension} not allowed. Allowed types: {allowed_extensions}",
                'extension': file_extension
            }
        
        return {
            'is_valid': True,
            'error': None,
            'extension': file_extension
        }
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: Optional[int] = None, min_size: Optional[int] = None) -> Dict[str, Any]:
        """Validate file size against limits"""
        if max_size is None:
            max_size = DocumentValidationRules.MAX_FILE_SIZE
        if min_size is None:
            min_size = DocumentValidationRules.MIN_FILE_SIZE
        
        if file_size <= 0:
            return {
                'is_valid': False,
                'error': "File is empty or has invalid size",
                'file_size': file_size
            }
        
        if file_size < min_size:
            return {
                'is_valid': False,
                'error': f"File size {file_size} is below minimum {min_size} bytes",
                'file_size': file_size
            }
        
        if file_size > max_size:
            return {
                'is_valid': False,
                'error': f"File size {file_size} exceeds maximum {max_size} bytes",
                'file_size': file_size
            }
        
        return {
            'is_valid': True,
            'error': None,
            'file_size': file_size
        }
    
    @staticmethod
    def validate_document_type(document_type: str, allowed_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate document type against allowed types"""
        if allowed_types is None:
            allowed_types = DocumentValidationRules.ALLOWED_DOCUMENT_TYPES
        
        if document_type not in allowed_types:
            return {
                'is_valid': False,
                'error': f"Invalid document type: {document_type}. Allowed types: {allowed_types}",
                'document_type': document_type
            }
        
        return {
            'is_valid': True,
            'error': None,
            'document_type': document_type
        }
    
    @staticmethod
    def validate_mime_type(mime_type: str, file_extension: str) -> Dict[str, Any]:
        """Validate MIME type matches file extension"""
        expected_mime = DocumentValidationRules.EXPECTED_MIME_TYPES.get(file_extension)
        
        if not expected_mime:
            return {
                'is_valid': True,  # Allow unknown extensions through MIME check
                'error': None,
                'mime_type': mime_type
            }
        
        # Check exact match
        if mime_type == expected_mime:
            return {
                'is_valid': True,
                'error': None,
                'mime_type': mime_type
            }
        
        # Check variations
        variations = DocumentValidationRules.MIME_TYPE_VARIATIONS.get(file_extension, [])
        if mime_type in variations:
            return {
                'is_valid': True,
                'error': None,
                'mime_type': mime_type
            }
        
        return {
            'is_valid': False,
            'error': f"MIME type {mime_type} doesn't match extension .{file_extension}. Expected: {expected_mime}",
            'mime_type': mime_type
        }
    
    @staticmethod
    def get_validation_config(custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get validation configuration with optional overrides"""
        config = {
            'allowed_extensions': DocumentValidationRules.ALLOWED_EXTENSIONS,
            'max_file_size': DocumentValidationRules.MAX_FILE_SIZE,
            'min_file_size': DocumentValidationRules.MIN_FILE_SIZE,
            'allowed_document_types': DocumentValidationRules.ALLOWED_DOCUMENT_TYPES
        }
        
        if custom_config:
            config.update(custom_config)
        
        return config
    
    @staticmethod
    def validate_filename_security(filename: str) -> Dict[str, Any]:
        """Perform security validation on filename"""
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return {
                'is_valid': False,
                'error': "Filename contains path traversal characters",
                'filename': filename
            }
        
        # Check for null bytes
        if '\x00' in filename:
            return {
                'is_valid': False,
                'error': "Filename contains null bytes",
                'filename': filename
            }
        
        # Check filename length
        if len(filename) > 255:
            return {
                'is_valid': False,
                'error': "Filename too long (max 255 characters)",
                'filename': filename
            }
        
        return {
            'is_valid': True,
            'error': None,
            'filename': filename
        }