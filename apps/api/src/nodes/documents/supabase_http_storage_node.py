"""
SupabaseHttpStorageNode for storing embedded chunks in Supabase via HTTP API

Stores text chunks with 1536-dimensional embeddings directly into your Supabase
documents table using HTTP requests to the REST API.
"""

import logging
import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pocketflow import AsyncNode
from databases import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseHttpStorageNode(AsyncNode):
    """Stores embedded chunks in Supabase via direct HTTP API calls"""
    
    def __init__(self, sqlite_database: Optional[Database] = None):
        """Initialize HTTP-based Supabase storage node"""
        super().__init__()
        self.sqlite_database = sqlite_database
        self.logger = logging.getLogger(__name__)
        self.batch_size = 50  # Smaller batches for HTTP requests
        
        # Get Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_service_key:
            self.logger.warning("Supabase not configured (missing SUPABASE_URL or SUPABASE_SERVICE_KEY)")
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate embedded chunks and prepare for HTTP storage"""
        try:
            # Validate required shared store keys
            required_keys = ['embedded_chunks', 'embedding_count', 'document_id']
            for key in required_keys:
                if key not in shared_store:
                    raise ValueError(f"Missing required key '{key}' for Supabase HTTP storage")
            
            embedded_chunks = shared_store['embedded_chunks']
            
            # Validate chunk structure
            if not embedded_chunks or not isinstance(embedded_chunks, list):
                raise ValueError("Embedded chunks must be a non-empty list")
            
            for i, chunk in enumerate(embedded_chunks):
                if not isinstance(chunk, dict):
                    raise ValueError(f"Chunk {i} must be a dictionary")
                
                # Required keys for HTTP storage
                required_chunk_keys = ['content', 'embedding']
                for key in required_chunk_keys:
                    if key not in chunk:
                        raise ValueError(f"Chunk {i} missing required key '{key}'")
                
                # Validate embedding dimensions
                embedding = chunk['embedding']
                if not isinstance(embedding, list) or len(embedding) != 1536:
                    raise ValueError(f"Chunk {i} embedding must be a list of 1536 floats")
            
            if self.supabase_url and self.supabase_service_key:
                self.logger.info(f"Prepared for HTTP storage of {len(embedded_chunks)} chunks to Supabase")
            else:
                self.logger.info(f"Prepared for test mode processing of {len(embedded_chunks)} chunks (Supabase not configured)")
            
            return {
                'chunks': embedded_chunks,
                'document_id': shared_store['document_id'],
                'chunk_count': len(embedded_chunks),
                'ready_for_storage': True
            }
            
        except Exception as e:
            self.logger.error(f"SupabaseHttpStorageNode prep failed: {str(e)}")
            return {
                'ready_for_storage': False,
                'error': str(e)
            }
    
    async def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP storage of chunks to Supabase documents table"""
        try:
            if not prep_data.get('ready_for_storage', False):
                return {
                    'success': False,
                    'error': prep_data.get('error', 'Preparation failed')
                }
            
            chunks = prep_data['chunks']
            document_id = prep_data['document_id']
            
            # Skip actual storage if not configured (test mode)
            if not self.supabase_url or not self.supabase_service_key:
                self.logger.info(f"Test mode: Would store {len(chunks)} chunks for document {document_id}")
                return {
                    'success': True,
                    'stored_count': len(chunks),
                    'test_mode': True
                }
            
            # Store chunks in batches via HTTP
            stored_count = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                batch_result = await self._store_batch_http(batch, document_id)
                
                if batch_result['success']:
                    stored_count += batch_result['count']
                    self.logger.info(f"Stored batch {i//self.batch_size + 1}: {batch_result['count']} chunks")
                else:
                    self.logger.error(f"Batch {i//self.batch_size + 1} failed: {batch_result['error']}")
                    # Continue with other batches but log the failure
            
            self.logger.info(f"HTTP storage completed: {stored_count}/{len(chunks)} chunks stored")
            
            return {
                'success': stored_count > 0,
                'stored_count': stored_count,
                'total_chunks': len(chunks),
                'storage_method': 'http_api'
            }
            
        except Exception as e:
            self.logger.error(f"SupabaseHttpStorageNode exec failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _store_batch_http(self, batch: List[Dict[str, Any]], document_id: str) -> Dict[str, Any]:
        """Store a batch of chunks via HTTP POST to Supabase REST API"""
        try:
            # Prepare HTTP request
            url = f"{self.supabase_url}/rest/v1/documents"
            headers = {
                'apikey': self.supabase_service_key,
                'Authorization': f'Bearer {self.supabase_service_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            }
            
            # Format data for your Supabase documents table schema
            payload = []
            for chunk in batch:
                payload.append({
                    'content': chunk['content'],
                    'embedding': chunk['embedding'],
                    'metadata': {
                        'document_id': document_id,
                        'chunk_index': chunk.get('chunk_index', 0),
                        'stored_at': datetime.now(timezone.utc).isoformat()
                    }
                })
            
            # Make HTTP request
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'count': len(batch)
                }
            else:
                self.logger.error(f"HTTP storage failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"HTTP batch storage failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def post(self, exec_result: Dict[str, Any], shared_store: Dict[str, Any]) -> None:
        """Update shared store with storage results"""
        try:
            if exec_result.get('success', False):
                stored_count = exec_result.get('stored_count', 0)
                shared_store['supabase_storage_success'] = True
                shared_store['supabase_stored_count'] = stored_count
                shared_store['stored_chunk_count'] = stored_count  # For flow compatibility
                shared_store['supabase_storage_method'] = exec_result.get('storage_method', 'http_api')
                
                if exec_result.get('test_mode', False):
                    shared_store['supabase_test_mode'] = True
                
                self.logger.info(f"Supabase HTTP storage successful: {exec_result.get('stored_count', 0)} chunks")
            else:
                shared_store['supabase_storage_error'] = exec_result.get('error', 'Unknown storage error')
                self.logger.error(f"Supabase HTTP storage failed: {exec_result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"SupabaseHttpStorageNode post failed: {str(e)}")
            shared_store['supabase_storage_error'] = str(e)