"""
SupabaseStorageNode for storing embedded chunks in Supabase vector database

Stores text chunks with 1536-dimensional embeddings from EmbeddingGeneratorNode
into Supabase PostgreSQL with pgvector extension for semantic search.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pocketflow import AsyncNode
from databases import Database
from ...utils.supabase_utils import SupabaseUtils


class SupabaseStorageNode(AsyncNode):
    """Stores embedded chunks in Supabase vector database with metadata"""
    
    def __init__(self, sqlite_database: Optional[Database] = None):
        """Initialize Supabase storage node with database connections"""
        super().__init__()
        self.sqlite_database = sqlite_database
        self.supabase_utils = SupabaseUtils()
        self.logger = logging.getLogger(__name__)
        self.batch_size = 100
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate embedded chunks and initialize database connections"""
        try:
            # Validate required shared store keys
            required_keys = ['embedded_chunks', 'embedding_count', 'document_id']
            for key in required_keys:
                if key not in shared_store:
                    raise ValueError(f"Missing required key '{key}' for Supabase storage")
            
            embedded_chunks = shared_store['embedded_chunks']
            
            # Validate chunk structure using utility
            self.supabase_utils.validate_chunk_structure(embedded_chunks)
            
            # Create Supabase client (may be None in test mode)
            supabase_client = self.supabase_utils.create_client()
            
            if supabase_client:
                self.logger.info(f"Prepared for storing {len(embedded_chunks)} chunks to Supabase")
            else:
                self.logger.info(f"Prepared for test mode processing of {len(embedded_chunks)} chunks (Supabase not configured)")
            
            return {
                'chunks': embedded_chunks,
                'document_id': shared_store['document_id'],
                'total_chunks': len(embedded_chunks),
                'client': supabase_client,
                'test_mode': supabase_client is None
            }
            
        except Exception as e:
            self.logger.error(f"Supabase storage prep failed: {str(e)}")
            shared_store['error'] = f"Storage preparation failed: {str(e)}"
            raise
    
    async def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert chunks with embeddings into Supabase database or run in test mode"""
        try:
            chunks = prep_data['chunks']
            document_id = int(prep_data['document_id'])
            client = prep_data['client']
            test_mode = prep_data.get('test_mode', False)
            
            completion_time = datetime.now(timezone.utc)
            
            if test_mode:
                # Test mode: just count chunks without storing to Supabase
                self.logger.info(f"Test mode: processed {len(chunks)} chunks for document {document_id}")
                return {
                    'stored_chunk_count': len(chunks),
                    'failed_insertions': [],
                    'storage_completed_at': completion_time,
                    'document_id': document_id,
                    'total_processed': len(chunks),
                    'test_mode': True
                }
            else:
                # Use utility for batch insertion
                result = await self.supabase_utils.batch_insert_chunks(
                    client, chunks, document_id, self.batch_size
                )
                
                return {
                    'stored_chunk_count': result['stored_count'],
                    'failed_insertions': result['failed_insertions'],
                    'storage_completed_at': completion_time,
                    'document_id': document_id,
                    'total_processed': result['total_processed'],
                    'test_mode': False
                }
            
        except Exception as e:
            self.logger.error(f"Supabase storage execution failed: {str(e)}")
            raise
    
    async def post(self, exec_result: Dict[str, Any], shared_store: Dict[str, Any]) -> str:
        """Update document status and shared store with completion data"""
        try:
            # Update shared store with results
            shared_store['storage_completed_at'] = exec_result['storage_completed_at']
            shared_store['stored_chunk_count'] = exec_result['stored_chunk_count']
            shared_store['failed_insertions'] = exec_result['failed_insertions']
            
            # Update SQLite document status to 'completed' if all chunks stored successfully
            if len(exec_result['failed_insertions']) == 0:
                if self.sqlite_database:
                    query = """
                        UPDATE documents 
                        SET processing_status = 'completed', updated_at = :updated_at 
                        WHERE id = :document_id
                    """
                    await self.sqlite_database.execute(
                        query, 
                        {
                            'document_id': exec_result['document_id'],
                            'updated_at': exec_result['storage_completed_at']
                        }
                    )
                
                self.logger.info(f"Document {exec_result['document_id']} processing completed successfully")
                shared_store['processing_status'] = 'completed'
            else:
                self.logger.warning(f"Document {exec_result['document_id']} had {len(exec_result['failed_insertions'])} failed insertions")
                shared_store['processing_status'] = 'partial_failure'
            
            return "default"
            
        except Exception as e:
            self.logger.error(f"Post-processing failed: {str(e)}")
            shared_store['error'] = f"Post-processing failed: {str(e)}"
            raise 