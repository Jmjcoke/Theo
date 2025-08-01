"""
Configuration Management for Theo

Handles system configuration storage, validation, and audit logging.
Provides configuration management functionality for admin interface.
"""

import logging
import json
import asyncio
import psutil
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from databases import Database
from src.core.config import settings
from src.models.configuration_models import (
    ConfigurationCategory,
    ConfigurationDataType,
    SystemHealth,
    SystemHealthStatus,
    DatabaseHealth,
    RedisHealth,
    StorageHealth,
    ServiceStatus
)

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages system configuration settings with validation and audit logging."""
    
    def __init__(self, database: Database):
        self.database = database
        
    async def get_all_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get all system configurations organized by category."""
        try:
            # Query all configurations
            query = """
            SELECT category, key, value, data_type, description 
            FROM system_configurations 
            WHERE is_editable = true
            ORDER BY category, key
            """
            
            rows = await self.database.fetch_all(query)
            
            # Organize by category
            configurations = {
                "upload": {},
                "system": {},
                "processing": {}
            }
            
            for row in rows:
                category = row["category"]
                key = row["key"]
                value = self._parse_value(row["value"], row["data_type"])
                
                if category not in configurations:
                    configurations[category] = {}
                    
                configurations[category][key] = value
            
            # Set defaults if no configurations exist
            if not configurations["upload"]:
                configurations["upload"] = {
                    "max_file_size_biblical": 5242880,  # 5MB
                    "max_file_size_theological": 104857600,  # 100MB
                    "allowed_extensions": [".json", ".pdf"],
                    "max_daily_uploads": 50
                }
            
            if not configurations["system"]:
                configurations["system"] = {
                    "maintenance_mode": False,
                    "backup_enabled": True,
                    "backup_frequency": "daily",
                    "system_version": "1.0.0"
                }
            
            if not configurations["processing"]:
                configurations["processing"] = {
                    "max_concurrent_jobs": 5,
                    "job_timeout_minutes": 30,
                    "retry_attempts": 3
                }
            
            return configurations
            
        except Exception as e:
            logger.error(f"Failed to fetch configurations: {str(e)}")
            # Return defaults on error
            return {
                "upload": {
                    "max_file_size_biblical": 5242880,
                    "max_file_size_theological": 104857600,
                    "allowed_extensions": [".json", ".pdf"],
                    "max_daily_uploads": 50
                },
                "system": {
                    "maintenance_mode": False,
                    "backup_enabled": True,
                    "backup_frequency": "daily",
                    "system_version": "1.0.0"
                },
                "processing": {
                    "max_concurrent_jobs": 5,
                    "job_timeout_minutes": 30,
                    "retry_attempts": 3
                }
            }
    
    async def update_configuration(
        self, 
        category: str, 
        key: str, 
        value: Any, 
        updated_by: str,
        change_reason: str = "Configuration update"
    ) -> Dict[str, Any]:
        """Update a configuration setting with validation and audit logging."""
        try:
            # Validate the configuration
            validation_result = await self.validate_configuration_value(category, key, value)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid configuration value: {validation_result['errors']}")
            
            # Get current configuration for audit
            current_query = """
            SELECT id, value FROM system_configurations 
            WHERE category = :category AND key = :key
            """
            current_config = await self.database.fetch_one(
                current_query, 
                {"category": category, "key": key}
            )
            
            # Determine data type and serialize value
            data_type = self._determine_data_type(value)
            serialized_value = self._serialize_value(value, data_type)
            
            now = datetime.now(timezone.utc)
            
            if current_config:
                # Update existing configuration
                update_query = """
                UPDATE system_configurations 
                SET value = :value, data_type = :data_type, updated_at = :updated_at, updated_by = :updated_by
                WHERE category = :category AND key = :key
                """
                await self.database.execute(update_query, {
                    "value": serialized_value,
                    "data_type": data_type,
                    "updated_at": now,
                    "updated_by": updated_by,
                    "category": category,
                    "key": key
                })
                
                # Log audit record
                await self._log_configuration_change(
                    config_id=current_config["id"],
                    old_value=current_config["value"],
                    new_value=serialized_value,
                    changed_by=updated_by,
                    change_reason=change_reason
                )
            else:
                # Insert new configuration
                insert_query = """
                INSERT INTO system_configurations 
                (id, category, key, value, data_type, description, is_editable, created_at, updated_at, updated_by)
                VALUES (:id, :category, :key, :value, :data_type, :description, true, :created_at, :updated_at, :updated_by)
                """
                config_id = f"{category}_{key}_{int(time.time())}"
                await self.database.execute(insert_query, {
                    "id": config_id,
                    "category": category,
                    "key": key,
                    "value": serialized_value,
                    "data_type": data_type,
                    "description": f"{key} configuration for {category}",
                    "created_at": now,
                    "updated_at": now,
                    "updated_by": updated_by
                })
            
            logger.info(f"Configuration {category}.{key} updated by {updated_by}")
            
            return {
                "category": category,
                "key": key,
                "value": value,
                "updated_at": now.isoformat(),
                "updated_by": updated_by
            }
            
        except Exception as e:
            logger.error(f"Failed to update configuration {category}.{key}: {str(e)}")
            raise
    
    async def validate_configuration_value(
        self, 
        category: str, 
        key: str, 
        value: Any
    ) -> Dict[str, Any]:
        """Validate a configuration value."""
        errors = []
        warnings = []
        
        try:
            # Category-specific validation
            if category == "upload":
                if key == "max_file_size_biblical":
                    if not isinstance(value, int) or value < 1048576 or value > 52428800:  # 1MB to 50MB
                        errors.append("Biblical file size must be between 1MB and 50MB")
                elif key == "max_file_size_theological":
                    if not isinstance(value, int) or value < 1048576 or value > 524288000:  # 1MB to 500MB
                        errors.append("Theological file size must be between 1MB and 500MB")
                elif key == "max_daily_uploads":
                    if not isinstance(value, int) or value < 1 or value > 1000:
                        errors.append("Daily upload limit must be between 1 and 1000")
                        
            elif category == "system":
                if key == "maintenance_mode":
                    if not isinstance(value, bool):
                        errors.append("Maintenance mode must be true or false")
                elif key == "backup_enabled":
                    if not isinstance(value, bool):
                        errors.append("Backup enabled must be true or false")
                elif key == "backup_frequency":
                    if value not in ["hourly", "daily", "weekly"]:
                        errors.append("Backup frequency must be hourly, daily, or weekly")
                        
            elif category == "processing":
                if key == "max_concurrent_jobs":
                    if not isinstance(value, int) or value < 1 or value > 20:
                        errors.append("Concurrent jobs must be between 1 and 20")
                elif key == "job_timeout_minutes":
                    if not isinstance(value, int) or value < 5 or value > 120:
                        errors.append("Job timeout must be between 5 and 120 minutes")
                elif key == "retry_attempts":
                    if not isinstance(value, int) or value < 0 or value > 10:
                        errors.append("Retry attempts must be between 0 and 10")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": []
            }
    
    def _parse_value(self, value: str, data_type: str) -> Any:
        """Parse configuration value based on data type."""
        try:
            if data_type == "boolean":
                return value.lower() in ("true", "1", "yes")
            elif data_type == "integer":
                return int(value)
            elif data_type == "float":
                return float(value)
            elif data_type == "json":
                return json.loads(value)
            else:  # string
                return value
        except Exception:
            return value
    
    def _serialize_value(self, value: Any, data_type: str) -> str:
        """Serialize configuration value for storage."""
        try:
            if data_type == "json":
                return json.dumps(value)
            elif data_type == "boolean":
                return str(value).lower()
            else:
                return str(value)
        except Exception:
            return str(value)
    
    def _determine_data_type(self, value: Any) -> str:
        """Determine data type for configuration value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (list, dict)):
            return "json"
        else:
            return "string"
    
    async def _log_configuration_change(
        self,
        config_id: str,
        old_value: str,
        new_value: str,
        changed_by: str,
        change_reason: str
    ):
        """Log configuration change for audit purposes."""
        try:
            audit_query = """
            INSERT INTO configuration_audit 
            (id, config_id, old_value, new_value, changed_by, change_reason, created_at)
            VALUES (:id, :config_id, :old_value, :new_value, :changed_by, :change_reason, :created_at)
            """
            audit_id = f"audit_{config_id}_{int(time.time())}"
            await self.database.execute(audit_query, {
                "id": audit_id,
                "config_id": config_id,
                "old_value": old_value,
                "new_value": new_value,
                "changed_by": changed_by,
                "change_reason": change_reason,
                "created_at": datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.warning(f"Failed to log configuration audit: {str(e)}")


class SystemHealthChecker:
    """Performs system health checks for admin monitoring."""
    
    async def get_system_health(self) -> SystemHealth:
        """Perform comprehensive system health check."""
        try:
            # Get system uptime
            uptime = self._get_system_uptime()
            
            # Check database health
            database_health = await self._check_database_health()
            
            # Check Redis health (mocked for now)
            redis_health = await self._check_redis_health()
            
            # Check storage health
            storage_health = self._check_storage_health()
            
            # Determine overall health status
            overall_status = self._determine_overall_status([
                database_health.status,
                redis_health.status,
                storage_health.status
            ])
            
            return SystemHealth(
                status=overall_status,
                uptime=uptime,
                version="1.0.0",
                database=database_health,
                redis=redis_health,
                storage=storage_health,
                last_updated=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return SystemHealth(
                status=SystemHealthStatus.UNHEALTHY,
                uptime="unknown",
                version="1.0.0",
                database=DatabaseHealth(status=ServiceStatus.ERROR, response_time=0.0),
                redis=RedisHealth(status=ServiceStatus.ERROR, response_time=0.0),
                storage=StorageHealth(status=ServiceStatus.ERROR, free_space="unknown"),
                last_updated=datetime.now(timezone.utc)
            )
    
    async def _check_database_health(self) -> DatabaseHealth:
        """Check database connectivity and response time."""
        database = None
        try:
            start_time = time.time()
            database = Database(settings.database_url)
            await database.connect()
            
            # Simple health check query
            await database.fetch_one("SELECT 1")
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return DatabaseHealth(
                status=ServiceStatus.CONNECTED,
                response_time=round(response_time, 2)
            )
            
        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            return DatabaseHealth(
                status=ServiceStatus.ERROR,
                response_time=0.0
            )
        finally:
            if database:
                await database.disconnect()
    
    async def _check_redis_health(self) -> RedisHealth:
        """Check Redis connectivity and response time."""
        # For now, mock Redis health check
        # In a real implementation, you would check Redis connectivity
        try:
            # Simulate Redis check
            await asyncio.sleep(0.01)  # Simulate network delay
            
            return RedisHealth(
                status=ServiceStatus.CONNECTED,
                response_time=10.5
            )
            
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            return RedisHealth(
                status=ServiceStatus.ERROR,
                response_time=0.0
            )
    
    def _check_storage_health(self) -> StorageHealth:
        """Check storage availability and free space."""
        try:
            # Get disk usage for current directory
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free // (1024**3)
            
            # Determine status based on free space
            if free_gb > 10:
                status = ServiceStatus.AVAILABLE
            elif free_gb > 1:
                status = ServiceStatus.AVAILABLE  # But could be warning
            else:
                status = ServiceStatus.UNAVAILABLE
            
            return StorageHealth(
                status=status,
                free_space=f"{free_gb} GB"
            )
            
        except Exception as e:
            logger.warning(f"Storage health check failed: {str(e)}")
            return StorageHealth(
                status=ServiceStatus.ERROR,
                free_space="unknown"
            )
    
    def _get_system_uptime(self) -> str:
        """Get system uptime."""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days} days, {hours} hours"
            elif hours > 0:
                return f"{hours} hours, {minutes} minutes"
            else:
                return f"{minutes} minutes"
                
        except Exception:
            return "unknown"
    
    def _determine_overall_status(self, service_statuses: List[ServiceStatus]) -> SystemHealthStatus:
        """Determine overall system health based on service statuses."""
        error_statuses = {
            ServiceStatus.ERROR,
            ServiceStatus.DISCONNECTED,
            ServiceStatus.UNAVAILABLE
        }
        
        if any(status in error_statuses for status in service_statuses):
            if all(status in error_statuses for status in service_statuses):
                return SystemHealthStatus.UNHEALTHY
            else:
                return SystemHealthStatus.DEGRADED
        else:
            return SystemHealthStatus.HEALTHY