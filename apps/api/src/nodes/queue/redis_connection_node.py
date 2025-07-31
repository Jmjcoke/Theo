"""
RedisConnectionNode - Redis connection management for queue operations
PocketFlow AsyncNode implementation (≤150 lines)

Cookbook References:
- pocketflow-external-service: Redis service integration patterns
- pocketflow-async-background: Asynchronous connection handling
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from pocketflow import AsyncNode
from src.core.redis_client import redis_client
from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisConnectionNode(AsyncNode):
    """
    Redis connection management node for queue operations
    
    Handles Redis connection lifecycle and health monitoring
    with proper error handling and PocketFlow compliance.
    """
    
    def __init__(self):
        super().__init__()
        self.node_id = "redis_connection"
        self.node_type = "RedisConnectionNode"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare Redis operation parameters"""
        action = shared.get("action", "health_check")
        config_override = shared.get("redis_config", {})
        
        return {
            "action": action,
            "config": config_override,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Redis operation based on action type"""
        action = prep_result["action"]
        
        try:
            if action == "connect":
                return await self._handle_connect()
            elif action == "disconnect":
                return await self._handle_disconnect()
            elif action == "health_check":
                return await self._handle_health_check()
            elif action == "test_connection":
                return await self._handle_test_connection()
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def post(self, shared: Dict[str, Any], prep_result: Dict[str, Any], 
             exec_result: Dict[str, Any]) -> str:
        """Process execution results and determine next action"""
        status = exec_result.get("status", "error")
        
        if status == "error":
            logger.error(f"Redis operation failed: {exec_result.get('error')}")
            return "error"
        elif status in ["healthy", "connected", "disconnected"]:
            return "success"
        else:
            return "continue"
    
    async def _handle_connect(self) -> Dict[str, Any]:
        """Handle Redis connection establishment"""
        try:
            await redis_client.connect()
            return {
                "status": "connected",
                "connection_id": f"redis_{datetime.utcnow().timestamp()}",
                "redis_url": settings.redis_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Redis connection failed: {e}")
    
    async def _handle_disconnect(self) -> Dict[str, Any]:
        """Handle Redis connection cleanup"""
        try:
            await redis_client.disconnect()
            return {
                "status": "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Redis disconnect failed: {e}")
    
    async def _handle_health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            health_data = await redis_client.health_check()
            return {
                "status": health_data["status"],
                "health_data": health_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Redis health check failed: {e}")
    
    async def _handle_test_connection(self) -> Dict[str, Any]:
        """Test Redis connection with ping"""
        try:
            await redis_client.client.ping()
            return {
                "status": "healthy",
                "test_result": "ping_successful",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Redis ping test failed: {e}")


# Export for PocketFlow integration
def create_redis_connection_node() -> RedisConnectionNode:
    """Factory function for creating RedisConnectionNode instances"""
    return RedisConnectionNode()


# Node metadata for PocketFlow
NODE_METADATA = {
    "name": "RedisConnectionNode",
    "description": "Redis connection management for queue operations",
    "version": "1.0.0",
    "cookbook_refs": ["pocketflow-external-service", "pocketflow-async-background"],
    "max_lines": 150,
    "async_capable": True
}