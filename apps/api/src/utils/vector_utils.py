"""
Vector Database Utilities

Provides utilities for vector database operations including deletion.
"""

import logging
import os
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


async def delete_document_vectors(document_id: str) -> int:
    """
    Delete all vector embeddings for a specific document from Supabase.
    
    Args:
        document_id: The ID of the document whose vectors to delete
        
    Returns:
        Number of vectors deleted
    """
    client = None
    try:
        # Create Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
        
        client = create_client(supabase_url, supabase_key)
        
        # Delete all chunks for this document
        result = client.table('document_chunks').delete().eq('document_id', document_id).execute()
        
        # Get count of deleted records
        deleted_count = len(result.data) if result.data else 0
        
        logger.info(f"Deleted {deleted_count} vector chunks for document {document_id}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to delete vectors for document {document_id}: {str(e)}")
        raise 