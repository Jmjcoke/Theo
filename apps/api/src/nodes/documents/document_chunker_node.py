"""
DocumentChunkerNode for text chunking based on document type

Following PocketFlow Node pattern for chunking document content.
Handles biblical and theological document types with specific chunking strategies.
"""

from typing import Dict, Any, List
from ...utils.chunking_utils import ChunkingUtils


class DocumentChunkerNode:
    """Chunks document content based on document type following PocketFlow patterns"""
    
    def __init__(self):
        """Initialize the document chunker node"""
        self.chunking_utils = ChunkingUtils()
    
    async def prep(self, shared_store: Dict[str, Any]) -> bool:
        """Validate document content and metadata availability"""
        try:
            required_keys = ['document_content', 'document_metadata', 'document_id']
            for key in required_keys:
                if key not in shared_store:
                    shared_store['error'] = f"Missing required key '{key}' for document chunking"
                    return False
            
            document_content = shared_store['document_content']
            if not document_content or not isinstance(document_content, str):
                shared_store['error'] = "Document content must be a non-empty string"
                return False
            
            document_metadata = shared_store['document_metadata']
            # Handle both 'type' and 'document_type' fields for compatibility
            doc_type = document_metadata.get('type') or document_metadata.get('document_type')
            if not doc_type:
                shared_store['error'] = "Document metadata must include 'type' or 'document_type' field"
                return False
            if doc_type not in ['biblical', 'theological']:
                shared_store['error'] = f"Unsupported document type: {doc_type}"
                return False
            
            return True
            
        except Exception as e:
            shared_store['error'] = f"Document chunker prep failed: {str(e)}"
            return False
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Chunk document content according to type-specific rules"""
        try:
            document_content = data['document_content']
            document_metadata = data['document_metadata']
            document_id = data['document_id']
            doc_type = document_metadata.get('type') or document_metadata.get('document_type')
            
            if doc_type == 'biblical':
                # Check if this is a JSON Bible file for specialized handling
                file_extension = document_metadata.get('file_extension', '').lower()
                if file_extension == '.json':
                    chunks = self.chunking_utils.chunk_json_bible_document(
                        document_content, document_id, document_metadata
                    )
                else:
                    chunks = self.chunking_utils.chunk_biblical_document(
                        document_content, document_id, document_metadata
                    )
            elif doc_type == 'theological':
                chunks = self.chunking_utils.chunk_theological_document(
                    document_content, document_id, document_metadata
                )
            else:
                return {
                    'success': False,
                    'error': f"Unsupported document type: {doc_type}",
                    'chunks': []
                }
            
            return {
                'success': True,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'document_type': doc_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to chunk document: {str(e)}",
                'chunks': []
            }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Update shared store with chunks and update processing status"""
        try:
            if not result.get('success', False):
                shared_store['error'] = result.get('error', 'Unknown chunking error')
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown chunking error'),
                    'chunks_stored': False
                }
            
            chunks = result['chunks']
            chunk_count = result['chunk_count']
            
            # Store chunks in shared store
            shared_store['document_chunks'] = chunks
            shared_store['chunk_count'] = chunk_count
            shared_store['chunking_completed_at'] = self.chunking_utils.get_timestamp()
            shared_store['chunk_metadata'] = {
                'chunking_method': result['document_type'],
                'total_chunks': chunk_count,
                'chunking_strategy': f"{result['document_type']}_standard"
            }
            
            return {
                'success': True,
                'chunks_stored': True,
                'chunk_count': chunk_count,
                'chunk_metadata': shared_store['chunk_metadata']
            }
            
        except Exception as e:
            shared_store['error'] = f'Post-chunking failed: {str(e)}'
            return {
                'success': False,
                'error': f'Post-chunking failed: {str(e)}',
                'chunks_stored': False
            }
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete document chunking workflow"""
        if not await self.prep(shared_store):
            return {
                'success': False,
                'error': shared_store.get('error', 'Preparation failed'),
                'chunks_stored': False
            }
        
        exec_result = await self.exec(shared_store)
        final_result = await self.post(exec_result, shared_store)
        
        return final_result