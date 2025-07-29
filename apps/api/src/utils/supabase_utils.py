"""
SupabaseUtils utility class for Supabase database operations

Provides vector data validation, preprocessing, and batch operations
to support the SupabaseStorageNode while maintaining code organization.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client


class SupabaseUtils:
    """Utility class for Supabase vector database operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client: Optional[Client] = None
    
    def create_client(self) -> Optional[Client]:
        """Create and return authenticated Supabase client, or None if not configured"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            self.logger.warning("Supabase not configured (missing SUPABASE_URL or SUPABASE_SERVICE_KEY). Using test mode.")
            return None
        
        self.client = create_client(supabase_url, supabase_key)
        return self.client
    
    def validate_chunk_structure(self, chunks: List[Dict[str, Any]]) -> bool:
        """Validate embedded chunks structure and dimensions"""
        if not chunks or not isinstance(chunks, list):
            raise ValueError("Embedded chunks must be a non-empty list")
        
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise ValueError(f"Chunk {i} must be a dictionary")
            
            required_keys = ['content', 'embedding', 'chunk_index']
            for key in required_keys:
                if key not in chunk:
                    raise ValueError(f"Chunk {i} missing required key '{key}'")
            
            # Validate embedding dimensions
            if len(chunk['embedding']) != 1536:
                raise ValueError(f"Chunk {i} embedding must be 1536 dimensions")
        
        return True
    
    def map_chunk_to_db_format(self, chunk: Dict[str, Any], document_id: int) -> Dict[str, Any]:
        """Map chunk data to database schema format"""
        db_chunk = {
            'document_id': document_id,
            'chunk_index': chunk['chunk_index'],
            'content': chunk['content'],
            'embedding': chunk['embedding']
        }
        
        # Add metadata based on chunk type
        metadata = chunk.get('metadata', {})
        chunk_type = chunk.get('chunk_type', 'unknown')
        
        if chunk_type == 'biblical':
            db_chunk.update({
                'biblical_version': metadata.get('version'),
                'biblical_book': metadata.get('book'),
                'biblical_chapter': metadata.get('chapter'),
                'biblical_verse_start': metadata.get('verse_start'),
                'biblical_verse_end': metadata.get('verse_end')
            })
        elif chunk_type == 'theological':
            db_chunk.update({
                'theological_document_name': metadata.get('document_name'),
                'theological_page_number': metadata.get('page_number'),
                'theological_section': metadata.get('section')
            })
        
        return db_chunk
    
    async def batch_insert_chunks(self, client: Client, chunks: List[Dict[str, Any]], 
                                  document_id: int, batch_size: int = 100) -> Dict[str, Any]:
        """Perform batch insertion of chunks with error handling"""
        stored_count = 0
        failed_insertions = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_data = []
            
            for chunk in batch:
                db_chunk = self.map_chunk_to_db_format(chunk, document_id)
                batch_data.append(db_chunk)
            
            # Insert batch to Supabase
            try:
                result = client.table('document_chunks').insert(batch_data).execute()
                stored_count += len(batch_data)
                self.logger.info(f"Stored batch {i//batch_size + 1}: {len(batch_data)} chunks")
                
            except Exception as batch_error:
                self.logger.error(f"Batch insertion failed: {str(batch_error)}")
                failed_insertions.extend([chunk['chunk_index'] for chunk in batch])
        
        return {
            'stored_count': stored_count,
            'failed_insertions': failed_insertions,
            'total_processed': len(chunks)
        } 