"""
Chat Request/Response Models for Theo RAG System

Pydantic models for chat interaction with validation and serialization.
Implements the chat API specification from Story 6.1 requirements.
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Literal
import uuid


class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    message: str
    context: Optional[str] = "general"
    sessionId: str
    useAdvancedPipeline: Optional[bool] = True
    
    @field_validator('message')
    @classmethod
    def validate_message_length(cls, v):
        if len(v) > 1000:
            raise ValueError('Message too long')
        if len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        return v.strip()

    @field_validator('sessionId')
    @classmethod
    def validate_session_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid session ID format')
        return v


class DocumentSource(BaseModel):
    """Document source information in chat responses"""
    documentId: str
    title: str
    excerpt: str
    relevance: float
    citation: Optional[str]


class ChatResponse(BaseModel):
    """Response model for chat interactions with intent recognition"""
    response: str
    confidence: float
    sources: List[DocumentSource]
    processingTime: int
    sessionId: str
    messageId: str
    intent: str = "new_query"
    intentConfidence: float = 0.0
    advancedPipeline: Optional[Dict[str, Any]] = None


class FormattingOptions(BaseModel):
    """Formatting options for structured output"""
    useEmojis: bool = True
    bulletStyle: Literal['bullets', 'numbers', 'checkmarks', 'arrows'] = 'bullets'
    includeCallouts: bool = True
    headerStyle: Literal['minimal', 'decorative', 'academic'] = 'normal'
    spacing: Literal['tight', 'normal', 'loose'] = 'normal'


class StructuredFormatRequest(BaseModel):
    """Request model for structured document formatting"""
    content: str
    templateId: str
    formattingOptions: FormattingOptions
    context: Optional[str] = None
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v):
        if len(v) > 50000:  # 50KB limit
            raise ValueError('Content too long')
        if len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        return v.strip()


class StructuredFormatResponse(BaseModel):
    """Response model for structured document formatting"""
    formattedContent: str
    appliedFormatting: List[str]
    templateUsed: str
    processingTime: int
    suggestions: Optional[List[str]] = None