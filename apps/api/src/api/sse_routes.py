"""
Server-Sent Events (SSE) API routes.

Provides real-time job status updates through SSE endpoints.
"""
from typing import Optional
import json
import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.nodes.documents.job_status_node import JobStatusNode


router = APIRouter(prefix="/api", tags=["server-sent-events"])


async def verify_admin_token_from_query(token: str) -> dict:
    """
    Verify admin JWT token from query parameter for SSE authentication.
    
    EventSource doesn't support custom headers, so we use query parameter for auth.
    """
    from src.nodes.auth.auth_middleware_node import AuthMiddlewareNode
    
    auth_middleware = AuthMiddlewareNode()
    
    shared_store = {
        "authorization_header": f"Bearer {token}",
        "required_roles": ["admin"]
    }
    
    result = await auth_middleware.run(shared_store)
    
    if not result["authenticated"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"]
        )
    
    return {
        "user_id": result["user_id"],
        "email": result["email"],
        "role": result["role"]
    }


@router.get(
    "/jobs/{job_id}/events",
    summary="Stream job status events",
    description="Server-Sent Events endpoint for real-time job status updates. Requires admin role."
)
async def stream_job_status(
    job_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    Server-Sent Events endpoint for real-time job status updates.
    
    This endpoint provides real-time updates about job processing status using SSE.
    EventSource doesn't support custom headers, so authentication is done via query parameter.
    
    **Authentication:** Requires admin role JWT token as query parameter.
    
    **Path Parameters:**
    - `job_id`: The Celery job ID to monitor
    
    **Query Parameters:**
    - `token`: JWT authentication token (admin role required)
    
    **Response Format:**
    ```
    Content-Type: text/event-stream
    Cache-Control: no-cache
    Connection: keep-alive
    
    data: {"status": "queued", "progress": 0.0, "step": "initializing"}
    
    data: {"status": "processing", "progress": 0.25, "step": "parsing-document"}
    
    data: {"status": "completed", "progress": 1.0, "step": "storing-vectors"}
    ```
    
    **Status Values:**
    - `queued`: Job is waiting to be processed
    - `processing`: Job is currently being processed
    - `completed`: Job completed successfully
    - `failed`: Job failed with error
    - `error`: System error occurred
    """
    # Authenticate admin user from query parameter
    try:
        authenticated_user = await verify_admin_token_from_query(token)
    except HTTPException:
        # Return 401/403 as SSE response for authentication failures
        async def auth_error_generator():
            yield f"data: {json.dumps({'status': 'error', 'progress': 0.0, 'step': 'authentication_failed', 'message': 'Admin access required'})}\n\n"
        
        return StreamingResponse(
            auth_error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    # Initialize job status node
    job_status_node = JobStatusNode()
    
    async def event_generator():
        """Generate SSE events for job status updates"""
        try:
            # Send initial connection confirmation
            yield f"data: {json.dumps({'status': 'connected', 'progress': 0.0, 'step': 'initializing', 'message': 'Connected to job status stream'})}\n\n"
            
            last_status = None
            connection_timeout = 30  # 30 seconds timeout for idle connections
            poll_interval = 2  # Poll every 2 seconds
            timeout_counter = 0
            
            while timeout_counter < connection_timeout:
                try:
                    # Prepare shared store for job status node
                    shared_store = {
                        'job_id': job_id,
                        'authenticated_user': authenticated_user
                    }
                    
                    # Get job status using job status node
                    result = await job_status_node.run(shared_store)
                    
                    if 'sse_data' in result:
                        current_status = result['sse_data']
                        
                        # Only send update if status changed or it's the first status
                        if last_status != current_status:
                            yield f"data: {json.dumps(current_status)}\n\n"
                            last_status = current_status
                            timeout_counter = 0  # Reset timeout on activity
                        
                        # Break if job is in final status
                        if current_status.get('status') in ['completed', 'failed']:
                            break
                    
                    # Wait before next poll
                    await asyncio.sleep(poll_interval)
                    timeout_counter += poll_interval
                    
                except Exception as e:
                    error_data = {
                        'status': 'error',
                        'progress': 0.0,
                        'step': 'polling_error',
                        'message': f'Error polling job status: {str(e)}'
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
            
            # Send timeout message if connection timed out
            if timeout_counter >= connection_timeout:
                timeout_data = {
                    'status': 'timeout',
                    'progress': 0.0,
                    'step': 'connection_timeout',
                    'message': 'Connection timed out due to inactivity'
                }
                yield f"data: {json.dumps(timeout_data)}\n\n"
                
        except Exception as e:
            # Send error message for any unexpected errors
            error_data = {
                'status': 'error',
                'progress': 0.0,
                'step': 'stream_error',
                'message': f'Stream error: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )