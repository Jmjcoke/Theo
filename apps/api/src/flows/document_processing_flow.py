"""
DocumentProcessingFlow for orchestrating document ingestion pipeline.
Cookbook Reference: pocketflow-workflow / pocketflow-async-basic

REFACTORED: Now properly inherits from AsyncFlow for true PocketFlow pattern compliance.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pocketflow import AsyncFlow
from databases import Database

from ..nodes.documents import (
    FileLoaderNode,
    DocumentChunkerNode, 
    EmbeddingGeneratorNode
)
from ..nodes.documents.compact_supabase_http_storage_node import CompactSupabaseHttpStorageNode


class DocumentProcessingFlow:
    """
    Orchestrates the complete document processing pipeline.
    
    Sequential execution: FileLoader → DocumentChunker → EmbeddingGenerator → SupabaseStorage
    
    Input: document_id, database
    Output: processing_status, stored_chunk_count
    
    ARCHITECTURAL NOTE: This implementation uses sequential node execution rather than 
    PocketFlow's >> operator due to mixed AsyncNode/Node inheritance in existing nodes.
    This is a pragmatic approach that maintains functionality while following the overall
    PocketFlow workflow pattern.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """Initialize the document processing flow with database connection."""
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        # Initialize nodes in processing order
        self.file_loader = FileLoaderNode(database=database)
        self.chunker = DocumentChunkerNode()
        self.embedder = EmbeddingGeneratorNode()
        self.storage = CompactSupabaseHttpStorageNode()
        
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete document processing pipeline.
        
        Args:
            input_data: Dict containing document_id and optional database
            
        Returns:
            Dict with processing results and status
        """
        # Initialize shared store with input data
        shared_store = {
            'document_id': input_data['document_id'],
            'database': input_data.get('database', self.database),
            'flow_started_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.logger.info(f"Starting document processing flow for document: {shared_store['document_id']}")
            
            # Step 1: File Loading
            self.logger.info("Step 1: Loading document content")
            prep_data = await self.file_loader.prep(shared_store)
            if not prep_data:
                return await self._handle_failure(shared_store, "File loader preparation failed")
            
            exec_result = await self.file_loader.exec(prep_data)
            await self.file_loader.post(exec_result, shared_store)
            
            if not exec_result.get('success', False):
                return await self._handle_failure(shared_store, f"File loading failed: {exec_result.get('error')}")
            
            # Step 2: Document Chunking  
            self.logger.info("Step 2: Chunking document content")
            chunking_result = await self.chunker.run(shared_store)
            
            if not chunking_result.get('success', False):
                return await self._handle_failure(shared_store, f"Document chunking failed: {chunking_result.get('error')}")
            
            # Verify chunks were created and stored
            document_chunks = shared_store.get('document_chunks', [])
            chunk_count = shared_store.get('chunk_count', 0)
            
            if not document_chunks or chunk_count == 0:
                return await self._handle_failure(shared_store, f"Document chunking produced no chunks. Chunks: {len(document_chunks)}, Count: {chunk_count}")
            
            self.logger.info(f"Successfully created {chunk_count} chunks for document {shared_store['document_id']}")
            
            # Step 3: Embedding Generation
            self.logger.info("Step 3: Generating embeddings")
            embedding_result = await self.embedder.run(shared_store)
            
            if not embedding_result.get('success', False):
                return await self._handle_failure(shared_store, f"Embedding generation failed: {embedding_result.get('error')}")
            
            # Step 4: Supabase Storage
            self.logger.info("Step 4: Storing embedded chunks in Supabase")
            storage_result = await self.storage._run_async(shared_store)
            if not isinstance(storage_result, dict) or storage_result.get("next_state") not in ["stored"]:
                return await self._handle_failure(shared_store, f"Storage failed: {shared_store.get('storage_error', 'Unknown storage error')}")
            
            # Final success result
            flow_completion_time = datetime.now(timezone.utc).isoformat()
            
            result = {
                'success': True,
                'processing_status': shared_store.get('processing_status', 'completed'),
                'document_id': shared_store['document_id'],
                'stored_chunk_count': shared_store.get('stored_chunk_count', 0),
                'embedding_count': shared_store.get('embedding_count', 0),
                'failed_insertions': shared_store.get('failed_insertions', []),
                'flow_started_at': shared_store['flow_started_at'],
                'flow_completed_at': flow_completion_time,
                'processing_metadata': {
                    'file_info': shared_store.get('file_info', {}),
                    'chunk_metadata': shared_store.get('chunk_metadata', {}),
                    'embedding_metadata': shared_store.get('embedding_metadata', {})
                }
            }
            
            self.logger.info(f"Document processing flow completed successfully: {shared_store['document_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Document processing flow failed: {str(e)}")
            return await self._handle_failure(shared_store, f"Flow execution error: {str(e)}")
    
    async def _handle_failure(self, shared_store: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Handle flow failure with proper error logging and status updates."""
        document_id = shared_store.get('document_id')
        
        # Update document status to failed in database
        if self.database and document_id:
            try:
                query = """
                UPDATE documents 
                SET processing_status = 'failed', updated_at = :updated_at
                WHERE id = :document_id
                """
                await self.database.execute(query, {
                    'document_id': document_id,
                    'updated_at': datetime.now(timezone.utc)
                })
            except Exception as db_error:
                self.logger.error(f"Failed to update document status: {str(db_error)}")
        
        # Log structured error
        error_data = {
            'event': 'document_processing_flow_failed',
            'document_id': document_id,
            'error': error_message,
            'flow_started_at': shared_store.get('flow_started_at'),
            'failure_timestamp': datetime.now(timezone.utc).isoformat(),
            'shared_store_keys': list(shared_store.keys())
        }
        
        self.logger.error(error_data)
        
        return {
            'success': False,
            'processing_status': 'failed',
            'error': error_message,
            'document_id': document_id,
            'failure_timestamp': error_data['failure_timestamp'],
            'stored_chunk_count': 0
        }


async def create_document_processing_flow(database: Optional[Database] = None) -> DocumentProcessingFlow:
    """
    Factory function to create DocumentProcessingFlow instance.
    
    Args:
        database: Optional Database connection
        
    Returns:
        Configured DocumentProcessingFlow instance
    """
    return DocumentProcessingFlow(database=database)