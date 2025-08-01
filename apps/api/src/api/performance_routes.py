"""
Performance monitoring routes for tracking flow optimizations.
Provides endpoints to view performance metrics, cache status, and system health.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from ..utils.performance_utils import (
    get_performance_metrics,
    get_performance_cache,
    get_circuit_breaker
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/metrics")
async def get_performance_metrics_endpoint() -> Dict[str, Any]:
    """Get current performance metrics for all operations."""
    try:
        metrics = get_performance_metrics()
        return {
            "success": True,
            "metrics": metrics.get_metrics(),
            "timestamp": metrics._start_times  # Show any operations currently running
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/cache/status")
async def get_cache_status() -> Dict[str, Any]:
    """Get cache status and statistics."""
    try:
        cache = get_performance_cache()
        
        # Calculate cache statistics
        total_entries = len(cache._cache)
        expired_entries = sum(1 for key in cache._cache.keys() if cache._is_expired(key))
        active_entries = total_entries - expired_entries
        
        return {
            "success": True,
            "cache_status": {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "cache_hit_ratio": "Not implemented",  # Could be added later
                "oldest_entry": min(cache._timestamps.values()) if cache._timestamps else None,
                "newest_entry": max(cache._timestamps.values()) if cache._timestamps else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear the performance cache."""
    try:
        cache = get_performance_cache()
        cache.clear()
        
        return {
            "success": True,
            "message": "Performance cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/circuit-breakers")
async def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers."""
    try:
        # Get all known circuit breakers (this is a simplified approach)
        from ..utils.performance_utils import _circuit_breakers
        
        breaker_status = {}
        for name, breaker in _circuit_breakers.items():
            breaker_status[name] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "failure_threshold": breaker.failure_threshold,
                "timeout": breaker.timeout,
                "last_failure_time": breaker.last_failure_time,
                "can_execute": breaker.can_execute()
            }
        
        return {
            "success": True,
            "circuit_breakers": breaker_status
        }
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get circuit breaker status: {str(e)}")


@router.post("/circuit-breakers/{service_name}/reset")
async def reset_circuit_breaker(service_name: str) -> Dict[str, Any]:
    """Reset a specific circuit breaker."""
    try:
        breaker = get_circuit_breaker(service_name)
        breaker.failure_count = 0
        breaker.state = "CLOSED"
        breaker.last_failure_time = None
        
        return {
            "success": True,
            "message": f"Circuit breaker for {service_name} has been reset"
        }
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {str(e)}")


@router.get("/health")
async def get_performance_health() -> Dict[str, Any]:
    """Get overall performance system health."""
    try:
        metrics = get_performance_metrics()
        cache = get_performance_cache()
        
        # Get metrics summary
        all_metrics = metrics.get_metrics()
        
        # Calculate overall health score
        total_operations = sum(m.get('total_operations', 0) for m in all_metrics.values())
        total_successful = sum(m.get('success_rate', 0) * m.get('total_operations', 0) for m in all_metrics.values())
        overall_success_rate = (total_successful / total_operations) if total_operations > 0 else 1.0
        
        # Calculate average response time
        avg_response_times = [m.get('avg_duration_seconds', 0) for m in all_metrics.values() if m.get('avg_duration_seconds', 0) > 0]
        overall_avg_response = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
        
        # Determine health status
        health_status = "healthy"
        if overall_success_rate < 0.95:  # Less than 95% success rate
            health_status = "degraded"
        if overall_success_rate < 0.85:  # Less than 85% success rate
            health_status = "unhealthy"
        
        return {
            "success": True,
            "health": {
                "status": health_status,
                "overall_success_rate": overall_success_rate,
                "overall_avg_response_seconds": overall_avg_response,
                "total_operations": total_operations,
                "cache_entries": len(cache._cache),
                "active_circuit_breakers": len([b for b in getattr(__import__('..utils.performance_utils', fromlist=['_circuit_breakers']), '_circuit_breakers', {}).values() if b.state != "CLOSED"]),
                "performance_optimizations_active": True
            },
            "recommendations": []  # Could add performance recommendations based on metrics
        }
    except Exception as e:
        logger.error(f"Failed to get performance health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance health: {str(e)}")


@router.post("/metrics/reset")
async def reset_performance_metrics() -> Dict[str, Any]:
    """Reset all performance metrics."""
    try:
        metrics = get_performance_metrics()
        metrics.reset_metrics()
        
        return {
            "success": True,
            "message": "Performance metrics have been reset"
        }
    except Exception as e:
        logger.error(f"Failed to reset performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.get("/config")
async def get_performance_config() -> Dict[str, Any]:
    """Get current performance configuration settings."""
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        return {
            "success": True,
            "config": {
                "timeouts": {
                    "request_timeout": settings.request_timeout,
                    "rag_pipeline_timeout": settings.rag_pipeline_timeout,
                    "edge_function_timeout": settings.edge_function_timeout,
                    "llm_request_timeout": settings.llm_request_timeout
                },
                "circuit_breaker": {
                    "failure_threshold": settings.circuit_breaker_failure_threshold,
                    "timeout": settings.circuit_breaker_timeout
                },
                "http_pool": {
                    "pool_connections": settings.http_pool_connections,
                    "pool_maxsize": settings.http_pool_maxsize,
                    "max_retries": settings.http_max_retries
                },
                "caching": {
                    "enabled": settings.enable_result_caching,
                    "ttl_seconds": settings.cache_ttl_seconds
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to get performance config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance config: {str(e)}")