"""
Pydantic models for document upload and management.

Defines request/response models for document upload endpoints
with proper validation and serialization.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """Allowed document types."""
    BIBLICAL = "biblical"
    THEOLOGICAL = "theological"


class ProcessingStatus(str, Enum):
    """Document processing status values."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload (form fields only, file handled separately)."""
    document_type: DocumentType = Field(..., description="Type of document: biblical or theological")
    category: Optional[str] = Field(None, max_length=100, description="Optional document category")
    
    @validator('category')
    def validate_category(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else None


class DocumentUploadResponse(BaseModel):
    """Response model for successful document upload."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(..., description="Document type")
    processing_status: ProcessingStatus = Field(..., description="Current processing status")
    uploaded_at: str = Field(..., description="Upload timestamp (ISO format)")
    job_id: str = Field(..., description="Background processing job ID")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the uploaded file")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "genesis_commentary.pdf",
                "document_type": "theological",
                "processing_status": "queued",
                "uploaded_at": "2025-07-23T10:30:00Z",
                "job_id": "456e7890-e89b-12d3-a456-426614174111",
                "file_size": 2048576,
                "mime_type": "application/pdf"
            }
        }


class DocumentMetadata(BaseModel):
    """Document metadata structure."""
    category: Optional[str] = None
    file_extension: Optional[str] = None
    upload_timestamp: Optional[str] = None
    processing_notes: Optional[List[str]] = None
    error: Optional[str] = None


class Document(BaseModel):
    """Complete document model for database representation."""
    id: str = Field(..., description="Document UUID")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    file_path: str = Field(..., description="File storage path")
    document_type: DocumentType = Field(..., description="Document type")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    uploaded_by: str = Field(..., description="User UUID who uploaded the document")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    metadata: Optional[DocumentMetadata] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    id: str
    filename: str
    original_filename: str
    document_type: DocumentType
    processing_status: ProcessingStatus
    uploaded_by: str
    file_size: int
    mime_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class DocumentListPagination(BaseModel):
    """Pagination information for document listing."""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of documents")
    pages: int = Field(..., ge=0, description="Total number of pages")


class DocumentListResult(BaseModel):
    """Complete response for document listing with pagination."""
    documents: List[DocumentListResponse] = Field(..., description="List of documents")
    pagination: DocumentListPagination = Field(..., description="Pagination information")


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion."""
    message: str = Field(..., description="Deletion confirmation message")
    document_id: str = Field(..., description="UUID of deleted document")
    deleted_at: str = Field(..., description="Deletion timestamp (ISO format)")


class DocumentUploadError(BaseModel):
    """Error response model for document upload failures."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "error": "validation_failed",
                "message": "File validation failed: File size exceeds maximum allowed",
                "details": {
                    "validation_errors": ["File size 60MB exceeds maximum 50MB"],
                    "max_file_size": 52428800,
                    "uploaded_file_size": 62914560
                }
            }
        }


class FileValidationResult(BaseModel):
    """Result of file validation process."""
    is_valid: bool = Field(..., description="Whether the file passed validation")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    file_info: Optional[Dict[str, Any]] = Field(None, description="File metadata information")


class JobStatusResponse(BaseModel):
    """Response model for background job status."""
    job_id: str = Field(..., description="Job UUID")
    status: str = Field(..., description="Job status")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Processing progress (0.0-1.0)")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Job creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")