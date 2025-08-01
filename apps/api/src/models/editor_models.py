"""
Data models for the Document Editor Module
Pydantic models for request/response validation and serialization
"""

from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    SERMON = "sermon"
    ARTICLE = "article"
    RESEARCH_PAPER = "research_paper"
    LESSON_PLAN = "lesson_plan"
    DEVOTIONAL = "devotional"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CitationFormat(str, Enum):
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    TURABIAN = "turabian"


class ExportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"


class CommentStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    DELETED = "deleted"


# Request Models
class CreateEditorDocument(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = Field(default="", max_length=100000)
    template_id: Optional[str] = None
    document_type: DocumentType
    metadata: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class UpdateEditorDocument(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, max_length=100000)
    template_id: Optional[str] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v


class CreateEditorTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_content: str = Field(..., min_length=1)
    document_type: DocumentType
    metadata: Optional[Dict[str, Any]] = None


class ContentTransfer(BaseModel):
    """Model for transferring content from chat to editor"""
    source_message_id: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    suggested_template: Optional[str] = None
    title: Optional[str] = None


class FormatRequest(BaseModel):
    """Model for natural language formatting requests"""
    command: str = Field(..., min_length=1, max_length=500)
    selected_text: Optional[str] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None


class CreateCitation(BaseModel):
    source_id: str
    citation_text: str = Field(..., min_length=1)
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    citation_format: CitationFormat = CitationFormat.APA


class CreateComment(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[int] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None


class ExportRequest(BaseModel):
    format: ExportFormat
    include_citations: bool = True
    custom_styling: Optional[Dict[str, Any]] = None


# Response Models
class EditorDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    title: str
    content: str
    template_id: Optional[str]
    document_type: DocumentType
    status: DocumentStatus
    version: int
    word_count: int
    reading_time: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class EditorDocumentSummary(BaseModel):
    """Lightweight document summary for lists"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    document_type: DocumentType
    status: DocumentStatus
    word_count: int
    reading_time: int
    created_at: datetime
    updated_at: datetime


class EditorTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str]
    template_content: str
    document_type: DocumentType
    is_system: bool
    created_by: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


class EditorTemplateSummary(BaseModel):
    """Lightweight template summary for selection"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str]
    document_type: DocumentType
    is_system: bool


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    source_id: str
    citation_text: str
    position_start: Optional[int]
    position_end: Optional[int]
    citation_format: CitationFormat
    created_at: datetime


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    user_id: int
    parent_comment_id: Optional[int]
    content: str
    position_start: Optional[int]
    position_end: Optional[int]
    status: CommentStatus
    created_at: datetime
    # User info would be added via join in the actual implementation
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    version_number: int
    content: str
    change_summary: Optional[str]
    created_at: datetime


class ExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    export_format: ExportFormat
    file_path: str
    file_size: int
    export_status: str
    error_message: Optional[str]
    created_at: datetime


# Utility Models
class DocumentStats(BaseModel):
    """Document statistics for analytics"""
    total_documents: int
    documents_by_type: Dict[str, int]
    documents_by_status: Dict[str, int]
    average_word_count: float
    total_exports: int
    exports_by_format: Dict[str, int]


class TemplateStats(BaseModel):
    """Template usage statistics"""
    total_templates: int
    system_templates: int
    user_templates: int
    usage_by_template: Dict[str, int]
    most_popular_template: Optional[str]


class UserDocumentStats(BaseModel):
    """User-specific document statistics"""
    total_documents: int
    draft_documents: int
    published_documents: int
    total_words_written: int
    average_document_length: float
    most_used_template: Optional[str]
    recent_activity: List[Dict[str, Any]]


# Error Models
class EditorError(BaseModel):
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationError(EditorError):
    field_errors: Dict[str, List[str]]


# Batch Operation Models
class BulkDocumentOperation(BaseModel):
    document_ids: List[int] = Field(..., min_length=1, max_length=100)
    operation: str = Field(..., pattern=r'^(delete|archive|publish|change_status)$')
    parameters: Optional[Dict[str, Any]] = None


class BulkOperationResult(BaseModel):
    successful_ids: List[int]
    failed_ids: List[int]
    errors: Dict[int, str]
    total_processed: int