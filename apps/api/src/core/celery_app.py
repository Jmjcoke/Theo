"""
Celery application configuration and setup
Manages Celery worker with Redis broker integration
"""

from celery import Celery
from src.core.config import settings

# Create Celery application instance
celery_app = Celery(
    "theo_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=[settings.celery_task_serializer],
    result_expires=3600,  # Results expire after 1 hour
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Tasks are defined directly in this module


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery worker functionality"""
    print(f'Request: {self.request!r}')
    return {"status": "success", "message": "Debug task completed"}


@celery_app.task
def test_redis_task():
    """Simple test task to verify queue functionality"""
    import time
    time.sleep(2)  # Simulate work
    return {
        "status": "completed",
        "message": "Test task executed successfully",
        "timestamp": time.time()
    }


@celery_app.task(bind=True, name='process_document')
def process_document_async(self, document_id: str):
    """
    Background document processing task using DocumentProcessingFlow.
    
    Args:
        document_id: ID of the document to process
        
    Returns:
        Dict containing processing results and status
    """
    import asyncio
    import logging
    from databases import Database
    from src.flows.document_processing_flow import DocumentProcessingFlow
    from src.core.config import settings
    
    logger = logging.getLogger(__name__)
    
    try:
        # Update task status to PROGRESS
        self.update_state(
            state='PROGRESS',
            meta={
                'document_id': document_id,
                'stage': 'starting',
                'message': 'Initializing document processing flow'
            }
        )
        
        logger.info(f"Starting document processing task for document: {document_id}")
        
        # Create database connection for the task
        database = Database(settings.database_url)
        
        async def run_processing_flow():
            """Internal async function to run the document processing flow"""
            await database.connect()
            try:
                # Create and run the document processing flow
                flow = DocumentProcessingFlow(database=database)
                result = await flow.run({'document_id': document_id, 'database': database})
                return result
            finally:
                await database.disconnect()
        
        # Run the async flow
        result = asyncio.run(run_processing_flow())
        
        if result.get('success', False):
            logger.info(f"Document processing completed successfully: {document_id}")
            return {
                'status': 'completed',
                'document_id': document_id,
                'stored_chunk_count': result.get('stored_chunk_count', 0),
                'embedding_count': result.get('embedding_count', 0),
                'processing_status': result.get('processing_status', 'completed'),
                'flow_completed_at': result.get('flow_completed_at'),
                'processing_metadata': result.get('processing_metadata', {})
            }
        else:
            logger.error(f"Document processing failed: {document_id} - {result.get('error')}")
            return {
                'status': 'failed',
                'document_id': document_id,
                'error': result.get('error', 'Unknown processing error'),
                'failure_timestamp': result.get('failure_timestamp'),
                'stored_chunk_count': 0
            }
            
    except Exception as e:
        logger.error(f"Celery task failed for document {document_id}: {str(e)}")
        
        # Update task state to FAILURE
        self.update_state(
            state='FAILURE',
            meta={
                'document_id': document_id,
                'error': str(e),
                'exc_type': type(e).__name__,
                'stage': 'error'
            }
        )
        
        # Re-raise the exception so Celery marks the task as failed
        raise