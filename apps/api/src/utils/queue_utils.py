"""
Queue utilities for FastAPI integration
Provides helper functions for task dispatch and monitoring
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.celery_app import celery_app
from src.nodes.queue import RedisConnectionNode, CeleryTaskDispatchNode, TaskStatusMonitorNode


logger = logging.getLogger(__name__)


class QueueManager:
    """Queue management utility for FastAPI routes"""
    
    def __init__(self):
        self.redis_node = RedisConnectionNode()
        self.dispatch_node = CeleryTaskDispatchNode()
        self.monitor_node = TaskStatusMonitorNode()
    
    async def dispatch_task(
        self, 
        task_name: str, 
        args: List[Any] = None, 
        kwargs: Dict[str, Any] = None,
        queue: str = None,
        countdown: int = None
    ) -> Dict[str, Any]:
        """Dispatch task to queue"""
        try:
            input_data = {
                "action": "dispatch",
                "task_name": task_name,
                "task_args": args or [],
                "task_kwargs": kwargs or {},
            }
            
            if queue:
                input_data["queue"] = queue
            if countdown:
                input_data["countdown"] = countdown
                
            result = await self.dispatch_node.process(input_data)
            return result
            
        except Exception as e:
            logger.error(f"Task dispatch error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result"""
        try:
            result = await self.monitor_node.process({
                "action": "get_result",
                "task_id": task_id,
                "include_traceback": True
            })
            return result
            
        except Exception as e:
            logger.error(f"Task status error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def wait_for_task(
        self, 
        task_id: str, 
        timeout: int = 60, 
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for task completion"""
        try:
            result = await self.monitor_node.process({
                "action": "wait_for_result",
                "task_id": task_id,
                "timeout": timeout,
                "poll_interval": poll_interval
            })
            return result
            
        except Exception as e:
            logger.error(f"Task wait error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel running task"""
        try:
            result = await self.dispatch_node.process({
                "action": "cancel",
                "task_id": task_id
            })
            return result
            
        except Exception as e:
            logger.error(f"Task cancel error: {str(e)}")
            return {
                "status": "error", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_batch_status(self, task_ids: List[str]) -> Dict[str, Any]:
        """Get status for multiple tasks"""
        try:
            result = await self.monitor_node.process({
                "action": "batch_status",
                "task_ids": task_ids
            })
            return result
            
        except Exception as e:
            logger.error(f"Batch status error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check queue system health"""
        try:
            redis_result = await self.redis_node.process({
                "action": "test_connection"
            })
            
            return {
                "status": "healthy" if redis_result["status"] == "success" else "unhealthy",
                "redis": redis_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global queue manager instance
queue_manager = QueueManager()