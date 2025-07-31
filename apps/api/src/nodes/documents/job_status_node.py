"""
JobStatusNode for retrieving job status for SSE streaming

Following PocketFlow AsyncNode pattern for I/O operations.
Retrieves job status from Celery/Redis and formats for SSE response.
"""

from typing import Dict, Any
from celery.result import AsyncResult
from src.core.celery_app import celery_app
from src.core.redis_client import get_redis


class JobStatusNode:
    """Retrieves job status for SSE streaming following PocketFlow patterns"""
    
    def __init__(self):
        """Initialize the job status node"""
        self.status_mapping = {
            'PENDING': 'queued',
            'STARTED': 'processing', 
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'RETRY': 'processing'
        }
    
    def _validate_inputs(self, shared_store: Dict[str, Any]) -> tuple[bool, str]:
        """Validate required inputs"""
        if 'job_id' not in shared_store:
            return False, "Missing job_id parameter"
        if 'authenticated_user' not in shared_store:
            return False, "Missing authentication information"
        job_id = shared_store['job_id']
        if not job_id or not isinstance(job_id, str):
            return False, "Invalid job_id format"
        return True, ""
    
    async def _test_redis_connection(self) -> bool:
        """Test Redis connection availability"""
        try:
            async with get_redis() as redis_client:
                return True
        except Exception:
            return False
    
    def _get_job_progress(self, result) -> tuple[float, str]:
        """Extract progress and step from Celery result"""
        progress = 0.0
        current_step = "initializing"
        
        if result.info and isinstance(result.info, dict):
            progress = result.info.get("progress", 0.0)
            current_step = result.info.get("current_step", "initializing")
        
        return progress, current_step
    
    def _format_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Format error response for SSE"""
        return {
            'sse_data': {
                'status': 'error',
                'progress': 0.0,
                'step': 'error',
                'message': error_msg
            }
        }
    
    async def prep(self, shared_store: Dict[str, Any]) -> bool:
        """Validate job_id and authentication"""
        try:
            valid, error_msg = self._validate_inputs(shared_store)
            if not valid:
                shared_store['error'] = error_msg
                return False
            
            if not await self._test_redis_connection():
                shared_store['error'] = "Failed to connect to Redis"
                return False
            
            return True
        except Exception as e:
            shared_store['error'] = f"Prep phase failed: {str(e)}"
            return False
    
    async def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Query job status from Celery/Redis"""
        try:
            job_id = data['job_id']
            result = AsyncResult(job_id, app=celery_app)
            
            app_status = self.status_mapping.get(result.status, 'unknown')
            progress, current_step = self._get_job_progress(result)
            
            if app_status == 'completed':
                progress = 1.0
                current_step = "completed"
            
            return {
                'success': True,
                'status': app_status,
                'progress': progress,
                'step': current_step,
                'celery_status': result.status,
                'job_id': job_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to retrieve job status: {str(e)}",
                'status': 'unknown',
                'progress': 0.0,
                'step': 'error'
            }
    
    async def post(self, result: Dict[str, Any], shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Format status for SSE response"""
        try:
            if not result.get('success', False):
                return self._format_error_response(result.get('error', 'Unknown error occurred'))
            
            sse_data = {
                'status': result['status'],
                'progress': result['progress'],
                'step': result['step']
            }
            
            if result['status'] == 'failed':
                sse_data['message'] = 'Job processing failed'
            elif result['status'] == 'completed':
                sse_data['message'] = 'Job completed successfully'
            
            return {
                'sse_data': sse_data,
                'formatted_response': True
            }
        except Exception as e:
            return self._format_error_response(f'Response formatting failed: {str(e)}')
    
    async def run(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete job status retrieval workflow"""
        if not await self.prep(shared_store):
            return self._format_error_response(shared_store.get('error', 'Preparation failed'))
        
        exec_result = await self.exec(shared_store)
        final_result = await self.post(exec_result, shared_store)
        
        return final_result