"""
Configuration Models for Theo

Data models for system configuration management including
settings storage, validation, and audit logging.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ConfigurationCategory(str, Enum):
    """Configuration categories."""
    UPLOAD = "upload"
    SYSTEM = "system"
    PROCESSING = "processing"


class ConfigurationDataType(str, Enum):
    """Configuration value data types."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    JSON = "json"


class SystemConfiguration(BaseModel):
    """System configuration model."""
    id: str
    category: ConfigurationCategory
    key: str
    value: str
    data_type: ConfigurationDataType
    description: str
    is_editable: bool = True
    created_at: datetime
    updated_at: datetime
    updated_by: str


class ConfigurationAudit(BaseModel):
    """Configuration audit log model."""
    id: str
    config_id: str
    old_value: str
    new_value: str
    changed_by: str
    change_reason: str
    created_at: datetime


class ConfigurationUpdate(BaseModel):
    """Request model for configuration updates."""
    category: ConfigurationCategory
    key: str
    value: Any
    change_reason: Optional[str] = "Configuration update"


class SystemConfigurationResponse(BaseModel):
    """Response model for system configuration."""
    configurations: Dict[str, Dict[str, Any]]


class UploadConfiguration(BaseModel):
    """Upload configuration settings."""
    max_file_size_biblical: int = Field(default=5242880, description="Max biblical file size in bytes")
    max_file_size_theological: int = Field(default=104857600, description="Max theological file size in bytes")
    allowed_extensions: List[str] = Field(default=[".json", ".pdf"], description="Allowed file extensions")
    max_daily_uploads: int = Field(default=50, description="Max uploads per user per day")


class SystemSettings(BaseModel):
    """System configuration settings."""
    maintenance_mode: bool = Field(default=False, description="System maintenance mode")
    backup_enabled: bool = Field(default=True, description="Automatic backup enabled")
    backup_frequency: str = Field(default="daily", description="Backup frequency")
    system_version: str = Field(default="1.0.0", description="Current system version")


class ProcessingConfiguration(BaseModel):
    """Processing configuration settings."""
    max_concurrent_jobs: int = Field(default=5, description="Maximum concurrent processing jobs")
    job_timeout_minutes: int = Field(default=30, description="Job timeout in minutes")
    retry_attempts: int = Field(default=3, description="Retry attempts for failed jobs")


class SystemHealthStatus(str, Enum):
    """System health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceStatus(str, Enum):
    """Service status values."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class DatabaseHealth(BaseModel):
    """Database health status."""
    status: ServiceStatus
    response_time: float


class RedisHealth(BaseModel):
    """Redis health status."""
    status: ServiceStatus
    response_time: float


class StorageHealth(BaseModel):
    """Storage health status."""
    status: ServiceStatus
    free_space: str


class SystemHealth(BaseModel):
    """System health information."""
    status: SystemHealthStatus
    uptime: str
    version: str
    database: DatabaseHealth
    redis: RedisHealth
    storage: StorageHealth
    last_updated: datetime


class ConfigurationValidationError(BaseModel):
    """Configuration validation error."""
    field: str
    message: str
    current_value: Any
    suggested_value: Optional[Any] = None