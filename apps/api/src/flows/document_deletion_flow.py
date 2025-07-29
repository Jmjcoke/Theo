"""
Document Deletion Flow using PocketFlow Pattern

This flow orchestrates the complete deletion of a document including:
1. Metadata deletion from database
2. Vector embeddings cleanup from Supabase
3. File storage cleanup
"""

from pocketflow import Flow, Node, AsyncFlow, AsyncNode
from databases import Database
from src.core.config import settings
from src.utils.vector_utils import delete_document_vectors
import logging
import os

logger = logging.getLogger(__name__)


class DeleteDocumentMetadataNode(AsyncNode):
    """Delete document metadata from the main database"""
    
    async def prep_async(self, shared):
        """Prepare document ID for deletion"""
        return shared["document_id"]
    
    async def exec_async(self, document_id):
        """Execute metadata deletion"""
        database = None
        try:
            database = Database(settings.database_url)
            await database.connect()
            
            # Delete from documents table
            result = await database.execute(
                "DELETE FROM documents WHERE id = :document_id",
                {"document_id": document_id}
            )
            
            if result == 0:
                raise Exception(f"Document {document_id} not found in database")
            
            logger.info(f"Document metadata deleted for ID: {document_id}")
            return True
            
        finally:
            if database:
                await database.disconnect()
    
    async def post_async(self, shared, prep_res, exec_res):
        """Mark metadata deletion as complete"""
        shared["metadata_deleted"] = exec_res
        return "cleanup_vectors"


class CleanupVectorDataNode(AsyncNode):
    """Clean up vector embeddings from Supabase pgvector"""
    
    async def prep_async(self, shared):
        """Prepare document ID for vector cleanup"""
        return shared["document_id"]
    
    async def exec_async(self, document_id):
        """Execute vector data cleanup"""
        try:
            # Use vector utils to delete embeddings
            deleted_count = await delete_document_vectors(document_id)
            logger.info(f"Deleted {deleted_count} vector embeddings for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors for document {document_id}: {str(e)}")
            # Non-critical failure - continue with cleanup
            return False
    
    async def post_async(self, shared, prep_res, exec_res):
        """Mark vector cleanup status"""
        shared["vectors_deleted"] = exec_res
        return "cleanup_files"


class CleanupFileStorageNode(AsyncNode):
    """Clean up file storage if applicable"""
    
    async def prep_async(self, shared):
        """Prepare document ID for file cleanup"""
        return shared["document_id"]
    
    async def exec_async(self, document_id):
        """Execute file storage cleanup"""
        try:
            # Check if we have a file path stored
            # In a real implementation, this would query the database for file location
            # For now, we'll assume files are stored with document ID as filename
            file_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file storage for document {document_id}")
                return True
            else:
                logger.info(f"No file found for document {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete file for document {document_id}: {str(e)}")
            # Non-critical failure
            return False
    
    async def post_async(self, shared, prep_res, exec_res):
        """Mark file cleanup status"""
        shared["files_deleted"] = exec_res
        return "notify_completion"


class NotifyDeletionCompleteNode(AsyncNode):
    """Notify that deletion is complete (placeholder for future notifications)"""
    
    async def prep_async(self, shared):
        """Prepare deletion status"""
        return {
            "document_id": shared["document_id"],
            "metadata_deleted": shared.get("metadata_deleted", False),
            "vectors_deleted": shared.get("vectors_deleted", False),
            "files_deleted": shared.get("files_deleted", False)
        }
    
    async def exec_async(self, status):
        """Log completion status"""
        logger.info(f"Document deletion completed: {status}")
        return status
    
    async def post_async(self, shared, prep_res, exec_res):
        """Mark workflow as complete"""
        shared["deletion_complete"] = True
        shared["deletion_status"] = exec_res
        return None  # End of flow


class DocumentDeletionFlow(AsyncFlow):
    """Orchestrate document deletion workflow"""
    
    def __init__(self):
        # Create nodes
        delete_metadata = DeleteDocumentMetadataNode(max_retries=3, wait=1)
        cleanup_vectors = CleanupVectorDataNode(max_retries=2, wait=1)
        cleanup_files = CleanupFileStorageNode(max_retries=2, wait=1)
        notify_completion = NotifyDeletionCompleteNode()
        
        # Define flow transitions
        delete_metadata - "cleanup_vectors" >> cleanup_vectors
        cleanup_vectors - "cleanup_files" >> cleanup_files
        cleanup_files - "notify_completion" >> notify_completion
        
        # Initialize flow with start node
        super().__init__(start=delete_metadata) 