"""
CompactSupabaseHttpStorageNode for storing embedded chunks in Supabase via HTTP API.

Streamlined replacement for supabase_http_storage_node.py to comply with PocketFlow 150-line limit.
Stores text chunks with embeddings directly into Supabase documents table.
"""

import logging
import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pocketflow import AsyncNode

logger = logging.getLogger(__name__)


class CompactSupabaseHttpStorageNode(AsyncNode):
    """Stores embedded chunks in Supabase via direct HTTP API calls."""
    
    def __init__(self):
        super().__init__()
        self.batch_size = 50
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
    async def prep_async(self, shared_store: Dict[str, Any]) -> dict:
        """Validate embedded chunks and prepare for HTTP storage."""
        try:
            required_keys = ['embedded_chunks', 'embedding_count', 'document_id']
            for key in required_keys:
                if key not in shared_store:
                    return {"error": f"Missing required key '{key}' for Supabase HTTP storage"}
            
            embedded_chunks = shared_store['embedded_chunks']
            if not embedded_chunks or not isinstance(embedded_chunks, list):
                return {"error": "embedded_chunks must be a non-empty list"}
            
            # Basic chunk validation
            for i, chunk in enumerate(embedded_chunks[:3]):  # Check first 3 only
                if not isinstance(chunk, dict) or 'embedding' not in chunk or 'content' not in chunk:
                    return {"error": f"Invalid chunk structure at index {i}"}
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"CompactSupabaseHttpStorageNode prep error: {str(e)}")
            return {"error": f"Storage preparation failed: {str(e)}"}
    
    async def exec_async(self, shared_store: Dict[str, Any]) -> dict:
        """Execute HTTP storage of embedded chunks to Supabase."""
        try:
            chunks = shared_store['embedded_chunks']
            document_id = shared_store['document_id']
            
            # Test mode if no Supabase config
            if not self.supabase_url or not self.supabase_service_key:
                logger.info(f"Test mode: Would store {len(chunks)} chunks for document {document_id}")
                return {
                    'success': True,
                    'stored_count': len(chunks),
                    'test_mode': True,
                    'total_chunks': len(chunks),
                    'storage_method': 'test_mode'
                }
            
            # Store chunks in batches
            stored_count = 0
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                batch_result = await self._store_batch_http(batch, document_id)
                
                if batch_result['success']:
                    stored_count += batch_result['count']
                else:
                    logger.error(f"Batch {i//self.batch_size + 1} failed: {batch_result['error']}")
            
            return {
                'success': stored_count > 0,
                'stored_count': stored_count,
                'total_chunks': len(chunks),
                'storage_method': 'http_api'
            }
            
        except Exception as e:
            error_msg = f"HTTP storage execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stored_count': 0,
                'total_chunks': len(shared_store.get('embedded_chunks', []))
            }
    
    async def post_async(self, shared_store: Dict[str, Any]) -> dict:
        """Store HTTP storage results in shared store."""
        try:
            exec_result = shared_store.get('exec_result', {})
            
            if exec_result.get('success', False):
                shared_store['storage_result'] = exec_result
                shared_store['stored_count'] = exec_result.get('stored_count', 0)
                shared_store['storage_method'] = exec_result.get('storage_method', 'unknown')
                
                logger.info(f"HTTP storage completed: {exec_result.get('stored_count', 0)} chunks stored")
                return {"next_state": "stored"}
            else:
                shared_store['storage_error'] = exec_result.get('error', 'Unknown storage error')
                shared_store['stored_count'] = exec_result.get('stored_count', 0)
                
                logger.error(f"HTTP storage failed: {exec_result.get('error')}")
                return {"next_state": "failed"}
                
        except Exception as e:
            logger.error(f"CompactSupabaseHttpStorageNode post error: {str(e)}")
            return {"next_state": "failed"}
    
    async def _store_batch_http(self, batch: List[Dict[str, Any]], document_id: str) -> Dict[str, Any]:
        """Store a batch of chunks via HTTP POST to Supabase REST API."""
        try:
            url = f"{self.supabase_url}/rest/v1/documents"
            headers = {
                'apikey': self.supabase_service_key,
                'Authorization': f'Bearer {self.supabase_service_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            }
            
            # Prepare batch data
            batch_data = []
            for chunk in batch:
                chunk_data = {
                    'content': chunk['content'],
                    'embedding': chunk['embedding'],
                    'document_id': document_id,
                    'metadata': chunk.get('metadata', {}),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                batch_data.append(chunk_data)
            
            # Make HTTP request
            response = requests.post(url, json=batch_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return {'success': True, 'count': len(batch_data)}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                return {'success': False, 'error': error_msg, 'count': 0}
                
        except Exception as e:
            return {'success': False, 'error': str(e), 'count': 0}