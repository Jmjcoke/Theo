"""
Export API Routes for Theo

Provides protected endpoints for exporting content in various formats.
Includes PDF generation from markdown content with authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from src.middleware.auth_dependencies import require_user_role
from src.nodes.documents.pdf_generator_node import PDFGeneratorNode

router = APIRouter()


class PDFExportRequest(BaseModel):
    """Request model for PDF export endpoint."""
    content: str = Field(..., description="Markdown content to convert to PDF")
    filename: Optional[str] = Field(None, description="Optional custom filename for the PDF")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1_000_000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if v is not None:
            # Basic filename validation
            if len(v) > 255:
                raise ValueError("Filename too long")
            # Remove any potentially dangerous characters
            import re
            if not re.match(r'^[a-zA-Z0-9._-]+$', v.replace(' ', '_')):
                raise ValueError("Invalid filename characters")
        return v


@router.post("/export/pdf")
async def export_pdf(
    request: PDFExportRequest,
    current_user: Dict[str, Any] = Depends(require_user_role)
):
    """
    Export markdown content as PDF file.
    
    Protected endpoint that converts markdown content to a downloadable PDF file.
    Requires valid JWT authentication with user or admin role.
    
    Args:
        request: PDFExportRequest containing markdown content and optional filename
        current_user: Current authenticated user from JWT token
        
    Returns:
        PDF file as downloadable attachment
        
    Raises:
        HTTPException: 400 for invalid content, 500 for generation errors
        HTTPException: 401/403 for authentication/authorization failures
    """
    try:
        # Initialize PDF generator node
        pdf_generator = PDFGeneratorNode()
        
        # Prepare shared store for node execution
        shared_store = {
            "markdown_content": request.content,
            "filename": request.filename
        }
        
        # Execute PDF generation
        result = await pdf_generator.run(shared_store)
        
        # Get generated PDF data
        pdf_buffer = shared_store["pdf_buffer"]
        generated_filename = shared_store["generated_filename"]
        
        # Return PDF as downloadable file
        return Response(
            content=pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{generated_filename}\"",
                "Content-Length": str(len(pdf_buffer))
            }
        )
        
    except ValueError as e:
        # Handle validation errors from the node
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_content",
                "message": str(e),
                "timestamp": "2025-07-27T10:30:00Z"
            }
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "pdf_generation_failed",
                "message": "Unable to generate PDF from provided content",
                "details": str(e),
                "timestamp": "2025-07-27T10:30:00Z"
            }
        )