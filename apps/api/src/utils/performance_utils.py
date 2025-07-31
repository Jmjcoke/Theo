"""
Performance utilities for optimizing flow execution.
Provides timeout management, circuit breakers, connection pooling, and caching.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import json

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global HTTP session with connection pooling
_http_session = None

def get_http_session() -> requests.Session:
    """Get a configured HTTP session with connection pooling and retries."""
    global _http_session
    
    if _http_session is None:
        _http_session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=settings.http_max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=settings.http_pool_connections,
            pool_maxsize=settings.http_pool_maxsize,
            max_retries=retry_strategy
        )
        
        _http_session.mount("http://", adapter)
        _http_session.mount("https://", adapter)
        
        logger.info(f"HTTP session configured with {settings.http_pool_connections} pool connections, "
                   f"{settings.http_pool_maxsize} max pool size, {settings.http_max_retries} max retries")
    
    return _http_session


class CircuitBreaker:
    """Simple circuit breaker implementation for external service reliability."""
    
    def __init__(self, failure_threshold: int = None, timeout: int = None, name: str = "default"):
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.timeout = timeout or settings.circuit_breaker_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN state")
                return True
            return False
            
        # HALF_OPEN state
        return True
    
    def record_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info(f"Circuit breaker {self.name} moving to CLOSED state")
    
    def record_failure(self, exception: Exception):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")


# Global circuit breakers for different services
_circuit_breakers = {}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name)
    return _circuit_breakers[name]


class TimeoutManager:
    """Manages timeouts for different operation types."""
    
    @staticmethod
    def get_timeout(operation_type: str) -> int:
        """Get appropriate timeout for operation type."""
        timeout_map = {
            'edge_function': settings.edge_function_timeout,
            'llm_request': settings.llm_request_timeout,
            'rag_pipeline': settings.rag_pipeline_timeout,
            'default': settings.request_timeout
        }
        return timeout_map.get(operation_type, timeout_map['default'])
    
    @staticmethod
    async def with_timeout(coro, operation_type: str = 'default'):
        """Execute coroutine with appropriate timeout."""
        timeout = TimeoutManager.get_timeout(operation_type)
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Operation '{operation_type}' timed out after {timeout}s")
            raise TimeoutError(f"Operation '{operation_type}' timed out after {timeout}s")


class PerformanceCache:
    """Simple in-memory cache for expensive operations."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > settings.cache_ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if not settings.enable_result_caching:
            return None
            
        if key in self._cache and not self._is_expired(key):
            logger.debug(f"Cache hit for key: {key}")
            return self._cache[key]
        
        if key in self._cache:
            # Remove expired entry
            del self._cache[key]
            del self._timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        if not settings.enable_result_caching:
            return
            
        self._cache[key] = value
        self._timestamps[key] = time.time()
        logger.debug(f"Cache set for key: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Performance cache cleared")
    
    def generate_key(self, operation: str, **kwargs) -> str:
        """Generate cache key from operation and parameters."""
        # Create deterministic key from operation and sorted kwargs
        key_data = {
            'operation': operation,
            'params': sorted(kwargs.items()) if kwargs else []
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()


# Global performance cache
_performance_cache = PerformanceCache()

def get_performance_cache() -> PerformanceCache:
    """Get the global performance cache."""
    return _performance_cache


def with_circuit_breaker(service_name: str):
    """Decorator to add circuit breaker protection to functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_breaker = get_circuit_breaker(service_name)
            
            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker {service_name} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure(e)
                raise
                
        return wrapper
    return decorator


def with_performance_monitoring(operation_name: str):
    """Decorator to add performance monitoring to functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Operation '{operation_name}' completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Operation '{operation_name}' failed after {duration:.3f}s: {str(e)}")
                raise
                
        return wrapper
    return decorator


async def execute_with_fallback(primary_func: Callable, fallback_func: Optional[Callable] = None, operation_name: str = "operation"):
    """Execute function with optional fallback on failure."""
    try:
        return await primary_func()
    except Exception as e:
        logger.warning(f"Primary {operation_name} failed: {str(e)}")
        
        if fallback_func:
            try:
                logger.info(f"Attempting fallback for {operation_name}")
                return await fallback_func()
            except Exception as fallback_error:
                logger.error(f"Fallback {operation_name} also failed: {str(fallback_error)}")
                raise fallback_error
        else:
            raise e


class PerformanceMetrics:
    """Track and report performance metrics."""
    
    def __init__(self):
        self._metrics = {}
        self._start_times = {}
    
    def start_operation(self, operation_id: str, operation_type: str):
        """Start tracking an operation."""
        self._start_times[operation_id] = {
            'start_time': time.time(),
            'operation_type': operation_type
        }
    
    def end_operation(self, operation_id: str, success: bool = True, error: str = None):
        """End tracking an operation and record metrics."""
        if operation_id not in self._start_times:
            logger.warning(f"No start time found for operation: {operation_id}")
            return
        
        start_info = self._start_times[operation_id]
        duration = time.time() - start_info['start_time']
        operation_type = start_info['operation_type']
        
        # Initialize metrics for operation type if needed
        if operation_type not in self._metrics:
            self._metrics[operation_type] = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'errors': []
            }
        
        metrics = self._metrics[operation_type]
        metrics['total_operations'] += 1
        metrics['total_duration'] += duration
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        metrics['max_duration'] = max(metrics['max_duration'], duration)
        
        if success:
            metrics['successful_operations'] += 1
        else:
            metrics['failed_operations'] += 1
            if error:
                metrics['errors'].append({
                    'timestamp': time.time(),
                    'error': error,
                    'duration': duration
                })
        
        # Clean up
        del self._start_times[operation_id]
        
        logger.info(f"Operation {operation_type} ({operation_id}) completed in {duration:.3f}s (success: {success})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        summary = {}
        
        for operation_type, metrics in self._metrics.items():
            total_ops = metrics['total_operations']
            if total_ops > 0:
                avg_duration = metrics['total_duration'] / total_ops
                success_rate = metrics['successful_operations'] / total_ops
                
                summary[operation_type] = {
                    'total_operations': total_ops,
                    'success_rate': success_rate,
                    'avg_duration_seconds': avg_duration,
                    'min_duration_seconds': metrics['min_duration'],
                    'max_duration_seconds': metrics['max_duration'],
                    'recent_errors': metrics['errors'][-5:]  # Last 5 errors
                }
        
        return summary
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._metrics.clear()
        self._start_times.clear()
        logger.info("Performance metrics reset")


# Global performance metrics tracker
_performance_metrics = PerformanceMetrics()

def get_performance_metrics() -> PerformanceMetrics:
    """Get the global performance metrics tracker."""
    return _performance_metrics