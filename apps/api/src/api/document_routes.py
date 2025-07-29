"""
Document upload API routes.

Provides admin endpoints for document upload with multipart/form-data support
and integration with DocumentUploadFlow.
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from databases import Database
import os
from src.flows.document_upload_flow import DocumentUploadFlow
from src.middleware.auth_dependencies import require_admin_role
from src.core.config import get_settings
from src.core.redis_client import get_redis
from src.core.celery_app import celery_app


router = APIRouter(prefix="/api/admin", tags=["document-upload"])
security = HTTPBearer()


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    documentId: str
    filename: str
    documentType: str
    processingStatus: str
    uploadedAt: str
    jobId: str
    fileSize: int
    mimeType: str


class DocumentUploadError(BaseModel):
    """Error response model for document upload."""
    error: str
    message: str
    details: Optional[dict] = None


async def get_database() -> Database:
    """Get database connection."""
    from src.core.config import settings
    from databases import Database
    
    database = Database(settings.database_url)
    await database.connect()
    return database


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={
        400: {"model": DocumentUploadError, "description": "Validation error"},
        401: {"model": DocumentUploadError, "description": "Authentication required"},
        403: {"model": DocumentUploadError, "description": "Admin role required"},
        413: {"model": DocumentUploadError, "description": "File too large"},
        422: {"model": DocumentUploadError, "description": "Invalid file type"},
        500: {"model": DocumentUploadError, "description": "Upload failed"}
    },
    summary="Upload document for processing",
    description="Standardized document upload endpoint with enhanced validation and reliability."
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT, MD)"),
    documentType: str = Form(..., description="Document type: 'biblical' or 'theological'"),
    category: Optional[str] = Form(None, description="Optional document category"),
    current_user = Depends(require_admin_role)
):
    """
    Standardized document upload endpoint.
    
    This endpoint redirects to the enhanced simple upload system which provides:
    - Comprehensive file validation (type, size, MIME type, security)
    - Secure file storage with unique naming
    - Proper error handling with specific error codes
    - Database record creation with detailed metadata
    
    **Authentication:** Requires admin role JWT token in Authorization header.
    
    **File Requirements:**
    - Maximum size: 50MB
    - Supported types: PDF, DOCX, TXT, MD
    - File must not be empty
    - MIME type must match file extension
    
    **Response:**
    Returns document metadata and processing information on success.
    """
    # Import the enhanced upload function
    try:
        from src.api.simple_document_upload import upload_document as enhanced_upload
        
        # Redirect to enhanced upload endpoint
        result = await enhanced_upload(
            background_tasks=background_tasks,
            file=file,
            documentType=documentType,
            category=category,
            current_user=current_user
        )
        
        # Convert response to match expected format
        return DocumentUploadResponse(
            documentId=str(result["documentId"]),
            filename=result["filename"],
            documentType=result["documentType"],
            processingStatus=result["processingStatus"],
            uploadedAt=result["uploadedAt"],
            jobId="enhanced-upload",  # No separate job ID in enhanced system
            fileSize=result["fileSize"],
            mimeType=result["mimeType"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "upload_redirect_failed",
                "message": f"Failed to process upload: {str(e)}",
                "details": None
            }
        )




@router.post(
    "/upload-legacy",
    response_model=DocumentUploadResponse,
    responses={
        400: {"model": DocumentUploadError, "description": "Validation error"},
        401: {"model": DocumentUploadError, "description": "Authentication required"},
        403: {"model": DocumentUploadError, "description": "Admin role required"},
        413: {"model": DocumentUploadError, "description": "File too large"},
        422: {"model": DocumentUploadError, "description": "Invalid file type"},
        500: {"model": DocumentUploadError, "description": "Upload failed"}
    },
    summary="[DEPRECATED] Legacy document upload with complex flow",
    description="[DEPRECATED] This endpoint uses complex flows and has known issues. Use /api/admin/upload instead.",
    deprecated=True
)
async def upload_document_legacy(
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT, MD)"),
    documentType: str = Form(..., description="Document type: 'biblical' or 'theological'"),
    category: Optional[str] = Form(None, description="Optional document category"),
    current_user = Depends(require_admin_role),
    database: Database = Depends(get_database)
):
    """
    Upload a document file for background processing.
    
    This endpoint:
    1. Validates the uploaded file and metadata
    2. Stores the file securely with a unique filename
    3. Creates a database record with 'queued' status
    4. Dispatches a background job for document processing
    5. Returns upload confirmation with document ID and job ID
    
    **Authentication:** Requires admin role JWT token in Authorization header.
    
    **File Requirements:**
    - Maximum size: 50MB
    - Supported types: PDF, DOCX, TXT, MD
    - File must not be empty
    
    **Request Body (multipart/form-data):**
    - `file`: The document file to upload
    - `documentType`: Either 'biblical' or 'theological'
    - `category`: Optional category for organization
    
    **Response:**
    Returns document metadata and processing information on success.
    """
    settings = get_settings()
    
    try:
        # Initialize upload flow
        upload_flow = DocumentUploadFlow(
            database=database,
            celery_app=celery_app,
            upload_dir=settings.upload_dir
        )
        
        # Prepare shared store for flow
        shared_store = {
            'uploaded_file': file,
            'document_type': documentType,
            'category': category,
            'uploaded_by': current_user['user_id'],
            'upload_dir': settings.upload_dir,
            'max_file_size': settings.max_upload_size,
            'allowed_extensions': settings.allowed_file_types.split(','),
            'database': database,
            'celery_app': celery_app
        }
        
        # Execute upload flow
        result = await upload_flow.run_async(shared_store)
        
        if result['upload_success']:
            return DocumentUploadResponse(
                documentId=result['document_id'],
                filename=result['filename'],
                documentType=result['document_type'],
                processingStatus=result['processing_status'],
                uploadedAt=result['uploaded_at'],
                jobId=result['job_id'],
                fileSize=result['file_size'],
                mimeType=result['mime_type']
            )
        else:
            # Handle different error types with appropriate HTTP status codes
            error_type = result.get('error_type', 'unknown_error')
            error_message = result.get('error_message', 'Upload failed')
            
            if error_type == 'validation_failed':
                status_code = 422 if 'not allowed' in error_message else 413
            elif error_type == 'storage_failed':
                status_code = 500
            elif error_type == 'job_dispatch_failed':
                status_code = 500
            else:
                status_code = 500
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": error_type,
                    "message": error_message,
                    "details": {
                        "validation_errors": result.get('validation_errors'),
                        "storage_error": result.get('storage_error'),
                        "dispatch_error": result.get('dispatch_error')
                    }
                }
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": f"Unexpected error during upload: {str(e)}",
                "details": None
            }
        )


@router.get(
    "/documents",
    summary="List uploaded documents",
    description="Get a list of all uploaded documents with pagination. Requires admin role."
)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user = Depends(require_admin_role),
    database: Database = Depends(get_database)
):
    """
    List uploaded documents with pagination and filtering.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 20, max: 100)
    - `status`: Filter by processing status ('queued', 'processing', 'completed', 'failed')
    - `document_type`: Filter by document type ('biblical', 'theological')
    """
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Build query with filters
    where_clauses = []
    params = {'limit': limit, 'offset': offset}
    
    if status:
        where_clauses.append("processing_status = :status")
        params['status'] = status
    
    if document_type:
        where_clauses.append("document_type = :document_type")
        params['document_type'] = document_type
    
    where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Get documents
    query = f"""
    SELECT id, filename, original_filename, document_type, processing_status,
           uploaded_by, file_size, mime_type, metadata, created_at, updated_at
    FROM documents
    {where_clause}
    ORDER BY created_at DESC
    LIMIT :limit OFFSET :offset
    """
    
    documents = await database.fetch_all(query, params)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM documents{where_clause}"
    count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
    total_result = await database.fetch_one(count_query, count_params)
    total = total_result['total'] if total_result else 0
    
    return {
        "documents": [dict(doc) for doc in documents],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.delete(
    "/documents/{document_id}",
    summary="Delete uploaded document",
    description="Delete a document and its associated file. Requires admin role."
)
async def delete_document(
    document_id: str,
    current_user = Depends(require_admin_role),
    database: Database = Depends(get_database)
):
    """
    Delete a document and its associated file.
    
    **Path Parameters:**
    - `document_id`: UUID of the document to delete
    """
    # Get document info
    query = "SELECT file_path FROM documents WHERE id = :document_id"
    document = await database.fetch_one(query, {'document_id': document_id})
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "document_not_found",
                "message": f"Document with ID {document_id} not found"
            }
        )
    
    try:
        # Delete file if it exists
        if document['file_path'] and os.path.exists(document['file_path']):
            os.remove(document['file_path'])
        
        # Delete database record
        delete_query = "DELETE FROM documents WHERE id = :document_id"
        await database.execute(delete_query, {'document_id': document_id})
        
        return {
            "message": "Document deleted successfully",
            "documentId": document_id,
            "deletedAt": "2025-07-23T10:35:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "deletion_failed",
                "message": f"Failed to delete document: {str(e)}"
            }
        )


