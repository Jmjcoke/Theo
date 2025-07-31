"""
Document Storage Node for file storage and database record creation.
Cookbook Reference: pocketflow-external-service
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import aiofiles
from pocketflow import AsyncNode
from databases import Database


class DocumentStorageNode(AsyncNode):
    """
    Stores files and creates database records with 'queued' status.
    
    Input: uploaded_file, file_info, uploaded_by, upload_dir, database
    Output: document_id, file_path, storage_result
    """
    
    def __init__(self, database: Optional[Database] = None, upload_dir: Optional[str] = None):
        super().__init__()
        self.database = database
        self.upload_dir = upload_dir or "uploads"
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs and prepare execution."""
        required_keys = ['uploaded_file', 'file_info', 'uploaded_by']
        missing_keys = [key for key in required_keys if key not in shared_store]
        
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        upload_dir = shared_store.get('upload_dir', self.upload_dir)
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        return {
            'uploaded_file': shared_store['uploaded_file'],
            'file_info': shared_store['file_info'],
            'uploaded_by': shared_store['uploaded_by'],
            'upload_dir': upload_dir,
            'database': shared_store.get('database', self.database)
        }
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Core file storage and database record creation logic."""
        uploaded_file = data['uploaded_file']
        file_info = data['file_info']
        uploaded_by = data['uploaded_by']
        upload_dir = data['upload_dir']
        database = data['database']
        
        document_id = str(uuid.uuid4())
        file_extension = file_info['file_extension']
        secure_filename = f"{document_id}.{file_extension}"
        file_path = os.path.join(upload_dir, secure_filename)
        
        try:
            # Store file to disk
            async with aiofiles.open(file_path, 'wb') as f:
                content = await uploaded_file.read()
                await f.write(content)
            
            # Create database record
            if database:
                await self._create_db_record(database, document_id, secure_filename, 
                                           file_path, file_info, uploaded_by)
            
            return {
                'success': True,
                'document_id': document_id,
                'file_path': file_path,
                'secure_filename': secure_filename,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            # Clean up file if database operation fails
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            return {'success': False, 'error': str(e), 'document_id': None, 'file_path': None}
    
    async def _create_db_record(self, database: Database, document_id: str, 
                               secure_filename: str, file_path: str, 
                               file_info: Dict[str, Any], uploaded_by: str) -> None:
        """Create database record for uploaded document."""
        query = """
        INSERT INTO documents (
            id, filename, original_filename, file_path, document_type,
            processing_status, uploaded_by, file_size, mime_type, metadata,
            created_at, updated_at
        ) VALUES (
            :id, :filename, :original_filename, :file_path, :document_type,
            :processing_status, :uploaded_by, :file_size, :mime_type, :metadata,
            :created_at, :updated_at
        )
        """
        
        now = datetime.now(timezone.utc)
        metadata = {
            'category': file_info.get('category'),
            'file_extension': file_info.get('file_extension'),
            'upload_timestamp': now.isoformat()
        }
        
        values = {
            'id': document_id, 'filename': secure_filename,
            'original_filename': file_info['filename'], 'file_path': file_path,
            'document_type': file_info['document_type'], 'processing_status': 'queued',
            'uploaded_by': uploaded_by, 'file_size': file_info['file_size'],
            'mime_type': file_info['mime_type'], 'metadata': metadata,
            'created_at': now, 'updated_at': now
        }
        
        await database.execute(query, values)
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> None:
        """Update shared store with storage results."""
        shared_store['storage_result'] = result
        
        if result['success']:
            shared_store['document_id'] = result['document_id']
            shared_store['file_path'] = result['file_path']
            shared_store['secure_filename'] = result['secure_filename']
        else:
            shared_store['storage_error'] = result.get('error')