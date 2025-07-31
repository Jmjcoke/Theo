"""
Configuration management for Theo API
Handles environment variables and application settings
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database settings
    database_url: str = Field(default="sqlite:///./theo.db", env="DATABASE_URL")
    
    # JWT settings
    jwt_secret: str = Field(default="dev-secret-key", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # Celery settings
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    
    # AI/LLM settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Supabase settings
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    supabase_edge_function_url: Optional[str] = Field(default=None, env="SUPABASE_EDGE_FUNCTION_URL")
    
    # File upload settings
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_upload_size: int = Field(default=52428800, env="MAX_UPLOAD_SIZE")  # 50MB
    allowed_file_types: str = Field(default="pdf,docx,txt,md", env="ALLOWED_FILE_TYPES")
    upload_scan_enabled: bool = Field(default=True, env="UPLOAD_SCAN_ENABLED")
    
    # Development settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings