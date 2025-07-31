"""
TaskStatusMonitorNode - Task result retrieval and status monitoring
PocketFlow AsyncNode implementation (≤150 lines)

Cookbook References:
- pocketflow-async-background: Asynchronous task monitoring patterns
- pocketflow-external-service: External service status checking
"""

import logging
from typing import Dict, Any
from datetime import datetime

from pocketflow import AsyncNode
from src.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class TaskStatusMonitorNode(AsyncNode):
    """
    Task status monitoring and result retrieval node
    
    Handles monitoring of Celery task execution status,
    result retrieval, and error tracking.
    """
    
    def __init__(self):
        super().__init__()
        self.node_id = "task_status_monitor"
        self.node_type = "TaskStatusMonitorNode"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare task monitoring parameters"""
        return {
            "task_id": shared.get("task_id", ""),
            "action": shared.get("action", "status"),
            "timeout": shared.get("timeout", 30),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task monitoring operation"""
        try:
            task_id = prep_result["task_id"]
            action = prep_result["action"]
            
            if not task_id:
                raise ValueError("task_id is required")
            
            result = celery_app.AsyncResult(task_id)
            
            if action == "status":
                return self._build_status_response(result, task_id)
            elif action == "result":
                return self._build_result_response(result, task_id)
            elif action == "wait":
                return await self._wait_for_completion(result, task_id, prep_result["timeout"])
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Task monitoring failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def post(self, shared: Dict[str, Any], prep_result: Dict[str, Any], 
             exec_result: Dict[str, Any]) -> str:
        """Process monitoring results"""
        status = exec_result.get("status", "error")
        
        if status in ["SUCCESS", "FAILURE", "REVOKED", "completed"]:
            return "success"
        elif status in ["PENDING", "STARTED", "monitoring"]:
            return "continue"
        else:
            return "error"
    
    def _build_status_response(self, result, task_id: str) -> Dict[str, Any]:
        """Build status response"""
        return {
            "status": "monitoring",
            "task_id": task_id,
            "task_status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_result_response(self, result, task_id: str) -> Dict[str, Any]:
        """Build result response"""
        task_result = result.result if result.ready() and result.successful() else None
        error_info = {"exception": str(result.result)} if result.ready() and result.failed() else None
        
        return {
            "status": result.status,
            "task_id": task_id,
            "ready": result.ready(),
            "result": task_result,
            "error_info": error_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _wait_for_completion(self, result, task_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for task completion with timeout"""
        try:
            task_result = result.get(timeout=timeout, propagate=False)
            
            return {
                "status": "completed",
                "task_id": task_id,
                "task_status": result.status,
                "result": task_result if result.successful() else None,
                "error_info": {"exception": str(task_result)} if result.failed() else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as wait_error:
            return {
                "status": "timeout",
                "task_id": task_id,
                "task_status": result.status,
                "timeout": timeout,
                "error": str(wait_error),
                "timestamp": datetime.utcnow().isoformat()
            }


# Export for PocketFlow integration
def create_task_monitor_node() -> TaskStatusMonitorNode:
    """Factory function for creating TaskStatusMonitorNode instances"""
    return TaskStatusMonitorNode()


# Node metadata for PocketFlow
NODE_METADATA = {
    "name": "TaskStatusMonitorNode",
    "description": "Task status monitoring and result retrieval",
    "version": "1.0.0",
    "cookbook_refs": ["pocketflow-async-background", "pocketflow-external-service"],
    "max_lines": 150,
    "async_capable": True
}