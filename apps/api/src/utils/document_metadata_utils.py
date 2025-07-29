"""
Document metadata utilities extracted from FileLoaderNode
to maintain PocketFlow 150-line limit compliance.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from databases import Database


class DocumentMetadataUtils:
    """Utility class for document metadata operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_document_metadata(self, database: Database, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata from database."""
        # Handle both SQLite (local) and PostgreSQL (database) connections
        if hasattr(database, 'execute'):
            # Databases library connection (PostgreSQL)
            query = """
            SELECT id, filename, original_filename, file_path, document_type,
                   processing_status, uploaded_by, file_size, mime_type, metadata,
                   created_at, updated_at
            FROM documents WHERE id = :document_id
            """
            result = await database.fetch_one(query, {'document_id': document_id})
        else:
            # Direct SQLite connection - use aiosqlite
            import aiosqlite
            database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
            
            async with aiosqlite.connect(database_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT id, filename, original_filename, file_path, document_type,
                           processing_status, uploaded_by, file_size, mime_type, metadata,
                           created_at, updated_at
                    FROM documents WHERE id = ?
                """, (document_id,))
                result = await cursor.fetchone()
        
        if not result:
            return None
        
        return self._process_metadata(dict(result))
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance metadata from database"""
        # Map document_type to type for chunker compatibility
        if 'document_type' in metadata:
            metadata['type'] = metadata['document_type']
        
        # Extract file extension from original_filename
        if 'original_filename' in metadata and metadata['original_filename']:
            _, file_extension = os.path.splitext(metadata['original_filename'])
            metadata['file_extension'] = file_extension.lower()
        
        # Parse metadata JSON if it's a string (SQLite)
        if 'metadata' in metadata and isinstance(metadata['metadata'], str):
            try:
                metadata['metadata'] = json.loads(metadata['metadata'])
            except (json.JSONDecodeError, TypeError):
                metadata['metadata'] = {}
        
        return metadata
    
    async def update_processing_status(self, database: Database, document_id: str) -> None:
        """Update document status to 'processing' in database."""
        # Handle both SQLite (local) and PostgreSQL (database) connections
        if hasattr(database, 'execute'):
            # Databases library connection (PostgreSQL)
            query = """
            UPDATE documents 
            SET processing_status = 'processing', updated_at = :updated_at
            WHERE id = :document_id
            """
            await database.execute(query, {
                'document_id': document_id,
                'updated_at': datetime.now(timezone.utc)
            })
        else:
            # Direct SQLite connection - use aiosqlite
            import aiosqlite
            database_path = os.getenv("DATABASE_PATH", "/Users/joshuacoke/dev/Theo/apps/api/theo.db")
            
            async with aiosqlite.connect(database_path) as db:
                await db.execute("""
                    UPDATE documents 
                    SET processing_status = 'processing', updated_at = ?
                    WHERE id = ?
                """, (datetime.now(timezone.utc).isoformat(), document_id))
                await db.commit()