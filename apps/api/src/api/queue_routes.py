"""
Queue management API routes
Provides endpoints for task dispatch, monitoring, and management
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.utils.queue_utils import queue_manager
from src.core.celery_app import test_redis_task, debug_task


router = APIRouter(prefix="/queue", tags=["Queue Management"])


# Request/Response models
class TaskDispatchRequest(BaseModel):
    """Request model for task dispatch"""
    task_name: str = Field(..., description="Name of the Celery task to dispatch")
    args: List[Any] = Field(default=[], description="Positional arguments for the task")
    kwargs: Dict[str, Any] = Field(default={}, description="Keyword arguments for the task")
    queue: Optional[str] = Field(None, description="Queue name for task routing")
    countdown: Optional[int] = Field(None, description="Delay in seconds before execution")


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    status: str = Field(..., description="Operation status")
    task_id: Optional[str] = Field(None, description="Task identifier")
    task_status: Optional[str] = Field(None, description="Celery task state")
    result: Optional[Any] = Field(None, description="Task result if completed")
    error_info: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    timestamp: str = Field(..., description="Response timestamp")


@router.post("/dispatch", response_model=Dict[str, Any])
async def dispatch_task(request: TaskDispatchRequest) -> Dict[str, Any]:
    """
    Dispatch a task to the queue
    
    Sends a task to the Celery queue for asynchronous execution.
    Returns the task ID for status monitoring.
    
    Args:
        request: Task dispatch parameters
        
    Returns:
        Dict containing task_id and dispatch status
    """
    try:
        result = await queue_manager.dispatch_task(
            task_name=request.task_name,
            args=request.args,
            kwargs=request.kwargs,
            queue=request.queue,
            countdown=request.countdown
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get task status and result
    
    Retrieves the current status and result (if completed) of a task.
    
    Args:
        task_id: Celery task identifier
        
    Returns:
        Dict containing task status, result, and metadata
    """
    try:
        result = await queue_manager.get_task_status(task_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wait/{task_id}", response_model=Dict[str, Any])
async def wait_for_task(
    task_id: str,
    timeout: int = Query(default=60, description="Timeout in seconds"),
    poll_interval: float = Query(default=1.0, description="Polling interval in seconds")
) -> Dict[str, Any]:
    """
    Wait for task completion
    
    Polls the task until completion or timeout.
    
    Args:
        task_id: Celery task identifier
        timeout: Maximum wait time in seconds
        poll_interval: Time between status checks
        
    Returns:
        Dict containing final task status and result
    """
    try:
        result = await queue_manager.wait_for_task(task_id, timeout, poll_interval)
        
        if result["status"] == "timeout":
            raise HTTPException(status_code=408, detail="Task execution timeout")
        elif result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}", response_model=Dict[str, Any])
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running task
    
    Attempts to cancel a queued or running task.
    
    Args:
        task_id: Celery task identifier
        
    Returns:
        Dict containing cancellation status
    """
    try:
        result = await queue_manager.cancel_task(task_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-status", response_model=Dict[str, Any])
async def get_batch_status(task_ids: List[str] = Body(...)) -> Dict[str, Any]:
    """
    Get status for multiple tasks
    
    Retrieves status information for a batch of tasks.
    
    Args:
        task_ids: List of Celery task identifiers
        
    Returns:
        Dict containing batch results
    """
    try:
        result = await queue_manager.get_batch_status(task_ids)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def queue_health_check() -> Dict[str, Any]:
    """
    Check queue system health
    
    Verifies Redis connectivity and Celery worker availability.
    
    Returns:
        Dict containing health status and diagnostics
    """
    try:
        result = await queue_manager.health_check()
        
        if result["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail="Queue system unhealthy")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Test task endpoints
@router.post("/test/redis", response_model=Dict[str, Any])
async def test_redis_connection() -> Dict[str, Any]:
    """
    Test Redis connection with a simple task
    
    Dispatches a test task to verify queue functionality.
    
    Returns:
        Dict containing test task ID and dispatch status
    """
    try:
        result = await queue_manager.dispatch_task("test_redis_task")
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/debug", response_model=Dict[str, Any])
async def test_debug_task() -> Dict[str, Any]:
    """
    Test Celery worker with debug task
    
    Dispatches a debug task to verify worker functionality.
    
    Returns:
        Dict containing debug task ID and dispatch status
    """
    try:
        result = await queue_manager.dispatch_task("debug_task")
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))