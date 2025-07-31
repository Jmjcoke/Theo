"""
Job Dispatch Node for Celery background job creation.
Cookbook Reference: pocketflow-fastapi-background
"""
from typing import Dict, Any, Optional
from pocketflow import AsyncNode
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)


class JobDispatchNode(AsyncNode):
    """
    Dispatches background jobs for document processing.
    
    Input: document_id, file_path, celery_app, task_name
    Output: job_id, job_result, dispatch_result
    """
    
    def __init__(self, celery_app=None, default_task_name: str = 'process_document'):
        super().__init__()
        self.celery_app = celery_app
        self.default_task_name = default_task_name
    
    async def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs and prepare execution."""
        required_keys = ['document_id', 'file_path']
        missing_keys = [key for key in required_keys if key not in shared_store]
        
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        celery_app = shared_store.get('celery_app', self.celery_app)
        if not celery_app:
            raise ValueError("Celery app instance required for job dispatch")
        
        return {
            'document_id': shared_store['document_id'],
            'file_path': shared_store['file_path'],
            'celery_app': celery_app,
            'task_name': shared_store.get('task_name', self.default_task_name),
            'task_args': shared_store.get('task_args', {}),
            'task_kwargs': shared_store.get('task_kwargs', {})
        }
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Core job dispatch logic."""
        document_id = data['document_id']
        file_path = data['file_path']
        celery_app = data['celery_app']
        task_name = data['task_name']
        task_args = data['task_args']
        task_kwargs = data['task_kwargs']
        
        try:
            # Prepare task arguments
            base_args = {'document_id': document_id, 'file_path': file_path}
            base_args.update(task_args)
            
            # Dispatch background job
            job_result = celery_app.send_task(task_name, kwargs=base_args, **task_kwargs)
            job_id = job_result.id
            
            logger.info(f"Dispatched background job {job_id} for document {document_id}")
            
            return {
                'success': True, 'job_id': job_id, 'job_result': job_result,
                'document_id': document_id, 'task_name': task_name
            }
            
        except Exception as e:
            logger.error(f"Failed to dispatch job for document {document_id}: {str(e)}")
            
            return {
                'success': False, 'error': str(e), 'job_id': None,
                'job_result': None, 'document_id': document_id
            }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> None:
        """Update shared store with dispatch results."""
        shared_store['dispatch_result'] = result
        
        if result['success']:
            shared_store['job_id'] = result['job_id']
            shared_store['job_result'] = result['job_result']
        else:
            shared_store['dispatch_error'] = result.get('error')
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of dispatched job."""
        if not self.celery_app:
            return {'error': 'No Celery app available'}
        
        try:
            result = AsyncResult(job_id, app=self.celery_app)
            return {
                'job_id': job_id, 'status': result.status, 'result': result.result,
                'ready': result.ready(), 'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None
            }
        except Exception as e:
            return {'job_id': job_id, 'error': str(e), 'status': 'UNKNOWN'}
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a dispatched job."""
        if not self.celery_app:
            return {'error': 'No Celery app available'}
        
        try:
            self.celery_app.control.revoke(job_id, terminate=True)
            return {'job_id': job_id, 'cancelled': True}
        except Exception as e:
            return {'job_id': job_id, 'cancelled': False, 'error': str(e)}