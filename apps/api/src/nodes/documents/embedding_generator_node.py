"""
EmbeddingGeneratorNode for generating vector embeddings from text chunks using OpenAI

Following PocketFlow AsyncNode pattern for OpenAI API integration.
Handles text chunks from DocumentChunkerNode and generates 1536-dimensional embeddings.
"""

from typing import Dict, Any, List
from pocketflow import AsyncNode
from ...utils.embedding_utils import EmbeddingUtils


class EmbeddingGeneratorNode(AsyncNode):
    """Generates vector embeddings for text chunks using OpenAI API following PocketFlow patterns"""
    
    def __init__(self):
        """Initialize the embedding generator node"""
        super().__init__()
        self.embedding_utils = EmbeddingUtils()
    
    async def prep(self, shared_store: Dict[str, Any]) -> bool:
        """Validate chunk data and API configuration"""
        try:
            required_keys = ['document_chunks', 'chunk_count', 'document_id']
            for key in required_keys:
                if key not in shared_store:
                    shared_store['error'] = f"Missing required key '{key}' for embedding generation"
                    return False
            
            document_chunks = shared_store['document_chunks']
            if not document_chunks or not isinstance(document_chunks, list):
                shared_store['error'] = "Document chunks must be a non-empty list"
                return False
            
            # Validate each chunk has required content
            for i, chunk in enumerate(document_chunks):
                if not isinstance(chunk, dict) or 'content' not in chunk:
                    shared_store['error'] = f"Chunk {i} missing required 'content' field"
                    return False
                if not chunk['content'] or not isinstance(chunk['content'], str):
                    shared_store['error'] = f"Chunk {i} content must be a non-empty string"
                    return False
            
            # Validate API configuration
            if not await self.embedding_utils.validate_api_config():
                shared_store['error'] = "OpenAI API configuration validation failed"
                return False
            
            return True
            
        except Exception as e:
            shared_store['error'] = f"Embedding generator prep failed: {str(e)}"
            return False
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings for all chunks with error handling"""
        try:
            document_chunks = data['document_chunks']
            document_id = data['document_id']
            
            # Generate embeddings with batch processing and error handling
            embedded_chunks, failed_chunks = await self.embedding_utils.generate_embeddings_batch(
                chunks=document_chunks,
                document_id=document_id
            )
            
            return {
                'success': True,
                'embedded_chunks': embedded_chunks,
                'embedding_count': len(embedded_chunks),
                'failed_embeddings': failed_chunks,
                'total_processed': len(document_chunks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to generate embeddings: {str(e)}",
                'embedded_chunks': [],
                'failed_embeddings': []
            }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Update shared store with embedded chunks and metadata"""
        try:
            if not result.get('success', False):
                shared_store['error'] = result.get('error', 'Unknown embedding error')
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown embedding error'),
                    'embeddings_stored': False
                }
            
            embedded_chunks = result['embedded_chunks']
            embedding_count = result['embedding_count']
            failed_embeddings = result.get('failed_embeddings', [])
            
            # Store embedded chunks in shared store
            shared_store['embedded_chunks'] = embedded_chunks
            shared_store['embedding_count'] = embedding_count
            shared_store['failed_embeddings'] = failed_embeddings
            shared_store['embedding_completed_at'] = self.embedding_utils.get_timestamp()
            shared_store['embedding_metadata'] = {
                'model': 'text-embedding-ada-002',
                'dimensions': 1536,
                'total_processed': result['total_processed'],
                'successful': embedding_count,
                'failed': len(failed_embeddings),
                'api_version': 'v1'
            }
            
            return {
                'success': True,
                'embeddings_stored': True,
                'embedding_count': embedding_count,
                'failed_count': len(failed_embeddings),
                'embedding_metadata': shared_store['embedding_metadata']
            }
            
        except Exception as e:
            shared_store['error'] = f'Post-embedding failed: {str(e)}'
            return {
                'success': False,
                'error': f'Post-embedding failed: {str(e)}',
                'embeddings_stored': False
            }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete embedding generation workflow"""
        if not await self.prep(shared_store):
            return {
                'success': False,
                'error': shared_store.get('error', 'Preparation failed'),
                'embeddings_stored': False
            }
        
        exec_result = await self.exec(shared_store)
        final_result = await self.post(exec_result, shared_store)
        
        return final_result