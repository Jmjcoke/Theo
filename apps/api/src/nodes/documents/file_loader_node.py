"""
File Loader Node for document processing pipeline.
Cookbook Reference: pocketflow-external-service / pocketflow-rag
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pocketflow import AsyncNode
from databases import Database
from ...utils.file_readers import FileReaderUtils
from ...utils.document_metadata_utils import DocumentMetadataUtils


class FileLoaderNode(AsyncNode):
    """
    Loads document content for processing pipeline.
    
    Input: document_id, database
    Output: document_content, document_metadata, file_info
    """
    
    def __init__(self, database: Optional[Database] = None):
        super().__init__()
        self.database = database
        self.file_reader = FileReaderUtils()
        self.metadata_utils = DocumentMetadataUtils()
        self.logger = logging.getLogger(__name__)
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document_id and prepare execution."""
        if 'document_id' not in shared_store:
            raise ValueError("Missing required key: document_id")
        
        database = shared_store.get('database', self.database)
        if not database:
            raise ValueError("Database connection required")
        
        return {
            'document_id': shared_store['document_id'],
            'database': database
        }
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Load document content and metadata from storage."""
        document_id = data['document_id']
        database = data['database']
        
        try:
            self.logger.info(f"Loading document: {document_id}")
            doc_metadata = await self.metadata_utils.get_document_metadata(database, document_id)
            if not doc_metadata:
                self.logger.warning(f"Document not found: {document_id}")
                return {
                    'success': False,
                    'error': f'Document not found: {document_id}',
                    'document_content': None,
                    'document_metadata': None
                }
            
            content = await self.file_reader.read_file_content(
                doc_metadata['file_path'], 
                doc_metadata['mime_type']
            )
            
            if content is None:
                self.logger.error(f"Failed to read file: {doc_metadata['file_path']}")
                return {
                    'success': False,
                    'error': f'Failed to read file: {doc_metadata["file_path"]}',
                    'document_content': None,
                    'document_metadata': doc_metadata
                }
            
            return {
                'success': True,
                'document_content': content,
                'document_metadata': doc_metadata,
                'file_info': {
                    'filename': doc_metadata['original_filename'],
                    'file_size': doc_metadata['file_size'],
                    'mime_type': doc_metadata['mime_type']
                },
                'processing_started_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading document {document_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'document_content': None,
                'document_metadata': None
            }
    
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> None:
        """Update shared store and database status."""
        shared_store['file_loader_result'] = result
        
        if result['success']:
            shared_store['document_content'] = result['document_content']
            shared_store['document_metadata'] = result['document_metadata']
            shared_store['file_info'] = result['file_info']
            shared_store['processing_started_at'] = result['processing_started_at']
            
            if 'database' in shared_store:
                await self.metadata_utils.update_processing_status(
                    shared_store['database'], 
                    shared_store['document_id']
                )
        else:
            shared_store['file_loader_error'] = result.get('error')
    
