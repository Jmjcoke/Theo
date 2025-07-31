"""
CeleryTaskDispatchNode - Task queuing and dispatch operations
PocketFlow AsyncNode implementation (≤150 lines)

Cookbook References:
- pocketflow-async-background: Asynchronous task handling patterns
- pocketflow-external-service: External service integration
"""

import logging
from typing import Dict, Any
from datetime import datetime

from pocketflow import AsyncNode
from src.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class CeleryTaskDispatchNode(AsyncNode):
    """
    Celery task dispatch and management node
    
    Handles task queuing, scheduling, and basic management
    operations with PocketFlow compliance.
    """
    
    def __init__(self):
        super().__init__()
        self.node_id = "celery_task_dispatch"
        self.node_type = "CeleryTaskDispatchNode"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare task dispatch parameters"""
        task_name = shared.get("task_name", "")
        args = shared.get("args", [])
        kwargs = shared.get("kwargs", {})
        queue = shared.get("queue", "default")
        countdown = shared.get("countdown", 0)
        
        return {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "queue": queue,
            "countdown": countdown,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task dispatch operation"""
        try:
            task_name = prep_result["task_name"]
            if not task_name:
                raise ValueError("task_name is required")
            
            # Dispatch task to Celery
            result = celery_app.send_task(
                task_name,
                args=prep_result["args"],
                kwargs=prep_result["kwargs"],
                queue=prep_result["queue"],
                countdown=prep_result["countdown"]
            )
            
            return {
                "status": "dispatched",
                "task_id": result.id,
                "task_name": task_name,
                "queue": prep_result["queue"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Task dispatch failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def post(self, shared: Dict[str, Any], prep_result: Dict[str, Any], 
             exec_result: Dict[str, Any]) -> str:
        """Process dispatch results"""
        status = exec_result.get("status", "error")
        
        if status == "dispatched":
            # Store task ID in shared data for monitoring
            shared["task_id"] = exec_result.get("task_id")
            return "success"
        elif status == "error":
            logger.error(f"Task dispatch error: {exec_result.get('error')}")
            return "error"
        else:
            return "continue"
    
    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get basic task information by ID"""
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get task info: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running task"""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            return {
                "task_id": task_id,
                "status": "cancelled",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Export for PocketFlow integration
def create_task_dispatch_node() -> CeleryTaskDispatchNode:
    """Factory function for creating CeleryTaskDispatchNode instances"""
    return CeleryTaskDispatchNode()


# Node metadata for PocketFlow
NODE_METADATA = {
    "name": "CeleryTaskDispatchNode",
    "description": "Celery task dispatch and management operations",
    "version": "1.0.0",
    "cookbook_refs": ["pocketflow-async-background", "pocketflow-external-service"],
    "max_lines": 150,
    "async_capable": True
}