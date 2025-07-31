"""
Processing Queue Manager for handling concurrent document uploads
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from databases import Database
from ..flows.document_processing_flow import DocumentProcessingFlow


class ProcessingQueueManager:
    """Manages concurrent document processing with rate limiting and progress tracking"""
    
    def __init__(self, database: Database, max_concurrent: int = 3):
        """
        Initialize the processing queue manager
        
        Args:
            database: Database connection
            max_concurrent: Maximum number of documents to process simultaneously
        """
        self.database = database
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        self.processing_semaphore = asyncio.Semaphore(max_concurrent)
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.queue_lock = asyncio.Lock()
    
    async def queue_document_for_processing(self, document_id: str) -> Dict[str, Any]:
        """
        Queue a document for processing
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dictionary with queuing status and job info
        """
        async with self.queue_lock:
            # Check if already processing
            if document_id in self.active_jobs:
                return {
                    'success': False,
                    'error': f'Document {document_id} is already being processed',
                    'status': 'already_processing'
                }
            
            # Create job entry
            job_info = {
                'document_id': document_id,
                'status': 'queued',
                'queued_at': datetime.now(timezone.utc),
                'started_at': None,
                'completed_at': None,
                'progress': 0,
                'total_chunks': 0,
                'processed_chunks': 0,
                'error': None
            }
            
            self.active_jobs[document_id] = job_info
            
            # Start processing task
            task = asyncio.create_task(self._process_document_with_semaphore(document_id))
            job_info['task'] = task
            
            self.logger.info(f"Queued document {document_id} for processing")
            
            return {
                'success': True,
                'document_id': document_id,
                'status': 'queued',
                'position_in_queue': len(self.active_jobs),
                'estimated_wait_time': self._estimate_wait_time()
            }
    
    async def _process_document_with_semaphore(self, document_id: str):
        """Process document with semaphore rate limiting"""
        async with self.processing_semaphore:
            await self._process_single_document(document_id)
    
    async def _process_single_document(self, document_id: str):
        """Process a single document with progress tracking"""
        job_info = self.active_jobs.get(document_id)
        if not job_info:
            return
        
        try:
            # Update status to processing
            job_info['status'] = 'processing'
            job_info['started_at'] = datetime.now(timezone.utc)
            
            # Update database status
            await self._update_document_status(document_id, 'processing')
            
            self.logger.info(f"Starting processing for document {document_id}")
            
            # Create processing flow with progress callback
            flow = DocumentProcessingFlow(database=self.database)
            
            # Create a custom progress tracker
            original_run = flow.run
            async def tracked_run(input_data):
                return await self._run_with_progress_tracking(original_run, input_data, job_info)
            
            flow.run = tracked_run
            
            # Process the document
            result = await flow.run({'document_id': document_id, 'database': self.database})
            
            # Update job completion
            job_info['completed_at'] = datetime.now(timezone.utc)
            job_info['progress'] = 100
            
            if result.get('success'):
                job_info['status'] = 'completed'
                job_info['processed_chunks'] = result.get('stored_chunk_count', 0)
                self.logger.info(f"Successfully processed document {document_id}: {job_info['processed_chunks']} chunks")
            else:
                job_info['status'] = 'failed'
                job_info['error'] = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to process document {document_id}: {job_info['error']}")
            
        except Exception as e:
            job_info['status'] = 'failed'
            job_info['error'] = str(e)
            job_info['completed_at'] = datetime.now(timezone.utc)
            await self._update_document_status(document_id, 'failed')
            self.logger.error(f"Exception processing document {document_id}: {e}")
        
        finally:
            # Clean up job after delay (keep for status checking)
            asyncio.create_task(self._cleanup_job(document_id, delay=300))  # 5 minute delay
    
    async def _run_with_progress_tracking(self, original_run, input_data, job_info):
        """Wrapper to track progress during processing"""
        # This is a simplified progress tracker
        # In a full implementation, you'd hook into each processing step
        result = await original_run(input_data)
        
        if result.get('success'):
            job_info['total_chunks'] = result.get('stored_chunk_count', 0)
            job_info['processed_chunks'] = job_info['total_chunks']
            job_info['progress'] = 100
        
        return result
    
    async def _update_document_status(self, document_id: str, status: str):
        """Update document status in database"""
        try:
            query = """
            UPDATE documents 
            SET processing_status = :status, updated_at = :updated_at
            WHERE id = :document_id
            """
            await self.database.execute(query, {
                'document_id': document_id,
                'status': status,
                'updated_at': datetime.now(timezone.utc)
            })
        except Exception as e:
            self.logger.error(f"Failed to update document status: {e}")
    
    async def _cleanup_job(self, document_id: str, delay: int = 300):
        """Clean up job info after delay"""
        await asyncio.sleep(delay)
        async with self.queue_lock:
            if document_id in self.active_jobs:
                del self.active_jobs[document_id]
                self.logger.debug(f"Cleaned up job info for document {document_id}")
    
    def _estimate_wait_time(self) -> int:
        """Estimate wait time in seconds based on queue length"""
        # Simple estimation: assume 30 seconds per document per concurrent slot
        active_processing = sum(1 for job in self.active_jobs.values() if job['status'] == 'processing')
        queued_count = sum(1 for job in self.active_jobs.values() if job['status'] == 'queued')
        
        if active_processing < self.max_concurrent:
            return 0  # Can start immediately
        else:
            # Estimate based on queue position and average processing time
            return (queued_count * 30) // self.max_concurrent
    
    async def get_job_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a processing job"""
        async with self.queue_lock:
            job_info = self.active_jobs.get(document_id)
            if not job_info:
                return None
            
            # Return copy without the task object
            status = job_info.copy()
            status.pop('task', None)
            
            # Add processing time if started
            if job_info['started_at']:
                processing_time = (datetime.now(timezone.utc) - job_info['started_at']).total_seconds()
                status['processing_time_seconds'] = int(processing_time)
            
            return status
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        async with self.queue_lock:
            total_jobs = len(self.active_jobs)
            processing_count = sum(1 for job in self.active_jobs.values() if job['status'] == 'processing')
            queued_count = sum(1 for job in self.active_jobs.values() if job['status'] == 'queued')
            completed_count = sum(1 for job in self.active_jobs.values() if job['status'] == 'completed')
            failed_count = sum(1 for job in self.active_jobs.values() if job['status'] == 'failed')
            
            return {
                'total_jobs': total_jobs,
                'processing': processing_count,
                'queued': queued_count,
                'completed': completed_count,
                'failed': failed_count,
                'max_concurrent': self.max_concurrent,
                'available_slots': self.max_concurrent - processing_count
            }
    
    async def cancel_job(self, document_id: str) -> bool:
        """Cancel a queued or processing job (if possible)"""
        async with self.queue_lock:
            job_info = self.active_jobs.get(document_id)
            if not job_info:
                return False
            
            if job_info['status'] == 'queued':
                # Can cancel queued jobs
                task = job_info.get('task')
                if task and not task.done():
                    task.cancel()
                
                job_info['status'] = 'cancelled'
                job_info['completed_at'] = datetime.now(timezone.utc)
                await self._update_document_status(document_id, 'failed')
                return True
            
            return False  # Cannot cancel processing jobs
    
    async def shutdown(self):
        """Gracefully shutdown the queue manager"""
        self.logger.info("Shutting down processing queue manager...")
        
        # Cancel all queued jobs
        async with self.queue_lock:
            for document_id, job_info in self.active_jobs.items():
                if job_info['status'] == 'queued':
                    task = job_info.get('task')
                    if task and not task.done():
                        task.cancel()
        
        # Wait for active processing to complete (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*[
                    job_info['task'] for job_info in self.active_jobs.values() 
                    if job_info.get('task') and not job_info['task'].done()
                ], return_exceptions=True),
                timeout=60  # 1 minute timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for processing jobs to complete")
        
        self.logger.info("Processing queue manager shutdown complete")


# Global queue manager instance
_queue_manager: Optional[ProcessingQueueManager] = None

async def get_queue_manager(database: Database) -> ProcessingQueueManager:
    """Get or create the global queue manager instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = ProcessingQueueManager(database, max_concurrent=3)
    return _queue_manager

async def shutdown_queue_manager():
    """Shutdown the global queue manager"""
    global _queue_manager
    if _queue_manager:
        await _queue_manager.shutdown()
        _queue_manager = None