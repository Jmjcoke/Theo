"""
Document Editor API Routes
FastAPI router for document editing functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any
import sqlite3
import json
import uuid
from datetime import datetime
import os
import asyncio

from ..middleware.auth_dependencies import get_current_user
from ..models.editor_models import *
from ..services.editor_service import EditorService
from ..services.export_service import ExportService
from ..services.template_service import TemplateService

router = APIRouter(prefix="/api/editor", tags=["Document Editor"])

# Initialize services
editor_service = EditorService()
export_service = ExportService()
template_service = TemplateService()


# Document CRUD Operations
@router.post("/documents", response_model=EditorDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc: CreateEditorDocument, 
    user = Depends(get_current_user)
) -> EditorDocumentResponse:
    """Create a new document"""
    try:
        document = await editor_service.create_document(doc, user["id"])
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create document")


@router.get("/documents", response_model=List[EditorDocumentSummary])
async def list_documents(
    user = Depends(get_current_user),
    document_type: Optional[DocumentType] = Query(None),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[EditorDocumentSummary]:
    """List user's documents with optional filtering"""
    try:
        documents = await editor_service.list_documents(
            user_id=user["id"], 
            document_type=document_type,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.get("/documents/{doc_id}", response_model=EditorDocumentResponse)
async def get_document(
    doc_id: int, 
    user = Depends(get_current_user)
) -> EditorDocumentResponse:
    """Get a specific document by ID"""
    try:
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.put("/documents/{doc_id}", response_model=EditorDocumentResponse)
async def update_document(
    doc_id: int, 
    doc: UpdateEditorDocument, 
    user = Depends(get_current_user)
) -> EditorDocumentResponse:
    """Update an existing document"""
    try:
        document = await editor_service.update_document(doc_id, doc, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update document")


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int, 
    user = Depends(get_current_user)
):
    """Delete a document"""
    try:
        success = await editor_service.delete_document(doc_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document")


# Template Management
@router.get("/templates", response_model=List[EditorTemplateSummary])
async def list_templates(
    user = Depends(get_current_user),
    document_type: Optional[DocumentType] = Query(None)
) -> List[EditorTemplateSummary]:
    """List available templates"""
    try:
        templates = await template_service.list_templates(
            user_id=user["id"],
            document_type=document_type
        )
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")


@router.get("/templates/{template_id}", response_model=EditorTemplateResponse)
async def get_template(
    template_id: str,
    user = Depends(get_current_user)
) -> EditorTemplateResponse:
    """Get a specific template"""
    try:
        template = await template_service.get_template(template_id, user["id"])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve template")


@router.post("/templates", response_model=EditorTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: CreateEditorTemplate,
    user = Depends(get_current_user)
) -> EditorTemplateResponse:
    """Create a custom template"""
    try:
        created_template = await template_service.create_template(template, user["id"])
        return created_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create template")


# Content Processing & AI Integration
@router.post("/documents/{doc_id}/format")
async def format_document(
    doc_id: int,
    format_request: FormatRequest,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Apply natural language formatting to document"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process formatting request
        result = await editor_service.format_document_content(
            doc_id, format_request, user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to format document")


@router.post("/format-template")
async def format_content_with_template(
    request: Dict[str, Any],
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Format existing content according to a template using LLM"""
    try:
        content = request.get("content", "")
        template_type = request.get("template_type", "")
        template_name = request.get("template_name", "")
        template_structure = request.get("template_structure", "")
        title = request.get("title", "")
        
        # Process template formatting request
        result = await editor_service.format_content_with_template(
            content=content,
            template_type=template_type,
            template_name=template_name,
            template_structure=template_structure,
            title=title
        )
        return {"formatted_content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to format content with template: {str(e)}")


@router.post("/documents/{doc_id}/transfer-content")
async def transfer_chat_content(
    doc_id: int,
    transfer: ContentTransfer,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Transfer content from chat to document"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process content transfer
        result = await editor_service.transfer_content(
            doc_id, transfer, user["id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to transfer content")


# Export Operations
@router.post("/documents/{doc_id}/export/{format}")
async def export_document(
    doc_id: int,
    format: ExportFormat,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    include_citations: bool = Query(True),
    custom_styling: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Export document in specified format"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse custom styling if provided
        styling = None
        if custom_styling:
            try:
                styling = json.loads(custom_styling)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid custom styling JSON")
        
        # Start export process
        export_request = ExportRequest(
            format=format,
            include_citations=include_citations,
            custom_styling=styling
        )
        
        export_id = await export_service.start_export(
            doc_id, export_request, user["id"]
        )
        
        # Add background task to process export
        background_tasks.add_task(
            export_service.process_export,
            export_id, document, export_request
        )
        
        return {
            "export_id": export_id,
            "status": "processing",
            "message": "Export started successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start export")


@router.get("/exports/{export_id}/status")
async def get_export_status(
    export_id: int,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get export status"""
    try:
        status_info = await export_service.get_export_status(export_id, user["id"])
        if not status_info:
            raise HTTPException(status_code=404, detail="Export not found")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get export status")


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: int,
    user = Depends(get_current_user)
) -> FileResponse:
    """Download completed export"""
    try:
        file_info = await export_service.get_export_file(export_id, user["id"])
        if not file_info:
            raise HTTPException(status_code=404, detail="Export not found")
        
        if not os.path.exists(file_info["file_path"]):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["filename"],
            media_type=file_info["media_type"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to download export")


# Citation Management
@router.post("/documents/{doc_id}/citations", response_model=CitationResponse)
async def add_citation(
    doc_id: int,
    citation: CreateCitation,
    user = Depends(get_current_user)
) -> CitationResponse:
    """Add a citation to a document"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        created_citation = await editor_service.add_citation(doc_id, citation)
        return created_citation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add citation")


@router.get("/documents/{doc_id}/citations", response_model=List[CitationResponse])
async def get_citations(
    doc_id: int,
    user = Depends(get_current_user)
) -> List[CitationResponse]:
    """Get all citations for a document"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        citations = await editor_service.get_citations(doc_id)
        return citations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve citations")


@router.delete("/citations/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(
    citation_id: int,
    user = Depends(get_current_user)
):
    """Delete a citation"""
    try:
        success = await editor_service.delete_citation(citation_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Citation not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete citation")


# Document Version History
@router.get("/documents/{doc_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    doc_id: int,
    user = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
) -> List[DocumentVersionResponse]:
    """Get document version history"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        versions = await editor_service.get_document_versions(doc_id, limit)
        return versions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve document versions")


@router.post("/documents/{doc_id}/restore/{version_id}")
async def restore_document_version(
    doc_id: int,
    version_id: int,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Restore document to a previous version"""
    try:
        # Verify document ownership
        document = await editor_service.get_document(doc_id, user["id"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        success = await editor_service.restore_document_version(doc_id, version_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {"message": "Document restored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to restore document version")


# Analytics and Statistics
@router.get("/stats/user", response_model=UserDocumentStats)
async def get_user_stats(
    user = Depends(get_current_user)
) -> UserDocumentStats:
    """Get user document statistics"""
    try:
        stats = await editor_service.get_user_stats(user["id"])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics")


# Bulk Operations
@router.post("/documents/bulk")
async def bulk_document_operation(
    operation: BulkDocumentOperation,
    user = Depends(get_current_user)
) -> BulkOperationResult:
    """Perform bulk operations on documents"""
    try:
        result = await editor_service.bulk_document_operation(operation, user["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to perform bulk operation")


# Health check for editor services
@router.get("/health")
async def editor_health_check() -> Dict[str, Any]:
    """Health check for editor services"""
    try:
        # Check database connectivity
        db_status = await editor_service.check_database_health()
        
        # Check export service
        export_status = await export_service.check_health()
        
        # Check template service
        template_status = await template_service.check_health()
        
        overall_status = "healthy" if all([db_status, export_status, template_status]) else "degraded"
        
        return {
            "status": overall_status,
            "services": {
                "database": "healthy" if db_status else "unhealthy",
                "export": "healthy" if export_status else "unhealthy",
                "template": "healthy" if template_status else "unhealthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }