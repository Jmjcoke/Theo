"""
Document Upload Flow for orchestrating document upload process.

This flow orchestrates the complete document upload workflow using
the three document upload nodes with proper error handling.

Cookbook Reference: pocketflow-fastapi-background
"""
from typing import Dict, Any, Optional
from pocketflow import AsyncFlow
from databases import Database
from src.nodes.documents import (
    DocumentValidationNode,
    DocumentStorageNode,
    JobDispatchNode
)


class DocumentUploadFlow(AsyncFlow):
    """
    Orchestrates the complete document upload workflow.
    
    Coordinates validation, storage, and job dispatch for uploaded documents
    with proper error handling and rollback mechanisms.
    
    Flow sequence:
    1. DocumentValidationNode - validates file and metadata
    2. DocumentStorageNode - stores file and creates database record
    3. JobDispatchNode - dispatches background processing job
    
    Input (shared_store):
        - uploaded_file: UploadFile object from FastAPI
        - document_type: str ('biblical' | 'theological')
        - category: Optional[str]
        - uploaded_by: str (user UUID)
        - upload_dir: str (storage directory)
        - database: Database connection
        - celery_app: Celery application instance
        
    Output (shared_store):
        - document_id: str (UUID of created document)
        - file_path: str (stored file path)
        - job_id: str (Celery job UUID)
        - upload_success: bool
        - upload_result: Dict with complete results
    """
    
    def __init__(self, database: Optional[Database] = None, celery_app=None, upload_dir: Optional[str] = None):
        super().__init__()
        self.validation_node = DocumentValidationNode()
        self.storage_node = DocumentStorageNode(database=database, upload_dir=upload_dir)
        self.job_dispatch_node = JobDispatchNode(celery_app=celery_app)
        self.database = database
        self.celery_app = celery_app
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete document upload workflow.
        
        Args:
            shared_store: Dictionary containing input data
            
        Returns:
            Dictionary with upload results and status
        """
        try:
            # Initialize shared store with dependencies
            shared_store.setdefault('database', self.database)
            shared_store.setdefault('celery_app', self.celery_app)
            
            # Step 1: Validate uploaded file and metadata
            await self.validation_node.run(shared_store)
            
            if not shared_store.get('is_valid', False):
                return self._create_error_result(
                    'validation_failed',
                    f"File validation failed: {shared_store.get('validation_errors', [])}",
                    shared_store
                )
            
            # Step 2: Store file and create database record
            await self.storage_node.run(shared_store)
            
            storage_result = shared_store.get('storage_result', {})
            if not storage_result.get('success', False):
                return self._create_error_result(
                    'storage_failed',
                    f"File storage failed: {storage_result.get('error', 'Unknown error')}",
                    shared_store
                )
            
            # Step 3: Dispatch background processing job
            await self.job_dispatch_node.run(shared_store)
            
            dispatch_result = shared_store.get('dispatch_result', {})
            if not dispatch_result.get('success', False):
                # Storage succeeded but job dispatch failed - flag for cleanup
                await self._handle_job_dispatch_failure(shared_store)
                return self._create_error_result(
                    'job_dispatch_failed',
                    f"Job dispatch failed: {dispatch_result.get('error', 'Unknown error')}",
                    shared_store
                )
            
            # Success - return complete results
            return self._create_success_result(shared_store)
            
        except Exception as e:
            # Handle unexpected errors with rollback
            await self._handle_flow_error(e, shared_store)
            return self._create_error_result(
                'flow_error',
                f"Unexpected error in upload flow: {str(e)}",
                shared_store
            )
    
    def _create_success_result(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Create success result dictionary."""
        file_info = shared_store.get('file_info', {})
        
        return {
            'upload_success': True,
            'document_id': shared_store.get('document_id'),
            'filename': file_info.get('filename'),
            'document_type': file_info.get('document_type'),
            'processing_status': 'queued',
            'job_id': shared_store.get('job_id'),
            'file_path': shared_store.get('file_path'),
            'uploaded_at': shared_store.get('storage_result', {}).get('created_at'),
            'file_size': file_info.get('file_size'),
            'mime_type': file_info.get('mime_type')
        }
    
    def _create_error_result(self, error_type: str, error_message: str, 
                           shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            'upload_success': False,
            'error_type': error_type,
            'error_message': error_message,
            'document_id': shared_store.get('document_id'),
            'file_path': shared_store.get('file_path'),
            'validation_errors': shared_store.get('validation_errors'),
            'storage_error': shared_store.get('storage_error'),
            'dispatch_error': shared_store.get('dispatch_error')
        }
    
    async def _handle_job_dispatch_failure(self, shared_store: Dict[str, Any]) -> None:
        """Handle job dispatch failure by updating document status."""
        if self.database and shared_store.get('document_id'):
            try:
                # Update document status to 'failed' since job dispatch failed
                query = """
                UPDATE documents 
                SET processing_status = 'failed', 
                    metadata = jsonb_set(metadata, '{error}', '"Job dispatch failed"'),
                    updated_at = NOW()
                WHERE id = :document_id
                """
                await self.database.execute(query, {'document_id': shared_store['document_id']})
            except Exception as e:
                # Log error but don't fail the entire flow
                pass
    
    async def _handle_flow_error(self, error: Exception, shared_store: Dict[str, Any]) -> None:
        """Handle unexpected flow errors with cleanup."""
        # Clean up any created files
        if shared_store.get('file_path'):
            try:
                import os
                if os.path.exists(shared_store['file_path']):
                    os.remove(shared_store['file_path'])
            except Exception:
                pass  # Best effort cleanup
        
        # Update database record if it exists
        if self.database and shared_store.get('document_id'):
            try:
                query = """
                UPDATE documents 
                SET processing_status = 'failed',
                    metadata = jsonb_set(metadata, '{error}', :error_msg),
                    updated_at = NOW()
                WHERE id = :document_id
                """
                await self.database.execute(query, {
                    'document_id': shared_store['document_id'],
                    'error_msg': f'"{str(error)}"'
                })
            except Exception:
                pass  # Best effort cleanup